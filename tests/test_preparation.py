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
from unittest.mock import Mock, patch
from wiiforge.prepare import plan_preparation, execute_preparation, _copy_new
from wiiforge.__main__ import read

ROOT = Path(__file__).resolve().parents[1]


def fixture(entries=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        for name, data in entries or [('apps/demo/a.txt', b'alpha'), ('apps/demo/b.txt', b'beta')]:
            archive.writestr(name, data)
    return stream.getvalue()


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.dest = self.root / 'destination'
        self.dest.mkdir()
        self.data = fixture()

    def execute(self, plan):
        return execute_preparation(self.data, self.dest, 'original', plan, plan['digest'])

    def test_plan_is_read_only_and_preparation_preserves_unrelated_data(self):
        unrelated = self.dest / 'keep.txt'
        unrelated.write_bytes(b'original')
        plan = plan_preparation(self.data, self.dest, 'original')
        self.assertEqual(list(self.dest.iterdir()), [unrelated])
        self.assertEqual(plan['required_bytes'], 9)
        self.assertEqual([f['action'] for f in plan['files']], ['create', 'create'])
        result = self.execute(plan)
        self.assertEqual(result['status'], 'files-prepared')
        self.assertFalse(result['installation_supported'])
        self.assertEqual(unrelated.read_bytes(), b'original')
        self.assertEqual((self.dest / 'apps/demo/a.txt').read_bytes(), b'alpha')
        resumed = self.execute(plan)
        self.assertEqual(resumed['written'], [])
        self.assertEqual(len(resumed['verified_existing']), 2)

    def test_conflicts_stop_before_any_writes(self):
        (self.dest / 'apps/demo').mkdir(parents=True)
        target = self.dest / 'apps/demo/b.txt'
        target.write_bytes(b'different')
        with self.assertRaises(ValueError):
            plan_preparation(self.data, self.dest, 'original')
        self.assertFalse((self.dest / 'apps/demo/a.txt').exists())
        self.assertEqual(target.read_bytes(), b'different')

    def test_changed_source_target_plan_or_approval_rejected(self):
        plan = plan_preparation(self.data, self.dest, 'original')
        with self.assertRaises(ValueError):
            execute_preparation(self.data, self.dest, 'original', plan, 'wrong')
        with self.assertRaises(ValueError):
            execute_preparation(fixture([('other', b'x')]), self.dest, 'original', plan, plan['digest'])
        changed = copy.deepcopy(plan)
        changed['files'][0]['path'] = '../escape'
        with self.assertRaises(ValueError):
            self.execute(changed)
        other = self.root / 'other'
        other.mkdir()
        with self.assertRaises(ValueError):
            execute_preparation(self.data, other, 'original', plan, plan['digest'])
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_symlinks_and_unsafe_archive_are_rejected(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (self.dest / 'apps').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(OSError):
            plan_preparation(self.data, self.dest, 'original')
        self.assertEqual(list(outside.iterdir()), [])
        with self.assertRaises(ValueError):
            plan_preparation(fixture([('../escape', b'x')]), outside, 'original')

    def test_resume_after_interruption_between_files(self):
        plan = plan_preparation(self.data, self.dest, 'original')
        count = 0
        def interrupt(archive, item, root):
            nonlocal count
            count += 1
            if count == 2:
                raise KeyboardInterrupt()
            _copy_new(archive, item, root)
        with patch('wiiforge.prepare._copy_new', interrupt), self.assertRaises(KeyboardInterrupt):
            self.execute(plan)
        result = self.execute(plan)
        self.assertEqual(result['verified_existing'], ['apps/demo/a.txt'])
        self.assertEqual(result['written'], ['apps/demo/b.txt'])

    def test_failure_during_copy_removes_only_new_file(self):
        plan = plan_preparation(self.data, self.dest, 'original')
        with patch('wiiforge.prepare.os.fsync', side_effect=OSError('simulated full disk')):
            with self.assertRaises(OSError):
                self.execute(plan)
        self.assertFalse((self.dest / 'apps/demo/a.txt').exists())
        self.assertEqual(len(self.execute(plan)['written']), 2)

    def test_incomplete_crash_leftover_never_overwritten(self):
        plan = plan_preparation(self.data, self.dest, 'original')
        (self.dest / 'apps/demo').mkdir(parents=True)
        target = self.dest / 'apps/demo/a.txt'
        target.write_bytes(b'al')
        with self.assertRaises(ValueError):
            self.execute(plan)
        self.assertEqual(target.read_bytes(), b'al')

    def test_destination_replacement_and_lost_preserved_file_rejected(self):
        plan = plan_preparation(self.data, self.dest, 'original')
        moved = self.root / 'moved'
        self.dest.rename(moved)
        self.dest.mkdir()
        with self.assertRaises(ValueError):
            self.execute(plan)
        self.assertEqual(list(self.dest.iterdir()), [])
        fresh = plan_preparation(self.data, self.dest, 'original')
        self.execute(fresh)
        preserved = plan_preparation(self.data, self.dest, 'original')
        (self.dest / 'apps/demo/a.txt').unlink()
        with self.assertRaises(ValueError):
            self.execute(preserved)
        self.assertFalse((self.dest / 'apps/demo/a.txt').exists())

    def test_destination_symlink_inserted_after_plan_rejected(self):
        plan = plan_preparation(self.data, self.dest, 'original')
        outside = self.root / 'outside'
        outside.mkdir()
        (self.dest / 'apps').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(OSError):
            self.execute(plan)
        self.assertEqual(list(outside.iterdir()), [])

    def test_space_and_models_fail_closed(self):
        with patch('wiiforge.prepare.os.fstatvfs', return_value=Mock(f_bavail=0, f_frsize=4096)):
            with self.assertRaisesRegex(ValueError, 'space'):
                plan_preparation(self.data, self.dest, 'original')
        for model in ['mini', 'vwii', 'family', 'unknown']:
            with self.assertRaises(ValueError):
                plan_preparation(self.data, self.dest, model)
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_cli_review_approve_and_resume(self):
        artifact = self.root / 'synthetic.zip'
        artifact.write_bytes(self.data)
        manifest = read(ROOT / 'packages/usb-loader-gx.yaml')
        manifest.update(size=len(self.data), sha256=hashlib.sha256(self.data).hexdigest())
        manifest_path = self.root / 'manifest.json'
        manifest_path.write_text(json.dumps(manifest))
        args = ['--manifest', str(manifest_path), '--artifact', str(artifact), '--model', 'original', '--destination', str(self.dest)]
        env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'))
        def run(command, extra=()):
            return subprocess.run([sys.executable, '-m', 'wiiforge', command, *args, *extra], env=env, capture_output=True, text=True)
        reviewed = run('prepare-plan')
        self.assertEqual(reviewed.returncode, 0, reviewed.stderr)
        plan = json.loads(reviewed.stdout)
        plan_path = self.root / 'plan.json'
        plan_path.write_text(reviewed.stdout)
        extra = ['--plan', str(plan_path), '--approve-plan', plan['digest']]
        for iteration in range(2):
            result = run('prepare', extra)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads(result.stdout)['installation_supported'])
        self.assertEqual(len(json.loads(result.stdout)['verified_existing']), 2)
