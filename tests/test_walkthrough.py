"""Simulated first-time flow. Every file and console outcome here is invented."""
import io
import tempfile
from pathlib import Path
import unittest
import zipfile

from wiiforge.__main__ import journey
from wiiforge.games import check_gamecube
from wiiforge.onboarding import start
from wiiforge.prepare import plan_preparation, execute_preparation
from test_games import synthetic_header


class WalkthroughTests(unittest.TestCase):
    def test_first_time_sd_journey_prepares_files_but_waits_for_console_outcomes(self):
        self.assertFalse(start()['reference_plan_scope'])
        # Owns an original Wii, suitable existing SD/reader and component cable;
        # the buying playbook reuses these instead of requiring a USB purchase.
        answers = dict(model='original', menu='4.3U', computer='macos', homebrew='no',
                       sd='yes', storage='sd', display='hd', cable='component', gamecube='yes')
        intake = start(answers)
        self.assertTrue(intake['route']['source'].endswith('/wilbrand'))
        self.assertEqual(intake['profile_draft']['output'], 'preserve')
        session = journey(answers)
        for checkpoint in ['review', 'storage-review']:
            session = journey(answers, session, checkpoint, 'user-confirmed')
        self.assertEqual(session['next_checkpoint']['id'], 'homebrew')
        # Exercise the real preparation engine with a synthetic app ZIP, not
        # an upstream artifact or a bypass of its public manifest validation.
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / 'synthetic-card'
            destination.mkdir()
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, 'w') as archive:
                archive.writestr('apps/synthetic/boot.dol', b'Not executable; invented app')
            data = stream.getvalue()
            plan = plan_preparation(data, destination, 'original')
            with self.assertRaises(ValueError):
                execute_preparation(data, destination, 'original', plan, 'not-approved')
            result = execute_preparation(data, destination, 'original', plan, plan['digest'])
            self.assertEqual(result['status'], 'files-prepared')
            self.assertEqual(execute_preparation(data, destination, 'original', plan, plan['digest'])['written'], [])
            self.assertEqual(journey(answers, session)['next_checkpoint']['id'], 'homebrew')
            answers['homebrew'] = 'yes'  # Invented user observation for this test only.
            session = journey(answers, session, 'homebrew', 'console-tested')
            for checkpoint, level in [('backup', 'user-confirmed'), ('recovery', 'console-tested'),
                                      ('cios', 'user-confirmed'), ('loader', 'console-tested'),
                                      ('wii-test', 'console-tested')]:
                self.assertEqual(session['next_checkpoint']['id'], checkpoint)
                session = journey(answers, session, checkpoint, level, wii_network='online')
            self.assertIn('check-gamecube', session['next_checkpoint']['computer_preparation']['instruction'])
            game = Path(folder) / 'invented.iso'
            game.write_bytes(synthetic_header())
            self.assertFalse(check_gamecube(game)['gameplay_verified'])
            self.assertEqual(journey(answers, session)['next_checkpoint']['id'], 'gamecube-test')
            session = journey(answers, session, 'gamecube-test', 'console-tested')
        self.assertEqual(session['status'], 'manual-checkpoints-complete')
        self.assertFalse(session['write_authorized'])
        self.assertFalse(session['installation_supported'])
