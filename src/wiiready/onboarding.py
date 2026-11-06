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
    questions = [question for key, (_, question) in FIELDS.items()
                 if values[key] == 'unknown' and not (values['model'] == 'mini' and key in ('sd', 'storage'))]
    if values['model'] == 'mini' and values['storage'] == 'unknown':
        questions.append('What USB storage do you have for the Wii mini? It has no SD slot.')
    if menu == 'unknown':
        primary_unknowns = sum(values[key] == 'unknown' for key in ('model', 'computer', 'homebrew'))
        questions.insert(primary_unknowns, 'What full version appears at the top right of Wii Settings (for example 4.3E)? Do not update just to match an example.')
    route, url = 'Identify your console before choosing an exploit.', GUIDE + 'get-started'
    model = values['model']
    if values['homebrew'] == 'yes':
        route = 'Already modded: inventory the existing setup first. Do not rerun an exploit or replace cIOS blindly.'
    elif values['homebrew'] == 'unknown':
        route = 'Check whether Homebrew Channel already opens before choosing a fresh-install route.'
    elif model in ('mini', 'vwii', 'family'):
        route = {'mini': 'Wii mini: use the dedicated BlueBomb guide; WiiReady installation and package preparation stay blocked.',
                 'vwii': 'Wii U: use the dedicated vWii route; never use original-Wii IOS or recovery instructions.',
                 'family': 'Family Edition: review its route in Get Started; WiiReady installation and package preparation stay blocked.'}[model]
        if model == 'mini':
            url = GUIDE + 'bluebomb'
    elif model == 'original':
        if values['homebrew'] == 'unknown' or menu == 'unknown':
            route = 'Confirm menu and existing homebrew before choosing a fresh-install route.'
        elif int(menu[0]) < 3:
            route = 'This pre-3.0 menu is outside the reviewed Wilbrand route. Review the current guide; do not update or run an exploit automatically.'
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
    if model == 'mini':
        notes.append('Wii mini has no SD slot. SD storage cannot be used directly; use its dedicated USB-based guide. WiiReady preparation remains blocked.')
        if values['storage'] == 'sd':
            notes.append('Your SD choice does not fit a stock Wii mini; revise the storage choice before proceeding.')
    if values['storage'] == 'usb-flash':
        alternative = 'a USB hard drive' if model == 'mini' else 'SD or a USB hard drive'
        notes.append('Choose ' + alternative + ' instead if possible: USB flash-drive reliability is unpredictable.')
    if values['storage'] == 'sd' and model != 'mini':
        notes.append('Current USB Loader GX supports Wii games on SD. The existing disk planner is USB-oriented; do not fabricate a passing inspection for SD.')
    if values['computer'] == 'windows':
        notes.append('WiiReady destination preparation requires POSIX; Windows users use the reviewed guide/ModMii workflow, not a guessed drive mapping.')
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



def shopping():
    """Start before a console exists, without manufacturing installation evidence."""
    return {'status': 'shopping',
            'route': {'instruction': 'Choose gear before choosing an exploit. Reuse what you own.',
                      'source': GUIDE + 'get-started'},
            'questions': ['What country are you buying in, and what is your total budget?',
                          'What computer, TV inputs, controllers, cables and storage do you already have?',
                          'Do you want Wii games only, or GameCube too, including your own discs and controllers?'],
            'notes': ['Use docs/buying.md for the basket and tradeoffs; check current listings and return policies before naming products.',
                      'An original RVL-001 with a working disc drive and matching power supply is the starting suggestion, not an observed console or compatibility guarantee.',
                      'Confirm included Wii Remote, Nunchuk, sensor bar, cables and storage before buying duplicates. Avoid paying for preloaded games.',
                      'Once you have the console, run start without --shopping and identify its actual model/menu before setup.'],
            'reference_plan_scope': False, 'write_authorized': False, 'installation_supported': False,
            'next': 'Your assistant should compare a short list against your budget and existing gear. No purchase, exploit or installation is authorized.'}


def render(result):
    lines = ['WiiReady — start here', '', result['route']['instruction'], result['route']['source']]
    if result['questions']:
        lines += ['', 'Ask next:'] + ['- ' + q for q in result['questions'][:3]]
        if len(result['questions']) > 3:
            lines.append('Then collect the remaining setup details with your assistant; unknown video settings stay unchanged.')
    lines += ['', 'For this setup:'] + ['- ' + note for note in result['notes']]
    return '\n'.join(lines + ['', result['next']])
