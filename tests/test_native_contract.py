"""CLI I/O contract tests with a fake executable; NOT native KiCad execution."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pcbverify.kicad import native_check

MOCK_EXE = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args=sys.argv
out=Path(args[args.index('--output')+1])
kind=args[1]
mode=os.environ.get('PCBVERIFY_MOCK_MODE','ok')
if mode == 'missing': sys.exit(0)
if mode == 'invalid': out.write_text('{invalid'); sys.exit(0)
if kind == 'sch':
    data={'sheets':[{'path':'/','violations':[]}]} 
else:
    data={'violations':[],'unconnected_items':[],'schematic_parity':[]}
if mode == 'findings':
    if kind == 'sch': data['sheets'][0]['violations'].append({'severity':'error','type':'electrical','description':'synthetic'})
    else: data['unconnected_items'].append({'severity':'error','type':'unconnected','description':'synthetic'})
out.write_text(json.dumps(data))
sys.exit(2 if mode=='nonzero' else 0)
'''

class NativeContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        exe=root/'kicad-cli'
        exe.write_text(MOCK_EXE)
        exe.chmod(0o755)
        self.exe=str(exe)
        self.sch=root/'test.kicad_sch'; self.sch.write_text('synthetic')
        self.pcb=root/'test.kicad_pcb'; self.pcb.write_text('synthetic')

    def check_mode(self, mode, path):
        with patch('pcbverify.kicad.shutil.which', return_value=self.exe):
            with patch.dict(os.environ, {'PCBVERIFY_MOCK_MODE': mode}):
                return native_check(path)

    def test_both_synthetic_valid_reports(self):
        for path in (self.sch,self.pcb):
            with self.subTest(path=path):
                data=self.check_mode('ok',path)
                self.assertEqual(data['status'],'CLI_COMPLETED')
                self.assertTrue(data['validation_passed'])
                self.assertEqual(data['native_report_summary']['issue_count'],0)

    def test_missing_or_unparseable_fail_closed(self):
        for mode in ('missing','invalid'):
            with self.subTest(mode=mode):
                r=self.check_mode(mode,self.sch)
                self.assertEqual(r['status'],'REPORT_UNREADABLE')
                self.assertFalse(r['validation_passed'])

    def test_nonzero_cannot_pass(self):
        r=self.check_mode('nonzero',self.pcb)
        self.assertEqual(r['status'],'CLI_NONZERO')
        self.assertFalse(r['validation_passed'])

    def test_findings_zero_exit_not_marked_clean(self):
        r=self.check_mode('findings',self.sch)
        self.assertEqual(r['status'],'CLI_REPORTED_ISSUES')
        self.assertFalse(r['validation_passed'])

if __name__ == '__main__': unittest.main()