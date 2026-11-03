"""Reproducible, opt-in regressions of *evidence*, never PCB certifications.

The manifest can be checked into a repository only if its input files and
expected values are safe to publish. By design, it cannot reference files
outside its own containing directory (including symlink escapes).
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any
from .easyeda import analyze_path
from .enet import read_enet
from .manufacturing import inspect_manufacturing_zip

MAX_MANIFEST_BYTES = 128 * 1024
MAX_CASES = 50
MAX_ASSERTIONS_PER_CASE = 60
ALLOWED_KINDS = {'easyeda', 'enet', 'manufacturing'}

class RegressionError(ValueError):
    """Malformed or unsafe regression configuration."""


def _resolve_within(base: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise RegressionError('Input must be a relative path inside the manifest directory')
    resolved = (base / relative).resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise RegressionError('Regression input escapes manifest directory') from exc
    if not resolved.is_file():
        raise RegressionError(f'Regression input is not a file: {relative}')
    return resolved


def _pointer_value(value: Any, pointer: str) -> Any:
    """Conservative RFC 6901 JSON Pointer lookup. Missing is an error."""
    if not pointer.startswith('/') or len(pointer) > 250:
        raise RegressionError('Assertion paths must be JSON pointers beginning with /')
    for part in pointer[1:].split('/'):
        # Reject invalid escapes, rather than accidentally resolving wrong keys.
        if re.search(r'~(?![01])', part):
            raise RegressionError('Malformed JSON pointer escape')
        part = part.replace('~1', '/').replace('~0', '~')
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, list) and part.isascii() and part.isdecimal() and (part == '0' or not part.startswith('0')) and int(part) < len(value):
            value = value[int(part)]
        else:
            raise KeyError(pointer)
    return value


def run_regression(manifest: str | Path) -> dict[str, Any]:
    manifest = Path(manifest)
    if not manifest.is_file() or manifest.stat().st_size > MAX_MANIFEST_BYTES:
        raise RegressionError('Manifest is missing or exceeds 128 KiB')
    base = manifest.resolve().parent
    try:
        definition = json.loads(manifest.read_text(encoding='utf-8'))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RegressionError('Manifest is not UTF-8 JSON') from exc
    if not isinstance(definition, dict) or definition.get('schema_version') != 1:
        raise RegressionError('Expected schema_version 1 manifest object')
    cases = definition.get('cases')
    if not isinstance(cases, list) or not 1 <= len(cases) <= MAX_CASES:
        raise RegressionError('Manifest requires between 1 and 50 cases')
    seen: set[str] = set()
    results = []
    for entry in cases:
        if not isinstance(entry, dict):
            raise RegressionError('Every case must be an object')
        name = entry.get('name')
        kind = entry.get('kind')
        expected = entry.get('expected')
        if not isinstance(name, str) or not name or name in seen or len(name) > 100:
            raise RegressionError('Case names must be unique, nonempty, and at most 100 characters')
        seen.add(name)
        if not isinstance(kind, str) or kind not in ALLOWED_KINDS:
            raise RegressionError(f'Unknown case kind for {name}: {kind}')
        if not isinstance(expected, dict) or not 1 <= len(expected) <= MAX_ASSERTIONS_PER_CASE:
            raise RegressionError('Each case requires 1 to 60 assertions')
        path = _resolve_within(base, entry.get('input'))
        if kind == 'easyeda' and path.suffix.lower() not in {'.epro2', '.zip'}:
            raise RegressionError('EasyEDA case needs .epro2 or .zip input')
        if kind == 'enet' and path.suffix.lower() != '.enet':
            raise RegressionError('Netlist case needs .enet input')
        if kind == 'manufacturing' and path.suffix.lower() != '.zip':
            raise RegressionError('Manufacturing case needs .zip input')
        # A broken source file is recorded as a failed case, rather than
        # silently skipping or being reported as a passed regression.
        failures = []
        try:
            if kind == 'easyeda':
                report = analyze_path(path)
            elif kind == 'enet':
                report = read_enet(path)
            else:
                report = inspect_manufacturing_zip(path, assembly=entry.get('assembly') is True)
            for pointer, wanted in expected.items():
                try:
                    actual = _pointer_value(report, pointer)
                except KeyError:
                    failures.append({'pointer': pointer, 'reason': 'MISSING_VALUE'})
                    continue
                if type(actual) is not type(wanted) or actual != wanted:
                    failures.append({'pointer': pointer, 'reason': 'VALUE_CHANGED', 'expected': wanted, 'actual': actual})
        except (OSError, ValueError) as exc:
            failures.append({'pointer': '', 'reason': 'INPUT_ERROR', 'detail': str(exc)[:300]})
        results.append({'name': name, 'kind': kind, 'input': entry['input'],
                        'status': 'PASS' if not failures else 'FAIL',
                        'assertions': len(expected), 'failures': failures})
    return {'status': 'PASS' if all(r['status'] == 'PASS' for r in results) else 'FAIL',
            'case_count': len(results), 'pass_count': sum(r['status'] == 'PASS' for r in results),
            'fail_count': sum(r['status'] != 'PASS' for r in results),
            'cases': results,
            'note': 'Regression PASS only means expected software evidence is unchanged; it never approves a circuit or manufacturing release.'}