from contextlib import contextmanager
import io
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from wiiready.wiijoin import plan_wii_join, execute_wii_join
from wiiready.prepare import summarize_plan


@unittest.skipUnless(os.name == 'posix', 'POSIX directory descriptors required')
class JoinTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.parts = [self.root / ('invented.part%d.iso' % n) for n in range(3)]
        self.data = [b'a' * 70001, b'b' * 80003, b'c' * 17]
        for path, data in zip(self.parts, self.data): path.write_bytes(data)
        self.sha1 = hashlib.sha1(b''.join(self.data)).hexdigest()
        self.dest = self.root / 'staging'; self.dest.mkdir()

    def plan(self):
        return plan_wii_join(self.parts, self.sha1, self.dest, 'original')

    def run_join(self, plan):
        return execute_wii_join(self.parts, self.sha1, self.dest, 'original', plan, plan['digest'])

    def test_plan_copy_readback_and_verified_resume(self):
        plan = self.plan()
        self.assertEqual(list(self.dest.iterdir()), [])
        self.assertEqual(summarize_plan(plan)['operation'], 'wii-join')
        result = self.run_join(plan)
        self.assertTrue(result['supplied_checksum_matched'])
        self.assertFalse(result['image_format_verified'])
        self.assertEqual((self.dest / 'joined.iso').read_bytes(), b''.join(self.data))
        self.assertEqual(self.run_join(plan)['verified_existing'], ['joined.iso'])
        self.assertEqual([p.read_bytes() for p in self.parts], self.data)

    def test_bad_approval_and_conflict_do_not_write(self):
        plan = self.plan()
        with self.assertRaises(ValueError):
            execute_wii_join(self.parts, self.sha1, self.dest, 'original', plan, 'wrong')
        target = self.dest / 'joined.iso'; target.write_bytes(b'keep me')
        with self.assertRaises(ValueError): self.run_join(plan)
        self.assertEqual(target.read_bytes(), b'keep me')

    def test_checksum_order_missing_duplicate_and_mixed_parts_rejected(self):
        for parts in [self.parts[::-1], self.parts[1:], self.parts[:1], self.parts[:2], self.parts + [self.parts[0]]]:
            with self.assertRaises(ValueError): plan_wii_join(parts, self.sha1, self.dest, 'original')
        for checksum in ['x', '0' * 40]:
            with self.assertRaises(ValueError): plan_wii_join(self.parts, checksum, self.dest, 'original')
        other = self.root / 'other.part1.iso'; other.write_bytes(self.data[1])
        with self.assertRaises(ValueError): plan_wii_join([self.parts[0], other], self.sha1, self.dest, 'original')
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_changed_source_requires_new_plan_even_with_same_bytes(self):
        plan = self.plan()
        p = self.parts[1]; before = p.stat()
        os.utime(p, ns=(before.st_atime_ns, before.st_mtime_ns + 1000000))
        with self.assertRaises(ValueError): self.run_join(plan)
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_source_content_change_and_size_bounds(self):
        plan = self.plan()
        self.parts[0].write_bytes(b'changed')
        with self.assertRaises(ValueError): self.run_join(plan)
        with patch('wiiready.wiijoin.MAX_BYTES', 20):
            with self.assertRaises(ValueError): self.plan()
        self.parts[0].write_bytes(b'')
        with self.assertRaises(ValueError): self.plan()

    def test_nonregular_symlink_and_hardlink_duplicates_rejected(self):
        part = self.parts[1]; part.unlink(); part.symlink_to(self.parts[0])
        with self.assertRaises(ValueError): self.plan()
        part.unlink(); os.mkfifo(part)
        with self.assertRaises(ValueError): self.plan()
        part.unlink(); os.link(self.parts[0], part)
        with self.assertRaises(ValueError): self.plan()

    def test_interruption_cleans_only_new_output_and_retry_succeeds(self):
        plan = self.plan()
        from wiiready import wiijoin
        original = wiijoin._chunks
        calls = 0
        def interrupted(sources):
            nonlocal calls
            calls += 1
            if calls == 1:
                yield from original(sources)  # Execution preflight succeeds.
            else:
                yield b'a' * 65536
                raise KeyboardInterrupt()
        with patch.object(wiijoin, '_chunks', interrupted):
            with self.assertRaises(KeyboardInterrupt): self.run_join(plan)
        self.assertEqual(list(self.dest.iterdir()), [])
        self.run_join(plan)

    def test_copy_time_corruption_is_rejected_and_removed(self):
        plan = self.plan()
        from wiiready import wiijoin
        original = wiijoin._chunks
        calls = 0
        def corrupt(sources):
            nonlocal calls
            calls += 1
            if calls == 1: yield from original(sources)
            else: yield b'x' * sum(len(d) for d in self.data)
        with patch.object(wiijoin, '_chunks', corrupt):
            with self.assertRaises(ValueError): self.run_join(plan)
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_stream_rejects_growth_truncation_and_identity_change(self):
        from wiiready.wiijoin import _chunks
        identity = {'bytes': 4, 'inode': 1}
        for data, actual in [(b'abc', identity), (b'abcde', identity), (b'abcd', {'bytes': 4, 'inode': 2})]:
            @contextmanager
            def fake_part(path):
                yield io.BytesIO(data), actual
            with patch('wiiready.wiijoin._part', fake_part):
                with self.assertRaises(ValueError):
                    list(_chunks([{'path': 'synthetic', 'identity': identity}]))

    def test_model_and_destination_changes_rejected(self):
        for model in ['mini', 'family', 'vwii', 'unknown']:
            with self.assertRaises(ValueError): plan_wii_join(self.parts, self.sha1, self.dest, model)
        plan = self.plan()
        self.dest.rename(self.root / 'old'); self.dest.mkdir()
        with self.assertRaises(ValueError): self.run_join(plan)

    def test_cli_plan_summary_and_approved_join(self):
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
        common = ['--model', 'original', '--dump-sha1', self.sha1, '--destination', str(self.dest)]
        for part in self.parts: common += ['--part', str(part)]
        def cli(command, *extra):
            return subprocess.run([sys.executable, '-m', 'wiiready', command] + common + list(extra),
                                  env=env, text=True, capture_output=True)
        planned = cli('wii-join-plan'); self.assertEqual(planned.returncode, 0, planned.stderr)
        plan = json.loads(planned.stdout)
        saved = self.root / 'plan.json'; saved.write_text(planned.stdout)
        self.assertEqual(cli('wii-join', '--plan', str(saved), '--approve-plan', 'wrong').returncode, 2)
        copied = cli('wii-join', '--plan', str(saved), '--approve-plan', plan['digest'])
        self.assertEqual(copied.returncode, 0, copied.stderr)


class HostGateTests(unittest.TestCase):
    def test_unknown_host_rejected_before_source_access(self):
        with patch('wiiready.wiijoin.os.name', 'unsupported'):
            with self.assertRaisesRegex(ValueError, 'POSIX'):
                plan_wii_join([], '0' * 40, 'missing', 'original')
