"""Full CLI walkthrough with synthetic package bytes; no upstream code or games."""
import hashlib
import io
import json
import os
import tempfile
from pathlib import Path
import subprocess
import sys
import unittest
import zipfile

from wiiforge.__main__ import journey
from wiiforge.games import check_gamecube
from wiiforge.onboarding import start
from wiiforge.hackmii import MEMBERS
from test_games import synthetic_header
from test_hackmii import fixture as hackmii_fixture

ROOT = Path(__file__).resolve().parents[1]


def synthetic_package(root, manifest_path):
    """Keep publisher/model metadata, replacing only local test size/hash pins."""
    manifest = json.loads((ROOT / manifest_path).read_text())
    package = manifest['package']
    expected = {}
    artifact = root / package
    if package == 'nintendont':
        artifact.mkdir()
        for item in manifest['files']:
            data = ('Synthetic: ' + item['source']).encode()
            (artifact / Path(item['source']).name).write_bytes(data)
            expected[item['destination']] = data
            item.update(size=len(data), sha256=hashlib.sha256(data).hexdigest(),
                        git_blob=hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest())
    else:
        if package == 'hackmii':
            data = hackmii_fixture()
            expected = {(name if name == 'boot.elf' else 'wiiforge-notices/hackmii/' + name):
                        ('Synthetic: ' + name).encode() for name in MEMBERS}
        else:
            app = {'usb-loader-gx': 'usbloader_gx', 'loadpriiloader': 'LoadPriiloader',
                   'nanddumper-ios': 'nanddumper_ios', 'cleanrip': 'CleanRip'}.get(package, package)
            names = ['boot.dol', 'icon.png', 'META.XML' if package == 'priiloader' else 'meta.xml']
            if package == 'priiloader': names += ['hacks_hash.ini']
            if package == 'nanddumper-ios': names += ['nanddumper_ios.elf']
            if package == 'd2x-cios-installer':
                names += ['Changelog.txt', 'ciosmaps.xml'] + ['d2x-v11-beta3/' + part + '.app'
                          for part in ['DIPP', 'EHCI', 'ES', 'FAT', 'FFSP', 'MLOAD', 'USBS']]
            if package == 'usb-loader-gx': names += ['language/english.lang', 'wiitdb.xml']
            expected = {'apps/' + app + '/' + name: ('Synthetic placeholder: ' + name).encode() for name in names}
            if package == 'priiloader': expected['LICENSE'] = b'Synthetic notice, not upstream text'
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, 'w') as archive:
                for name, payload in expected.items(): archive.writestr(name, payload)
            data = stream.getvalue()
        artifact.write_bytes(data)
        manifest.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
    test_manifest = root / (package + '.json')
    test_manifest.write_text(json.dumps(manifest))
    return test_manifest, artifact, expected


@unittest.skipUnless(os.name == 'posix', 'Destination preparation is POSIX-only')
class WalkthroughTests(unittest.TestCase):
    def test_first_time_sd_journey_prepares_every_package_through_cli(self):
        self.assertFalse(start()['reference_plan_scope'])
        # Existing SD/reader and cable: no unnecessary USB or video purchase.
        answers = dict(model='original', menu='4.3U', computer='macos', homebrew='no',
                       sd='yes', storage='sd', display='hd', cable='component', gamecube='yes')
        self.assertTrue(start(answers)['route']['source'].endswith('/wilbrand'))
        session = journey(answers)
        publisher_pins = {p: p.read_bytes() for p in (ROOT / 'packages').glob('*.yaml')}
        packages_seen = set()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            destination = root / 'synthetic-card'; destination.mkdir()
            expected_files = {'keep.txt': b'Existing user data'}
            (destination / 'keep.txt').write_bytes(expected_files['keep.txt'])
            env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'))
            def cli(command, *args, expected=0):
                run = subprocess.run([sys.executable, '-m', 'wiiforge', command, *map(str, args)],
                                     cwd=root, env=env, capture_output=True, text=True)
                self.assertEqual(run.returncode, expected, run.stderr)
                return json.loads(run.stdout) if run.stdout else None
            def files():
                return {p.relative_to(destination).as_posix(): p.read_bytes()
                        for p in destination.rglob('*') if p.is_file()}
            while session['next_checkpoint']:
                checkpoint = session['next_checkpoint']
                before_state = session['state']
                for manifest_path in checkpoint['computer_preparation']['manifests']:
                    package = Path(manifest_path).stem
                    with self.subTest(package=package):
                        packages_seen.add(package)
                        manifest, artifact, payloads = synthetic_package(root, manifest_path)
                        # Published pins must reject our invented bytes. Only the private
                        # test manifest accepts them; no runtime validators are mocked.
                        self.assertIsNone(cli('verify-package', '--manifest', ROOT / manifest_path, '--artifact', artifact,
                                              '--model', 'original', expected=2))
                        common = ['--manifest', manifest, '--artifact', artifact, '--model', 'original']
                        verified = cli('verify-package', *common, '--check-archive', expected=2)
                        self.assertEqual(verified['status'], 'content-verified')
                        self.assertIn('license-review-pending', verified['blockers'])
                        plan = cli('prepare-plan', *common, '--destination', destination)
                        self.assertEqual(files(), expected_files)
                        plan_path = root / (package + '-plan.json'); plan_path.write_text(json.dumps(plan))
                        summary = cli('plan-summary', '--plan', plan_path)
                        self.assertEqual(summary['files_to_create'], len(payloads))
                        self.assertFalse(summary['write_authorized'])
                        self.assertNotIn(str(root), json.dumps(summary))
                        apply = [*common, '--destination', destination, '--plan', plan_path, '--approve-plan']
                        cli('prepare', *apply, 'wrong-approval', expected=2)
                        self.assertEqual(files(), expected_files)
                        prepared = cli('prepare', *apply, plan['digest'])
                        self.assertEqual(set(prepared['written']), set(payloads))
                        self.assertFalse(prepared['installation_supported'])
                        expected_files.update(payloads)
                        self.assertEqual(files(), expected_files)
                        self.assertEqual(cli('prepare', *apply, plan['digest'])['written'], [])
                        self.assertEqual(journey(answers, session)['state'], before_state)
                if checkpoint['id'] == 'homebrew': answers['homebrew'] = 'yes'
                if checkpoint['id'] == 'gamecube-test':
                    game = root / 'invented.iso'; game.write_bytes(synthetic_header())
                    self.assertFalse(check_gamecube(game)['gameplay_verified'])
                    common = ['--disc1', game, '--destination', destination, '--model', 'original']
                    plan = cli('gamecube-plan', *common)
                    saved = root / 'game-plan.json'; saved.write_text(json.dumps(plan))
                    copied = cli('gamecube-copy', *common, '--plan', saved, '--approve-plan', plan['digest'])
                    self.assertTrue(copied['copy_bytes_verified'])
                    self.assertFalse(copied['gameplay_verified'])
                    self.assertEqual((destination / 'games/TEST00/game.iso').read_bytes(), game.read_bytes())
                    self.assertEqual(journey(answers, session)['state'], before_state)
                # These are invented console attestations, not hardware evidence.
                session = journey(answers, session, checkpoint['id'], checkpoint['required_evidence'], wii_network='online')
            self.assertFalse((destination / 'bootmini.elf').exists())
            self.assertFalse((destination / 'wiiload').exists())
        self.assertEqual(packages_seen, {'hackmii', 'nanddumper-ios', 'priiloader', 'loadpriiloader',
                                        'd2x-cios-installer', 'usb-loader-gx', 'cleanrip', 'nintendont'})
        self.assertEqual({p: p.read_bytes() for p in publisher_pins}, publisher_pins)
        self.assertEqual(session['status'], 'manual-checkpoints-complete')
        self.assertFalse(session['write_authorized'])
        self.assertFalse(session['installation_supported'])
