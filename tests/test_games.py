import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from wiiforge.games import HEADER_BYTES, check_gamecube


def synthetic_header(game_id=b'TEST00', disc=0):
    data = bytearray(HEADER_BYTES)
    data[:6] = game_id
    data[6] = disc
    data[0x1c:0x20] = bytes.fromhex('c2339f3d')
    return data


class GameTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.first = self.root / 'own-dump.gcm'
        self.first.write_bytes(synthetic_header())

    def test_single_disc_is_partial_and_never_changes_or_discloses_source(self):
        before = self.first.read_bytes()
        result = check_gamecube(self.first)
        self.assertEqual(result['status'], 'header-check-only')
        for key in ['write_authorized', 'dump_integrity_verified', 'gameplay_verified', 'suggested_layout_matches']:
            self.assertFalse(result[key])
        self.assertNotIn(str(self.root), json.dumps(result))
        self.assertNotIn('TEST00', json.dumps(result))
        self.assertEqual(self.first.read_bytes(), before)
        self.assertEqual(list(self.root.iterdir()), [self.first])

    def test_two_discs_require_matching_id_and_correct_order(self):
        second = self.root / 'second.iso'
        second.write_bytes(synthetic_header(disc=1))
        self.assertEqual(len(check_gamecube(self.first, second)['images']), 2)
        for contents in [synthetic_header(disc=0), synthetic_header(b'OTHER0', 1)]:
            second.write_bytes(contents)
            with self.assertRaises(ValueError): check_gamecube(self.first, second)
        second.write_bytes(synthetic_header(disc=1))
        with self.assertRaises(ValueError): check_gamecube(second, self.first)
        with self.assertRaises(ValueError): check_gamecube(second)

    def test_expected_layout_and_different_parent(self):
        folder = self.root / 'games' / 'My game'
        folder.mkdir(parents=True)
        first, second = folder / 'game.iso', folder / 'disc2.iso'
        first.write_bytes(synthetic_header())
        second.write_bytes(synthetic_header(disc=1))
        self.assertTrue(check_gamecube(first, second)['suggested_layout_matches'])
        other = self.root / 'games' / 'Different game'
        other.mkdir()
        moved = other / 'disc2.iso'
        second.rename(moved)
        self.assertFalse(check_gamecube(first, moved)['suggested_layout_matches'])

    def test_bad_headers_compressed_formats_and_unsafe_ids_rejected(self):
        bad = [b'RVZ\x01' + bytes(HEADER_BYTES - 4), bytes(HEADER_BYTES),
               synthetic_header(b'../../'), synthetic_header(b'\xffABCDE'), synthetic_header(disc=2)]
        bad += [synthetic_header(game_id) for game_id in [b'COBRAM', b'GGCOSD', b'RGCOSD', b'GCOEDV']]
        nkit, wii = synthetic_header(), synthetic_header()
        nkit[0x200:0x204] = b'NKIT'
        wii[0x18:0x1c] = bytes.fromhex('5d1c9ea3')
        for data in bad + [nkit, wii, synthetic_header()[:-1]]:
            self.first.write_bytes(data)
            with self.assertRaises(ValueError): check_gamecube(self.first)
        renamed = self.root / 'game.rvz'
        renamed.write_bytes(synthetic_header())
        with self.assertRaises(ValueError): check_gamecube(renamed)

    def test_missing_directory_symlink_and_fifo_rejected(self):
        for path in [self.root / 'missing.iso', self.root / 'directory.iso']:
            if path.name.startswith('directory'): path.mkdir()
            with self.assertRaises(ValueError): check_gamecube(path)
        if os.name == 'posix':
            link = self.root / 'link.iso'
            link.symlink_to(self.first)
            with self.assertRaises(ValueError): check_gamecube(link)
            fifo = self.root / 'pipe.iso'
            os.mkfifo(fifo)
            with self.assertRaises(ValueError): check_gamecube(fifo)

    def test_changed_metadata_rejected_and_reads_are_bounded(self):
        actual = os.fstat
        calls = 0
        def changed(fd):
            nonlocal calls
            calls += 1
            result = actual(fd)
            if calls == 2:
                return SimpleNamespace(st_size=result.st_size + 1,
                                       st_mtime_ns=result.st_mtime_ns, st_ctime_ns=result.st_ctime_ns)
            return result
        with patch('wiiforge.games.os.fstat', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'changed'): check_gamecube(self.first)
        # Trailing bytes do not affect a header-only result and are not consumed.
        with self.first.open('ab') as file: file.write(b'Not executable game content' * 1000)
        original = os.fdopen
        reads = []
        class Reader:
            def __init__(self, file): self.file = file
            def __enter__(self): return self
            def __exit__(self, *args): self.file.close()
            def fileno(self): return self.file.fileno()
            def read(self, count):
                reads.append(count)
                return self.file.read(count)
        with patch('wiiforge.games.os.fdopen', side_effect=lambda *a, **k: Reader(original(*a, **k))):
            check_gamecube(self.first)
        self.assertEqual(reads, [HEADER_BYTES])

    def test_cli_has_actionable_report_and_clean_errors(self):
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / 'src'))
        command = [sys.executable, '-m', 'wiiforge', 'check-gamecube', '--disc1', str(self.first)]
        success = subprocess.run(command, env=env, capture_output=True, text=True)
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertEqual(json.loads(success.stdout)['suggested_layout'], ['games/<your-game-folder>/game.iso'])
        self.first.unlink()
        failed = subprocess.run(command, env=env, capture_output=True, text=True)
        self.assertEqual(failed.returncode, 2)
        self.assertNotIn(str(self.root), failed.stderr)
        self.assertNotIn('Traceback', failed.stderr)
