"""Small read-only GameCube header/layout check; never a dump integrity check."""
import os
from pathlib import Path
import re
import stat

from .prepare import require

HEADER_BYTES = 0x460
DISC_BYTES = 1459978240
SOURCE = 'https://github.com/FIX94/Nintendont#quick-installation'


def _header(path, disc_number):
    path = Path(path)
    require(path.suffix.lower() in ('.iso', '.gcm'),
            'Select a raw ISO/GCM dump; renaming compressed files is not conversion')
    try:
        # Inspect before opening to avoid special files on hosts without O_NONBLOCK.
        selected = path.lstat()
        require(stat.S_ISREG(selected.st_mode), 'Select a regular image file, not a link or device')
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_BINARY', 0) |
                     getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
        with os.fdopen(fd, 'rb', buffering=0) as source:
            before = os.fstat(source.fileno())
            require(stat.S_ISREG(before.st_mode) and
                    (selected.st_dev, selected.st_ino) == (before.st_dev, before.st_ino),
                    'Selected image changed before reading')
            require(HEADER_BYTES <= before.st_size <= DISC_BYTES,
                    'Image size is outside this raw GameCube check; review the dump before proceeding')
            header = source.read(HEADER_BYTES)
            after = os.fstat(source.fileno())
        require(len(header) == HEADER_BYTES and
                (before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'Image changed while reading')
    except OSError as exc:
        raise ValueError('Cannot read the selected game image; inspect the private file locally') from exc
    require(header[0x1c:0x20] == bytes.fromhex('c2339f3d') and
            header[0x18:0x1c] == bytes(4) and header[0x200:0x204] != b'NKIT',
            'Not a supported raw GameCube header; Wii, NKit and compressed images need a different workflow')
    require(re.fullmatch(rb'[A-Za-z0-9]{6}', header[:6]) is not None, 'Unsupported GameCube game ID')
    require(header[:6] not in (b'COBRAM', b'GGCOSD', b'RGCOSD') and
            not (header[:3] == b'GCO' and header[4:6] == b'DV'),
            'Multi-game compilations are outside this single-game check')
    require(header[6] == disc_number,
            'Disc number does not match the selected position; check disc order instead of renaming blindly')
    return header[:6], {'bytes': before.st_size, 'disc': disc_number + 1,
                       'revision': header[7], 'full_disc_size': before.st_size == DISC_BYTES}


def check_gamecube(disc1, disc2=None):
    paths = [Path(disc1)] + ([Path(disc2)] if disc2 is not None else [])
    results = [_header(path, number) for number, path in enumerate(paths)]
    require(all(game_id == results[0][0] for game_id, _ in results),
            'Disc game IDs differ; do not combine these images into one game folder')
    names = ['game.iso', 'disc2.iso'][:len(paths)]
    layout_matches = all(path.name == name and path.parent.parent.name == 'games'
                         for path, name in zip(paths, names))
    if len(paths) == 2:
        layout_matches = layout_matches and (
            os.path.normcase(os.path.abspath(paths[0].parent)) ==
            os.path.normcase(os.path.abspath(paths[1].parent)))
    return {'status': 'header-check-only', 'images': [result for _, result in results],
            'suggested_layout': ['games/<your-game-folder>/' + name for name in names],
            'suggested_layout_matches': layout_matches,
            'source': SOURCE, 'dump_integrity_verified': False, 'gameplay_verified': False,
            'write_authorized': False,
            'next': 'Review the suggested layout before any separately approved copy. Keep your original dump and its checksum record. Test Nintendont directly, including controls and save/reload, before GX integration.',
            'limitations': 'Only the first 1120 bytes and file metadata were read. Matching headers do not prove complete or matching disc contents, lawful provenance, compatibility or a playable game. A single disc check cannot tell whether a second disc is required. Alternate layouts may also work; nothing was renamed or copied.'}
