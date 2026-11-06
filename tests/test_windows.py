import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

from wiiready.prepare import plan_preparation, execute_preparation


@unittest.skipUnless(os.name == 'nt', 'Native Windows API tests')
class WindowsTests(unittest.TestCase):
    def test_read_only_volume_observation(self):
        from wiiready.windows import inspect_volume
        with tempfile.TemporaryDirectory() as folder:
            report = inspect_volume(folder)
            self.assertIn(report['drive_type'], ['fixed', 'removable'])
            self.assertFalse(report['write_authorized'])
            self.assertFalse(report['physical_identity_verified'])
            self.assertGreater(report['free_bytes'], 0)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_locked_ancestor_cannot_be_renamed(self):
        from wiiready.windows import Root
        with tempfile.TemporaryDirectory() as folder:
            parent = Path(folder)/'parent'; dest = parent/'destination'; dest.mkdir(parents=True)
            root = Root(dest)
            try:
                with self.assertRaises(OSError): parent.rename(Path(folder)/'moved')
            finally:
                root.close()
            parent.rename(Path(folder)/'moved')

    def test_junction_source_and_destination_rejected(self):
        from wiiready.windows import Root, source_file
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); target = root/'target'; target.mkdir(); (target/'app').write_bytes(b'x')
            link = root/'junction'
            subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)], check=True, capture_output=True)
            try:
                with self.assertRaises(ValueError): Root(link)
                with self.assertRaises(ValueError):
                    with source_file(link/'app'): pass
            finally:
                link.rmdir()

    def test_source_lock_prevents_writes(self):
        from wiiready.windows import source_file
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'source'; path.write_bytes(b'unchanged')
            with source_file(path) as source:
                with self.assertRaises(OSError): path.write_bytes(b'changed')
                self.assertEqual(source.read(), b'unchanged')

    def test_copy_failure_keeps_partial_without_overwrite(self):
        from unittest.mock import patch
        from wiiready.windows import verify_stream
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as z: z.writestr('apps/demo/boot.dol', b'synthetic')
        with tempfile.TemporaryDirectory() as folder:
            plan = plan_preparation(data.getvalue(), folder, 'original')
            with patch('wiiready.windows.verify_stream', side_effect=OSError('synthetic verification failure')):
                with self.assertRaises(OSError): execute_preparation(data.getvalue(), folder, 'original', plan, plan['digest'])
            target = Path(folder)/'apps/demo/boot.dol'
            self.assertEqual(target.read_bytes(), b'synthetic')
            target.write_bytes(b'partial')
            with self.assertRaises(ValueError): execute_preparation(data.getvalue(), folder, 'original', plan, plan['digest'])
            self.assertEqual(target.read_bytes(), b'partial')

    def test_reject_network_stream_and_fixed_root(self):
        from wiiready.windows import Root, local_path
        for path in [r'\\server\share\app', r'C:\file:stream', r'\\.\PhysicalDrive0']:
            with self.assertRaises(ValueError): local_path(path)
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError): Root(Path(folder).anchor)
