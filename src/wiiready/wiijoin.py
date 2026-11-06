"""Join explicit CleanRip parts; no conversion, image validation or media detection."""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import re
import stat

from .gamecopy import _identity
from .prepare import require, _plan_files, _execute_files, _check_approval

MAX_BYTES = 9 * 1024 ** 3


@contextmanager
def _part(path):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as source:
        before = os.fstat(source.fileno())
        require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= MAX_BYTES,
                'Select nonempty bounded regular parts')
        yield source, _identity(before)
        require(_identity(os.fstat(source.fileno())) == _identity(before), 'Part changed while reading')


def _chunks(sources):
    for item in sources:
        with _part(item['path']) as (source, identity):
            require(identity == item['identity'], 'Part identity changed')
            count = 0
            while True:
                chunk = source.read(min(65536, identity['bytes'] - count + 1))
                if not chunk:
                    break
                count += len(chunk)
                require(count <= identity['bytes'], 'Part grew while reading')
                yield chunk
            require(count == identity['bytes'], 'Part was truncated')


def plan_wii_join(parts, expected_sha1, destination, model):
    require(model == 'original', 'Joining currently requires explicit original-Wii selection')
    require(os.name == 'posix' and hasattr(os, 'O_NOFOLLOW'), 'Joining requires a POSIX host')
    require(isinstance(expected_sha1, str) and re.fullmatch('[a-fA-F0-9]{40}', expected_sha1),
            'Provide the SHA-1 from the original dump record')
    require(2 <= len(parts) <= 16, 'Select 2 to 16 ordered parts explicitly')
    sources, prefix, total = [], None, 0
    for number, selected in enumerate(parts):
        selected = Path(selected)
        match = re.fullmatch(r'(.+)\.part([0-9]+)\.iso', selected.name)
        require(match is not None and match[2] == str(number), 'Parts must be ordered consecutively from part0.iso')
        prefix = match[1] if prefix is None else prefix
        require(match[1] == prefix and not selected.is_symlink(), 'Parts must share a basename and must not be links')
        path = str(selected.resolve(strict=True))
        with _part(path) as (_, identity):
            total += identity['bytes']
            require(total <= MAX_BYTES, 'Joined file exceeds 9 GiB bound')
            require(all((s['identity']['device'], s['identity']['inode']) !=
                        (identity['device'], identity['inode']) for s in sources), 'Duplicate source part')
            sources.append({'path': path, 'identity': identity})
    sha1, sha256 = hashlib.sha1(), hashlib.sha256()
    for chunk in _chunks(sources):
        sha1.update(chunk)
        sha256.update(chunk)
    require(sha1.hexdigest() == expected_sha1.lower(), 'Joined checksum does not match the supplied dump record')
    return _plan_files([{'path': 'joined.iso', 'bytes': total, 'sha256': sha256.hexdigest()}], [], destination,
                       {'kind': 'wii-join', 'model': model, 'sources': sources,
                        'expected_sha1': expected_sha1.lower(), 'installation_supported': False,
                        'installation_blockers': ['image-format-unverified', 'dump-authenticity-unverified', 'hardware-untested']})


class _JoinedParts:
    def __init__(self, sources):
        self.sources = sources

    @contextmanager
    def open(self, relative):
        require(relative == 'joined.iso', 'Unexpected join output')
        chunks = _chunks(self.sources)
        pending = b''

        class Reader:
            def read(self, size):
                nonlocal pending
                require(0 < size <= 65536, 'Unbounded join read')
                if not pending:
                    pending = next(chunks, b'')
                result, pending = pending[:size], pending[size:]
                return result

        try:
            yield Reader()
        finally:
            chunks.close()


def execute_wii_join(parts, expected_sha1, destination, model, plan, approval):
    _check_approval(plan, approval)
    current = plan_wii_join(parts, expected_sha1, destination, model)
    result = _execute_files(current, destination, plan, approval, _JoinedParts(current['sources']))
    result.update(status='parts-joined', supplied_checksum_matched=True, copy_bytes_verified=True,
                  dump_authenticity_verified=False, image_format_verified=False, gameplay_verified=False,
                  sources_preserved=True)
    return result
