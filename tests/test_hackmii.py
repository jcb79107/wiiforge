import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from wiiforge.hackmii import MEMBERS, hackmii_snapshot
from wiiforge.__main__ import package_bytes, verify_package
from wiiforge.prepare import plan_preparation, execute_preparation

ROOT = Path(__file__).resolve().parents[1]


def fixture(missing=None, extra=None):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        for name in MEMBERS:
            if name != missing:
                archive.writestr('hackmii_installer_v1.2/' + name, ('Synthetic: ' + name).encode())
        archive.writestr('hackmii_installer_v1.2/bootmini.elf', b'Never select')
        archive.writestr('hackmii_installer_v1.2/wiiload/win32/wiiload.exe', b'Never select')
        if extra: archive.writestr(extra, b'Unsafe')
    return output.getvalue()


class HackMiiTests(unittest.TestCase):
    def test_selects_only_installer_and_preserves_notice_bytes(self):
        data = fixture()
        snapshot = hackmii_snapshot(data)
        self.assertEqual(snapshot, hackmii_snapshot(data))
        with zipfile.ZipFile(io.BytesIO(snapshot)) as archive:
            expected = {'boot.elf'} | {'wiiforge-notices/hackmii/' + name for name in MEMBERS if name != 'boot.elf'}
            self.assertEqual(set(archive.namelist()), expected)
            for name in MEMBERS:
                destination = name if name == 'boot.elf' else 'wiiforge-notices/hackmii/' + name
                self.assertEqual(archive.read(destination), ('Synthetic: ' + name).encode())

    def test_missing_notices_and_traversal_rejected(self):
        for name in MEMBERS:
            with self.subTest(name=name), self.assertRaises(ValueError):
                hackmii_snapshot(fixture(missing=name))
        with self.assertRaises(ValueError): hackmii_snapshot(fixture(extra='../outside'))
        with self.assertRaises((ValueError, zipfile.BadZipFile)): hackmii_snapshot(fixture()[:-30])

    def test_pinned_input_prepares_and_refuses_boot_elf_conflict(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source.zip'
            data = fixture(); source.write_bytes(data)
            manifest = json.loads((ROOT / 'packages/hackmii.yaml').read_text())
            manifest.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
            snapshot = package_bytes(manifest, source, 'original')
            destination = root / 'destination'; destination.mkdir()
            plan = plan_preparation(snapshot, destination, 'original')
            self.assertEqual(list(destination.iterdir()), [])
            result = execute_preparation(snapshot, destination, 'original', plan, plan['digest'])
            self.assertEqual(len(result['written']), len(MEMBERS))
            self.assertFalse((destination / 'bootmini.elf').exists())
            self.assertFalse((destination / 'wiiload').exists())
            result = execute_preparation(snapshot, destination, 'original', plan, plan['digest'])
            self.assertEqual(result['written'], [])
            (destination / 'boot.elf').write_bytes(b'Existing other app')
            with self.assertRaises(ValueError): plan_preparation(snapshot, destination, 'original')
            self.assertEqual((destination / 'boot.elf').read_bytes(), b'Existing other app')
            for model in ['family', 'mini', 'vwii', 'unknown']:
                with self.assertRaises(ValueError): package_bytes(manifest, source, model)
            with self.assertRaises(ValueError): package_bytes(dict(manifest, asset='bootmini.elf'), source, 'original')
            with self.assertRaises(ValueError): package_bytes(dict(manifest, url='http://bootmii.org/hackmii_installer_v1.2.zip'), source, 'original')
            staged = verify_package(manifest, source, 'original', experimental_stage=True)
            self.assertNotIn('bootmini.elf', staged['staging']['files'])
            self.assertEqual(set(staged['staging']['files']), {item['path'] for item in plan['files']})
            self.assertFalse(staged['execution_supported'])
