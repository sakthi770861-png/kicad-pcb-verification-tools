"""Synthetic examples only; no personal/client design files in the repository."""
import io
import json
import unittest
from zipfile import ZipFile

from pcbverify.easyeda import analyze_epro2_bytes, build_report


def record(typ, data, identifier=None):
    head = {"type": typ, "ticket": 1}
    if identifier is not None:
        head["id"] = identifier
    return json.dumps(head) + "||" + (json.dumps(data) if data is not None else '""') + "|\n"


def synthetic_design(*, pin_positions=((-10, 0), (10, 0)), wires=(),
                     origin=(50, 50), rotation=0, mirror=False, symbol_present=True,
                     placed_part="A", symbol_part="A", override=None, tombstone_wire=None):
    content = ""
    if symbol_present:
        content += record("DOCHEAD", {"docType": "SYMBOL", "uuid": "symbol-1"})
        content += record("META", {"title": "Test Symbol"})
        for k, (px, py) in enumerate(pin_positions, 1):
            content += record("PIN", {"x": px, "y": py, "partId": symbol_part}, f"pin{k}")
            for attr, value in (("Pin Number", str(k)), ("Pin Name", f"P{k}")):
                content += record("ATTR", {"parentId": f"pin{k}", "key": attr, "value": value}, f"pa{k}-{attr}")
    content += record("DOCHEAD", {"docType": "SCH_PAGE", "uuid": "page-1"})
    content += record("META", {"title": "Schematic"})
    content += record("COMPONENT", {"x": origin[0], "y": origin[1], "rotation": rotation,
                                    "isMirror": mirror, "partId": placed_part}, "c1")
    for key, value in (("Symbol", "symbol-1"), ("Designator", "U1")):
        content += record("ATTR", {"parentId": "c1", "key": key, "value": value}, f"c1-{key}")
    if override is not None:
        content += record("ATTR", {"parentId": "c1pin1", "key": "Pin Number", "value": override}, "o1")
    for wid, segments, net in wires:
        content += record("WIRE", {"zIndex": 0}, wid)
        if net is not None:
            content += record("ATTR", {"parentId": wid, "key": "NET", "value": net}, f"net-{wid}")
        for index, (x1, y1, x2, y2) in enumerate(segments):
            content += record("LINE", {"startX": x1, "startY": y1, "endX": x2,
                                       "endY": y2, "lineGroup": wid}, f"line-{wid}-{index}")
    if tombstone_wire:
        wid, seg = tombstone_wire
        content += record("LINE", {"startX": seg[0], "startY": seg[1], "endX": seg[2],
                                   "endY": seg[3], "lineGroup": wid}, "orphan")
    stream = io.BytesIO()
    with ZipFile(stream, "w") as z:
        z.writestr("example.epru", content)
    return analyze_epro2_bytes(stream.getvalue())["schematics"][0]["connectivity"]


class SchematicConnectivityTests(unittest.TestCase):
    def test_named_pin_nets_and_no_unconnected_candidates(self):
        c = synthetic_design(wires=[
            ("w1", [(0, 50, 40, 50)], "+5V"),
            ("w2", [(60, 50, 90, 50)], "GND"),
        ])
        self.assertEqual(c["connected_pin_count"], 2)
        self.assertEqual(c["unconnected_pin_candidates"], 0)
        self.assertEqual([(p["pin_number"], p["net_name"]) for p in c["pins"]],
                         [("1", "+5V"), ("2", "GND")])

    def test_missing_pin_is_info_only_and_not_certified_error(self):
        c = synthetic_design(wires=[("w1", [(0, 50, 40, 50)], None)])
        self.assertEqual(c["unconnected_pin_candidates"], 1)
        self.assertEqual(c["pins"][1]["connection_status"], "UNCONNECTED_CANDIDATE")
        self.assertTrue(all(f["severity"] == "info" for f in c["findings"]))

    def test_rotate_then_mirror_and_pin_number_override(self):
        c = synthetic_design(pin_positions=((10, 5),), origin=(100, 100), rotation=90,
                             mirror=True, override="A1",
                             wires=[("w1", [(105, 110, 120, 110)], "SIGNAL")])
        self.assertEqual(c["connected_pin_count"], 1)
        self.assertEqual(c["pins"][0]["position"], [105.0, 110.0])
        self.assertEqual(c["pins"][0]["pin_number"], "A1")

    def test_crossing_wires_not_assumed_electrically_joined(self):
        c = synthetic_design(pin_positions=((0, 0),), origin=(10, 0), wires=[
            ("a", [(0, 0, 20, 0)], "A"),
            ("b", [(10, -10, 10, 10)], "B"),
        ])
        self.assertEqual(c["ambiguous_pin_count"], 1)
        self.assertEqual(c["pins"][0]["connection_status"], "AMBIGUOUS_INTERSECTION")
        self.assertEqual(c["pins"][0]["candidate_net_names"], ["A", "B"])
        self.assertEqual(len(c["nets"]), 2)

    def test_t_junction_merges_groups_and_named_conflict_is_reported(self):
        c = synthetic_design(wires=[
            ("a", [(0, 50, 80, 50)], "+5V"),
            ("b", [(40, 50, 40, 70)], "GND"),
        ])
        self.assertEqual(len(c["nets"]), 1)
        self.assertIn("CONFLICTING_WIRE_NET_NAMES", [f["code"] for f in c["findings"]])

    def test_same_name_merges_separated_wire_groups(self):
        c = synthetic_design(wires=[
            ("a", [(0, 50, 40, 50)], "GLOBAL"),
            ("b", [(60, 50, 90, 50)], "GLOBAL"),
        ])
        self.assertEqual(len(c["nets"]), 1)
        self.assertEqual(c["nets"][0]["connected_pins"], ["U1.1", "U1.2"])

    def test_missing_symbol_is_unknown_not_disconnected(self):
        c = synthetic_design(symbol_present=False)
        self.assertEqual(c["unresolved_components"], ["U1"])
        self.assertEqual(c["unconnected_pin_candidates"], 0)
        self.assertEqual(c["pins"], [])

    def test_mismatched_multipart_symbol_not_miscounted(self):
        c = synthetic_design(placed_part="B", symbol_part="A")
        self.assertEqual(c["unresolved_components"], ["U1"])
        self.assertEqual(c["unconnected_pin_candidates"], 0)

    def test_orphan_deleted_wire_geometry_is_ignored(self):
        c = synthetic_design(tombstone_wire=("deleted", (0, 50, 40, 50)))
        self.assertEqual(c["skipped_wire_lines"], 1)
        self.assertEqual(c["unconnected_pin_candidates"], 2)

    def test_report_version_matches_current_release(self):
        # Real scan construction is tested separately via analyze_epro2_bytes.
        import pcbverify.easyeda as ed
        original = ed.analyze_epro2_bytes
        self.assertEqual(original_version(original), "0.5.0")


def original_version(fn):
    # Build a truly empty page rather than referencing any user data.
    content = record("DOCHEAD", {"docType": "SCH_PAGE", "uuid": "p1"})
    buf = io.BytesIO()
    with ZipFile(buf, "w") as z:
        z.writestr("e.epru", content)
    return build_report("test.zip", [fn(buf.getvalue())])["tool_version"]