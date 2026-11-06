import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from wiiready.extras import extras, OPTIONS
from wiiready.__main__ import journey, checkpoint_preparation


class ExtrasTests(unittest.TestCase):
    def test_only_selected_paths_are_returned_and_duplicates_collapse(self):
        result = extras(['nes', 'gba', 'nes'], 'original')
        self.assertEqual([p['system'] for p in result['selected']], ['nes', 'gba'])
        self.assertTrue(all(not p['automated_preparation'] for p in result['selected']))
        self.assertFalse(result['write_authorized'])
        self.assertFalse(result['installation_supported'])

    def test_every_model_and_path_stays_guided(self):
        for model in ['original', 'family', 'mini', 'vwii', 'unknown']:
            result = extras(list(OPTIONS), model)
            self.assertTrue(all(p['status'] == 'guide-review-required' for p in result['selected']))
            self.assertFalse(result['installation_supported'])
        for systems, model, skip in [(['ps5'], 'original', False), ([], 'invalid', False), (['nes'], 'original', True)]:
            with self.assertRaises(ValueError): extras(systems, model, skip)

    def test_model_specific_storage_and_build_handoffs(self):
        self.assertIn('no SD slot', extras(['nes'], 'mini')['selected'][0]['model_note'])
        self.assertIn('.wuhb', extras(['gba'], 'vwii')['selected'][0]['model_note'])
        self.assertIn('Identify', extras(['snes'])['selected'][0]['model_note'])
        self.assertNotIn('psp', OPTIONS)

    def test_skip_and_selection_never_change_core_progress(self):
        answers = dict(model='original', menu='4.3U', computer='linux', homebrew='yes', sd='yes', storage='sd', gamecube='yes')
        session = journey(answers); before = copy.deepcopy(session)
        self.assertEqual(extras(skip=True)['selected'], [])
        self.assertEqual(extras()['status'], 'choose-or-skip')
        extras(['n64'])
        self.assertEqual(journey(answers, session)['state'], before['state'])
        self.assertEqual(session, before)

    def test_gamecube_preparation_includes_nintendont_and_gx_confirmation(self):
        result = checkpoint_preparation('gamecube-test', 'unknown')
        self.assertEqual(result['manifests'], ['packages/nintendont.yaml'])
        self.assertEqual(len(result['completion_checks']), 3)
        self.assertIn('GX', result['completion_checks'][-1])

    def test_cli_selections_skip_and_rejection_without_files(self):
        with tempfile.TemporaryDirectory() as folder:
            env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
            def run(*args):
                return subprocess.run([sys.executable, '-m', 'wiiready', 'extras', *args], cwd=folder,
                                      env=env, capture_output=True, text=True)
            self.assertIn('choose any or skip', run().stdout)
            selected = run('--system', 'snes', '--system', 'dos', '--json')
            self.assertEqual(selected.returncode, 0)
            self.assertEqual(len(json.loads(selected.stdout)['selected']), 2)
            self.assertIn('skipped', run('--skip').stdout)
            self.assertEqual(run('--skip', '--system', 'nes').returncode, 2)
            self.assertEqual(run('--system', 'ps5').returncode, 2)
            self.assertEqual(list(Path(folder).iterdir()), [])
