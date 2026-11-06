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
        for question, prefix in zip(result['questions'][:3], ['What console', 'Which computer', 'Does the Homebrew']):
            self.assertTrue(question.startswith(prefix))
        next_round = start({'model': 'original', 'computer': 'macos', 'homebrew': 'no'})
        self.assertTrue(next_round['questions'][0].startswith('What full version'))

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

    def test_unknown_homebrew_never_selects_fresh_exploit(self):
        for model in ['original', 'family', 'mini', 'vwii', 'unknown']:
            result = start({'model': model, 'homebrew': 'unknown', 'menu': '4.3U', 'computer': 'windows'})
            self.assertIn('Check whether', result['route']['instruction'])
            self.assertTrue(result['route']['source'].endswith('get-started'))

    def test_mini_does_not_recommend_sd(self):
        for storage in ['unknown', 'sd', 'usb-flash']:
            result = start({'model': 'mini', 'storage': storage, 'sd': 'yes'})
            notes = ' '.join(result['notes'])
            self.assertIn('no SD slot', notes)
            if storage == 'sd':
                self.assertIn('does not fit', notes)
            else:
                self.assertNotIn('does not fit', notes)
            self.assertNotIn('supports Wii games on SD', notes)
            self.assertNotIn('Choose SD', notes)
            self.assertNotIn('Do you have an SD card', ' '.join(result['questions']))

    def test_mini_sd_ownership_does_not_conflict_with_usb_selection(self):
        result = start({'model': 'mini', 'sd': 'yes', 'storage': 'usb-hdd'})
        self.assertNotIn('revise', ' '.join(result['notes']))
        self.assertIn('no SD slot', ' '.join(result['notes']))

    def test_pre_3_menu_gets_review_not_identification_or_exploit(self):
        for computer in ['windows', 'macos', 'linux']:
            result = start({'model': 'original', 'menu': '2.2U', 'homebrew': 'no', 'sd': 'yes', 'computer': computer})
            self.assertIn('pre-3.0', result['route']['instruction'])
            self.assertTrue(result['route']['source'].endswith('get-started'))
            self.assertFalse(result['reference_plan_scope'])

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


class JourneyTests(unittest.TestCase):
    def setUp(self):
        self.answers = {'model': 'original', 'menu': '4.3U', 'computer': 'windows', 'homebrew': 'yes',
                        'sd': 'yes', 'storage': 'sd', 'display': 'hd', 'cable': 'component', 'gamecube': 'yes'}

    def test_complete_portable_session_requires_observed_checkpoints(self):
        from wiiforge.__main__ import journey
        result = journey(self.answers)
        expected = [('review', 'user-confirmed'), ('storage-review', 'user-confirmed'),
                    ('homebrew', 'console-tested'), ('backup', 'user-confirmed'),
                    ('recovery', 'console-tested'), ('cios', 'user-confirmed'),
                    ('loader', 'console-tested'), ('wii-test', 'console-tested'), ('gamecube-test', 'console-tested')]
        for checkpoint, level in expected:
            self.assertEqual(result['next_checkpoint']['id'], checkpoint)
            result = journey(self.answers, result, checkpoint, level)
            self.assertFalse(result['write_authorized'])
            self.assertFalse(result['inspection_performed'])
            self.assertFalse(result['installation_supported'])
        self.assertIsNone(result['next_checkpoint'])
        self.assertEqual(result['status'], 'manual-checkpoints-complete')

    def test_session_rejects_skips_changed_answers_and_other_models(self):
        from wiiforge.__main__ import journey
        result = journey(self.answers)
        with self.assertRaises(ValueError): journey(self.answers, result, 'loader', 'console-tested')
        result = journey(self.answers, result, 'review', 'user-confirmed')
        with self.assertRaises(ValueError): journey(dict(self.answers, storage='usb-hdd'), result)
        with self.assertRaises(ValueError): journey(self.answers, result, 'storage-review', 'console-tested')
        for model in ['family', 'mini', 'vwii', 'unknown']:
            with self.assertRaises(ValueError): journey(dict(self.answers, model=model))
        with self.assertRaises(ValueError): journey(dict(self.answers, menu='4.3E'))
        with self.assertRaises(ValueError): journey({})
        self.assertEqual(len(result['state']['completed']), 1)

    def test_unknown_video_and_optional_gamecube_do_not_block_start(self):
        from wiiforge.__main__ import journey
        answers = dict(self.answers, display='unknown', cable='unknown', gamecube='unknown')
        result = journey(answers)
        self.assertEqual(result['next_checkpoint']['id'], 'review')
        self.assertEqual(result['observations']['display'], 'unknown')
        self.assertFalse(result['write_authorized'])
        self.assertEqual(len([line for line in render(start()).split('For this setup:')[0].splitlines() if line.startswith('- ')]), 3)

    def test_computer_and_completed_installation_progress_preserve_session(self):
        from wiiforge.__main__ import journey
        answers = dict(self.answers, homebrew='no')
        result = journey(answers)
        original_route = result['guide_route']
        original_digest = result['state']['plan_digest']
        for checkpoint in ['review', 'storage-review']:
            result = journey(answers, result, checkpoint, 'user-confirmed')
        answers.update(computer='macos', homebrew='yes')
        result = journey(answers, result, 'homebrew', 'console-tested')
        self.assertEqual(result['next_checkpoint']['id'], 'backup')
        self.assertEqual(result['guide_route'], original_route)
        self.assertEqual(result['state']['plan_digest'], original_digest)
        result = journey(dict(answers, computer='linux'), result)
        self.assertEqual(len(result['state']['completed']), 3)
        self.assertEqual(result['guide_route'], original_route)
        with self.assertRaises(ValueError): journey(dict(answers, homebrew='no'), result)
        with self.assertRaises(ValueError): journey(dict(answers, cable='adapter'), result)

    def test_homebrew_transition_requires_checkpoint_and_legacy_state_resumes(self):
        from wiiforge.__main__ import journey
        answers = dict(self.answers, homebrew='no')
        result = journey(answers)
        del result['baseline_answers']  # Previous CLI output had no explicit baseline.
        with self.assertRaises(ValueError): journey(dict(answers, homebrew='yes'), result)
        result = journey(dict(answers, computer='linux'), result, 'review', 'user-confirmed')
        self.assertEqual(result['next_checkpoint']['id'], 'storage-review')
        self.assertEqual(result['baseline_answers']['computer'], 'windows')
        with self.assertRaises(ValueError):
            journey(dict(answers, homebrew='yes'), result, 'homebrew', 'console-tested')

    def test_cli_can_resume_saved_output_on_any_host_without_inspection(self):
        with tempfile.TemporaryDirectory() as folder:
            answers = Path(folder) / 'answers.json'
            saved = Path(folder) / 'progress.json'
            answers.write_text(json.dumps(self.answers))
            env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
            command = [sys.executable, '-m', 'wiiforge', 'journey', '--answers', str(answers)]
            first = subprocess.run(command, cwd=folder, env=env, text=True, capture_output=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            saved.write_text(first.stdout)
            second = subprocess.run(command + ['--state', str(saved), '--checkpoint', 'review', '--level', 'user-confirmed'],
                                    cwd=folder, env=env, text=True, capture_output=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(second.stdout)['next_checkpoint']['id'], 'storage-review')
            self.assertEqual(saved.read_text(), first.stdout)
            self.assertEqual(set(p.name for p in Path(folder).iterdir()), {'answers.json', 'progress.json'})


class CheckpointPreparationTests(unittest.TestCase):
    def test_working_homebrew_skips_installer_and_first_game_offers_optional_dumper(self):
        from wiiforge.__main__ import checkpoint_preparation, journey
        self.assertEqual(checkpoint_preparation('homebrew', 'unknown', 'yes')['manifests'], [])
        self.assertEqual(checkpoint_preparation('homebrew', 'unknown', 'no')['manifests'], ['packages/hackmii.yaml'])
        first_game = checkpoint_preparation('wii-test', 'online')
        self.assertEqual(first_game['manifests'], ['packages/cleanrip.yaml'])
        self.assertIn('Skip CleanRip', first_game['instruction'])
        answers = dict(model='original', menu='4.3U', computer='macos', homebrew='yes', sd='yes', storage='sd', gamecube='no')
        session = journey(answers)
        for checkpoint in ['review', 'storage-review']:
            session = journey(answers, session, checkpoint, 'user-confirmed')
        self.assertEqual(session['next_checkpoint']['computer_preparation']['manifests'], [])
        while session['next_checkpoint']:
            next_step = session['next_checkpoint']
            self.assertNotEqual(next_step['id'], 'gamecube-test')
            session = journey(answers, session, next_step['id'], next_step['required_evidence'])
        self.assertEqual(session['status'], 'manual-checkpoints-complete')

    def test_cios_guidance_only_requests_offline_files_when_needed(self):
        from wiiforge.__main__ import checkpoint_preparation
        unknown = checkpoint_preparation('cios', 'unknown')
        self.assertIn('Ask one question', unknown['instruction'])
        online = checkpoint_preparation('cios', 'online')
        self.assertNotIn('base_ios', online)
        offline = checkpoint_preparation('cios', 'offline')
        self.assertEqual([(x['ios'], x['version']) for x in offline['base_ios']],
                         [(38, 4123), (56, 5661), (57, 5918), (58, 6175)])
        self.assertIn('specific approval', offline['instruction'])
        self.assertEqual(offline['manifests'], ['packages/d2x-cios-installer.yaml'])

    def test_current_checkpoint_points_to_real_manifests_without_advancing(self):
        from wiiforge.__main__ import checkpoint_preparation, journey
        root = Path(__file__).resolve().parents[1]
        for checkpoint in ['homebrew', 'backup', 'recovery', 'cios', 'loader', 'wii-test', 'gamecube-test']:
            for manifest in checkpoint_preparation(checkpoint, 'unknown')['manifests']:
                self.assertTrue((root / manifest).is_file())
        answers = {
            'model': 'original', 'menu': '4.3U', 'computer': 'windows', 'homebrew': 'yes', 'sd': 'yes', 'storage': 'sd'}
        result = journey(answers, wii_network='online')
        updated = journey(answers, result, wii_network='offline')
        self.assertEqual(updated['state'], result['state'])
        self.assertFalse(updated['write_authorized'])
