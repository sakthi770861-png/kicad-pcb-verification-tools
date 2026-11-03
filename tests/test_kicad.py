import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pcbverify.kicad import native_check

class KiCadTests(unittest.TestCase):
    def test_missing_cli_is_not_reported_as_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "example.kicad_sch"
            p.write_text("(kicad_sch)")
            with patch("pcbverify.kicad.shutil.which", return_value=None):
                r = native_check(p)
        self.assertEqual(r["status"], "NOT_RUN")

    def test_invalid_extension_rejected(self):
        with self.assertRaises(ValueError):
            native_check("example.txt")