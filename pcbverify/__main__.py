"""CLI entry point: python -m pcbverify ..."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from .easyeda import FormatError, analyze_path
from .kicad import native_check


def to_markdown(r: dict) -> str:
    lines = [f"# PCB Verification Report: {r['input']}", "",
             f"**Status:** {r['status']} (not manufacturing approval)", "",
             "## Inventory", ""]
    for entry in r["files"]:
        lines.append(f"### {entry['file']}")
        for page in entry["schematics"]:
            lines.append(f"- Schematic `{page['name']}`: {page['component_count']} designators, {page['wire_record_count']} wire records")
            c = page["connectivity"]
            lines.append(f"- Pin geometry: {c['connected_pin_count']} on wires, {c['direct_contact_pin_count']} direct contacts, {c['unconnected_pin_candidates']} unconnected candidates, {c['ambiguous_pin_count']} ambiguous; {c['unresolved_component_count']} unresolved components")
        for board in entry["boards"]:
            lines.append(f"- PCB `{board['name']}`: {board['component_count']} designators, {board['active_copper_layer_count']} active copper layers")
            lines.append(f"- PCB net names: {board['net_count']}; vias: {board['via_records']}; PAD_NET records: {board['pad_net_records']}")
        lines.append("")
    lines += ["## Schematic pin-to-net evidence", "",
              "These are inferred geometric contacts, not an authoritative electrical netlist.", ""]
    for entry in r["files"]:
        for page in entry["schematics"]:
            lines.append(f"### {entry['file']} / {page['name']}")
            lines.append("| Component | Pin | State | Wire NET label |")
            lines.append("| --- | --- | --- | --- |")
            for pin in page["connectivity"]["pins"]:
                lines.append(f"| {pin['ref']} | {pin['pin_number']} | {pin['connection_status']} | {pin['net_name'] or "(none)"} |")
            lines.append("")
    lines += ["## Findings", ""]
    for finding in r["findings"]:
        lines.append(f"- **{finding['severity'].upper()} / {finding['code']}**: {finding['message']}")
    lines += ["", "## Verification limits", "",
              "Pin-to-wire geometry and stored NET labels are not authoritative native schematic connectivity or ERC. This report does not validate circuit operation, datasheet ratings, native ERC/DRC, current density, thermal behavior, manufacturing CAM, or JLCPCB assembly."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only EasyEDA Pro project inventory and native KiCad CLI checks")
    subs = parser.add_subparsers(dest="command", required=True)
    p_analyze = subs.add_parser("analyze", help="Inspect an .epro2 file or ZIP of .epro2 files")
    p_analyze.add_argument("input", type=Path)
    p_analyze.add_argument("--json", type=Path, dest="json_output")
    p_analyze.add_argument("--markdown", type=Path, dest="markdown_output")
    p_native = subs.add_parser("kicad-check", help="Run real native KiCad ERC or DRC if kicad-cli is installed")
    p_native.add_argument("input", type=Path)
    p_native.add_argument("--json", type=Path, dest="json_output")
    args = parser.parse_args(argv)
    try:
        if args.command == "analyze":
            report = analyze_path(args.input)
        else:
            report = native_check(args.input)
    except (OSError, ValueError, FormatError) as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2
    out = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(out, encoding="utf-8")
    else:
        print(out)
    if args.command == "analyze" and args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(to_markdown(report), encoding="utf-8")
    if args.command == "kicad-check" and report["status"] != "CLI_COMPLETED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())