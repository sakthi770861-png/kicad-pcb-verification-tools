"""Invoke the official KiCad CLI for ERC/DRC; summarize native JSON safely.

Never synthesize a passing result when the executable or report is unavailable.
"""
from __future__ import annotations
import json
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


class NativeReportError(ValueError):
    pass


def summarize_native_json(report: Any, kind: str) -> dict[str, Any]:
    """Count ERC per-sheet or PCB DRC violations across *all* known categories."""
    if kind not in {'erc','drc'} or not isinstance(report,dict):
        raise NativeReportError('Invalid native KiCad report')
    records=[]
    if kind=='erc':
        if not isinstance(report.get('sheets'),list):
            raise NativeReportError('ERC JSON is missing the sheets array')
        for sheet in report['sheets']:
            if not isinstance(sheet,dict) or not isinstance(sheet.get('violations'),list):
                raise NativeReportError('Invalid ERC sheet violations')
            for item in sheet['violations']:
                records.append(('sheet:'+str(sheet.get('path','')),item))
    else:
        for section in ('violations','unconnected_items','schematic_parity'):
            if not isinstance(report.get(section),list):
                raise NativeReportError('DRC JSON is missing required violation array: '+section)
            records.extend((section,item) for item in report[section])
    counts=Counter()
    issues=[]
    for category,item in records:
        if not isinstance(item,dict):
            raise NativeReportError('Invalid native violation record')
        severity=item.get('severity','unknown')
        if not isinstance(severity,str):
            severity='unknown'
        severity=severity.lower()
        counts[severity]+=1
        issues.append({'category':category,'severity':severity,
                       'type':item.get('type') if isinstance(item.get('type'),str) else '',
                       'description':item.get('description') if isinstance(item.get('description'),str) else ''})
    return {'kind':kind,'issue_count':len(issues),'severity_counts':dict(sorted(counts.items())),
            'issues':issues,
            'note':'Native reported issues; exclusions and hidden/disabled rules require separate review.'}


def native_check(path: Path | str) -> dict[str, Any]:
    path=Path(path).resolve()
    if path.suffix not in {'.kicad_sch','.kicad_pcb'}:
        raise ValueError('Expected .kicad_sch or .kicad_pcb')
    if not path.is_file():
        raise FileNotFoundError(path)
    exe=shutil.which('kicad-cli')
    if not exe:
        return {'input':path.name,'status':'NOT_RUN','reason':'kicad-cli is not installed or not on PATH'}
    kind='erc' if path.suffix=='.kicad_sch' else 'drc'
    subcommand=['sch','erc'] if kind=='erc' else ['pcb','drc']
    with tempfile.TemporaryDirectory() as folder:
        output=Path(folder)/'native-report.json'
        args=[exe,*subcommand,'--format','json','--severity-all',
              '--exit-code-violations','--output',str(output),str(path)]
        try:
            completed=subprocess.run(args,capture_output=True,text=True,timeout=120,check=False)
        except (OSError,subprocess.TimeoutExpired) as exc:
            return {'input':path.name,'status':'NOT_RUN','reason':str(exc)}
        native_text=output.read_text(encoding='utf-8',errors='replace') if output.exists() else ''
    summary=None
    parsing_problem=None
    if native_text:
        try:
            summary=summarize_native_json(json.loads(native_text),kind)
        except (NativeReportError,json.JSONDecodeError) as exc:
            parsing_problem=str(exc)
    else:
        parsing_problem='No native JSON report was generated'
    status=('CLI_NONZERO' if completed.returncode else
            'CLI_COMPLETED' if summary is not None else 'REPORT_UNREADABLE')
    return {'input':path.name,'status':status,'exit_code':completed.returncode,
            'command':'kicad-cli '+' '.join(subcommand)+' --format json',
            'native_report_summary':summary,'native_report_parse_error':parsing_problem,
            'report':native_text,'stdout':completed.stdout[-2000:],'stderr':completed.stderr[-2000:],
            'note':'Review native KiCad findings and exclusions. Passing ERC/DRC never establishes manufacturing or functional safety.'}