import csv
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from pcbverify.manufacturing import inspect_manufacturing_zip, ManufacturingArchiveError

class TestManufacturingManifest(unittest.TestCase):
    def make_archive(self, members):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        output=Path(temp.name)/'cam.zip'
        with ZipFile(output,'w') as z:
            for name, payload in members.items():z.writestr(name,payload)
        return output

    def test_complete_manifest_and_assembly(self):
        path=self.make_archive({'Project-F_Cu.gbr':'Gerber','Project-B_Cu.gbr':'Gerber',
          'Project-Edge_Cuts.gbr':'Gerber','Project-PTH.drl':'drill',
          'Project-F_Mask.gbr':'mask','Project-B_Mask.gbr':'mask',
          'BOM_JLCPCB.csv':'Designator,Value\n"R1,R2",10k\n',
          'CPL_JLCPCB.csv':'Designator,Mid X,Mid Y\nR1,1,2\nR2,3,4\n'})
        r=inspect_manufacturing_zip(path,assembly=True)
        self.assertEqual(r['missing_required_categories'],[])
        self.assertEqual(r['csv_summary']['BOM_JLCPCB.csv']['references'],['R1','R2'])
        self.assertEqual(r['bom_placement_reference_differences']['bom_only'],[])
        self.assertEqual(r['status'],'MANIFEST_REVIEW_ONLY')

    def test_missing_required_cannot_pass(self):
        r=inspect_manufacturing_zip(self.make_archive({'board-F_Cu.gbr':'x'}),assembly=True)
        self.assertIn('back_copper',r['missing_required_categories'])
        self.assertIn('bom',r['missing_required_categories'])

    def test_gerber_legacy_suffix(self):
        r=inspect_manufacturing_zip(self.make_archive({'a.gtl':'','a.gbl':'','a.gko':'','a.xln':''}))
        self.assertEqual(r['missing_required_categories'],[])

    def test_bad_zip(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        p=Path(temp.name)/'bad.zip';p.write_bytes(b'fake')
        with self.assertRaises(ManufacturingArchiveError):inspect_manufacturing_zip(p)

    def test_reject_path_traversal(self):
        with self.assertRaises(ManufacturingArchiveError):
            inspect_manufacturing_zip(self.make_archive({'../board.gtl':'bad'}))

    def test_bom_cpl_difference_is_advisory(self):
        r=inspect_manufacturing_zip(self.make_archive({'BOM.csv':'Designator\nR1\n',
                                                         'CPL.csv':'Designator\nR2\n'}),assembly=True)
        self.assertEqual(r['bom_placement_reference_differences']['bom_only'],['R1'])
        self.assertTrue(r['missing_required_categories'])

if __name__=='__main__':unittest.main()