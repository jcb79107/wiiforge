"""Windows handle-based package preparation. No raw disk access or formatting."""
from contextlib import contextmanager, ExitStack
import ctypes
from ctypes import wintypes as W
import hashlib
import os
from pathlib import Path
import shutil


def require(ok, message):
    if not ok:
        raise ValueError(message)


def api():
    require(os.name == 'nt', 'Windows filesystem operations require Windows')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, W.LPVOID, W.DWORD, W.DWORD, W.HANDLE]
    kernel.CreateFileW.restype = W.HANDLE
    kernel.CloseHandle.argtypes = [W.HANDLE]
    kernel.CloseHandle.restype = W.BOOL
    kernel.GetFileInformationByHandle.argtypes = [W.HANDLE, ctypes.POINTER(Information)]
    kernel.GetFileInformationByHandle.restype = W.BOOL
    kernel.GetDriveTypeW.argtypes = [W.LPCWSTR]
    kernel.GetDriveTypeW.restype = W.UINT
    kernel.GetVolumeInformationW.argtypes = [W.LPCWSTR, W.LPWSTR, W.DWORD, ctypes.POINTER(W.DWORD),
                                             ctypes.POINTER(W.DWORD), ctypes.POINTER(W.DWORD), W.LPWSTR, W.DWORD]
    kernel.GetVolumeInformationW.restype = W.BOOL
    return kernel


class Information(ctypes.Structure):
    _fields_ = [('attributes', W.DWORD), ('created', W.FILETIME), ('accessed', W.FILETIME),
                ('modified', W.FILETIME), ('volume', W.DWORD), ('size_high', W.DWORD),
                ('size_low', W.DWORD), ('links', W.DWORD), ('index_high', W.DWORD), ('index_low', W.DWORD)]


def information(handle):
    info = Information()
    if not api().GetFileInformationByHandle(handle, ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    require(not info.attributes & 0x400, 'Reparse points (including junctions) are not allowed')
    return info


def identity(info):
    return info.volume, (info.index_high << 32) | info.index_low


def local_path(path):
    value = os.path.abspath(os.fspath(path))
    require(not value.startswith('\\\\') and len(value) < 240 and ':' not in value[2:],
            'Choose a local drive path below 240 characters, without alternate streams')
    result = Path(value)
    require(len(result.drive) == 2 and result.drive[1] == ':', 'Choose a local drive letter')
    return result


@contextmanager
def opened(path, directory=False, create=False):
    # Deny concurrent writers and deletion; open the reparse point itself, never its target.
    access = 0x80 if directory else (0xC0000000 if create else 0x80000000)
    handle = api().CreateFileW(str(path), access, 1, None, 1 if create else 3,
                               0x00200000 | (0x02000000 if directory else 0), None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        info = information(handle)
        require(bool(info.attributes & 0x10) == directory, 'Unexpected file/directory type')
        yield handle, info
    finally:
        api().CloseHandle(handle)


class Root:
    def __init__(self, destination, validate=True):
        self.path = local_path(destination)
        self.stack = ExitStack()
        try:
            # Hold every ancestor open against rename/reparse replacement for this operation.
            for ancestor in [*reversed(self.path.parents), self.path]:
                _, info = self.stack.enter_context(opened(ancestor, directory=True))
            self.device, self.inode = identity(info)
            drive_type = api().GetDriveTypeW(self.path.anchor)
            require(drive_type in (2, 3), 'Only local removable/fixed volumes are accepted')
            if validate:
                require(self.path != Path.home() and
                        (self.path != Path(self.path.anchor) or drive_type == 2),
                        'Use a dedicated directory, or the root of a confirmed removable drive')
        except BaseException:
            self.stack.close()
            raise

    def close(self):
        self.stack.close()

    @contextmanager
    def parent(self, relative):
        parts = relative.split('/')
        require(all(p and p not in ('.', '..') and not any(c in p for c in '\\:<>"|?*') for p in parts),
                'Invalid relative Windows path')
        with ExitStack() as stack:
            path = self.path
            for part in parts[:-1]:
                path /= part
                _, info = stack.enter_context(opened(path, directory=True))
                require(info.volume == self.device, 'Destination crosses a volume boundary')
            target = path / parts[-1]
            require(len(str(target)) < 240, 'Destination path exceeds Windows review limit')
            yield target

    def directory_state(self, relative):
        try:
            with self.parent(relative) as path, opened(path, directory=True) as (_, info):
                require(info.volume == self.device, 'Destination crosses a volume boundary')
        except FileNotFoundError:
            return 'create'
        return 'keep'

    def file_state(self, item):
        try:
            with self.parent(item['path']) as path, opened(path) as (handle, info):
                require(info.volume == self.device, 'Destination crosses a volume boundary')
                require((info.size_high << 32) | info.size_low == item['bytes'], 'Existing destination size conflicts')
                with stream_from_handle(handle, writable=False) as source:
                    verify_stream(source, item)
        except FileNotFoundError:
            return 'create'
        return 'keep'

    def mkdir(self, relative):
        with self.parent(relative) as path:
            path.mkdir()  # Never exist_ok: a concurrent creation must stop for review.
        require(self.directory_state(relative) == 'keep', 'New directory validation failed')

    def copy_new(self, archive, item):
        with self.parent(item['path']) as path, opened(path, create=True) as (handle, info):
            require(info.volume == self.device, 'Destination crosses a volume boundary')
            with stream_from_handle(handle, writable=True) as output, archive.open(item['path']) as source:
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
                output.seek(0)
                verify_stream(output, item)
        # On error retain the new partial file for explicit review; never delete by an unlocked path.


@contextmanager
def stream_from_handle(handle, writable=False):
    import msvcrt
    # Duplicate the CRT descriptor; the original Win32 handle remains owned by opened().
    kernel = api()
    kernel.GetCurrentProcess.restype = W.HANDLE
    kernel.DuplicateHandle.argtypes = [W.HANDLE, W.HANDLE, W.HANDLE, ctypes.POINTER(W.HANDLE), W.DWORD, W.BOOL, W.DWORD]
    kernel.DuplicateHandle.restype = W.BOOL
    duplicate = W.HANDLE()
    process = kernel.GetCurrentProcess()
    if not kernel.DuplicateHandle(process, handle, process, ctypes.byref(duplicate), 0, False, 2):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        fd = msvcrt.open_osfhandle(duplicate.value, os.O_BINARY | (os.O_RDWR if writable else os.O_RDONLY))
    except BaseException:
        kernel.CloseHandle(duplicate)
        raise
    with os.fdopen(fd, 'r+b' if writable else 'rb') as stream:
        yield stream


def verify_stream(source, item):
    checksum, count = hashlib.sha256(), 0
    while True:
        chunk = source.read(min(65536, item['bytes'] - count + 1))
        if not chunk:
            break
        count += len(chunk)
        require(count <= item['bytes'], 'File exceeds expected size')
        checksum.update(chunk)
    require(count == item['bytes'] and checksum.hexdigest() == item['sha256'], 'File content conflicts')


@contextmanager
def source_file(path):
    path = local_path(path)
    root = Root(path.parent, validate=False)
    try:
        with opened(path) as (handle, _), stream_from_handle(handle) as stream:
            yield stream
    finally:
        root.close()


def inspect_volume(path):
    root = Root(path, validate=False)
    try:
        fs, label = ctypes.create_unicode_buffer(64), ctypes.create_unicode_buffer(261)
        serial, maximum, flags = W.DWORD(), W.DWORD(), W.DWORD()
        if not api().GetVolumeInformationW(root.path.anchor, label, len(label), ctypes.byref(serial),
                                           ctypes.byref(maximum), ctypes.byref(flags), fs, len(fs)):
            raise ctypes.WinError(ctypes.get_last_error())
        drive_type = api().GetDriveTypeW(root.path.anchor)
        return {'platform': 'windows', 'path': str(root.path), 'filesystem': fs.value,
                'drive_type': 'removable' if drive_type == 2 else 'fixed',
                'free_bytes': shutil.disk_usage(root.path).free,
                'write_authorized': False, 'physical_identity_verified': False,
                'notice': 'Read-only volume observation, not physical-device identification or MBR/cluster-size validation. Confirm the actual card/drive separately; reconnects require a new review.'}
    finally:
        root.close()
