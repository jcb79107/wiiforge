import hashlib
import json
import os
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from wiiforge.__main__ import read, verify_package

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.artifact = Path(self.tmp.name) / 'synthetic.zip'
        self.artifact.write_bytes(b'synthetic bytes, deliberately not an archive')
        self.manifest = read(ROOT / 'packages/usb-loader-gx.yaml')
        self.manifest.update(size=self.artifact.stat().st_size,
                             sha256=hashlib.sha256(self.artifact.read_bytes()).hexdigest())

    def test_match_is_not_installation_approval(self):
        result = verify_package(self.manifest, self.artifact, 'original')
        self.assertEqual(result['status'], 'content-verified')
        self.assertIn('license-review-pending', result['blockers'])
        self.assertIn('archive-safety-unverified', result['blockers'])
        self.assertFalse(result['execution_supported'])

    def test_optional_archive_check_remains_blocked(self):
        with zipfile.ZipFile(self.artifact, 'w') as output:
            output.writestr('apps/usbloader_gx/boot.dol', b'synthetic')
        self.manifest.update(size=self.artifact.stat().st_size,
                             sha256=hashlib.sha256(self.artifact.read_bytes()).hexdigest())
        result = verify_package(self.manifest, self.artifact, 'original', check_archive=True)
        self.assertEqual(result['archive']['status'], 'metadata-checked')
        self.assertIn('archive-content-unverified', result['blockers'])
        self.assertIn('license-review-pending', result['blockers'])
        self.assertFalse(result['execution_supported'])
        self.manifest['sha256'] = 'a' * 64
        with patch('wiiforge.__main__.check_zip', side_effect=AssertionError('Unverified bytes parsed')):
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                verify_package(self.manifest, self.artifact, 'original', check_archive=True)

    def test_experimental_stage_uses_verified_snapshot_and_keeps_blockers(self):
        with zipfile.ZipFile(self.artifact, 'w') as output:
            output.writestr('apps/demo/readme.txt', b'synthetic')
        original = self.artifact.read_bytes()
        self.manifest.update(size=len(original), sha256=hashlib.sha256(original).hexdigest())
        result = verify_package(self.manifest, self.artifact, 'original', experimental_stage=True)
        self.assertFalse(result['staging']['synthetic'])
        self.assertEqual(result['staging']['status'], 'experimental-stage-verified')
        self.assertTrue(result['staging']['temporary_files_removed'])
        self.assertFalse(result['execution_supported'])
        self.assertIn('license-review-pending', result['blockers'])
        self.assertIn('hardware-untested', result['blockers'])
        self.assertEqual(self.artifact.read_bytes(), original)
        with patch('wiiforge.__main__._stage_zip', return_value={}) as stage:
            verify_package(self.manifest, self.artifact, 'original', experimental_stage=True)
            stage.assert_called_once_with(original, synthetic=False)
        self.manifest['sha256'] = 'a' * 64
        with patch('wiiforge.__main__._stage_zip') as stage:
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                verify_package(self.manifest, self.artifact, 'original', experimental_stage=True)
            stage.assert_not_called()

    def test_wrong_size_and_hash_rejected(self):
        for change in [{'size': 1}, {'sha256': 'a' * 64}]:
            with self.assertRaises(ValueError):
                verify_package(dict(self.manifest, **change), self.artifact, 'original')

    def test_invalid_manifest_and_models_fail_before_file_access(self):
        for change in [{'url': 'https://example.org/evil.zip'}, {'sha256': None},
                       {'schema': True}, {'version': 'latest'}, {'asset': '../evil.zip'},
                       {'models': ['vwii']}, {'license_review': 'approved'}, {'extra': 1},
                       {'size': True}, {'size': 1000000000}, {'digest_source': 'self-computed'}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                verify_package(dict(self.manifest, **change), '/nonexistent', 'original')
        for model in ['family', 'mini', 'vwii', 'unknown']:
            with self.assertRaises(ValueError):
                verify_package(self.manifest, '/nonexistent', model)

    @unittest.skipUnless(hasattr(os, 'O_NOFOLLOW'), 'Host supports no-follow opens')
    def test_symlink_rejected(self):
        link = Path(self.tmp.name) / 'link'
        link.symlink_to(self.artifact)
        with self.assertRaises(OSError):
            verify_package(self.manifest, link, 'original')

    def test_file_changes_during_verification_are_rejected(self):
        original = self.artifact.read_bytes()
        real_fstat = os.fstat
        for change, message in [('truncate', 'truncated'), ('grow', 'grew'),
                                ('metadata', 'changed')]:
            self.artifact.write_bytes(original)
            calls = 0

            def mutate_after_initial_stat(fd):
                nonlocal calls
                info = real_fstat(fd)
                calls += 1
                if calls == 1:
                    if change == 'truncate':
                        self.artifact.write_bytes(original[:5])
                    elif change == 'grow':
                        self.artifact.write_bytes(original + b'extra')
                    else:
                        os.utime(self.artifact, ns=(info.st_atime_ns, info.st_mtime_ns + 2000000000))
                return info

            with self.subTest(change=change), patch('wiiforge.__main__.os.fstat', mutate_after_initial_stat):
                with self.assertRaisesRegex(ValueError, message):
                    verify_package(self.manifest, self.artifact, 'original')

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX FIFO check')
    def test_nonregular_artifact_is_rejected_without_blocking(self):
        fifo = Path(self.tmp.name) / 'fifo'
        os.mkfifo(fifo)
        manifest = Path(self.tmp.name) / 'manifest.json'
        manifest.write_text(json.dumps(self.manifest))
        result = subprocess.run([sys.executable, '-m', 'wiiforge', 'verify-package',
                                 '--manifest', str(manifest), '--artifact', str(fifo),
                                 '--model', 'original'], capture_output=True, text=True, timeout=5,
                                env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')))
        self.assertEqual(result.returncode, 2)
        self.assertIn('regular file', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(result.stdout, '')

    def test_cli_corrupt_deflate_and_unsupported_flags_are_clean(self):
        scratch = Path(self.tmp.name) / 'scratch'
        scratch.mkdir()
        for kind in ['deflate', 'patched-data']:
            with zipfile.ZipFile(self.artifact, 'w', compression=zipfile.ZIP_DEFLATED) as output:
                output.writestr('a.txt', b'synthetic')
            data = bytearray(self.artifact.read_bytes())
            if kind == 'deflate':
                name_length, extra_length = struct.unpack_from('<HH', data, 26)
                data[30 + name_length + extra_length] = 7  # Reserved DEFLATE block type.
            else:
                central = data.index(b'PK\x01\x02')
                struct.pack_into('<H', data, central + 8, 1 << 5)
                struct.pack_into('<H', data, 6, 1 << 5)
            self.artifact.write_bytes(data)
            self.manifest.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
            manifest = Path(self.tmp.name) / 'manifest.json'
            manifest.write_text(json.dumps(self.manifest))
            result = subprocess.run([sys.executable, '-m', 'wiiforge', 'verify-package',
                                     '--manifest', str(manifest), '--artifact', str(self.artifact),
                                     '--model', 'original', '--experimental-stage'], capture_output=True, text=True,
                                    env=dict(os.environ, PYTHONPATH=str(ROOT / 'src'), TMPDIR=str(scratch)))
            with self.subTest(kind=kind):
                self.assertEqual(result.returncode, 2)
                self.assertIn('Invalid or unsupported ZIP contents', result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertEqual(result.stdout, '')
                self.assertEqual(list(scratch.iterdir()), [])

    def test_cli_staging_crc_error_is_clean(self):
        with zipfile.ZipFile(self.artifact, 'w') as output:
            output.writestr('a.txt', b'synthetic')
        data = self.artifact.read_bytes().replace(b'synthetic', b'corrupted', 1)
        self.artifact.write_bytes(data)
        self.manifest.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
        manifest = Path(self.tmp.name) / 'manifest.json'
        manifest.write_text(json.dumps(self.manifest))
        result = subprocess.run([sys.executable, '-m', 'wiiforge', 'verify-package',
                                 '--manifest', str(manifest), '--artifact', str(self.artifact),
                                 '--model', 'original', '--experimental-stage'], capture_output=True, text=True,
                                env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')))
        self.assertEqual(result.returncode, 2)
        self.assertIn('CRC', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(result.stdout, '')

    def test_cli_reports_verified_but_blocked(self):
        manifest = Path(self.tmp.name) / 'manifest.json'
        manifest.write_text(json.dumps(self.manifest))
        result = subprocess.run([sys.executable, '-m', 'wiiforge', 'verify-package',
                                 '--manifest', str(manifest), '--artifact', str(self.artifact),
                                 '--model', 'original'], capture_output=True, text=True,
                                env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'content-verified')
