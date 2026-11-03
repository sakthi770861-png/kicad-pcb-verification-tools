import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pcbverify.quality import release_gate
from pcbverify.__main__ import main

class ReleaseGateTests(unittest.TestCase):
    def test_missing_evidence_explicitly_blocks(self):
        r=release_gate()
        self.assertEqual(r['status'],'BLOCKED')
        self.assertEqual(len(r['checks']),5)
        self.assertEqual(len(r['blockers']),5)

    def test_cli_always_exit_nonzero_even_without_inputs(self):
        with tempfile.TemporaryDirectory() as td:
            o=Path(td)/'gate.json'
            self.assertEqual(main(['release-gate','--json',str(o)]),1)
            report=json.loads(o.read_text())
            self.assertEqual(report['status'],'BLOCKED')
            self.assertIn('PRERELEASE',report['software_release_status'])

    def test_clean_mocked_evidence_never_becomes_approval(self):
        fake={'status':'MANIFEST_REVIEW_ONLY','missing_required_categories':[], 'cam_header_findings':[]}
        net={'status':'EXPORTED_NETLIST_SNAPSHOT','component_count':1,'warnings':[]}
        geo={'status':'STRUCTURAL_INSPECTION_ONLY','findings':[]}
        native={'status':'CLI_COMPLETED','validation_passed':True,'exit_code':0,
                'native_report_summary':{'issue_count':0}}
        with patch('pcbverify.quality.analyze_path',return_value=geo), \
             patch('pcbverify.quality.read_enet',return_value=net), \
             patch('pcbverify.quality.compare_geometry',return_value={'findings':[]}), \
             patch('pcbverify.quality.inspect_manufacturing_zip',return_value=fake), \
             patch('pcbverify.quality.native_check',return_value=native):
            r=release_gate(easyeda=Path('a.zip'),netlist=Path('a.enet'),
                           fabrication=Path('fab.zip'),kicad_schematic=Path('a.kicad_sch'),kicad_board=Path('a.kicad_pcb'))
            self.assertEqual(r['status'],'ENGINEERING_REVIEW_REQUIRED')
            self.assertEqual(r['blockers'],[])

    def test_strict_fab_missing_files_returns_failure(self):
        with tempfile.TemporaryDirectory() as td:
            from zipfile import ZipFile
            z=Path(td)/'empty.zip'
            with ZipFile(z,'w') as f: f.writestr('readme.txt','no manufacture files')
            self.assertEqual(main(['manufacturing-audit',str(z),'--strict','--json',str(Path(td)/'o.json')]),1)
            self.assertEqual(main(['manufacturing-audit',str(z),'--json',str(Path(td)/'o2.json')]),0)

if __name__=='__main__':unittest.main()