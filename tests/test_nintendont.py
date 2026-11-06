import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from types import SimpleNamespace
from wiiready.nintendont import nintendont_bytes
from wiiready.prepare import plan_preparation, execute_preparation

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'posix', 'Nintendont preparation requires POSIX')
class NintendontTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.dest = self.root / 'destination'
        self.dest.mkdir()
        self.manifest = json.loads((ROOT / 'packages/nintendont.yaml').read_text())
        self.payloads = {}
        for item in self.manifest['files']:
            name = item['source'].split('/')[-1]
            data = ('Synthetic fixture: ' + name).encode()
            self.payloads[item['destination']] = data
            (self.source / name).write_bytes(data)
            item.update(size=len(data), sha256=hashlib.sha256(data).hexdigest(),
                        git_blob=hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest())

    def snapshot(self):
        return nintendont_bytes(self.manifest, self.source, 'original')

    def test_fixed_layout_deterministic_and_extras_ignored(self):
        (self.source / 'unrelated.txt').write_text('Do not copy')
        data = self.snapshot()
        self.assertEqual(data, self.snapshot())
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertEqual(set(archive.namelist()), set(self.payloads))
            for path, expected in self.payloads.items():
                self.assertEqual(archive.read(path), expected)
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_bad_pin_origin_model_and_destination_fail_closed(self):
        bad = []
        for key, value in [('repository', 'https://example.com'), ('commit', 'master'),
                           ('models', ['original', 'vwii']), ('license_review', 'approved'), ('schema', True)]:
            m = copy.deepcopy(self.manifest); m[key] = value; bad.append(m)
        for key, value in [('destination', '../boot.dol'), ('source', 'other/loader.dol'),
                           ('size', 100000000), ('sha256', '0' * 64), ('git_blob', '0' * 40)]:
            m = copy.deepcopy(self.manifest); m['files'][0][key] = value; bad.append(m)
        m = copy.deepcopy(self.manifest); m['files'].append(m['files'][0]); bad.append(m)
        for manifest in bad:
            with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                nintendont_bytes(manifest, self.source, 'original')
        for model in ['family', 'mini', 'vwii', 'unknown']:
            with self.assertRaises(ValueError):
                nintendont_bytes(self.manifest, self.source, model)
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_changed_truncated_grown_and_nonregular_inputs_rejected(self):
        target = self.source / 'loader.dol'
        original = target.read_bytes()
        for value in [original[:-1], original + b'x', b'x' * len(original)]:
            target.write_bytes(value)
            with self.assertRaises(ValueError): self.snapshot()
        target.unlink()
        target.symlink_to(self.source / 'meta.xml')
        with self.assertRaises(OSError): self.snapshot()
        target.unlink(); os.mkfifo(target)
        with self.assertRaises(ValueError): self.snapshot()
        target.unlink(); target.mkdir()
        with self.assertRaises((ValueError, OSError)): self.snapshot()

    def test_metadata_change_during_read_rejected(self):
        real = os.fstat
        calls = []
        def changing(fd):
            info = real(fd)
            calls.append(fd)
            if len(calls) == 2:
                return SimpleNamespace(st_size=info.st_size, st_mtime_ns=info.st_mtime_ns + 1,
                                       st_ctime_ns=info.st_ctime_ns)
            return info
        with patch('wiiready.nintendont.os.fstat', side_effect=changing), self.assertRaisesRegex(ValueError, 'changed'):
            self.snapshot()

    def test_source_directory_symlink_rejected(self):
        link = self.root / 'link'
        link.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(OSError):
            nintendont_bytes(self.manifest, link, 'original')

    def test_prepare_resume_conflict_and_interruption(self):
        data = self.snapshot()
        plan = plan_preparation(data, self.dest, 'original')
        from wiiready import prepare
        real_copy = prepare._copy_new
        calls = []
        def interrupted(archive, item, root):
            calls.append(item['path'])
            if len(calls) == 2: raise KeyboardInterrupt()
            return real_copy(archive, item, root)
        with patch('wiiready.prepare._copy_new', side_effect=interrupted), self.assertRaises(KeyboardInterrupt):
            execute_preparation(data, self.dest, 'original', plan, plan['digest'])
        result = execute_preparation(data, self.dest, 'original', plan, plan['digest'])
        self.assertEqual(len(result['verified_existing']), 1)
        self.assertEqual(len(result['written']), 2)
        for path, data in self.payloads.items(): self.assertEqual((self.dest / path).read_bytes(), data)
        self.assertIn('hardware-untested', result['installation_blockers'])
        conflict = self.dest / 'apps/Nintendont/boot.dol'
        conflict.write_bytes(b'keep this existing file')
        with self.assertRaises(ValueError):
            execute_preparation(self.snapshot(), self.dest, 'original', plan, plan['digest'])
        self.assertEqual(conflict.read_bytes(), b'keep this existing file')

    def test_cli_verify_plan_approval_prepare_and_resume(self):
        manifest = self.root / 'manifest.json'
        manifest.write_text(json.dumps(self.manifest))
        planpath = self.root / 'plan.json'
        common = ['--manifest', str(manifest), '--artifact', str(self.source), '--model', 'original']
        def cli(command, *extra):
            return subprocess.run([sys.executable, '-m', 'wiiready', command, *common, *extra],
                                  cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT / 'src')),
                                  capture_output=True, text=True)
        verified = cli('verify-package', '--check-archive')
        self.assertEqual(verified.returncode, 2, verified.stderr)
        self.assertEqual(json.loads(verified.stdout)['status'], 'content-verified')
        planned = cli('prepare-plan', '--destination', str(self.dest))
        self.assertEqual(planned.returncode, 0, planned.stderr)
        self.assertEqual(list(self.dest.iterdir()), [])
        planpath.write_text(planned.stdout)
        extra = ['--destination', str(self.dest), '--plan', str(planpath), '--approve-plan']
        rejected = cli('prepare', *extra, 'wrong')
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(list(self.dest.iterdir()), [])
        for expected in [3, 0]:
            prepared = cli('prepare', *extra, json.loads(planned.stdout)['digest'])
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            self.assertEqual(len(json.loads(prepared.stdout)['written']), expected)
