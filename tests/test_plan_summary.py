import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from wiiready.prepare import digest, summarize_plan


def fixture(kind=None):
    body = {'schema': 1, 'model': 'original', 'installation_supported': False,
            'destination': {'path': '/private/secret-person/target', 'device': 999, 'inode': 123},
            'files': [{'path': 'games/SECRET/game.iso', 'bytes': 1234, 'sha256': 'a' * 64, 'action': 'create'},
                      {'path': 'games/SECRET/disc2.iso', 'bytes': 42, 'sha256': 'b' * 64, 'action': 'keep'}],
            'required_bytes': 1234}
    if kind: body['kind'] = kind
    return dict(body, digest=digest(body))


class PlanSummaryTests(unittest.TestCase):
    def test_summary_omits_private_fields_and_never_authorizes_writes(self):
        for kind in [None, 'gamecube-copy']:
            plan = fixture(kind)
            original = copy.deepcopy(plan)
            result = summarize_plan(plan)
            self.assertEqual(result['files_to_create'], 1)
            self.assertEqual(result['files_to_preserve'], 1)
            self.assertEqual(result['bytes_to_write'], 1234)
            self.assertFalse(result['write_authorized'])
            for private in ['secret-person', 'SECRET', 'a' * 64, 'b' * 64, plan['digest']]:
                self.assertNotIn(private, json.dumps(result))
            self.assertEqual(plan, original)

    def test_tampering_unsupported_plans_and_inconsistent_counts_rejected(self):
        changed = fixture(); changed['required_bytes'] += 1
        with self.assertRaises(ValueError): summarize_plan(changed)
        for update in [{'required_bytes': 5}, {'required_bytes': True}, {'schema': True},
                       {'kind': 'unknown'}, {'files': None}, {'files': [{'action': 'delete', 'bytes': 1234}]}]:
            changed = fixture(); changed.update(update)
            changed['digest'] = digest({k: v for k, v in changed.items() if k != 'digest'})
            with self.assertRaises(ValueError): summarize_plan(changed)
        with self.assertRaises(ValueError): summarize_plan([])

    def test_cli_never_echoes_private_path_or_parse_errors_and_does_not_write(self):
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'sensitive-private-plan.json'
            data = json.dumps(fixture('gamecube-copy'))
            path.write_text(data)
            command = [sys.executable, '-m', 'wiiready', 'plan-summary', '--plan', str(path)]
            success = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertNotIn(str(path), success.stdout)
            self.assertEqual(json.loads(success.stdout)['operation'], 'gamecube-copy')
            self.assertEqual(path.read_text(), data)
            self.assertEqual(list(Path(folder).iterdir()), [path])
            path.write_text('{"secret-person":1,"secret-person":2}')
            for exists in [True, False]:
                if not exists: path.unlink()
                failed = subprocess.run(command, env=env, capture_output=True, text=True)
                self.assertEqual(failed.returncode, 2)
                self.assertEqual(failed.stdout, '')
                for private in [str(path), 'sensitive-private-plan', 'secret-person', 'Traceback']:
                    self.assertNotIn(private, failed.stderr)
