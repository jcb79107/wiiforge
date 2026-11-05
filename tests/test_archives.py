import io
import stat
import struct
import unittest
import warnings
import zipfile
from unittest.mock import patch
from wiiforge.archive import check_zip


def archive(entries):
    stream = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as output:
            for name, data in entries:
                output.writestr(name, data)
    stream.seek(0)
    return stream


class ArchiveTests(unittest.TestCase):
    def test_normal_layout_is_metadata_only(self):
        stream = archive([('apps/', b''), ('apps/usbloader_gx/boot.dol', b'synthetic')])
        with (patch.object(zipfile.ZipFile, 'extract', side_effect=AssertionError('extraction')),
              patch.object(zipfile.ZipFile, 'extractall', side_effect=AssertionError('extraction'))):
            result = check_zip(stream)
        self.assertEqual(result['status'], 'metadata-checked')
        self.assertFalse(result['content_verified'])
        self.assertEqual(result['entries'], 2)

    def test_unsafe_names(self):
        for name in ['../boot.dol', '/absolute', 'a/../b', 'a//b', 'a//', 'a\\b', 'C:/boot',
                     'a:stream', 'CON.txt', 'a/aux', 'a.', 'a ', './a', 'a\nb', 'e\u0301']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                check_zip(archive([(name, b'x')]))

    def test_collisions_and_file_parents(self):
        for names in [['a', 'a'], ['A', 'a'], ['a', 'a/b'], ['a/b', 'a'], ['a/', 'A']]:
            with self.subTest(names=names), self.assertRaises(ValueError):
                check_zip(archive([(n, b'' if n.endswith('/') else b'x') for n in names]))

    def test_links_and_special_files(self):
        for mode in [stat.S_IFLNK, stat.S_IFIFO, stat.S_IFCHR, stat.S_IFSOCK]:
            info = zipfile.ZipInfo('link')
            info.create_system = 3
            info.external_attr = (mode | 0o777) << 16
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                check_zip(archive([(info, b'target')]))

    def test_empty_invalid_encrypted_and_large_archives(self):
        for stream in [io.BytesIO(b'invalid'), archive([]), archive([('big', b'0' * 1000000)])]:
            with self.assertRaises(ValueError):
                check_zip(stream)
        data = bytearray(archive([('a', b'x')]).getvalue())
        central = data.index(b'PK\x01\x02')
        struct.pack_into('<H', data, central + 8, 1)
        with self.assertRaisesRegex(ValueError, 'Encrypted'):
            check_zip(io.BytesIO(data))

    def test_declared_size_and_count_limits(self):
        data = bytearray(archive([('a', b'x')]).getvalue())
        central = data.index(b'PK\x01\x02')
        struct.pack_into('<I', data, central + 24, 64 * 1024 * 1024 + 1)
        with self.assertRaisesRegex(ValueError, 'size limit'):
            check_zip(io.BytesIO(data))
        with self.assertRaisesRegex(ValueError, 'entry count'):
            check_zip(archive([(str(i), b'') for i in range(4097)]))
