"""Verify local Nintendont files and build an in-memory preparation snapshot."""
import hashlib
import io
import os
from pathlib import Path
import re
import stat
import zipfile
from .prepare import require

LAYOUT = [('loader/loader.dol', 'boot.dol', 8 * 1024 * 1024),
          ('nintendont/meta.xml', 'meta.xml', 64 * 1024),
          ('nintendont/icon.png', 'icon.png', 1024 * 1024)]


def nintendont_bytes(manifest, artifact, model):
    require(os.name == 'nt' or (os.name == 'posix' and hasattr(os, 'O_NOFOLLOW')), 'Unsupported Nintendont verification host')
    require(isinstance(manifest, dict) and set(manifest) == set(
        'schema package repository commit digest_source models license_review files'.split()), 'Invalid Nintendont manifest fields')
    require(type(manifest['schema']) is int and manifest['schema'] == 1 and manifest['package'] == 'nintendont', 'Invalid Nintendont manifest')
    require(manifest['repository'] == 'https://github.com/FIX94/Nintendont', 'Unreviewed Nintendont origin')
    require(isinstance(manifest['commit'], str) and re.fullmatch('[0-9a-f]{40}', manifest['commit']), 'Nintendont requires an exact commit')
    require(manifest['digest_source'] == 'local-sha256-verified-git-blob', 'Unreviewed digest source')
    require(manifest['models'] == ['original'] and model == 'original', 'Nintendont package model path is not reviewed')
    require(manifest['license_review'] == 'pending', 'License approval is not implemented')
    require(isinstance(manifest['files'], list) and len(manifest['files']) == 3, 'Nintendont requires exactly three pinned files')
    for item, (source, name, limit) in zip(manifest['files'], LAYOUT):
        require(isinstance(item, dict) and set(item) == set('source destination size sha256 git_blob'.split()), 'Invalid Nintendont file fields')
        require(item['source'] == source and item['destination'] == 'apps/Nintendont/' + name, 'Unreviewed Nintendont file layout')
        require(type(item['size']) is int and 0 < item['size'] <= limit, 'Nintendont file size outside bound')
        for key, length in [('sha256', 64), ('git_blob', 40)]:
            require(isinstance(item[key], str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', item[key]), 'Invalid Nintendont digest')
    root = None if os.name == 'nt' else os.open(artifact, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    snapshot = io.BytesIO()
    try:
        with zipfile.ZipFile(snapshot, 'w', compression=zipfile.ZIP_STORED) as archive:
            for item in manifest['files']:
                # Only these three basenames are read; extras, saves and configuration are never copied.
                name = item['source'].rsplit('/', 1)[1]
                if os.name == 'nt':
                    from .windows import source_file
                    source = source_file(Path(artifact) / name)
                else:
                    fd = os.open(name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=root)
                    source = os.fdopen(fd, 'rb')
                with source as stream:
                    before = os.fstat(stream.fileno())
                    require(stat.S_ISREG(before.st_mode) and before.st_size == item['size'], 'Nintendont input must be a regular file of the pinned size: ' + name)
                    data = stream.read(item['size'] + 1)
                    after = os.fstat(stream.fileno())
                require((before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                        (after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'Nintendont input changed while reading')
                require(len(data) == item['size'] and hashlib.sha256(data).hexdigest() == item['sha256'], 'Nintendont SHA-256/size mismatch: ' + name)
                blob = b'blob ' + str(len(data)).encode() + b'\0' + data
                require(hashlib.sha1(blob).hexdigest() == item['git_blob'], 'Nintendont Git blob mismatch: ' + name)
                entry = zipfile.ZipInfo(item['destination'], date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = (stat.S_IFREG | 0o600) << 16
                archive.writestr(entry, data)
    finally:
        if root is not None:
            os.close(root)
    return snapshot.getvalue()
