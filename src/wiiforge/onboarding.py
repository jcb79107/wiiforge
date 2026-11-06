"""Read-only intake: route observations to guidance, never to automatic installation."""
import re

GUIDE = 'https://wii.hacks.guide/'
FIELDS = {
    'model': (['original', 'family', 'mini', 'vwii', 'unknown'],
              'What console label do you see: RVL-001 (original), RVL-101 (Family), RVL-201 (mini), or Wii U? Do not share its serial.'),
    'computer': (['windows', 'macos', 'linux', 'unknown'], 'Which computer can you use: Windows, macOS or Linux?'),
    'homebrew': (['yes', 'no', 'unknown'], 'Does the Homebrew Channel open? Existing mods need an inventory before changes.'),
    'sd': (['yes', 'no', 'unknown'], 'Do you have an SD card and a computer card reader?'),
    'storage': (['sd', 'usb-hdd', 'usb-ssd', 'usb-flash', 'unknown'], 'Will games live on SD, a USB hard drive, SSD or flash drive?'),
    'display': (['crt', 'hd', 'unknown'], 'Is the TV a CRT or a modern display? Check its actual input sockets.'),
    'cable': (['composite', 'rgb', 'component', 'adapter', 'unknown'], 'Which cable connects the Wii to the TV? Identify any HDMI adapter separately.'),
    'gamecube': (['yes', 'no', 'unknown'], 'Do you want GameCube games as well as Wii games?'),
}


def start(answers=None):
    if answers is None:
        answers = {}
    if not isinstance(answers, dict) or set(answers) - (set(FIELDS) | {'menu'}):
        raise ValueError('Intake accepts only model, menu, computer, homebrew, sd, storage, display, cable and gamecube')
    values = {key: answers.get(key, 'unknown') for key in FIELDS}
    for key, (choices, _) in FIELDS.items():
        if values[key] not in choices:
            raise ValueError('Invalid intake ' + key)
    menu = answers.get('menu', 'unknown')
    if not isinstance(menu, str) or not re.fullmatch(r'unknown|[1-4]\.[0-3][UEJK]', menu):
        raise ValueError('Menu must be the observed version and region, such as 4.3U, or unknown')
    values['menu'] = menu
    questions = [question for key, (_, question) in FIELDS.items() if values[key] == 'unknown']
    if menu == 'unknown':
        questions.insert(1, 'What full version appears at the top right of Wii Settings (for example 4.3E)? Do not update just to match an example.')
    route, url = 'Identify your console before choosing an exploit.', GUIDE + 'get-started'
    model = values['model']
    if model in ('mini', 'vwii', 'family'):
        route = {'mini': 'Wii mini: use the dedicated BlueBomb guide; WiiForge installation and package preparation stay blocked.',
                 'vwii': 'Wii U: use the dedicated vWii route; never use original-Wii IOS or recovery instructions.',
                 'family': 'Family Edition: review its route in Get Started; WiiForge installation and package preparation stay blocked.'}[model]
        if model == 'mini':
            url = GUIDE + 'bluebomb'
    elif model == 'original':
        if values['homebrew'] == 'yes':
            route = 'Already modded: inventory the existing setup first. Do not rerun an exploit or replace cIOS blindly.'
        elif values['homebrew'] == 'unknown' or menu == 'unknown':
            route = 'Confirm menu and existing homebrew before choosing a fresh-install route.'
        elif values['computer'] == 'windows':
            route, url = 'Review ModMii for guided Windows preparation; approve running it separately and follow its generated guide.', GUIDE + 'modmii'
        elif values['computer'] in ('macos', 'linux') and values['sd'] == 'yes' and int(menu[0]) >= 3:
            route, url = 'Review Wilbrand for SD-card setup using the actual menu/region. Keep the required MAC address private.', GUIDE + 'wilbrand'
        elif values['sd'] == 'no':
            route = 'Review the no-SD route in Get Started, but arrange appropriate storage for recovery before proceeding.'
    notes = ['No installation or media writes are authorized by this intake.',
             'Preserve current video settings. Optional autoboot comes after recovery and actual gameplay tests.']
    if menu != 'unknown' and int(menu[0]) < 4 and model in ('original', 'family'):
        notes.append('Before System Menu 4.0, the stock menu needs an SD card of 2 GB or less; do not buy a larger card for the exploit stage.')
    if values['storage'] == 'usb-flash':
        notes.append('Choose SD or a USB hard drive instead if possible: USB flash-drive reliability is unpredictable.')
    if values['storage'] == 'sd':
        notes.append('Current USB Loader GX supports Wii games on SD. The existing disk planner is USB-oriented; do not fabricate a passing inspection for SD.')
    if values['computer'] == 'windows':
        notes.append('WiiForge destination preparation requires POSIX; Windows users use the reviewed guide/ModMii workflow, not a guessed drive mapping.')
    if values['gamecube'] == 'yes':
        notes.append('Review Nintendont, controller support and saves separately. A stock Family Edition, mini or vWii cannot dump GameCube discs.')
    if values['cable'] == 'adapter':
        notes.append('Identify the adapter and TV input support before changing output; an HDMI plug does not prove 480p compatibility.')
    region = menu[-1] if menu != 'unknown' else 'unknown'
    profile = {'schema': 1, 'model': model, 'region': region, 'display': values['display'],
               'cable': values['cable'], 'output': 'preserve', 'aspect': 'preserve',
               'loader': 'usb-loader-gx', 'autoboot': 'off',
               'gamecube': 'review' if values['gamecube'] == 'yes' else 'off'}
    evidence = {'schema': 1, 'model': model, 'model_source': 'unknown' if model == 'unknown' else 'user-observation',
                'region': region, 'region_source': 'unknown' if region == 'unknown' else 'user-observation', 'menu': menu}
    return {'status': 'questions-remain' if questions else 'guide-review', 'observations': values,
            'questions': questions, 'route': {'instruction': route, 'source': url}, 'notes': notes,
            'profile_draft': profile, 'evidence_draft': evidence,
            'reference_plan_scope': model == 'original' and menu == '4.3U',
            'write_authorized': False, 'installation_supported': False,
            'next': 'Read docs/playbook.md with your assistant; answer only from observation. Drafts are not inspection or test evidence.'}


def render(result):
    lines = ['WiiForge — start here', '', result['route']['instruction'], result['route']['source']]
    if result['questions']:
        lines += ['', 'Ask next:'] + ['- ' + q for q in result['questions']]
    lines += ['', 'For this setup:'] + ['- ' + note for note in result['notes']]
    return '\n'.join(lines + ['', result['next']])
