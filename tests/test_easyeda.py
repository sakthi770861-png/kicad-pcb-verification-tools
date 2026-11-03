"""Standard-library unittest suite; synthetic fixtures only, no private PCB sources."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from pcbverify.easyeda import FormatError, analyze_epro2_bytes, analyze_path, build_report
from pcbverify.__main__ import to_markdown


def line(kind, payload, **h):
    return json.dumps({"type": kind, **h}) + "||" + (json.dumps(payload) if payload is not None else "") + "|\n"


def fixture(doctype="PCB", refs=("R1",), layer_count=2):
    s = line("DOCHEAD", {"docType": "DEVICE", "uuid": "dev-id"})
    s += line("META", {"title": "Example Resistor"})
    s += line("DOCHEAD", {"docType": doctype, "uuid": "doc-id"})
    s += line("META", {"title": "example"})
    for index, ref in enumerate(refs):
        c = "component-" + str(index)
        s += line("COMPONENT", {"x": 0, "y": 0}, id=c)
        s += line("ATTR", {"key": "Designator", "value": ref, "parentId": c}, id=c + "ref")
        s += line("ATTR", {"key": "Device", "value": "dev-id", "parentId": c}, id=c + "dev")
    if doctype == "PCB":
        for index, typ in enumerate(["TOP", "BOTTOM"] + ["SIGNAL"] * (layer_count - 2)):
            s += line("LAYER", {"layerType": typ, "layerName": str(index), "use": True}, id="L" + str(index))
        s += line("NET", {}, id='["NET", "GND"]')
        s += line("POLY", {"polyType": "BOARD_OUTLINE"}, id="outline")
    b = io.BytesIO()
    with ZipFile(b, "w") as z:
        z.writestr("project2.json", '{"title":"example"}')
        z.writestr("example.epru", s)
    return b.getvalue()


class EasyEDAReadTests(unittest.TestCase):
    def test_pcb_layers_and_placed_components_only(self):
        report = analyze_epro2_bytes(fixture(refs=("R1", "C1")))
        board = report["boards"][0]
        self.assertEqual(board["active_copper_layer_count"], 2)
        self.assertEqual(board["component_count"], 2)
        self.assertEqual(board["nets"], ["GND"])
        self.assertEqual(board["components"][0]["device"], "Example Resistor")

    def test_detect_duplicate_designators(self):
        scan = analyze_epro2_bytes(fixture(refs=("U1", "U1")))
        self.assertEqual(scan["boards"][0]["duplicate_designators"], ["U1"])
        aggregated = build_report("x", [scan])
        self.assertTrue(any(f["code"] == "DUPLICATE_DESIGNATOR" for f in aggregated["findings"]))

    def test_schematic_pcb_parity(self):
        pcb = analyze_epro2_bytes(fixture(refs=("R1",)), "p.epro2")
        sch = analyze_epro2_bytes(fixture(doctype="SCH_PAGE", refs=("R1", "C1")), "s.epro2")
        r = build_report("fixture.zip", [sch, pcb])
        self.assertEqual(r["summary"]["schematic_only_references"], ["C1"])
        self.assertIn("SCH_ONLY_REFERENCE", [f["code"] for f in r["findings"]])
        self.assertIn("not manufacturing approval", to_markdown(r))

    def test_nested_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "archive.zip"
            with ZipFile(f, "w") as z:
                z.writestr("pcb.epro2", fixture())
                z.writestr("sch.epro2", fixture(doctype="SCH_PAGE"))
            result = analyze_path(f)
            self.assertEqual(result["summary"]["pcb_boards"], 1)
            self.assertEqual(result["summary"]["schematic_pages"], 1)

    def test_deleted_component_and_ticket_precedence(self):
        from pcbverify.easyeda import _parse_epru
        s = line("DOCHEAD", {"docType": "PCB", "uuid": "d"})
        s += line("COMPONENT", {"x": 1}, id="c", ticket=1)
        s += '{"type":"COMPONENT","id":"c","ticket":2}||""|\n'
        s += line("COMPONENT", {"x": 9}, id="c", ticket=0)
        docs = _parse_epru(s.encode())
        self.assertEqual([h for h, _ in docs[0]["records"] if h["type"] == "COMPONENT"], [])

    def test_corrupt_log_rejected(self):
        buf = io.BytesIO()
        with ZipFile(buf, "w") as z:
            z.writestr("broken.epru", "not a valid record")
        with self.assertRaises(FormatError):
            analyze_epro2_bytes(buf.getvalue())

    def test_reject_oversize_member(self):
        from pcbverify.easyeda import MAX_EPRU_BYTES
        buf = io.BytesIO()
        with ZipFile(buf, "w", compression=8) as z:
            z.writestr("large.epru", "a" * (MAX_EPRU_BYTES + 1))
        with self.assertRaises(FormatError):
            analyze_epro2_bytes(buf.getvalue())

    def test_no_designer_parts_from_embedded_libraries(self):
        r = analyze_epro2_bytes(fixture(doctype="PCB", refs=()))
        self.assertEqual(r["boards"][0]["component_count"], 0)


if __name__ == "__main__":
    unittest.main()