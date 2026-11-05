import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
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

    def test_cli_reports_verified_but_blocked(self):
        manifest = Path(self.tmp.name) / 'manifest.json'
        manifest.write_text(json.dumps(self.manifest))
        result = subprocess.run([sys.executable, '-m', 'wiiforge', 'verify-package',
                                 '--manifest', str(manifest), '--artifact', str(self.artifact),
                                 '--model', 'original'], capture_output=True, text=True,
                                env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'content-verified')
