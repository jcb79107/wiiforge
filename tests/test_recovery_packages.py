import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from wiiforge.__main__ import verify_package, package_bytes
from wiiforge.prepare import plan_preparation, execute_preparation

ROOT = Path(__file__).resolve().parents[1]


class RecoveryPackageTests(unittest.TestCase):
    def test_recovery_pins_verify_prepare_resume_and_keep_notices(self):
        for package, app in [('priiloader', 'priiloader'), ('loadpriiloader', 'LoadPriiloader'),
                             ('nanddumper-ios', 'nanddumper_ios'), ('d2x-cios-installer', 'd2x-cios-installer'),
                             ('cleanrip', 'CleanRip')]:
            with self.subTest(package=package), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                stream = io.BytesIO()
                with zipfile.ZipFile(stream, 'w') as archive:
                    archive.writestr('apps/' + app + '/boot.dol', b'Synthetic executable placeholder; never run')
                    if package == 'priiloader': archive.writestr('LICENSE', b'Synthetic notice')
                data = stream.getvalue()
                artifact = root / 'input.zip'; artifact.write_bytes(data)
                manifest = json.loads((ROOT / 'packages' / (package + '.yaml')).read_text())
                manifest.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
                result = verify_package(manifest, artifact, 'original', check_archive=True)
                self.assertEqual(result['status'], 'content-verified')
                self.assertIn('license-review-pending', result['blockers'])
                self.assertFalse(result['execution_supported'])
                snapshot = package_bytes(manifest, artifact, 'original')
                destination = root / 'destination'; destination.mkdir()
                plan = plan_preparation(snapshot, destination, 'original')
                self.assertEqual(list(destination.iterdir()), [])
                for expected in [len(plan['files']), 0]:
                    prepared = execute_preparation(snapshot, destination, 'original', plan, plan['digest'])
                    self.assertEqual(len(prepared['written']), expected)
                if package == 'priiloader': self.assertEqual((destination / 'LICENSE').read_bytes(), b'Synthetic notice')
                for field, value in [('version', '0.11.0'), ('asset', 'PriiloaderWiiUForwarder.zip'),
                                     ('url', 'https://example.com/input.zip'), ('digest_source', 'unreviewed')]:
                    with self.assertRaises(ValueError):
                        verify_package(dict(manifest, **{field: value}), artifact, 'original')
                for model in ['family', 'mini', 'vwii', 'unknown']:
                    with self.assertRaises(ValueError): verify_package(manifest, artifact, model)
                if package == 'cleanrip':
                    with self.assertRaises(ValueError):
                        verify_package(dict(manifest, asset='CleanRip-v2.4-gc.zip'), artifact, 'original')
                artifact.write_bytes(data[:-1])
                with self.assertRaises(ValueError): verify_package(manifest, artifact, 'original')

    def test_existing_root_license_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'LICENSE').write_bytes(b'Existing user file')
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, 'w') as archive:
                archive.writestr('LICENSE', b'Different notice')
                archive.writestr('apps/priiloader/boot.dol', b'Synthetic')
            with self.assertRaises(ValueError): plan_preparation(stream.getvalue(), root, 'original')
            self.assertEqual((root / 'LICENSE').read_bytes(), b'Existing user file')
            self.assertFalse((root / 'apps').exists())
