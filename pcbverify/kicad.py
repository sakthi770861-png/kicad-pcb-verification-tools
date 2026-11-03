"""Run official KiCad ERC/DRC and preserve failure states without certification.

Works with KiCad CLI when locally installed. Automated contract tests substitute
an executable and do not imply a real KiCad installation was used.
"""
from __future__ import annotations
import json
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

MAX_NATIVE_JSON = 12 * 1024 * 1024

class NativeReportError(ValueError):
    pass


def summarize_native_json(report: Any, kind: str) -> dict[str, Any]:
    if kind not in {'erc', 'drc'} or not isinstance(report, dict):
        raise NativeReportError('Invalid native KiCad report')
    records = []
    if kind == 'erc':
        if not isinstance(report.get('sheets'), list):
            raise NativeReportError('ERC JSON is missing the sheets array')
        for sheet in report['sheets']:
            if not isinstance(sheet, dict) or not isinstance(sheet.get('violations'), list):
                raise NativeReportError('Invalid ERC sheet violations')
            records.extend(('sheet:' + str(sheet.get('path', '')), i) for i in sheet['violations'])
    else:
        for section in ('violations', 'unconnected_items', 'schematic_parity'):
            if not isinstance(report.get(section), list):
                raise NativeReportError('DRC JSON is missing required violation array: ' + section)
            records.extend((section, i) for i in report[section])
    counts = Counter()
    issues = []
    for category, item in records:
        if not isinstance(item, dict):
            raise NativeReportError('Invalid native violation record')
        severity = item.get('severity', 'unknown')
        if not isinstance(severity, str):
            severity = 'unknown'
        severity = severity.lower()
        counts[severity] += 1
        issues.append({'category': category, 'severity': severity,
                       'type': item.get('type') if isinstance(item.get('type'), str) else '',
                       'description': item.get('description') if isinstance(item.get('description'), str) else ''})
    return {'kind': kind, 'issue_count': len(issues),
            'severity_counts': dict(sorted(counts.items())), 'issues': issues,
            'note': 'Native findings; exclusions and disabled rules require separate review.'}


def native_check(path: Path | str) -> dict[str, Any]:
    path = Path(path).resolve()
    if path.suffix not in {'.kicad_sch', '.kicad_pcb'}:
        raise ValueError('Expected .kicad_sch or .kicad_pcb')
    if not path.is_file():
        raise FileNotFoundError(path)
    kind = 'erc' if path.suffix == '.kicad_sch' else 'drc'
    exe = shutil.which('kicad-cli')
    if not exe:
        return {'input': path.name, 'status': 'NOT_RUN', 'validation_passed': False,
                'reason': 'kicad-cli is not installed or not on PATH', 'native_report_summary': None}
    subcommand = ['sch', 'erc'] if kind == 'erc' else ['pcb', 'drc']
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder) / 'native-report.json'
        args = [exe, *subcommand, '--format', 'json', '--severity-all',
                '--exit-code-violations', '--output', str(output), str(path)]
        try:
            completed = subprocess.run(args, capture_output=True, text=True, timeout=120, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {'input': path.name, 'status': 'NOT_RUN', 'validation_passed': False,
                    'reason': str(exc), 'native_report_summary': None}
        if output.exists() and output.stat().st_size > MAX_NATIVE_JSON:
            native_text = ''
            parse_error = 'Native JSON report exceeds 12 MiB limit'
        else:
            native_text = output.read_text(encoding='utf-8', errors='replace') if output.exists() else ''
            parse_error = None
    summary = None
    if native_text:
        try:
            summary = summarize_native_json(json.loads(native_text), kind)
        except (NativeReportError, json.JSONDecodeError) as exc:
            parse_error = str(exc)
    elif not parse_error:
        parse_error = 'No native JSON report was generated'
    if summary is None:
        status = 'REPORT_UNREADABLE'
    elif completed.returncode != 0:
        status = 'CLI_NONZERO'
    elif summary['issue_count']:
        # A zero exit status cannot silently override actual reported violations.
        status = 'CLI_REPORTED_ISSUES'
    else:
        status = 'CLI_COMPLETED'
    return {'input': path.name, 'status': status,
            'validation_passed': status == 'CLI_COMPLETED',
            'exit_code': completed.returncode,
            'command': 'kicad-cli ' + ' '.join(subcommand) + ' --format json',
            'native_report_summary': summary,
            'native_report_parse_error': parse_error,
            'report': native_text, 'stdout': completed.stdout[-2000:],
            'stderr': completed.stderr[-2000:],
            'note': 'KiCad CLI check only. Passing ERC/DRC never establishes manufacturing or functional safety.'}