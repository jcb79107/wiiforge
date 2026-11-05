"""Synthetic preparation only; no package or destination arguments."""
import hashlib
import io
from pathlib import Path
import tempfile
import zipfile
from .archive import check_zip


def _copy_member(source, target, expected_size):
    count, digest = 0, hashlib.sha256()
    with target.open('xb') as output:
        while True:
            chunk = source.read(min(65536, expected_size - count + 1))
            if not chunk:
                break
            count += len(chunk)
            if count > expected_size:
                raise ValueError('Member exceeds declared size')
            digest.update(chunk)
            output.write(chunk)
    if count != expected_size:
        raise ValueError('Incomplete member')
    if hashlib.sha256(target.read_bytes()).hexdigest() != digest.hexdigest():
        raise ValueError('Staged file verification failed')
    return {'bytes': count, 'sha256': digest.hexdigest()}


def _rehearse_zip(data):
    # Immutable bytes keep validation and copying on the same archive snapshot.
    if type(data) is not bytes or len(data) > 1024 * 1024:
        raise ValueError('Rehearsal requires at most 1 MiB of fixture bytes')
    stream = io.BytesIO(data)
    metadata = check_zip(stream)
    if metadata['declared_bytes'] > 1024 * 1024:
        raise ValueError('Rehearsal fixtures exceed 1 MiB expanded limit')
    files = {}
    with zipfile.ZipFile(stream) as archive, tempfile.TemporaryDirectory(prefix='wiiforge-rehearsal-') as folder:
        root = Path(folder)
        for entry in archive.infolist():
            target = root / entry.filename
            if entry.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry) as source:
                files[entry.filename] = _copy_member(source, target, entry.file_size)
    return {'synthetic': True, 'status': 'rehearsal-complete', 'files': files,
            'temporary_files_removed': True, 'installation_supported': False}


def rehearse():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('apps/wiiforge-demo/readme.txt', b'Synthetic WiiForge fixture. Not homebrew.\n')
        archive.writestr('apps/wiiforge-demo/settings.json', b'{"synthetic":true}\n')
    return _rehearse_zip(stream.getvalue())
