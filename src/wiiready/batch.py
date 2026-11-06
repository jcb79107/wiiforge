"""Combine verified package snapshots for the existing no-overwrite preparation engine."""
import io
import stat
import zipfile
from .prepare import contents, require

LIMIT = 64 * 1024 * 1024


def combine_packages(packages):
    """Consume a bounded iterator of verified bytes; never write extracted files."""
    files, directories = {}, set()
    input_bytes = expanded = count = 0
    for data in packages:
        count += 1
        require(count <= 12, 'At most 12 packages per batch')
        input_bytes += len(data)
        require(input_bytes <= LIMIT, 'Batch inputs exceed 64 MiB')
        inventory, dirs, _ = contents(data)
        directories.update(dirs)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for item in inventory:
                path = item['path']
                require(path not in files, 'Packages contain a duplicate file: ' + path)
                expanded += item['bytes']
                require(expanded <= LIMIT, 'Batch expanded files exceed 64 MiB')
                with archive.open(path) as source:
                    content = source.read(item['bytes'] + 1)
                require(len(content) == item['bytes'], 'Incomplete batch member')
                files[path] = content
        require(len(files) + len(directories) <= 4096, 'Batch has too many entries')
    require(count > 0, 'Choose at least one package')
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as archive:
        for path in sorted(directories) + sorted(files):
            directory = path not in files
            require(not (path in directories and path in files), 'Batch file/directory conflict')
            entry = zipfile.ZipInfo(path + '/' if directory else path, (1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = ((stat.S_IFDIR | 0o700) if directory else (stat.S_IFREG | 0o600)) << 16
            archive.writestr(entry, b'' if directory else files[path])
    result = output.getvalue()
    require(len(result) <= LIMIT, 'Combined ZIP exceeds 64 MiB')
    contents(result)  # Cross-package case, parent and portable-path collisions.
    return result


def check_emulator_layout(data, package):
    files, directories, _ = contents(data)
    require({f['path'] for f in files} == {
        'apps/' + package + '/' + name for name in ('boot.dol', 'meta.xml', 'icon.png')},
        'Unexpected emulator files; no saves, games, BIOS or installers may be included')
    require(set(directories) == {'apps', 'apps/' + package, package,
                               package + '/roms', package + '/saves', package + '/cheats'},
            'Unexpected emulator directory layout')
    return data
