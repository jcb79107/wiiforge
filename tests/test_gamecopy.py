import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from wiiready.gamecopy import plan_game_copy, execute_game_copy
from wiiready import prepare
from test_games import synthetic_header


@unittest.skipUnless(os.name == 'posix', 'Game copying is POSIX-only')
class GameCopyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'one.gcm'
        self.second = self.root / 'two.iso'
        self.source.write_bytes(synthetic_header() + b'Invented first-disc content')
        self.second.write_bytes(synthetic_header(disc=1) + b'Invented second-disc content')
        self.destination = self.root / 'destination'
        self.destination.mkdir()

    def plan(self, second=None):
        return plan_game_copy(self.source, second, self.destination, 'original')

    def execute(self, plan, second=None):
        return execute_game_copy(self.source, second, self.destination, 'original', plan, plan['digest'])

    def test_plan_hashes_full_files_and_copy_preserves_sources_and_unrelated_files(self):
        original = self.source.read_bytes(), self.second.read_bytes()
        (self.destination / 'keep.txt').write_bytes(b'Keep me')
        plan = self.plan(self.second)
        self.assertEqual(list(self.destination.iterdir()), [self.destination / 'keep.txt'])
        self.assertEqual({f['sha256'] for f in plan['files']}, {hashlib.sha256(data).hexdigest() for data in original})
        self.assertEqual({f['path'] for f in plan['files']}, {'games/TEST00/game.iso', 'games/TEST00/disc2.iso'})
        result = self.execute(plan, self.second)
        self.assertTrue(result['copy_bytes_verified'])
        self.assertFalse(result['dump_integrity_verified'])
        self.assertFalse(result['gameplay_verified'])
        self.assertEqual((self.destination / 'games/TEST00/game.iso').read_bytes(), original[0])
        self.assertEqual((self.destination / 'games/TEST00/disc2.iso').read_bytes(), original[1])
        self.assertEqual((self.destination / 'keep.txt').read_bytes(), b'Keep me')
        self.assertEqual((self.source.read_bytes(), self.second.read_bytes()), original)
        self.assertEqual(self.execute(plan, self.second)['written'], [])

    def test_approval_plan_tampering_and_changed_source_block_before_writes(self):
        plan = self.plan()
        with self.assertRaises(ValueError):
            execute_game_copy(self.source, None, self.destination, 'original', plan, 'wrong')
        changed = copy.deepcopy(plan); changed['files'][0]['path'] = '../outside'
        with self.assertRaises(ValueError): self.execute(changed)
        changed['digest'] = prepare.digest({k: v for k, v in changed.items() if k != 'digest'})
        with self.assertRaises(ValueError): self.execute(changed)
        self.source.write_bytes(self.source.read_bytes()[:-1] + b'X')
        with self.assertRaises(ValueError): self.execute(plan)
        self.assertEqual(list(self.destination.iterdir()), [])

    def test_existing_conflict_blocks_and_identical_content_can_be_preserved(self):
        target = self.destination / 'games/TEST00/game.iso'
        target.parent.mkdir(parents=True)
        target.write_bytes(b'Existing game or save; leave alone')
        with self.assertRaises(ValueError): self.plan()
        self.assertEqual(target.read_bytes(), b'Existing game or save; leave alone')
        target.write_bytes(self.source.read_bytes())
        plan = self.plan()
        self.assertEqual(plan['files'][0]['action'], 'keep')
        self.assertEqual(self.execute(plan)['written'], [])
        target.unlink()
        with self.assertRaises(ValueError): self.execute(plan)

    def test_interrupt_between_discs_resumes_completed_content(self):
        plan = self.plan(self.second)
        original = prepare._copy_new
        calls = 0
        def interrupted(*args):
            nonlocal calls
            calls += 1
            if calls == 2: raise KeyboardInterrupt()
            return original(*args)
        with patch('wiiready.prepare._copy_new', side_effect=interrupted), self.assertRaises(KeyboardInterrupt):
            self.execute(plan, self.second)
        result = self.execute(plan, self.second)
        self.assertEqual(len(result['verified_existing']), 1)
        self.assertEqual(len(result['written']), 1)

    def test_source_change_during_copy_removes_only_new_incomplete_file(self):
        plan = self.plan()
        original = prepare._copy_new
        def mutate(archive, item, root):
            # After revalidation, before copying: the source identity check must stop it.
            self.source.write_bytes(self.source.read_bytes() + b'changed')
            return original(archive, item, root)
        with patch('wiiready.prepare._copy_new', side_effect=mutate), self.assertRaises(ValueError):
            self.execute(plan)
        self.assertFalse((self.destination / 'games/TEST00/game.iso').exists())

    def test_interruption_inside_copy_removes_partial_output_and_keeps_source(self):
        from wiiready import gamecopy
        source_bytes = self.source.read_bytes()
        plan = self.plan()
        class Interrupted:
            calls = 0
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size):
                self.calls += 1
                if self.calls == 1: return source_bytes[:512]
                raise KeyboardInterrupt()
        with patch.object(gamecopy._LocalImages, 'open', return_value=Interrupted()), self.assertRaises(KeyboardInterrupt):
            self.execute(plan)
        self.assertFalse((self.destination / 'games/TEST00/game.iso').exists())
        self.assertEqual(self.source.read_bytes(), source_bytes)
        self.assertEqual(len(self.execute(plan)['written']), 1)

    def test_changed_destination_identity_and_source_hashing_changes_reject(self):
        plan = self.plan()
        self.destination.rename(self.root / 'old-destination')
        self.destination.mkdir()
        with self.assertRaises(ValueError): self.execute(plan)
        original_fstat = os.fstat
        calls = 0
        def changed(fd):
            nonlocal calls
            calls += 1
            info = original_fstat(fd)
            if calls == 2:
                return SimpleNamespace(st_dev=info.st_dev, st_ino=info.st_ino,
                                       st_size=info.st_size, st_mtime_ns=info.st_mtime_ns + 1,
                                       st_ctime_ns=info.st_ctime_ns)
            return info
        with patch('wiiready.gamecopy.os.fstat', side_effect=changed), self.assertRaisesRegex(ValueError, 'changed'):
            self.plan()
        self.assertEqual(list(self.destination.iterdir()), [])

    def test_bad_models_paths_and_space_rejected(self):
        for model in ['mini', 'family', 'vwii', 'unknown']:
            with self.assertRaises(ValueError): plan_game_copy(self.source, None, self.destination, model)
        self.second.write_bytes(synthetic_header(b'OTHER0', disc=1))
        with self.assertRaises(ValueError): self.plan(self.second)
        link = self.root / 'link.iso'; link.symlink_to(self.source)
        with self.assertRaises(ValueError): plan_game_copy(link, None, self.destination, 'original')
        fifo = self.root / 'pipe.iso'; os.mkfifo(fifo)
        with self.assertRaises(ValueError): plan_game_copy(fifo, None, self.destination, 'original')
        (self.destination / 'games').symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(OSError): self.plan()
        (self.destination / 'games').unlink()
        with patch('wiiready.prepare.os.fstatvfs', return_value=SimpleNamespace(f_bavail=0, f_frsize=4096)):
            with self.assertRaises(ValueError): self.plan()
        self.assertEqual(list(self.destination.iterdir()), [])

    def test_cli_saved_plan_and_explicit_digest_are_required(self):
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
        common = ['--disc1', str(self.source), '--destination', str(self.destination), '--model', 'original']
        def cli(command, *args):
            return subprocess.run([sys.executable, '-m', 'wiiready', command, *common, *args],
                                  env=env, capture_output=True, text=True)
        planned = cli('gamecube-plan')
        self.assertEqual(planned.returncode, 0, planned.stderr)
        saved = self.root / 'plan.json'; saved.write_text(planned.stdout)
        self.assertEqual(cli('gamecube-copy').returncode, 2)
        self.assertEqual(cli('gamecube-copy', '--plan', str(saved), '--approve-plan', 'wrong').returncode, 2)
        self.assertEqual(list(self.destination.iterdir()), [])
        copied = cli('gamecube-copy', '--plan', str(saved), '--approve-plan', json.loads(planned.stdout)['digest'])
        self.assertEqual(copied.returncode, 0, copied.stderr)
        self.assertEqual(json.loads(copied.stdout)['status'], 'game-files-copied')


class GameCopyHostTests(unittest.TestCase):
    def test_unknown_host_is_blocked_before_source_or_destination_access(self):
        with patch('wiiready.gamecopy.os.name', 'unsupported'), self.assertRaisesRegex(ValueError, 'POSIX'):
            plan_game_copy('missing.iso', None, 'missing-destination', 'original')
