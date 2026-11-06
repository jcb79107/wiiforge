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

    def test_gamecube_copy_and_wii_join_preserve_sources(self):
        import hashlib
        from test_games import synthetic_header
        from wiiready.gamecopy import plan_game_copy, execute_game_copy
        from wiiready.wiijoin import plan_wii_join, execute_wii_join
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); dest = root/'destination'; dest.mkdir()
            disc = root/'game.iso'; disc.write_bytes(synthetic_header() + b'invented')
            plan = plan_game_copy(disc, None, dest, 'original')
            with self.assertRaises(ValueError): execute_game_copy(disc, None, dest, 'original', plan, 'wrong')
            result = execute_game_copy(disc, None, dest, 'original', plan, plan['digest'])
            self.assertTrue(result['copy_bytes_verified'])
            self.assertEqual((dest/'games/TEST00/game.iso').read_bytes(), disc.read_bytes())
            self.assertEqual(execute_game_copy(disc, None, dest, 'original', plan, plan['digest'])['written'], [])
            parts = [root/'synthetic.part0.iso', root/'synthetic.part1.iso']
            for part, data in zip(parts, [b'a'*70000, b'b'*40000]): part.write_bytes(data)
            expected = b''.join(part.read_bytes() for part in parts)
            checksum = hashlib.sha1(expected).hexdigest()
            plan = plan_wii_join(parts, checksum, dest, 'original')
            execute_wii_join(parts, checksum, dest, 'original', plan, plan['digest'])
            self.assertEqual((dest/'joined.iso').read_bytes(), expected)
            self.assertEqual(b''.join(part.read_bytes() for part in parts), expected)
            parts[0].write_bytes(b'changed')
            with self.assertRaises(ValueError): execute_wii_join(parts, checksum, dest, 'original', plan, plan['digest'])

    def test_fat32_large_file_is_rejected_before_creating_files(self):
        from unittest.mock import patch
        from wiiready.prepare import _plan_files
        with tempfile.TemporaryDirectory() as folder:
            with patch('wiiready.windows.volume_information', return_value=('FAT32', 0)):
                with self.assertRaisesRegex(ValueError, 'FAT32'):
                    _plan_files([{'path': 'large.iso', 'bytes': 2**32, 'sha256': '0'*64}], [], folder, {})
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_nintendont_files_can_join_emulator_batch(self):
        import hashlib
        import json
        from test_batch import emulator
        from wiiready.nintendont import nintendont_bytes
        from wiiready.batch import combine_packages
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root/'source'; source.mkdir(); dest = root/'dest'; dest.mkdir()
            manifest = json.loads((Path(__file__).resolve().parents[1]/'packages/nintendont.yaml').read_text())
            for item in manifest['files']:
                data = ('synthetic ' + item['source']).encode()
                (source/item['source'].split('/')[-1]).write_bytes(data)
                item.update(size=len(data), sha256=hashlib.sha256(data).hexdigest(),
                            git_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest())
            data = combine_packages([nintendont_bytes(manifest, source, 'original'), emulator('fceugx')])
            plan = plan_preparation(data, dest, 'original')
            result = execute_preparation(data, dest, 'original', plan, plan['digest'])
            self.assertEqual(len(result['written']), 6)
            self.assertTrue((dest/'apps/Nintendont/boot.dol').is_file())


class WindowsEncodingTests(unittest.TestCase):
    def test_powershell_utf8_bom_json_is_accepted(self):
        from wiiready.__main__ import read
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'plan.json'
            path.write_text('{"schema": 1}', encoding='utf-8-sig')
            self.assertEqual(read(path), {'schema': 1})
            path.write_text('{"schema": 1}', encoding='utf-16')
            with self.assertRaises(ValueError): read(path)
