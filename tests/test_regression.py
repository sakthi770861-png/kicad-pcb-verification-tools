"""Synthetic-only repeatable evidence baseline tests (no user designs)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from examples.make_synthetic_regression import build
from pcbverify.__main__ import main
from pcbverify.regression import run_regression, RegressionError, _pointer_value


class RegressionSuite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.manifest = build(self.base)

    def edit(self, function):
        obj = json.loads(self.manifest.read_text(encoding='utf-8'))
        function(obj)
        self.manifest.write_text(json.dumps(obj), encoding='utf-8')

    def test_all_three_demo_formats_pass(self):
        result = run_regression(self.manifest)
        self.assertEqual(result['case_count'], 3)
        self.assertEqual(result['pass_count'], 3)
        self.assertEqual(result['status'], 'PASS')
        self.assertIn('never approves', result['note'])

    def test_changed_baseline_produces_failed_case_and_nonzero_cli(self):
        self.edit(lambda data: data['cases'][0]['expected'].update({'/summary/pcb_boards': 100}))
        r = run_regression(self.manifest)
        self.assertEqual(r['fail_count'], 1)
        self.assertEqual(r['cases'][0]['failures'][0]['reason'], 'VALUE_CHANGED')
        with patch('sys.stdout'):
            self.assertEqual(main(['regression-check', str(self.manifest)]), 1)

    def test_missing_pointer_fails_without_crash(self):
        self.edit(lambda data: data['cases'][0]['expected'].update({'/does/not/exist': 1}))
        result = run_regression(self.manifest)
        self.assertEqual(result['cases'][0]['failures'][0]['reason'], 'MISSING_VALUE')

    def test_schema_validation_and_duplicate_case_names(self):
        self.edit(lambda data: data.update({'schema_version': 55}))
        with self.assertRaises(RegressionError):
            run_regression(self.manifest)
        self.manifest = build(self.base)
        self.edit(lambda data: data['cases'][1].update({'name': data['cases'][0]['name']}))
        with self.assertRaises(RegressionError):
            run_regression(self.manifest)

    def test_no_paths_outside_regression_folder(self):
        self.edit(lambda data: data['cases'][0].update({'input': '../../secret.epro2'}))
        with self.assertRaises(RegressionError):
            run_regression(self.manifest)

    def test_no_symlink_escape(self):
        with tempfile.TemporaryDirectory() as other:
            external = Path(other) / 'outside.enet'
            external.write_text('{}')
            (self.base / 'link.enet').symlink_to(external)
            self.edit(lambda data: data['cases'][1].update({'input': 'link.enet'}))
            with self.assertRaises(RegressionError):
                run_regression(self.manifest)

    def test_malformed_or_missing_input_cannot_pass(self):
        (self.base / 'synthetic.enet').write_text('not-json')
        result = run_regression(self.manifest)
        self.assertEqual(result['cases'][1]['failures'][0]['reason'], 'INPUT_ERROR')
        (self.base / 'synthetic.enet').unlink()
        with self.assertRaises(RegressionError):
            run_regression(self.manifest)

    def test_invalid_json_pointers_rejected(self):
        for bad in ['/bad~x', '/bad~', 'bad']:
            with self.subTest(bad=bad), self.assertRaises(RegressionError):
                _pointer_value({'x': 1}, bad)
        self.assertEqual(_pointer_value({'a/b': {'~': [4]}}, '/a~1b/~0/0'), 4)

    def test_cli_pass_writes_json(self):
        out = self.base / 'report.json'
        with patch('sys.stdout'):
            code = main(['regression-check', str(self.manifest), '--json', str(out)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.read_text())['pass_count'], 3)


if __name__ == '__main__':
    unittest.main()