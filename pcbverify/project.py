"""Combine existing independent verification evidence without claiming approval."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from .easyeda import analyze_path
from .enet import read_enet, compare_geometry
from .manufacturing import inspect_manufacturing_zip
from .kicad import native_check


def project_audit(*, easyeda: str | Path | None = None,
                  netlist: str | Path | None = None,
                  fabrication: str | Path | None = None,
                  assembly: bool = False,
                  kicad_schematic: str | Path | None = None,
                  kicad_board: str | Path | None = None) -> dict[str, Any]:
    """Gather evidence; a PASS is *never* equivalent to board fabrication approval."""
    if not any((easyeda, netlist, fabrication, kicad_schematic, kicad_board)):
        raise ValueError('At least one input file is required for project-audit')
    evidence: dict[str, Any] = {}
    checks: list[dict[str, str]] = []
    geo = None
    if easyeda:
        geo = analyze_path(easyeda)
        evidence['easyeda'] = geo
        checks.append({'check': 'easyeda_geometry', 'status': geo['status']})
    if netlist:
        nl = read_enet(netlist)
        evidence['exported_netlist'] = nl
        checks.append({'check': 'exported_netlist', 'status': nl['status']})
        if geo:
            evidence['geometry_netlist_comparison'] = compare_geometry(nl, geo)
            checks.append({'check': 'geometry_netlist_comparison', 'status': 'REVIEW_ONLY'})
    if fabrication:
        fab = inspect_manufacturing_zip(fabrication, assembly=assembly)
        evidence['fabrication_manifest'] = fab
        checks.append({'check': 'fabrication_manifest', 'status': fab['status']})
    for name, path in (('kicad_schematic_erc', kicad_schematic), ('kicad_pcb_drc', kicad_board)):
        if path:
            check = native_check(path)
            evidence[name] = check
            checks.append({'check': name, 'status': check['status']})
    missing = [name for name in ('easyeda_geometry','exported_netlist','fabrication_manifest',
                                  'kicad_schematic_erc','kicad_pcb_drc')
               if name not in {c['check'] for c in checks}]
    statuses = [c for c in checks if c['status'] in {'CLI_NONZERO', 'NOT_RUN'}]
    return {
        'status': 'EVIDENCE_BUNDLE_NOT_MANUFACTURING_APPROVAL',
        'checks': checks, 'not_provided_checks': missing,
        'native_checks_unavailable_or_nonzero': statuses,
        'evidence': evidence,
        'note': 'No physical testing, circuit simulation, fab CAM validation, or engineering manufacturing certification is performed.'
    }


def project_markdown(report: dict[str, Any]) -> str:
    rows = ['# PCB Project Evidence Summary', '',
            '**Overall status: EVIDENCE ONLY — NOT MANUFACTURING APPROVAL**', '',
            '| Check | Reported status |', '| --- | --- |']
    rows += [f"| {x['check']} | {x['status']} |" for x in report['checks']]
    rows.extend(['', '## Not provided / not run', ''])
    rows += ['- '+s for s in report['not_provided_checks']] or ['- None of the declared checks omitted']
    rows += ['', '## Unavailable or nonzero native checks', '']
    rows += [f"- {c['check']}: {c['status']}" for c in report['native_checks_unavailable_or_nonzero']] or ['- None reported by selected checks']
    rows += ['', '## Limitations', '', report['note'],
             'Inspect accompanying JSON for the complete evidence, findings and original status text.', '']
    return '\n'.join(rows)