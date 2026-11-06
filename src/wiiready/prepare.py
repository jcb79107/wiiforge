"""Explicit, no-overwrite file preparation. POSIX directory descriptors required."""
from contextlib import contextmanager
import hashlib
import io
import json
import os
import shutil
from pathlib import Path
import stat
import zipfile
import zlib
from .archive import check_zip

PREPARATION_PLAN_LIMIT = 8 * 1024 * 1024


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@contextmanager
def root_directory(destination):
    if os.name == 'nt':
        from .windows import Root
        root = Root(destination)
        try:
            yield root, {'path': str(root.path), 'device': root.device, 'inode': root.inode}
        finally:
            root.close()
        return
    require(os.name == 'posix' and hasattr(os, 'O_NOFOLLOW'), 'Preparation requires a POSIX host')
    path = Path(destination)
    require(not path.is_symlink(), 'Destination must not be a symlink')
    path = path.resolve(strict=True)
    require(path != Path(path.anchor) and path != Path.home().resolve(), 'Select a dedicated destination directory')
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        yield fd, {'path': str(path), 'device': info.st_dev, 'inode': info.st_ino}
    finally:
        os.close(fd)


def same_device(root, child):
    require(os.fstat(root).st_dev == os.fstat(child).st_dev,
            'Destination subtree crosses a filesystem device boundary')


@contextmanager
def parent_directory(root, relative):
    fd = os.dup(root)
    try:
        for part in relative.split('/')[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
            same_device(root, fd)
        yield fd, relative.split('/')[-1]
    finally:
        os.close(fd)


def contents(data):
    metadata = check_zip(io.BytesIO(data))
    files, directories = [], set()
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for entry in archive.infolist():
                parts = entry.filename.rstrip('/').split('/')
                for i in range(1, len(parts) + (1 if entry.is_dir() else 0)):
                    directories.add('/'.join(parts[:i]))
                if entry.is_dir():
                    continue
                checksum, count = hashlib.sha256(), 0
                with archive.open(entry) as source:
                    while True:
                        chunk = source.read(min(65536, entry.file_size - count + 1))
                        if not chunk:
                            break
                        count += len(chunk)
                        require(count <= entry.file_size, 'Archive member exceeds declared size')
                        checksum.update(chunk)
                require(count == entry.file_size, 'Incomplete archive member')
                files.append({'path': entry.filename, 'bytes': count, 'sha256': checksum.hexdigest()})
    except (zipfile.BadZipFile, zlib.error, NotImplementedError) as exc:
        raise ValueError('Invalid or unsupported archive contents') from exc
    return sorted(files, key=lambda x: x['path']), sorted(directories, key=lambda x: (x.count('/'), x)), metadata


def file_state(root, item):
    if os.name == 'nt':
        return root.file_state(item)
    try:
        with parent_directory(root, item['path']) as (parent, name):
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    except FileNotFoundError:
        return 'create'
    with os.fdopen(fd, 'rb') as source:
        before = os.fstat(source.fileno())
        same_device(root, source.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size == item['bytes'], 'Existing destination conflicts: ' + item['path'])
        checksum, count = hashlib.sha256(), 0
        while True:
            chunk = source.read(min(65536, item['bytes'] - count + 1))
            if not chunk:
                break
            count += len(chunk)
            require(count <= item['bytes'], 'Destination changed while checking')
            checksum.update(chunk)
        after = os.fstat(source.fileno())
        require((before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'Destination changed while checking')
        require(count == item['bytes'] and checksum.hexdigest() == item['sha256'], 'Existing destination conflicts: ' + item['path'])
    return 'keep'


def directory_state(root, path):
    if os.name == 'nt':
        return root.directory_state(path)
    try:
        with parent_directory(root, path) as (parent, name):
            fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
    except FileNotFoundError:
        return 'create'
    try:
        same_device(root, fd)
    finally:
        os.close(fd)
    return 'keep'


def space_check(root, required):
    if os.name == 'nt':
        require(shutil.disk_usage(root.path).free >= required + 1024 * 1024, 'Insufficient destination space')
        return
    info = os.fstatvfs(root)
    require(info.f_bavail * info.f_frsize >= required + 1024 * 1024, 'Insufficient destination space (includes 1 MiB margin)')


def plan_preparation(data, destination, model):
    require(model == 'original', 'Only the original-Wii package path is reviewed')
    files, directories, _ = contents(data)
    return _plan_files(files, directories, destination,
                       {'model': model, 'source_sha256': hashlib.sha256(data).hexdigest(),
                        'installation_supported': False,
                        'installation_blockers': ['license-review-pending', 'console-installation-not-implemented', 'hardware-untested']})


def _plan_files(files, directories, destination, metadata):
    # Internal callers supply validated relative paths and bounded content hashes.
    with root_directory(destination) as (root, identity):
        if os.name == 'nt' and root.filesystem == 'FAT32':
            require(all(item['bytes'] < 2 ** 32 for item in files), 'FAT32 cannot hold this file; use suitable host staging')
        dirs = [{'path': p, 'action': directory_state(root, p)} for p in directories]
        files = [dict(item, action=file_state(root, item)) for item in files]
        required = sum(item['bytes'] for item in files if item['action'] == 'create')
        space_check(root, required)
    body = {**metadata, 'schema': 1, 'destination': identity, 'directories': dirs,
            'files': files, 'required_bytes': required}
    plan = dict(body, digest=digest(body))
    require(len(json.dumps(plan, indent=2, sort_keys=True).encode('utf-8')) + 1 <= PREPARATION_PLAN_LIMIT,
            'Preparation plan exceeds 8 MiB; reduce the package inventory')
    return plan


def _copy_new(archive, item, root):
    if os.name == 'nt':
        return root.copy_new(archive, item)
    with parent_directory(root, item['path']) as (parent, name):
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        created = os.fstat(fd)
        try:
            with os.fdopen(fd, 'wb') as output, archive.open(item['path']) as source:
                same_device(root, output.fileno())
                count, checksum = 0, hashlib.sha256()
                while True:
                    chunk = source.read(min(65536, item['bytes'] - count + 1))
                    if not chunk:
                        break
                    count += len(chunk)
                    require(count <= item['bytes'], 'Source exceeds expected size')
                    checksum.update(chunk)
                    output.write(chunk)
                require(count == item['bytes'] and checksum.hexdigest() == item['sha256'], 'Source content mismatch')
                output.flush()
                os.fsync(output.fileno())
            require(file_state(root, item) == 'keep', 'Written file failed read-back verification')
        except BaseException:
            # Remove only the new file we created, never a replacement or preexisting file.
            try:
                current = os.stat(name, dir_fd=parent, follow_symlinks=False)
                if (current.st_dev, current.st_ino) == (created.st_dev, created.st_ino):
                    os.unlink(name, dir_fd=parent)
            except FileNotFoundError:
                pass
            raise


def execute_preparation(data, destination, model, plan, approval):
    _check_approval(plan, approval)
    current = plan_preparation(data, destination, model)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return _execute_files(current, destination, plan, approval, archive)


def _check_approval(plan, approval):
    require(isinstance(plan, dict), 'Invalid preparation plan')
    require(approval == plan.get('digest'), 'Explicit --approve-plan must match the saved plan digest')
    body = {k: v for k, v in plan.items() if k != 'digest'}
    require(plan.get('digest') == digest(body), 'Preparation plan changed')


def summarize_plan(plan):
    """Aggregate saved plan contents without revealing paths, IDs or hashes."""
    require(isinstance(plan, dict), 'Invalid preparation plan')
    _check_approval(plan, plan.get('digest'))  # Consistency only, never user approval.
    require(type(plan.get('schema')) is int and plan['schema'] == 1 and
            plan.get('model') == 'original' and plan.get('installation_supported') is False and
            plan.get('kind') in (None, 'gamecube-copy', 'wii-join'), 'Unsupported preparation plan')
    files = plan.get('files')
    require(isinstance(files, list) and all(isinstance(item, dict) and
            item.get('action') in ('create', 'keep') and type(item.get('bytes')) is int and
            item['bytes'] >= 0 for item in files), 'Invalid file inventory')
    required = sum(item['bytes'] for item in files if item['action'] == 'create')
    require(type(plan.get('required_bytes')) is int and plan['required_bytes'] == required,
            'Inconsistent planned byte count')
    return {'status': 'private-plan-summary',
            'operation': plan.get('kind') or 'package-preparation',
            'files_to_create': sum(item['action'] == 'create' for item in files),
            'files_to_preserve': sum(item['action'] == 'keep' for item in files),
            'bytes_to_write': required, 'write_authorized': False,
            'notice': 'Saved-plan totals only; sources and destination were not rechecked. Review exact paths and digest locally before approval. Do not upload the raw plan.'}


def _execute_files(current, destination, plan, approval, archive):
    _check_approval(plan, approval)
    # Only create -> keep transitions are accepted: completed files can be resumed after verification.
    expected = dict(current)
    for kind in ['files', 'directories']:
        require(isinstance(plan.get(kind), list) and len(plan[kind]) == len(current[kind]), 'Plan inventory changed')
        restored = []
        for old, now in zip(plan[kind], current[kind]):
            require(isinstance(old, dict) and old.get('action') in ('create', 'keep'), 'Invalid plan action')
            require(old['action'] != 'keep' or now['action'] == 'keep', 'Previously preserved destination entry disappeared')
            restored.append(dict(now, action=old['action']))
        expected[kind] = restored
    expected['required_bytes'] = sum(f['bytes'] for f in expected['files'] if f['action'] == 'create')
    expected['digest'] = digest({k: v for k, v in expected.items() if k != 'digest'})
    require(plan == expected, 'Source, destination, model or write plan changed; review a new plan')
    written, kept = [], []
    with root_directory(destination) as (root, identity):
        require(identity == plan['destination'], 'Destination identity changed')
        for entry in current['directories']:
            if directory_state(root, entry['path']) == 'create':
                require(next(d['action'] for d in plan['directories'] if d['path'] == entry['path']) == 'create',
                        'Preserved directory disappeared')
                if os.name == 'nt':
                    root.mkdir(entry['path'])
                else:
                    with parent_directory(root, entry['path']) as (parent, name):
                        os.mkdir(name, mode=0o700, dir_fd=parent)
        for item in current['files']:
            if file_state(root, item) == 'keep':
                kept.append(item['path'])
                continue
            require(next(f['action'] for f in plan['files'] if f['path'] == item['path']) == 'create',
                    'Preserved file disappeared')
            space_check(root, item['bytes'])
            try:
                _copy_new(archive, item, root)
            except (zipfile.BadZipFile, zlib.error, NotImplementedError) as exc:
                raise ValueError('Invalid archive contents during preparation') from exc
            written.append(item['path'])
    return {'status': 'files-prepared', 'written': written, 'verified_existing': kept,
            'plan_digest': plan['digest'], 'installation_supported': False,
            'installation_blockers': plan['installation_blockers']}
