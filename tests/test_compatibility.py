"""Guard against accidentally using syntax newer than the declared Python floor."""
import ast
from pathlib import Path
import unittest


class Python310SyntaxTests(unittest.TestCase):
    def test_python_310_grammar_for_project_source(self):
        package_dir = Path(__file__).resolve().parents[1] / "pcbverify"
        for src in sorted(package_dir.glob("*.py")):
            with self.subTest(source=src.name):
                ast.parse(src.read_text(encoding="utf-8"),
                          filename=str(src), feature_version=(3, 10))