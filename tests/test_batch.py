import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from wiiready.batch import combine_packages, check_emulator_layout
from wiiready.prepare import plan_preparation, execute_preparation
from wiiready.__main__ import package_bytes

ROOT = Path(__file__).resolve().parents[1]


def archive(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as z:
        for name, data in files.items():
            z.writestr(name, data)
    return stream.getvalue()


def emulator(name):
    return archive({**{'apps/' + name + '/' + f: b'synthetic-' + f.encode()
                       for f in ['boot.dol', 'meta.xml', 'icon.png']},
                    **{name + '/' + d + '/': b'' for d in ['roms', 'saves', 'cheats']}})


class BatchTests(unittest.TestCase):
    def test_collision_and_unsafe_rejection(self):
        for a, b in [('apps/a', 'apps/a'), ('Apps/a', 'apps/b'), ('apps/a', 'apps/a/b')]:
            with self.assertRaises(ValueError):
                combine_packages([archive({a: b'a'}), archive({b: b'b'})])
        with self.assertRaises(ValueError): combine_packages([archive({'../bad': b'x'})])
        with self.assertRaises(ValueError): combine_packages([])
        with self.assertRaises(ValueError): combine_packages([archive({'x'+str(i): b'x'}) for i in range(13)])

    def test_aggregate_bound(self):
        with patch('wiiready.batch.LIMIT', 200):
            with self.assertRaises(ValueError):
                combine_packages([archive({'a': b'x'*20}), archive({'b': b'y'*20})])

    def test_exact_emulator_layout(self):
        for name in ['fceugx', 'snes9xgx', 'vbagx']:
            self.assertEqual(check_emulator_layout(emulator(name), name), emulator(name))
            for extra in [name+'/saves/user.sav', name+'/roms/game.nes', 'boot.wad']:
                data = combine_packages([emulator(name), archive({extra: b'x'})])
                with self.assertRaises(ValueError): check_emulator_layout(data, name)

    def test_one_plan_preserves_saves_and_resumes(self):
        data = combine_packages([emulator('fceugx'), emulator('snes9xgx')])
        self.assertEqual(data, combine_packages([emulator('snes9xgx'), emulator('fceugx')]))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); save = root/'fceugx/saves/keep.sav'
            save.parent.mkdir(parents=True); save.write_bytes(b'private-save')
            plan = plan_preparation(data, root, 'original')
            with self.assertRaises(ValueError): execute_preparation(data, root, 'original', plan, 'wrong')
            self.assertFalse((root/'apps').exists())
            result = execute_preparation(data, root, 'original', plan, plan['digest'])
            self.assertEqual(len(result['written']), 6)
            self.assertEqual(save.read_bytes(), b'private-save')
            self.assertEqual(execute_preparation(data, root, 'original', plan, plan['digest'])['written'], [])
            changed = combine_packages([data, archive({'other/file': b'new'})])
            with self.assertRaises(ValueError): execute_preparation(changed, root, 'original', plan, plan['digest'])
            self.assertFalse((root/'other').exists())

    def test_conflict_preflights_whole_batch(self):
        data = combine_packages([emulator('fceugx'), emulator('snes9xgx')])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); conflict = root/'apps/snes9xgx/boot.dol'
            conflict.parent.mkdir(parents=True); conflict.write_bytes(b'old-version')
            with self.assertRaises(ValueError): plan_preparation(data, root, 'original')
            self.assertFalse((root/'apps/fceugx').exists())
            self.assertEqual(conflict.read_bytes(), b'old-version')
            for model in ['mini', 'family', 'vwii', 'unknown']:
                with self.assertRaises(ValueError): plan_preparation(data, root, model)

    def test_interrupted_batch_can_resume_completed_files(self):
        from wiiready.prepare import _copy_new
        data = combine_packages([emulator('fceugx'), emulator('snes9xgx')])
        with tempfile.TemporaryDirectory() as folder:
            plan = plan_preparation(data, folder, 'original')
            calls = 0
            def interrupted(*args):
                nonlocal calls
                calls += 1
                if calls == 3: raise OSError('synthetic interruption')
                return _copy_new(*args)
            with patch('wiiready.prepare._copy_new', side_effect=interrupted):
                with self.assertRaises(OSError): execute_preparation(data, folder, 'original', plan, plan['digest'])
            result = execute_preparation(data, folder, 'original', plan, plan['digest'])
            self.assertEqual(len(result['verified_existing']), 2)
            self.assertEqual(len(result['written']), 4)

    def test_cli_real_verification_with_repinned_synthetic_packages(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); dest = root/'destination'; dest.mkdir()
            arguments = []
            for name in ['fceugx', 'snes9xgx', 'vbagx']:
                data = emulator(name); artifact = root/(name+'.zip'); artifact.write_bytes(data)
                manifest = json.loads((ROOT/'packages'/ (name+'.yaml')).read_text())
                with self.assertRaises(ValueError): package_bytes(manifest, artifact, 'original')
                manifest.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
                pin = root/(name+'.json'); pin.write_text(json.dumps(manifest))
                arguments += ['--package', str(pin), str(artifact)]
            arguments += ['--model', 'original', '--destination', str(dest)]
            env = dict(os.environ, PYTHONPATH=str(ROOT/'src'))
            def run(command, *extra):
                return subprocess.run([sys.executable, '-m', 'wiiready', command, *arguments, *extra],
                                      capture_output=True, text=True, env=env)
            result = run('batch-plan'); self.assertEqual(result.returncode, 0, result.stderr)
            plan = json.loads(result.stdout); saved = root/'plan.json'; saved.write_text(result.stdout)
            result = run('batch-prepare', '--plan', str(saved), '--approve-plan', plan['digest'])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(result.stdout)['written']), 9)
            self.assertFalse(any(dest.rglob('*.wad')))
            artifact.write_bytes(b'changed')
            result = run('batch-prepare', '--plan', str(saved), '--approve-plan', plan['digest'])
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)
            self.assertEqual(len(list((dest/'apps').rglob('boot.dol'))), 3)
