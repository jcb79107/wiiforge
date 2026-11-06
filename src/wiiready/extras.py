"""Opt-in emulator handoffs, independent of core console progress. No downloads/writes."""
from .prepare import require

GUIDE = 'https://wiki.hacks.guide/wiki/Wii:Emulators'
# Selection aids, not package pins or hardware-compatibility claims.
OPTIONS = {
    'nes': ('NES / Famicom', 'FCE Ultra GX', 'https://github.com/dborth/fceugx',
            'Check mapper support; Famicom Disk System needs its own lawful BIOS.'),
    'snes': ('SNES / Super Famicom', 'Snes9x GX', 'https://github.com/dborth/snes9xgx',
             'Check the chosen game, including special-chip requirements.'),
    'n64': ('Nintendo 64', 'Not64', 'https://github.com/extremscorner/not64',
            'Performance and compatibility vary by game; Wii64 is another guide-listed option.'),
    'sega': ('Genesis / Mega Drive, Master System, Game Gear, SG-1000, Sega CD',
             'Genesis Plus GX', 'https://github.com/ekeeke/Genesis-Plus-GX',
             'No 32X support. Sega CD needs a lawful matching BIOS and correctly paired disc files.'),
    '32x': ('Sega 32X', 'RetroArch Wii / PicoDrive', GUIDE,
            'Review the current Wii core and target game; do not substitute Genesis Plus GX.'),
    'gb': ('Game Boy / Game Boy Color', 'mGBA Wii build', 'https://mgba.io/downloads.html',
           'Select the Wii build, then check controls and save support for the game.'),
    'gba': ('Game Boy Advance', 'mGBA Wii build', 'https://mgba.io/downloads.html',
            'Select the Wii build; performance varies. Do not download a BIOS bundle.'),
    'ps1': ('PlayStation', 'WiiStation', 'https://github.com/xjsxjs197/WiiSXRX_2022/releases',
            'Per-game compatibility and performance review first; BIOS and disc requirements vary.'),
    'ds': ('Nintendo DS', 'DeSmuME Wii', GUIDE,
           'Limited/slow for many games. Review the specific game before spending time on setup.'),
    'arcade': ('Arcade', 'MAME-Wii or a suitable Wii core', GUIDE,
               'Name the game first. Match the exact emulator/core ROM-set version; no universal arcade pack.'),
    'dos': ('DOS', 'DOSBox Wii', 'https://oscwii.org/library/app/dosbox-wii',
            'Review input devices, game configuration and speed; not a general Windows PC replacement.'),
    'c64': ('Commodore 64', 'Frodo', GUIDE,
            'Review keyboard/controller mapping and disk/tape format for the chosen game.'),
    'other': ('Other systems', 'Choose from the guide after naming the system/game', GUIDE,
              'Do not promise unsupported systems or install a multi-system bundle by default.'),
}


def extras(systems=(), model='unknown', skip=False):
    require(model in ('original', 'family', 'mini', 'vwii', 'unknown'), 'Unknown console model')
    require(not (skip and systems), 'Choose systems or skip, not both')
    require(all(system in OPTIONS for system in systems), 'Unknown optional system')
    selected = list(dict.fromkeys(systems))
    model_note = {
        'mini': 'Wii mini has no SD slot. Verify USB support in this app before preparing files.',
        'vwii': 'Use the Wii build (.dol), not a native Wii U .wuhb; review vWii support for this app.',
        'unknown': 'Identify the console before choosing storage or preparing files.',
    }.get(model, 'Use the upstream Wii build and confirm its storage requirements.')
    paths = []
    for system in selected:
        title, app, source, limitation = OPTIONS[system]
        paths.append({'system': system, 'title': title, 'candidate': app, 'source': source,
                      'limitation': limitation, 'model_note': model_note, 'status': 'guide-review-required',
                      'steps': ['Confirm console model, working Homebrew Channel, controller and one lawful game.',
                                'Read current upstream Wii instructions; review release origin, license, storage layout and any BIOS requirement.',
                                'Review an exact file plan and obtain approval before guide-specific preparation; preserve existing apps/saves.',
                                'Launch from Homebrew Channel; test controls, gameplay, save and reload. Stop on errors.'],
                      'automated_preparation': False})
    return {'status': 'skipped' if skip else ('guide-review' if paths else 'choose-or-skip'),
            'available': {key: value[0] for key, value in OPTIONS.items()}, 'selected': paths,
            'model': model, 'source': GUIDE, 'write_authorized': False, 'installation_supported': False,
            'core_progress_changed': False,
            'notice': 'Optional guidance only; no packages, games or BIOS are downloaded, copied or run. These paths are not hardware-tested. Select only what you want; skipping leaves Wii/GameCube progress unchanged.'}


def render_extras(result):
    if result['status'] == 'skipped':
        return 'Extra systems skipped. Continue with Wii and GameCube.'
    if not result['selected']:
        return 'Optional systems (choose any or skip):\n' + '\n'.join(
            key + ': ' + title for key, title in result['available'].items()) + '\nUse extras --system NAME (repeat for more), or extras --skip.'
    lines = []
    for path in result['selected']:
        lines += [path['title'] + ' — ' + path['candidate'], path['source'], path['limitation'], path['model_note']]
        lines += [str(n) + '. ' + step for n, step in enumerate(path['steps'], 1)]
        lines.append('')
    return '\n'.join(lines + [result['notice']])
