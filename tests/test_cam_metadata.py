import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from pcbverify.cam import scan_cam_header, cam_cross_checks
from pcbverify.manufacturing import inspect_manufacturing_zip

TOP=b'%FSLAX24Y24*%\n%MOMM*%\n%TF.FileFunction,Copper,L1,Top*%\nG04 generated*\n'
BOT=b'%FSLAX24Y24*%\n%MOMM*%\n%TF.FileFunction,Copper,L2,Bot*%\nG04 other*\n'
DRILL=b'M48\nMETRIC,TZ\nT01C0.3\nT02C0.8\n%\nT01\nX0123Y0456\nM30\n'

class CamHeaderTests(unittest.TestCase):
    def test_header_units_format_x2(self):
        x=scan_cam_header(TOP, 'front_copper')
        self.assertEqual(x['status'],'HEADER_FOUND')
        self.assertEqual(x['units'],'mm')
        self.assertIn('Copper,L1,Top',x['file_function'])
        self.assertIn('FSLAX24Y24',x['coordinate_format'])

    def test_drill_metadata_not_coordinate_certification(self):
        x=scan_cam_header(DRILL,'drill')
        self.assertEqual(x['drill_tool_diameters'],[0.3,0.8])
        self.assertEqual(x['units'],'mm')

    def test_mismatched_x2_layer(self):
        a=scan_cam_header(BOT,'front_copper')
        self.assertIn('COPPER_X2_LAYER_MISMATCH',
            [f['code'] for f in cam_cross_checks({'front_copper':[a]})])

    def test_identical_copper_files(self):
        a=scan_cam_header(TOP,'front_copper')
        b=scan_cam_header(TOP,'back_copper')
        self.assertIn('IDENTICAL_COPPER_EXPORTS',
                      [f['code'] for f in cam_cross_checks({'front_copper':[a],'back_copper':[b]})])

    def test_binary_no_false_verified_header(self):
        x=scan_cam_header(b'abc\x00def', 'front_copper')
        self.assertEqual(x['status'],'BINARY_OR_UNREADABLE')

    def test_archive_reports_preserve_metadata_and_no_certification(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'export.zip'
            with ZipFile(p,'w') as z:
                z.writestr('test-F_Cu.gbr',TOP)
                z.writestr('test-B_Cu.gbr',BOT)
                z.writestr('test-Edge_Cuts.gbr',b'%MOMM*%\n')
                z.writestr('test.drl',DRILL)
            r=inspect_manufacturing_zip(p)
            self.assertEqual(r['status'],'MANIFEST_REVIEW_ONLY')
            self.assertEqual(r['missing_required_categories'],[])
            self.assertEqual(r['cam_header_metadata']['drill'][0]['drill_tool_diameters'],[0.3,0.8])
            self.assertEqual(r['cam_header_findings'],[])

    def test_archive_flags_identical_copper_exports(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'dup.zip'
            with ZipFile(p,'w') as z:
                z.writestr('test-F_Cu.gbr',TOP)
                z.writestr('test-B_Cu.gbr',TOP)
                z.writestr('test-Edge_Cuts.gbr',b'%MOMM*%')
                z.writestr('test.drl',DRILL)
            r=inspect_manufacturing_zip(p)
            self.assertIn('IDENTICAL_COPPER_EXPORTS',[x['code'] for x in r['cam_header_findings']])

if __name__=='__main__':unittest.main()