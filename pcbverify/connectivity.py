"""Conservative pin-to-wire inspection for EasyEDA Pro V3 schematic pages.

Evidence is geometric contact with an active WIRE/LINE and a matching embedded
SYMBOL PIN, *not* a substitute for the editor's native netlist or ERC.
Explicit named WIRE nets are respected; crossing segments do not silently join.
"""
from __future__ import annotations

from collections import defaultdict
from math import cos, radians, sin
from typing import Any

COORD_TOL = 1e-5
MAX_WIRE_LINES = 5000
MAX_COMPONENT_PINS = 10000


def _xy(obj: dict, x: str, y: str) -> tuple[float, float] | None:
    px = obj.get(x)
    py = obj.get(y)
    if isinstance(px, (float, int)) and not isinstance(px, bool) and isinstance(py, (float, int)) and not isinstance(py, bool):
        return float(px), float(py)
    return None


def _pin_location(pin: dict, component: dict) -> tuple[float, float] | None:
    """Symbol-space pin endpoint -> placed schematic-space endpoint."""
    p = _xy(pin, "x", "y") or _xy(pin, "positionX", "positionY")
    base = _xy(component, "x", "y") or _xy(component, "positionX", "positionY")
    if p is None or base is None:
        return None
    angle = component.get("rotation", 0)
    if not isinstance(angle, (int, float)) or isinstance(angle, bool):
        return None
    angle = radians(angle)
    x, y = p
    rx, ry = x * cos(angle) - y * sin(angle), x * sin(angle) + y * cos(angle)
    if component.get("isMirror"):
        rx = -rx  # EasyEDA rotates, then mirrors around the vertical Y axis.
    return (round(base[0] + rx, 6), round(base[1] + ry, 6))


def _touches(point: tuple[float, float], segment: tuple[float, float, float, float]) -> bool:
    x, y = point
    ax, ay, bx, by = segment
    dx, dy = bx - ax, by - ay
    if abs(dx) < COORD_TOL and abs(dy) < COORD_TOL:
        return abs(x - ax) < COORD_TOL and abs(y - ay) < COORD_TOL
    # Perpendicular distance normalized by segment length; reject extensions.
    cross = (x - ax) * dy - (y - ay) * dx
    if abs(cross) > COORD_TOL * max((dx * dx + dy * dy) ** 0.5, 1):
        return False
    return (min(ax, bx) - COORD_TOL <= x <= max(ax, bx) + COORD_TOL
            and min(ay, by) - COORD_TOL <= y <= max(ay, by) + COORD_TOL)


class _Union:
    def __init__(self, identifiers: list[str]):
        self.parents = {item: item for item in identifiers}

    def find(self, item: str) -> str:
        while self.parents[item] != item:
            self.parents[item] = self.parents[self.parents[item]]
            item = self.parents[item]
        return item

    def union(self, left: str, right: str) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parents[max(a, b)] = min(a, b)  # deterministic roots


def _attributes(records: list) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = defaultdict(dict)
    for header, data in records:
        if header.get("type") == "ATTR" and isinstance(data.get("key"), str):
            result[str(data.get("parentId", ""))][data["key"]] = data.get("value")
    return result


def _symbol_pins(symbol: dict[str, Any]) -> list[tuple[str, dict, dict]]:
    attrs = _attributes(symbol["records"])
    return [(str(h.get("id", "")), p, attrs.get(str(h.get("id", "")), {}))
            for h, p in symbol["records"] if h.get("type") == "PIN"]


def inspect_schematic(doc: dict[str, Any], symbols: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Inspect wire/pin geometry, net labels and possible disconnected pins.

    Returns only evidence from embedded symbols and stored WIRE/LINE records.
    Unsupported/missing symbols remain unknown, never counted disconnected.
    """
    records = doc["records"]
    wires = {str(h["id"]): d for h, d in records
             if h.get("type") == "WIRE" and h.get("id")}
    attrs = _attributes(records)
    segments: list[tuple[str, tuple[float, float, float, float]]] = []
    unsupported_lines = 0
    for h, d in records:
        if h.get("type") != "LINE" or "lineGroup" not in d:
            continue
        group = str(d["lineGroup"])
        start, end = _xy(d, "startX", "startY"), _xy(d, "endX", "endY")
        if group not in wires or start is None or end is None:
            unsupported_lines += 1
            continue
        segments.append((group, (*start, *end)))
    result: dict[str, Any] = {
        "analysis_status": "COMPLETED", "wire_group_count": len(wires),
        "wire_segment_count": len(segments), "skipped_wire_lines": unsupported_lines,
        "pins": [], "nets": [], "connected_pin_count": 0,
        "direct_contact_pin_count": 0, "unconnected_pin_candidates": 0,
        "ambiguous_pin_count": 0, "unresolved_component_count": 0,
        "unresolved_components": [], "findings": [],
    }
    if len(segments) > MAX_WIRE_LINES:
        result["analysis_status"] = "NOT_RUN_TOO_MANY_WIRE_LINES"
        result["findings"].append({"severity": "info", "code": "CONNECTIVITY_NOT_RUN",
            "message": "Wire segment count exceeds safe v0.2 geometric-analysis limit"})
        return result

    named = {wid: str(attrs.get(wid, {}).get("NET") or "").strip()
             for wid in wires}
    dsu = _Union(sorted(wires))
    # Two drawn WIREs touching at a *segment endpoint* form a join/T. Plain
    # interior X crossings are deliberately NOT joined: no junction evidence.
    by_group: dict[str, list[tuple[float, float, float, float]]] = defaultdict(list)
    for group, seg in segments:
        by_group[group].append(seg)
    groups = sorted(by_group)
    for i, left in enumerate(groups):
        for right in groups[i + 1:]:
            joined = False
            for seg_a in by_group[left]:
                for seg_b in by_group[right]:
                    if any(_touches(p, seg_b) for p in ((seg_a[0], seg_a[1]), (seg_a[2], seg_a[3]))) or any(
                        _touches(p, seg_a) for p in ((seg_b[0], seg_b[1]), (seg_b[2], seg_b[3]))
                    ):
                        dsu.union(left, right)
                        joined = True
                        break
                if joined:
                    break
    # Explicit identical WIRE net labels electrically join separate islands.
    first_named: dict[str, str] = {}
    for wid, netname in sorted(named.items()):
        if netname:
            if netname in first_named:
                dsu.union(wid, first_named[netname])
            first_named[netname] = wid

    groups_by_root: dict[str, list[str]] = defaultdict(list)
    for wid in sorted(wires):
        groups_by_root[dsu.find(wid)].append(wid)
    net_labels = {root: sorted({named[w] for w in members if named[w]})
                  for root, members in groups_by_root.items()}
    for root, names in net_labels.items():
        if len(names) > 1:
            result["findings"].append({"severity": "warning", "code": "CONFLICTING_WIRE_NET_NAMES",
                "message": f"Physically joined wire groups contain different NET names: {', '.join(names)}; inspect in EasyEDA"})

    components = {str(h["id"]): d for h, d in records
                  if h.get("type") == "COMPONENT" and h.get("id")}
    all_pins: list[dict[str, Any]] = []
    for cid, component in components.items():
        cat = attrs.get(cid, {})
        ref = cat.get("Designator")
        is_physical = isinstance(ref, str) and bool(ref.strip()) and not ref.strip().startswith("#")
        symbol_id = str(cat.get("Symbol") or "")
        symbol = symbols.get(symbol_id)
        if symbol is None:
            if is_physical:
                result["unresolved_components"].append(str(ref).strip())
            continue
        # Parts in a multi-part symbol must match the placed partId.
        symbol_entries = _symbol_pins(symbol)
        found = 0
        for pin_id, pin, pin_attrs in symbol_entries:
            if str(pin.get("partId", "")) != str(component.get("partId", "")):
                continue
            found += 1
            location = _pin_location(pin, component)
            if location is None:
                continue
            override = attrs.get(cid + pin_id, {})
            a = {**pin_attrs, **override}
            number = a.get("Pin Number", a.get("NUMBER", a.get("Number")))
            name = a.get("Pin Name", a.get("NAME", a.get("Name")))
            all_pins.append({"component_id": cid, "ref": str(ref).strip() if is_physical else "",
                             "pin_number": str(number) if number is not None else "",
                             "pin_name": str(name) if name is not None else "",
                             "position": list(location), "is_physical": is_physical})
        if is_physical and not found:
            result["unresolved_components"].append(str(ref).strip())
    result["unresolved_components"] = sorted(set(result["unresolved_components"]))
    result["unresolved_component_count"] = len(result["unresolved_components"])
    if len(all_pins) > MAX_COMPONENT_PINS:
        result["analysis_status"] = "NOT_RUN_TOO_MANY_PINS"
        result["findings"].append({"severity": "info", "code": "CONNECTIVITY_NOT_RUN",
            "message": "Pin count exceeds safe v0.2 geometric-analysis limit"})
        return result
    for p in all_pins:
        pt = tuple(p["position"])
        roots = sorted({dsu.find(group) for group, seg in segments if _touches(pt, seg)})
        p["wire_roots"] = roots
    # Pin-to-pin direct contact with no visible wire is evidence of contact,
    # not proof of a named net. Include non-designated ground/flag symbols.
    locations: dict[tuple[float, float], list[dict]] = defaultdict(list)
    for p in all_pins:
        locations[tuple(p["position"])].append(p)
    nets_with_pins: dict[str, list[str]] = defaultdict(list)
    for p in all_pins:
        if not p["is_physical"]:
            continue
        roots = p.pop("wire_roots")
        p.pop("component_id")
        p.pop("is_physical")
        pt = tuple(p["position"])
        direct = len(locations[pt]) > 1
        if len(roots) == 1:
            root = roots[0]
            p["connection_status"] = "ON_WIRE"
            p["net_name"] = net_labels[root][0] if len(net_labels[root]) == 1 else None
            p["net_id"] = f"wire:{root}"
            nets_with_pins[root].append(f"{p['ref']}.{p['pin_number']}")
            result["connected_pin_count"] += 1
        elif len(roots) > 1:
            p["connection_status"] = "AMBIGUOUS_INTERSECTION"
            p["net_name"] = None
            p["net_id"] = None
            p["candidate_net_names"] = sorted({n for r in roots for n in net_labels[r]})
            result["ambiguous_pin_count"] += 1
        elif direct:
            p["connection_status"] = "DIRECT_PIN_CONTACT"
            p["net_name"] = None
            p["net_id"] = None
            result["direct_contact_pin_count"] += 1
        else:
            p["connection_status"] = "UNCONNECTED_CANDIDATE"
            p["net_name"] = None
            p["net_id"] = None
            result["unconnected_pin_candidates"] += 1
        result["pins"].append(p)
    result["pins"].sort(key=lambda p: (p["ref"], p["pin_number"], p["position"]))
    result["nets"] = [{"net_id": f"wire:{root}",
                       "net_name": net_labels[root][0] if len(net_labels[root]) == 1 else None,
                       "conflicting_names": net_labels[root] if len(net_labels[root]) > 1 else [],
                       "wire_groups": len(members),
                       "connected_pins": sorted(nets_with_pins[root])}
                      for root, members in sorted(groups_by_root.items())]
    if result["unconnected_pin_candidates"]:
        result["findings"].append({"severity": "info", "code": "UNCONNECTED_PIN_CANDIDATES",
            "message": f"{result['unconnected_pin_candidates']} physical symbol pins do not touch stored wire geometry or another pin; may be intentionally NC or connected through unmodeled features"})
    if result["ambiguous_pin_count"]:
        result["findings"].append({"severity": "info", "code": "AMBIGUOUS_PIN_INTERSECTIONS",
            "message": f"{result['ambiguous_pin_count']} pins touch multiple unjoined wire groups; review crossing/junction semantics in EasyEDA"})
    if result["unresolved_component_count"]:
        result["findings"].append({"severity": "info", "code": "UNRESOLVED_SYMBOLS",
            "message": f"No matching embedded symbol/part for {result['unresolved_component_count']} components; pins are UNKNOWN, not counted disconnected"})
    result["findings"].append({"severity": "info", "code": "SCHEMATIC_GEOMETRY_ONLY",
        "message": "Pin-to-wire contact inferred from coordinates and stored net labels, not from an EasyEDA-exported electrical netlist. No ERC or electrical safety validation."})
    return result