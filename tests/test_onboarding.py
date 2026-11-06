import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from wiiforge.onboarding import start, render
from wiiforge.__main__ import profile, evidence


class OnboardingTests(unittest.TestCase):
    def test_empty_intake_does_not_invent_console_or_test_evidence(self):
        result = start()
        self.assertEqual(len(result['questions']), 9)
        self.assertEqual(result['evidence_draft']['menu'], 'unknown')
        self.assertFalse(result['reference_plan_scope'])
        self.assertFalse(result['write_authorized'])
        self.assertFalse(result['installation_supported'])
        self.assertIn('Ask next:', render(result))

    def test_routes_and_drafts(self):
        base = {'model': 'original', 'menu': '4.3U', 'homebrew': 'no', 'sd': 'yes'}
        for computer, suffix in [('windows', 'modmii'), ('macos', 'wilbrand'), ('linux', 'wilbrand')]:
            with self.subTest(computer=computer):
                result = start(dict(base, computer=computer, gamecube='yes'))
                self.assertTrue(result['route']['source'].endswith(suffix))
                profile(result['profile_draft'])
                evidence(result['evidence_draft'])
                self.assertEqual(result['profile_draft']['gamecube'], 'review')
                self.assertEqual(result['profile_draft']['autoboot'], 'off')
                self.assertEqual(result['profile_draft']['output'], 'preserve')
                self.assertFalse(result['installation_supported'])

    def test_other_models_never_receive_original_wii_route(self):
        for model in ['family', 'mini', 'vwii', 'unknown']:
            result = start({'model': model, 'computer': 'windows', 'menu': '4.3U', 'homebrew': 'no'})
            self.assertFalse(result['reference_plan_scope'])
            self.assertNotIn('modmii', result['route']['source'])
            self.assertFalse(result['installation_supported'])

    def test_existing_or_unknown_homebrew_is_not_fresh_install(self):
        for homebrew in ['yes', 'unknown']:
            result = start({'model': 'original', 'computer': 'windows', 'menu': '4.3U', 'homebrew': homebrew})
            self.assertTrue(result['route']['source'].endswith('get-started'))

    def test_existing_homebrew_is_inventory_first_for_every_model(self):
        for model in ['original', 'family', 'mini', 'vwii', 'unknown']:
            with self.subTest(model=model):
                result = start({'model': model, 'homebrew': 'yes', 'computer': 'windows', 'menu': '4.3U'})
                self.assertIn('inventory', result['route']['instruction'])
                self.assertTrue(result['route']['source'].endswith('get-started'))
                self.assertFalse(result['installation_supported'])

    def test_non_reference_region_does_not_gain_planner_support(self):
        result = start({'model': 'original', 'menu': '4.3E', 'computer': 'macos', 'homebrew': 'no', 'sd': 'yes'})
        self.assertTrue(result['route']['source'].endswith('wilbrand'))
        self.assertEqual(result['profile_draft']['region'], 'E')
        self.assertFalse(result['reference_plan_scope'])

    def test_old_menu_and_storage_warnings(self):
        result = start({'model': 'original', 'menu': '3.2U', 'storage': 'usb-flash'})
        self.assertIn('2 GB', ' '.join(result['notes']))
        self.assertIn('unpredictable', ' '.join(result['notes']))
        result = start({'storage': 'sd', 'cable': 'adapter'})
        self.assertIn('supports Wii games on SD', ' '.join(result['notes']))
        self.assertIn('does not prove', ' '.join(result['notes']))

    def test_invalid_fields_types_and_values_rejected(self):
        for answers in [[], {'serial': 'private'}, {'model': []}, {'menu': None}, {'menu': '4.3'},
                        {'gamecube': True}, {'computer': 'Windows'}, {'menu': '4.3U\n'}]:
            with self.subTest(answers=answers), self.assertRaises(ValueError):
                start(answers)

    def test_cli_reads_private_answers_without_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'answers.json'
            path.write_text(json.dumps({'model': 'original', 'menu': '4.3U'}))
            before = path.read_bytes()
            env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
            run = subprocess.run([sys.executable, '-m', 'wiiforge', 'start', '--answers', str(path), '--json'],
                                 cwd=folder, env=env, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertFalse(json.loads(run.stdout)['write_authorized'])
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(Path(folder).iterdir()), [path])
            path.write_text('{"model":"original","model":"mini"}')
            run = subprocess.run([sys.executable, '-m', 'wiiforge', 'start', '--answers', str(path)],
                                 cwd=folder, env=env, text=True, capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertNotIn('Traceback', run.stderr)
