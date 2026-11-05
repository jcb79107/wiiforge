import io
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from wiiforge.rehearsal import _copy_member, _rehearse_zip, rehearse


def fixture(name='apps/demo/a.txt'):
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as output:
        output.writestr(name, b'synthetic')
    return data.getvalue()


class RehearsalTests(unittest.TestCase):
    def setUp(self):
        self.parent = tempfile.TemporaryDirectory()
        self.addCleanup(self.parent.cleanup)
        original = tempfile.TemporaryDirectory
        self.patch = patch('wiiforge.rehearsal.tempfile.TemporaryDirectory',
                           side_effect=lambda **kw: original(dir=self.parent.name, **kw))
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.sentinel = Path(self.parent.name) / 'unrelated'
        self.sentinel.write_text('preserve')

    def assert_clean(self):
        self.assertEqual(list(Path(self.parent.name).iterdir()), [self.sentinel])
        self.assertEqual(self.sentinel.read_text(), 'preserve')

    def test_success_verifies_and_removes_only_temporary_files(self):
        result = rehearse()
        self.assertTrue(result['synthetic'])
        self.assertFalse(result['installation_supported'])
        self.assertTrue(result['temporary_files_removed'])
        self.assertEqual(len(result['files']), 2)
        self.assert_clean()

    def test_interruption_and_io_failure_remove_partial_work(self):
        for error in [KeyboardInterrupt(), OSError('simulated full disk')]:
            def interrupted(source, target, expected):
                target.write_bytes(b'partial')
                raise error
            with self.subTest(error=type(error)), patch('wiiforge.rehearsal._copy_member', interrupted):
                with self.assertRaises(type(error)):
                    rehearse()
            self.assert_clean()
        self.assertEqual(rehearse()['status'], 'rehearsal-complete')
        self.assert_clean()

    def test_unsafe_archive_rejected_before_temporary_directory(self):
        info = zipfile.ZipInfo('link')
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        for name in ['../outside', '/absolute', 'COM¹.txt', info]:
            with self.subTest(name=str(name)), self.assertRaises(ValueError):
                _rehearse_zip(fixture(name))
            self.assert_clean()

    def test_crc_failure_cleans_partial_copy(self):
        data = fixture()
        data = data.replace(b'synthetic', b'corrupted', 1)
        with self.assertRaises(zipfile.BadZipFile):
            _rehearse_zip(data)
        self.assert_clean()

    def test_copy_rejects_truncation_growth_and_existing_file(self):
        target = Path(self.parent.name) / 'test'
        for payload, expected in [(b'a', 2), (b'abc', 2)]:
            with self.assertRaises(ValueError):
                _copy_member(io.BytesIO(payload), target, expected)
            target.unlink()
        target.write_bytes(b'preserve')
        with self.assertRaises(FileExistsError):
            _copy_member(io.BytesIO(b'x'), target, 1)
        self.assertEqual(target.read_bytes(), b'preserve')

    def test_cli_rejects_destination_or_artifact_arguments(self):
        root = Path(__file__).resolve().parents[1]
        for option in ['--destination', '--artifact']:
            result = subprocess.run([sys.executable, '-m', 'wiiforge', 'rehearse', option, 'unused'],
                                    capture_output=True, env=dict(os.environ, PYTHONPATH=str(root / 'src')))
            self.assertEqual(result.returncode, 2)
