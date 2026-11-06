import copy
import json
import tempfile
import subprocess
import sys
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from wiiready.__main__ import demo, evidence, inspect, normalize, plan, profile, read, resume

ROOT = Path(__file__).resolve().parents[1]


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.p = read(ROOT / 'profiles/original-wii.yaml')
        self.e = {'schema': 1, 'model': 'original', 'model_source': 'user-observation',
                  'region': 'U', 'region_source': 'user-observation', 'menu': '4.3U'}
        self.info = {'DeviceIdentifier': 'disk9', 'DiskUUID': 'synthetic-id', 'TotalSize': 2000000000,
                     'Internal': False, 'Whole': True, 'VirtualOrPhysical': 'Physical',
                     'Content': 'FDisk_partition_scheme'}
        self.parts = [{'DeviceIdentifier': 'disk9s1', 'PartitionType': 'DOS_FAT_32',
                       'FilesystemType': 'msdos', 'TotalSize': 1999000000,
                       'VolumeAllocationBlockSize': 32768}]
        self.d = normalize(self.info, self.parts)

    @patch('wiiready.__main__.diskutil', side_effect=AssertionError('Demo accessed hardware'))
    def test_demo_is_synthetic_and_has_no_completed_checkpoints(self, diskutil):
        result = demo()
        self.assertTrue(result['demo'])
        self.assertEqual(result['manual_plan']['status'], 'manual-review-only')
        self.assertFalse(result['manual_plan']['execution_supported'])
        self.assertEqual(result['unknown_model_plan']['status'], 'blocked')
        self.assertEqual(result['unknown_model_plan']['steps'], [])
        self.assertEqual(result['initial_state']['completed'], [])
        diskutil.assert_not_called()

    def test_demo_cli_and_help(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'))
        result = subprocess.run([sys.executable, '-m', 'wiiready', 'demo'],
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['demo'])
        result = subprocess.run([sys.executable, '-m', 'wiiready', '--help'],
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Try synthetic plans', result.stdout)

    def test_valid_plan_is_never_executable(self):
        p = plan(self.p, self.e, self.d)
        self.assertEqual(p['status'], 'manual-review-only')
        self.assertFalse(p['execution_supported'])
        self.assertEqual(p, plan(self.p, self.e, self.d))

    def test_complete_manual_workflow_survives_save_and_reload(self):
        current = plan(dict(self.p, gamecube='review'), self.e, self.d)
        expected = [('review', 'user-confirmed'), ('backup', 'user-confirmed'),
                    ('recovery', 'console-tested'), ('cios', 'user-confirmed'),
                    ('loader', 'console-tested'), ('wii-test', 'console-tested'),
                    ('gamecube-test', 'console-tested'), ('autoboot-test', 'console-tested')]
        self.assertEqual([step['id'] for step in current['steps']], [i for i, _ in expected])
        state = resume(current)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'state.json'
            for checkpoint, level in expected:
                path.write_text(json.dumps(state))
                state = resume(current, read(path), checkpoint, level)
            path.write_text(json.dumps(state))
            self.assertEqual(resume(current, read(path)), state)
        self.assertEqual(len(state['completed']), len(expected))
        self.assertFalse(current['execution_supported'])
        with self.assertRaises(ValueError):
            resume(current, state, 'autoboot-test', 'console-tested')

    def test_internal_unknown_virtual_and_partition_rejected(self):
        for key, value in [('Internal', True), ('Internal', None), ('Whole', False),
                           ('VirtualOrPhysical', 'Virtual'), ('DiskUUID', None), ('TotalSize', 0),
                           ('Content', 'GUID_partition_scheme')]:
            with self.subTest(key=key, value=value):
                info = dict(self.info, **{key: value})
                self.assertTrue(normalize(info, self.parts)['blockers'])
        for parts in [[], self.parts * 2, [dict(self.parts[0], FilesystemType='exfat')],
                      [dict(self.parts[0], VolumeAllocationBlockSize=None)]]:
            self.assertTrue(normalize(self.info, parts)['blockers'])

    def test_private_device_metadata_not_emitted(self):
        info = dict(self.info, VolumeName='PRIVATE', SerialNumber='SECRET', MountPoint='/private')
        output = json.dumps(normalize(info, self.parts))
        for secret in ['PRIVATE', 'SECRET', '/private', 'synthetic-id']:
            self.assertNotIn(secret, output)

    def test_model_and_region_unknown_conflicts_block(self):
        for model in ['unknown', 'family', 'mini', 'vwii']:
            p, e = dict(self.p, model=model), dict(self.e, model=model)
            self.assertEqual(plan(p, e, self.d)['steps'], [])
        for change in [{'model': 'family'}, {'model_source': 'unknown'}, {'region': 'E'},
                       {'menu': '4.2U'}, {'menu': 'unknown'}, {'region_source': 'unknown'}]:
            self.assertTrue(plan(self.p, dict(self.e, **change), self.d)['blockers'])

    def test_strict_profiles_and_video(self):
        for change in [{'surprise': True}, {'output': '480p'}, {'output': '576i'},
                       {'schema': True}, {'loader': 'arbitrary'}, {'display': 'crt', 'output': '480p'}]:
            with self.assertRaises(ValueError):
                profile(dict(self.p, **change))
        profile(dict(self.p, output='480p', display='hd', cable='component'))
        for key in self.p:
            p = dict(self.p)
            del p[key]
            with self.assertRaises(ValueError):
                profile(p)

    def test_duplicate_keys_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'profile.yaml'
            f.write_text('{"schema":1,"schema":1}')
            with self.assertRaises(ValueError):
                read(f)

    def test_resume_order_evidence_and_changed_inputs(self):
        p = plan(self.p, self.e, self.d)
        state = resume(p, checkpoint='review', level='user-confirmed')
        self.assertEqual(resume(p, copy.deepcopy(state)), state)
        for checkpoint, level in [('review', 'user-confirmed'), ('loader', 'console-tested'), ('backup', 'console-tested')]:
            with self.assertRaises(ValueError):
                resume(p, copy.deepcopy(state), checkpoint, level)
        for d in [dict(self.d, fingerprint='a' * 64), dict(self.d, capacity=3000000000), dict(self.d, device='disk8')]:
            with self.assertRaises(ValueError):
                resume(plan(self.p, self.e, d), copy.deepcopy(state))
        with self.assertRaises(ValueError):
            resume(plan(dict(self.p, autoboot='off'), self.e, self.d), state)

    def test_console_launch_needs_console_evidence(self):
        p = plan(self.p, self.e, self.d)
        s = resume(p, checkpoint='review', level='user-confirmed')
        s = resume(p, s, 'backup', 'user-confirmed')
        with self.assertRaises(ValueError):
            resume(p, copy.deepcopy(s), 'recovery', 'user-confirmed')
        resume(p, s, 'recovery', 'console-tested')

    def test_blocked_plan_cannot_resume(self):
        with self.assertRaises(ValueError):
            resume(plan(self.p, dict(self.e, model='unknown'), self.d))

    @patch('wiiready.__main__.platform.system', return_value='Darwin')
    @patch('wiiready.__main__.diskutil')
    def test_live_inspection_only_calls_list_and_info(self, diskutil, system):
        listing = {'AllDisksAndPartitions': [{'DeviceIdentifier': 'disk9', 'Partitions': [{'DeviceIdentifier': 'disk9s1'}]}]}
        diskutil.side_effect = [listing, self.info, self.parts[0]] * 2
        self.assertEqual(inspect('disk9'), self.d)
        self.assertEqual([c.args for c in diskutil.call_args_list], [('list', '-plist'), ('info', '-plist', 'disk9'), ('info', '-plist', 'disk9s1')] * 2)

    @patch('wiiready.__main__.platform.system', return_value='Darwin')
    @patch('wiiready.__main__.diskutil')
    def test_ambiguous_and_changed_devices(self, diskutil, system):
        row = {'DeviceIdentifier': 'disk9', 'Partitions': []}
        diskutil.return_value = {'AllDisksAndPartitions': [row, row]}
        with self.assertRaises(ValueError):
            inspect('disk9')
        diskutil.side_effect = [{'AllDisksAndPartitions': [row]}, self.info, {'AllDisksAndPartitions': [row]}, dict(self.info, DiskUUID='changed')]
        with self.assertRaises(ValueError):
            inspect('disk9')
        for device in ['disk9s1', '/dev/disk9', 'disk9;touch x']:
            with self.assertRaises(ValueError):
                inspect(device)

    def test_cli_invalid_and_blocked_exit_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, value in [('profile', self.p), ('evidence', dict(self.e, model='unknown')), ('inspection', self.d)]:
                (root / name).write_text(json.dumps(value))
            cmd = [sys.executable, '-m', 'wiiready', 'plan']
            for name in ['profile', 'evidence', 'inspection']:
                cmd += ['--' + name, str(root / name)]
            env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'))
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)['steps'], [])
            (root / 'profile').write_text('invalid')
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 2)
            self.assertIn('WiiReady:', result.stderr)
            self.assertNotIn('Traceback', result.stderr)

    def test_rejected_resume_does_not_mutate_input(self):
        p = plan(self.p, self.e, self.d)
        state = resume(p)
        original = copy.deepcopy(state)
        with self.assertRaises(ValueError):
            resume(p, state, 'review', 'console-tested')
        self.assertEqual(state, original)
        updated = resume(p, state, 'review', 'user-confirmed')
        self.assertEqual(state, original)
        self.assertEqual(len(updated['completed']), 1)

    def test_resume_requires_paired_arguments_and_unchanged_plan(self):
        p = plan(self.p, self.e, self.d)
        for checkpoint, level in [(None, 'user-confirmed'), ('review', None)]:
            with self.assertRaises(ValueError):
                resume(p, checkpoint=checkpoint, level=level)
        changed = copy.deepcopy(p)
        changed['steps'][0]['instruction'] = 'changed'
        with self.assertRaises(ValueError):
            resume(changed)

    def test_bounded_strict_json_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'input.json'
            for raw in [b'x' * 1048577, b'\xff', b'[' * 2000 + b']' * 2000,
                        b'{"value": NaN}', b'{"value": Infinity}', b'{"value": -Infinity}', b'{"value": 1e999}']:
                f.write_bytes(raw)
                with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                    read(f)
            f.write_text('{"ok": true}', encoding='utf-8')
            self.assertEqual(read(f), {'ok': True})

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX special file check')
    def test_fifo_rejected_without_waiting_for_writer(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'pipe'
            os.mkfifo(f)
            with self.assertRaises(ValueError):
                read(f)

    @unittest.skipUnless(hasattr(os, 'O_NOFOLLOW'), 'Host supports no-follow opens')
    def test_symlink_input_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'data'
            f.write_text('{}')
            link = Path(tmp) / 'link'
            link.symlink_to(f)
            with self.assertRaises(OSError):
                read(link)

    def test_partition_identity_changes_invalidate_resume(self):
        first = normalize(self.info, [dict(self.parts[0], VolumeUUID='synthetic-a')])
        second = normalize(self.info, [dict(self.parts[0], VolumeUUID='synthetic-b')])
        self.assertNotEqual(first['fingerprint'], second['fingerprint'])
        state = resume(plan(self.p, self.e, first))
        with self.assertRaises(ValueError):
            resume(plan(self.p, self.e, second), state)

    @patch('wiiready.__main__.platform.system', return_value='Darwin')
    @patch('wiiready.__main__.diskutil')
    def test_disk_info_identity_mismatch_blocks(self, diskutil, system):
        listing = {'AllDisksAndPartitions': [{'DeviceIdentifier': 'disk9', 'Partitions': [{'DeviceIdentifier': 'disk9s1'}]}]}
        for responses in [[listing, dict(self.info, DeviceIdentifier='disk8')],
                          [listing, self.info, dict(self.parts[0], DeviceIdentifier='disk8s1')]]:
            diskutil.side_effect = responses
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                inspect('disk9')

    @patch('wiiready.__main__.platform.system', return_value='Darwin')
    @patch('wiiready.__main__.diskutil')
    def test_volatile_metadata_does_not_break_identity(self, diskutil, system):
        listing = {'AllDisksAndPartitions': [{'DeviceIdentifier': 'disk9', 'Partitions': [{'DeviceIdentifier': 'disk9s1'}]}]}
        diskutil.side_effect = [listing, dict(self.info, FreeSpace=100), self.parts[0],
                               listing, dict(self.info, FreeSpace=90), self.parts[0]]
        self.assertEqual(inspect('disk9'), self.d)

    def test_partition_capacity_and_identity_types_fail_closed(self):
        for size in [None, True, 0, -1, 3000000000]:
            self.assertIn('invalid-partition-capacity',
                          normalize(self.info, [dict(self.parts[0], TotalSize=size)])['blockers'])
        for identity in [True, 1, [], '   ']:
            self.assertIn('no-stable-identity',
                          normalize(dict(self.info, DiskUUID=identity), self.parts)['blockers'])

    @patch('wiiready.__main__.platform.system', return_value='Darwin')
    @patch('wiiready.__main__.diskutil')
    def test_partition_changes_during_inspection_block(self, diskutil, system):
        listing = {'AllDisksAndPartitions': [{'DeviceIdentifier': 'disk9', 'Partitions': [{'DeviceIdentifier': 'disk9s1'}]}]}
        diskutil.side_effect = [listing, self.info, self.parts[0], listing, self.info,
                               dict(self.parts[0], TotalSize=1000000000)]
        with self.assertRaisesRegex(ValueError, 'changed'):
            inspect('disk9')

    @patch('wiiready.__main__.platform.system', return_value='Darwin')
    @patch('wiiready.__main__.diskutil')
    def test_untrusted_partition_identifiers_not_queried(self, diskutil, system):
        for ids in [['disk8s1'], ['-plist'], ['disk9s1', 'disk9s1'], [None]]:
            diskutil.reset_mock()
            diskutil.return_value = {'AllDisksAndPartitions': [
                {'DeviceIdentifier': 'disk9', 'Partitions': [{'DeviceIdentifier': i} for i in ids]}]}
            with self.assertRaises(ValueError):
                inspect('disk9')
            self.assertEqual(diskutil.call_count, 1)

    @patch('wiiready.__main__.platform.system', return_value='Darwin')
    @patch('wiiready.__main__.diskutil')
    def test_malformed_disk_listing_fails_cleanly(self, diskutil, system):
        for value in [None, [], {}, {'AllDisksAndPartitions': [None]},
                      {'AllDisksAndPartitions': [{'DeviceIdentifier': 'disk9'}]}]:
            diskutil.return_value = value
            with self.assertRaises(ValueError):
                inspect('disk9')

    @patch('wiiready.__main__.platform.system', return_value='Linux')
    def test_unsupported_host_fails_closed(self, system):
        with self.assertRaises(ValueError):
            inspect('disk9')


if __name__ == '__main__':
    unittest.main()
