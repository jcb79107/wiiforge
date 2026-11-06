"""Exact-plan, no-overwrite copies of local raw GameCube images. No conversion."""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import stat

from .games import HEADER_BYTES, DISC_BYTES, _parse_header
from .prepare import require, _plan_files, _execute_files, _check_approval


def _identity(info):
    return {'device': info.st_dev, 'inode': info.st_ino, 'bytes': info.st_size,
            'mtime_ns': info.st_mtime_ns, 'ctime_ns': info.st_ctime_ns}


@contextmanager
def _source(path):
    require(os.name == 'posix' and hasattr(os, 'O_NOFOLLOW'), 'Game copying requires a POSIX host')
    require(Path(path).suffix.lower() in ('.iso', '.gcm'), 'Select a raw ISO/GCM file; conversion is not implemented')
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as source:
        before = os.fstat(source.fileno())
        require(stat.S_ISREG(before.st_mode) and HEADER_BYTES <= before.st_size <= DISC_BYTES,
                'Game source must be a bounded regular raw image')
        yield source, _identity(before)
        require(_identity(os.fstat(source.fileno())) == _identity(before), 'Game source changed while reading')


def _inventory(disc1, disc2):
    files, sources, ids = [], [], []
    for number, selected in enumerate([disc1] + ([disc2] if disc2 is not None else [])):
        selected = Path(selected)
        require(not selected.is_symlink(), 'Game source must not be a symlink')
        path = str(selected.resolve(strict=True))
        with _source(path) as (source, identity):
            header = source.read(HEADER_BYTES)
            game_id, _ = _parse_header(header, identity['bytes'], number)
            ids.append(game_id)
            source.seek(0)
            checksum, count = hashlib.sha256(), 0
            while True:
                chunk = source.read(min(65536, identity['bytes'] - count + 1))
                if not chunk:
                    break
                count += len(chunk)
                require(count <= identity['bytes'], 'Game source grew while hashing')
                checksum.update(chunk)
            require(count == identity['bytes'], 'Game source was truncated while hashing')
        relative = 'games/' + game_id.decode('ascii') + ('/game.iso' if number == 0 else '/disc2.iso')
        files.append({'path': relative, 'bytes': count, 'sha256': checksum.hexdigest()})
        sources.append({'path': path, 'identity': identity})
    require(len(set(ids)) == 1, 'Disc game IDs differ; do not combine these images')
    # Keep a deterministic order for exact-plan comparison and interrupted resumes.
    pairs = sorted(zip(files, sources), key=lambda pair: pair[0]['path'])
    return [pair[0] for pair in pairs], [pair[1] for pair in pairs]


def plan_game_copy(disc1, disc2, destination, model):
    require(model == 'original', 'Game preparation currently requires explicit original-Wii selection')
    require(os.name == 'posix' and hasattr(os, 'O_NOFOLLOW'), 'Game copying requires a POSIX host')
    files, sources = _inventory(disc1, disc2)
    return _plan_files(files, ['games', files[0]['path'].rsplit('/', 1)[0]], destination,
                       {'kind': 'gamecube-copy', 'model': model, 'sources': sources,
                        'installation_supported': False,
                        'installation_blockers': ['dump-integrity-unverified', 'lawful-provenance-user-responsibility', 'hardware-untested']})


class _LocalImages:
    def __init__(self, plan):
        self.sources = {item['path']: source for item, source in zip(plan['files'], plan['sources'])}

    @contextmanager
    def open(self, relative):
        expected = self.sources[relative]
        with _source(expected['path']) as (source, identity):
            require(identity == expected['identity'], 'Game source identity changed before copying')
            yield source


def execute_game_copy(disc1, disc2, destination, model, plan, approval):
    _check_approval(plan, approval)
    current = plan_game_copy(disc1, disc2, destination, model)
    result = _execute_files(current, destination, plan, approval, _LocalImages(current))
    result.update(status='game-files-copied', copy_bytes_verified=True,
                  dump_integrity_verified=False, gameplay_verified=False, sources_preserved=True)
    return result
