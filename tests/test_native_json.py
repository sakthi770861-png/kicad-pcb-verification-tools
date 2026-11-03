import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from pcbverify.kicad import summarize_native_json, NativeReportError, native_check

class NativeJsonTests(unittest.TestCase):
    def test_erc_counts_all_sheets(self):
        r=summarize_native_json({'sheets':[
           {'path':'/','violations':[{'severity':'error','type':'pin_conflict','description':'bad'}]},
           {'path':'/Power','violations':[{'severity':'warning','type':'power_pin_not_driven'}]}]},'erc')
        self.assertEqual(r['issue_count'],2)
        self.assertEqual(r['severity_counts'],{'error':1,'warning':1})
        self.assertEqual(r['issues'][1]['category'],'sheet:/Power')

    def test_drc_unconnected_is_not_ignored(self):
        r=summarize_native_json({'violations':[],
                                  'unconnected_items':[{'severity':'error','type':'unconnected'}],
                                  'schematic_parity':[{'severity':'warning'}]},'drc')
        self.assertEqual(r['issue_count'],2)
        self.assertEqual(r['severity_counts']['error'],1)

    def test_missing_drc_sections_are_not_reported_as_zero(self):
        with self.assertRaises(NativeReportError):
            summarize_native_json({'violations':[]},'drc')

    def test_unknown_document_rejected(self):
        with self.assertRaises(NativeReportError):summarize_native_json({'sheets':[]},'drc')

    @patch('pcbverify.kicad.shutil.which',return_value='/usr/bin/kicad-cli')
    @patch('pcbverify.kicad.subprocess.run')
    def test_native_cli_json_integration(self,run,which):
        def fake(argv,**kwargs):
            self.assertIn('--format',argv)
            self.assertEqual(argv[argv.index('--format')+1],'json')
            out=Path(argv[argv.index('--output')+1]);out.write_text(json.dumps({'sheets':[{'path':'/','violations':[]}]}))
            return SimpleNamespace(returncode=0,stdout='',stderr='')
        run.side_effect=fake
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'example.kicad_sch';p.write_text('dummy')
            r=native_check(p)
            self.assertEqual(r['status'],'CLI_COMPLETED')
            self.assertEqual(r['native_report_summary']['issue_count'],0)

    @patch('pcbverify.kicad.shutil.which',return_value='/usr/bin/kicad-cli')
    @patch('pcbverify.kicad.subprocess.run')
    def test_no_report_is_not_success(self,run,which):
        run.return_value=SimpleNamespace(returncode=0,stdout='',stderr='')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'example.kicad_pcb';p.write_text('dummy')
            r=native_check(p)
            self.assertEqual(r['status'],'REPORT_UNREADABLE')

if __name__=='__main__':unittest.main()