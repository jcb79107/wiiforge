"""Public command migration and optional-picture regression checks."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from wiiready.__main__ import journey


class IdentityTests(unittest.TestCase):
    def test_legacy_command_forwards_without_changing_json(self):
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
        with tempfile.TemporaryDirectory() as folder:
            results = [subprocess.run([sys.executable, '-m', name, 'start', '--shopping', '--json'],
                                     cwd=folder, env=env, capture_output=True, text=True)
                       for name in ['wiiready', 'wiiforge']]
            self.assertTrue(all(r.returncode == 0 for r in results))
            self.assertEqual(json.loads(results[0].stdout), json.loads(results[1].stdout))
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_skipping_picture_advice_does_not_block_journey(self):
        answers = dict(model='original', menu='4.3U', computer='linux', homebrew='no', sd='yes', storage='sd')
        session = journey(answers)
        self.assertEqual(session['observations']['display'], 'unknown')
        self.assertEqual(session['observations']['cable'], 'unknown')
        self.assertEqual(session['next_checkpoint']['id'], 'review')
        advanced = journey(answers, session, 'review', 'user-confirmed')
        self.assertEqual(advanced['next_checkpoint']['id'], 'storage-review')
