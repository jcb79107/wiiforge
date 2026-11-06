"""Select only the original-Wii installer and notices from a verified local archive."""
import io
import zipfile
import zlib
from .archive import check_zip
from .prepare import require

MEMBERS = ['boot.elf', 'LICENSE.txt', 'CREDITS.txt', 'README.txt', 'README-HBC.txt',
           'README-BootMii.txt', 'licenses/APACHE-2.0.txt']


def hackmii_snapshot(data):
    check_zip(io.BytesIO(data))
    output = io.BytesIO()
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(output, 'w') as target:
            for name in MEMBERS:
                member = 'hackmii_installer_v1.2/' + name
                require(member in source.namelist(), 'HackMii archive is missing a required installer/notice file')
                entry = source.getinfo(member)
                limit = 8 * 1024 * 1024 if name == 'boot.elf' else 64 * 1024
                require(0 < entry.file_size <= limit, 'HackMii member exceeds reviewed size bound')
                with source.open(entry) as stream:
                    payload = stream.read(entry.file_size + 1)
                require(len(payload) == entry.file_size, 'Incomplete HackMii member')
                destination = name if name == 'boot.elf' else 'wiiready-notices/hackmii/' + name
                info = zipfile.ZipInfo(destination, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100600 << 16
                target.writestr(info, payload)
    except (zipfile.BadZipFile, zlib.error, NotImplementedError) as exc:
        raise ValueError('Invalid or unsupported HackMii archive contents') from exc
    return output.getvalue()
