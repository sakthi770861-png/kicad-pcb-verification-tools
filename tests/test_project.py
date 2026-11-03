import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pcbverify.project import project_audit, project_markdown
from pcbverify.__main__ import main

class ProjectAuditTests(unittest.TestCase):
    def test_no_inputs_rejected(self):
        with self.assertRaises(ValueError): project_audit()

    @patch('pcbverify.project.inspect_manufacturing_zip')
    def test_manifest_only_does_not_approve(self,mock):
        mock.return_value={'status':'MANIFEST_REVIEW_ONLY','missing_required_categories':[]}
        result=project_audit(fabrication='example.zip', assembly=True)
        self.assertEqual(result['status'],'EVIDENCE_BUNDLE_NOT_MANUFACTURING_APPROVAL')
        self.assertIn('kicad_pcb_drc',result['not_provided_checks'])
        self.assertIn('NOT MANUFACTURING APPROVAL',project_markdown(result))
        mock.assert_called_once_with('example.zip',assembly=True)

    @patch('pcbverify.project.native_check')
    def test_failed_native_drc_is_preserved(self,mock):
        mock.return_value={'status':'CLI_NONZERO','exit_code':5}
        result=project_audit(kicad_board='bad.kicad_pcb')
        self.assertEqual(result['native_checks_unavailable_or_nonzero'][0]['status'],'CLI_NONZERO')

    @patch('pcbverify.project.compare_geometry')
    @patch('pcbverify.project.read_enet')
    @patch('pcbverify.project.analyze_path')
    def test_comparison_only_when_both_supplied(self, a, n, c):
        a.return_value={'status':'STRUCTURAL_INSPECTION_ONLY'}
        n.return_value={'status':'EXPORTED_NETLIST_SNAPSHOT'}
        c.return_value={'status':'COMPARISON_REQUIRES_SAME_REVISION'}
        r=project_audit(easyeda='x.epro2',netlist='x.enet')
        self.assertIn('geometry_netlist_comparison',r['evidence'])
        c.assert_called_once()

    def test_cli_requires_input(self):
        self.assertEqual(main(['project-audit']),2)

    @patch('pcbverify.__main__.project_audit')
    def test_cli_json_and_markdown(self,mock):
        mock.return_value={'status':'EVIDENCE_BUNDLE_NOT_MANUFACTURING_APPROVAL','checks':[],
                            'not_provided_checks':[],'native_checks_unavailable_or_nonzero':[],
                            'evidence':{},'note':'Not approval.'}
        with tempfile.TemporaryDirectory() as t:
            j,m=Path(t)/'report.json',Path(t)/'report.md'
            self.assertEqual(main(['project-audit','--fabrication','x.zip','--json',str(j),'--markdown',str(m)]),0)
            self.assertEqual(json.loads(j.read_text())['status'],'EVIDENCE_BUNDLE_NOT_MANUFACTURING_APPROVAL')
            self.assertIn('NOT MANUFACTURING APPROVAL',m.read_text())

if __name__ == '__main__':unittest.main()