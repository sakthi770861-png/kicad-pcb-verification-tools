"""Explicit evidence gate for a software release candidate, not board approval.

A native KiCad check is run only when the user supplies the real design files.
The gate cannot prove manufacturing safety, authentic KiCad provenance or source
revisions; human inspection remains required even with complete evidence.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
from .easyeda import analyze_path
from .enet import read_enet, compare_geometry
from .manufacturing import inspect_manufacturing_zip
from .kicad import native_check


def release_gate(*, easyeda: Path | None = None, netlist: Path | None = None,
                 fabrication: Path | None = None, kicad_schematic: Path | None = None,
                 kicad_board: Path | None = None, assembly: bool = False) -> dict[str, Any]:
    """Check presence and conservative evidence on one design set."""
    results: list[dict[str, Any]] = []
    blockers: list[str] = []
    geometry = None
    if easyeda is None:
        results.append({'name':'easyeda_archive','status':'NOT_PROVIDED'})
        blockers.append('EasyEDA archive not provided (if EasyEDA scope is claimed).')
    else:
        geometry = analyze_path(easyeda)
        results.append({'name':'easyeda_archive','status':geometry['status']})
        if geometry['findings']:
            blockers.append('EasyEDA inventory has findings requiring manual review.')
    if netlist is None:
        results.append({'name':'exported_enet','status':'NOT_PROVIDED'})
        blockers.append('Authentic exported .enet netlist not provided.')
    else:
        net_report = read_enet(netlist)
        results.append({'name':'exported_enet','status':net_report['status'],
                        'component_count':net_report['component_count'],
                        'netlist_warnings':len(net_report['warnings'])})
        if net_report['warnings']:
            blockers.append('Exported netlist contains parse warnings.')
        if geometry is not None:
            compare = compare_geometry(net_report, geometry)
            results.append({'name':'netlist_geometry_comparison',
                            'status':'REVIEW_REQUIRED' if compare['findings'] else 'NO_RECORDED_DIFFERENCES',
                            'finding_count':len(compare['findings'])})
            if compare['findings']:
                blockers.append('Netlist and geometry differ; confirm matching revision and investigate.')
    if fabrication is None:
        results.append({'name':'manufacturing_archive','status':'NOT_PROVIDED'})
        blockers.append('Gerber/drill archive not supplied.')
    else:
        fab = inspect_manufacturing_zip(fabrication, assembly=assembly)
        results.append({'name':'manufacturing_archive','status':fab['status'],
                        'missing_categories':fab['missing_required_categories'],
                        'cam_header_findings':fab.get('cam_header_findings',[])})
        if fab['missing_required_categories'] or fab.get('cam_header_findings'):
            blockers.append('Fabrication export has missing required files or CAM header review findings.')
    for name, path in [('native_erc', kicad_schematic),('native_drc', kicad_board)]:
        if path is None:
            results.append({'name':name,'status':'NOT_PROVIDED'})
            blockers.append(name + ' not run against a real KiCad source file.')
        else:
            outcome = native_check(path)
            results.append({'name':name,'status':outcome['status'],
                            'exit_code':outcome.get('exit_code'),
                            'issue_count':(outcome.get('native_report_summary') or {}).get('issue_count')})
            if not outcome.get('validation_passed'):
                blockers.append(name + ' did not produce a clean parseable native KiCad report.')
    return {
        'status':'BLOCKED' if blockers else 'ENGINEERING_REVIEW_REQUIRED',
        'software_release_status':'PRERELEASE_VALIDATION_ONLY',
        'checks':results, 'blockers':blockers,
        'note':'This evidence gate cannot certify KiCad version, real hardware operation, CAM dimensions, solderability, thermal limits, JLCPCB assembly, or manufacturing fitness. An empty blocker list still requires engineering review.'
    }