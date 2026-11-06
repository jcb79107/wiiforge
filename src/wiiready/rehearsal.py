"""Isolated, disposable preparation; no caller-selected destinations."""
import hashlib
import io
import shutil
from pathlib import Path
import tempfile
import zipfile
import zlib
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
    verified, actual = hashlib.sha256(), 0
    with target.open('rb') as staged:
        while True:
            chunk = staged.read(min(65536, expected_size - actual + 1))
            if not chunk:
                break
            actual += len(chunk)
            if actual > expected_size:
                raise ValueError('Staged file grew during verification')
            verified.update(chunk)
    if actual != expected_size or verified.hexdigest() != digest.hexdigest():
        raise ValueError('Staged file verification failed')
    return {'bytes': count, 'sha256': digest.hexdigest()}


def _stage_zip(data, *, synthetic=True):
    # Immutable bytes keep validation and copying on the same archive snapshot.
    input_limit = (1 if synthetic else 64) * 1024 * 1024
    output_limit = (1 if synthetic else 128) * 1024 * 1024
    if type(data) is not bytes or len(data) > input_limit:
        raise ValueError('Staging input exceeds bounded byte limit')
    stream = io.BytesIO(data)
    metadata = check_zip(stream)
    if metadata['declared_bytes'] > output_limit:
        raise ValueError('Staging expanded size exceeds limit')
    files = {}
    try:
        with zipfile.ZipFile(stream) as archive, tempfile.TemporaryDirectory(prefix='wiiready-rehearsal-') as folder:
            root = Path(folder)
            if shutil.disk_usage(root).free < metadata['declared_bytes'] + 1024 * 1024:
                raise ValueError('Insufficient temporary storage space')
            for entry in archive.infolist():
                target = root / entry.filename
                if entry.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as source:
                    files[entry.filename] = _copy_member(source, target, entry.file_size)
    except (zipfile.BadZipFile, zlib.error, NotImplementedError) as exc:
        raise ValueError('Invalid or unsupported ZIP contents: ' + str(exc)) from exc
    return {'synthetic': synthetic, 'status': 'rehearsal-complete' if synthetic else 'experimental-stage-verified', 'files': files,
            'temporary_files_removed': True, 'installation_supported': False}


def rehearse():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('apps/wiiready-demo/readme.txt', b'Synthetic WiiReady fixture. Not homebrew.\n')
        archive.writestr('apps/wiiready-demo/settings.json', b'{"synthetic":true}\n')
    return _stage_zip(stream.getvalue())
