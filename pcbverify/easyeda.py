"""Read-only EasyEDA Pro V3 (.epro2) project inspection.

This is an inventory and structural checker. It is NOT EasyEDA's native
ERC, DRC, circuit simulation, electrical current rating, or manufacturer check.
"""
from __future__ import annotations

from collections import Counter
from io import BytesIO
import json
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile
from .connectivity import inspect_schematic

MAX_EPRO2_BYTES = 30 * 1024 * 1024
MAX_EPRU_BYTES = 20 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 300

class FormatError(ValueError):
    """An input file could not safely be interpreted as EasyEDA Pro V3."""


def _members(z: ZipFile) -> list:
    entries = z.infolist()
    if len(entries) > MAX_ARCHIVE_ENTRIES:
        raise FormatError("Archive contains too many entries")
    return entries


def _read_limited(z: ZipFile, name: str, limit: int) -> bytes:
    item = z.getinfo(name)
    if item.file_size > limit:
        raise FormatError(f"Archive member {name!r} exceeds size limit")
    with z.open(item) as inp:
        data = inp.read(limit + 1)
    if len(data) > limit:
        raise FormatError(f"Archive member {name!r} exceeds size limit")
    return data


def _parse_epru(contents: bytes) -> list[dict[str, Any]]:
    """Parse DOCHEAD-separated records, ignoring embedded library geometries.

    EasyEDA Pro V3 log lines are HEADER||DATA| where both fields are JSON.
    A blank DATA field is allowed. A DOCHEAD begins a new document section.
    """
    try:
        raw = contents.decode("utf-8-sig")
    except UnicodeDecodeError as err:
        raise FormatError("EPRU content is not UTF-8") from err
    documents: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    # The official V3 format is append-only: latest logical ticket wins, and
    # an empty payload is a deletion tombstone, not an unconnected PCB pad.
    latest: dict[tuple[str, str], tuple[int, int, dict, Any]] = {}

    def finish_document() -> None:
        if current is None:
            return
        active = sorted(latest.values(), key=lambda entry: entry[1])
        current["records"] = [(h, d) for _, _, h, d in active if isinstance(d, dict)]
        meta = [d for _, _, h, d in active if h.get("type") == "META" and isinstance(d, dict)]
        current["metadata"] = meta[-1] if meta else {}
        deleted = [d for _, _, h, d in active if h.get("type") == "DELETE_DOC" and isinstance(d, dict) and d.get("isDelete")]
        if not deleted:
            documents.append(current)

    for number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        if "||" not in line:
            raise FormatError(f"Invalid EPRU log structure at line {number}")
        htext, rest = line.split("||", 1)
        dtext = rest[:-1] if rest.endswith("|") else rest
        try:
            header = json.loads(htext)
            payload = json.loads(dtext) if dtext else ""
        except json.JSONDecodeError as err:
            raise FormatError(f"Malformed JSON in EPRU at line {number}: {err.msg}") from err
        if not isinstance(header, dict) or not (isinstance(payload, dict) or payload == ""):
            raise FormatError(f"Unexpected log record at line {number}")
        typ = header.get("type")
        if typ == "DOCHEAD":
            if not isinstance(payload, dict):
                raise FormatError(f"Missing DOCHEAD at line {number}")
            finish_document()
            latest = {}
            current = {"doc_type": payload.get("docType", "UNKNOWN"),
                       "uuid": payload.get("uuid", ""),
                       "records": [], "metadata": {}}
            continue
        if current is None:
            raise FormatError(f"Record before DOCHEAD at line {number}")
        logical_id = str(header.get("id", ""))
        key = (str(typ), logical_id)
        ticket = header.get("ticket", 0)
        if not isinstance(ticket, int):
            raise FormatError(f"Invalid record ticket at line {number}")
        if key not in latest or ticket >= latest[key][0]:
            latest[key] = (ticket, number, header, payload)
    finish_document()
    if not documents:
        raise FormatError("No active EasyEDA documents present")
    return documents


def analyze_epro2_bytes(content: bytes, filename: str = "design.epro2") -> dict[str, Any]:
    """Return a conservative EasyEDA V3 inventory for one .epro2 archive."""
    if len(content) > MAX_EPRO2_BYTES:
        raise FormatError("EasyEDA archive is too large")
    try:
        with ZipFile(BytesIO(content)) as z:
            names = [entry.filename for entry in _members(z) if entry.filename.endswith(".epru")]
            if not names:
                raise FormatError("No .epru design log inside .epro2 archive")
            if len(names) > 20:
                raise FormatError("Too many .epru logs in archive")
            docs = []
            for name in names:
                docs.extend(_parse_epru(_read_limited(z, name, MAX_EPRU_BYTES)))
    except BadZipFile as err:
        raise FormatError("Not a valid .epro2 ZIP archive") from err

    # DOCHEADs for symbol/footprint/device libraries are NOT actual placed parts.
    devices = {str(doc["uuid"]): doc["metadata"].get("title", "")
               for doc in docs if doc["doc_type"] == "DEVICE"}
    footprints = {str(doc["uuid"]): doc["metadata"].get("title", "")
                  for doc in docs if doc["doc_type"] == "FOOTPRINT"}
    symbols = {str(doc["uuid"]): doc for doc in docs if doc["doc_type"] == "SYMBOL"}
    schematics = []
    boards = []
    for doc in docs:
        if doc["doc_type"] not in {"SCH_PAGE", "PCB"}:
            continue
        recs = doc["records"]
        components = {str(h["id"]): (d, {})
                      for h, d in recs if h.get("type") == "COMPONENT" and h.get("id")}
        for h, data in recs:
            if h.get("type") == "ATTR":
                parent = str(data.get("parentId", ""))
                key = data.get("key")
                if parent in components and isinstance(key, str):
                    components[parent][1][key] = data.get("value")
        placed = []
        for component_id, (raw, attrs) in components.items():
            des = attrs.get("Designator")
            if not isinstance(des, str) or not des.strip() or des.strip().startswith("#"):
                # GND symbols and page frames commonly have no designator.
                continue
            device_id = str(attrs.get("Device") or "")
            fp_id = str(attrs.get("Footprint") or "")
            origin_footprint = raw.get("attrs", {}).get("Origin Footprint", "")
            placed.append({"ref": des.strip(),
                           "device": devices.get(device_id, ""),
                           "footprint": footprints.get(fp_id) or origin_footprint or "",
                           "component_id": component_id})
        placed.sort(key=lambda item: item["ref"])
        duplicates = sorted(ref for ref, count in Counter(p["ref"] for p in placed).items() if count > 1)
        record_types = Counter(h.get("type") for h, _ in recs)
        result = {"name": doc["metadata"].get("title", ""),
                  "components": placed,
                  "component_count": len(placed),
                  "duplicate_designators": duplicates,
                  "record_counts": dict(sorted(record_types.items()))}
        if doc["doc_type"] == "SCH_PAGE":
            result["wire_record_count"] = record_types.get("WIRE", 0)
            result["connectivity"] = inspect_schematic(doc, symbols)
            schematics.append(result)
        else:
            layers = [d for h, d in recs if h.get("type") == "LAYER"]
            copper_layers = [str(l.get("layerName", "")) for l in layers
                             if l.get("layerType") in {"TOP", "BOTTOM", "SIGNAL"}
                             and l.get("use") is True]
            named_nets = []
            for h, _ in recs:
                if h.get("type") == "NET":
                    try:
                        key = json.loads(str(h.get("id", "")))
                        if len(key) > 1 and key[1]:
                            named_nets.append(key[1])
                    except (ValueError, TypeError, IndexError):
                        pass
            unassigned = sum(1 for h, d in recs
                             if h.get("type") == "PAD_NET" and not d.get("padNet"))
            board_outline = sum(1 for h, d in recs
                                if h.get("type") == "POLY" and d.get("polyType") == "BOARD_OUTLINE")
            result.update({"active_copper_layers": copper_layers,
                           "active_copper_layer_count": len(copper_layers),
                           "nets": sorted(set(named_nets)),
                           "net_count": len(set(named_nets)),
                           "pad_net_records": record_types.get("PAD_NET", 0),
                           "unassigned_pad_net_records": unassigned,
                           "via_records": record_types.get("VIA", 0),
                           "board_outline_polygons": board_outline})
            boards.append(result)
    return {"file": filename, "format": "EasyEDA Pro V3 (.epro2)",
            "schematics": schematics, "boards": boards,
            "library_document_count": sum(d["doc_type"] in {"SYMBOL", "FOOTPRINT", "DEVICE"} for d in docs)}


def analyze_path(path: Path | str) -> dict[str, Any]:
    """Analyze either one .epro2 or a ZIP containing multiple .epro2 files."""
    path = Path(path)
    if path.suffix.lower() == ".epro2":
        return build_report(path.name, [analyze_epro2_bytes(path.read_bytes(), path.name)])
    if path.suffix.lower() != ".zip":
        raise FormatError("Expected an .epro2 file or an outer .zip archive")
    with ZipFile(path) as z:
        entries = _members(z)
        names = [item.filename for item in entries if item.filename.lower().endswith(".epro2")]
        if not names:
            raise FormatError("ZIP contains no .epro2 files")
        file_reports = []
        for name in sorted(names):
            content = _read_limited(z, name, MAX_EPRO2_BYTES)
            file_reports.append(analyze_epro2_bytes(content, name))
    return build_report(path.name, file_reports)


def build_report(input_name: str, scans: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate files that belong to the same submitted project archive."""
    schematic_pages = [page for scan in scans for page in scan["schematics"]]
    pcbs = [board for scan in scans for board in scan["boards"]]
    sch_refs = {item["ref"] for page in schematic_pages for item in page["components"]}
    pcb_refs = {item["ref"] for board in pcbs for item in board["components"]}
    findings: list[dict[str, str]] = []
    for scan in scans:
        for board in scan["boards"]:
            if board["active_copper_layer_count"] < 2 or board["active_copper_layer_count"] % 2 != 0:
                findings.append({"severity": "warning", "code": "COPPER_LAYER_COUNT",
                                 "message": f"{scan['file']}: unusual active copper layer count {board['active_copper_layer_count']}"})
            if board["board_outline_polygons"] == 0:
                findings.append({"severity": "info", "code": "OUTLINE_NOT_DETECTED",
                                 "message": f"{scan['file']}: no POLY BOARD_OUTLINE record found; other outline primitives not evaluated"})
            if board["unassigned_pad_net_records"]:
                findings.append({"severity": "info", "code": "UNASSIGNED_PAD_NET",
                                 "message": f"{scan['file']}: {board['unassigned_pad_net_records']} PAD_NET records lack assigned nets (may be intentional NC pads)"})
            for des in board["duplicate_designators"]:
                findings.append({"severity": "warning", "code": "DUPLICATE_DESIGNATOR",
                                 "message": f"{scan['file']}: repeated PCB designator {des}"})
        for page in scan["schematics"]:
            for finding in page["connectivity"]["findings"]:
                findings.append({**finding, "message": f"{scan['file']} / {page['name']}: {finding['message']}"})
            for des in page["duplicate_designators"]:
                findings.append({"severity": "warning", "code": "DUPLICATE_DESIGNATOR",
                                 "message": f"{scan['file']}: repeated schematic designator {des}"})
    if schematic_pages and pcbs:
        for des in sorted(sch_refs - pcb_refs):
            findings.append({"severity": "warning", "code": "SCH_ONLY_REFERENCE",
                             "message": f"{des}: found in schematic but not PCB"})
        for des in sorted(pcb_refs - sch_refs):
            findings.append({"severity": "warning", "code": "PCB_ONLY_REFERENCE",
                             "message": f"{des}: found on PCB but not schematic"})
    findings.append({"severity": "info", "code": "NATIVE_VERIFICATION_REQUIRED",
                     "message": "Geometric pin-to-wire contact is not authoritative EasyEDA electrical net connectivity. No native EasyEDA ERC/DRC, trace current, thermal, USB-C or assembly validation was performed."})
    return {"tool_version": "0.2.0", "input": input_name, "files": scans,
            "summary": {"schematic_pages": len(schematic_pages), "pcb_boards": len(pcbs),
                        "schematic_references": len(sch_refs), "pcb_references": len(pcb_refs),
                        "schematic_only_references": sorted(sch_refs - pcb_refs) if pcbs else [],
                        "pcb_only_references": sorted(pcb_refs - sch_refs) if schematic_pages else []},
            "findings": findings,
            "status": "STRUCTURAL_INSPECTION_ONLY"}