"""Bounded Gerber/Excellon *header* evidence, not CAM geometry verification.

This intentionally does not parse complete RS-274X, X2, Excellon coordinates,
embedded macros, regions, clearances, mask expansions, or physical drill sizes.
"""
from __future__ import annotations
import hashlib
import re
from typing import Any

MAX_CAM_INSPECTION_BYTES = 256 * 1024


def scan_cam_header(data: bytes, category: str) -> dict[str, Any]:
    """Extract header hints from up to 256 KiB of Gerber/Excellon source."""
    sample = data[:MAX_CAM_INSPECTION_BYTES]
    digest = hashlib.sha256(data).hexdigest()
    if b'\x00' in sample:
        return {'category': category, 'status': 'BINARY_OR_UNREADABLE',
                'sha256': digest, 'units': None, 'file_function': None,
                'coordinate_format': None, 'drill_tool_diameters': []}
    text = sample.decode('latin-1')
    is_drill = category == 'drill'
    if is_drill:
        m = re.search(r'(?im)^\s*(METRIC|INCH)\b', text)
        tool_diams = []
        for number in re.findall(r'(?im)^\s*T\d+C\s*(\d+(?:\.\d+)?)', text):
            try:
                d = float(number)
                if d > 0:
                    tool_diams.append(d)
            except ValueError:
                continue
        return {'category': category,
                'status': 'HEADER_FOUND' if 'M48' in text.upper() else 'HEADER_UNCONFIRMED',
                'sha256': digest, 'units': 'mm' if m and m.group(1).upper() == 'METRIC' else
                'inch' if m else None, 'file_function': None,
                'coordinate_format': None, 'drill_tool_diameters': sorted(set(tool_diams)),
                'notes': ['Tool diameters are header strings, not validated hole counts or geometry.']}
    unit = re.search(r'%MO(MM|IN)\*%', text, re.I)
    fmt = re.search(r'%FS([LT])A?X(\d)(\d)Y(\d)(\d)\*%', text, re.I)
    func = re.search(r'%TF\.FileFunction,([^*%]+)\*%', text, re.I)
    return {'category': category,
            'status': 'HEADER_FOUND' if (unit or fmt) else 'HEADER_UNCONFIRMED',
            'sha256': digest,
            'units': 'mm' if unit and unit.group(1).upper() == 'MM' else 'inch' if unit else None,
            'file_function': func.group(1).strip() if func else None,
            'coordinate_format': fmt.group(0) if fmt else None,
            'drill_tool_diameters': [],
            'notes': ['Header evidence only; no Gerber drawing commands, geometry or spacing checked.']}


def cam_cross_checks(metadata: dict[str, list[dict[str, Any]]]) -> list[dict[str, str]]:
    """Never infer 'board ready'; return only traceable review findings."""
    findings: list[dict[str, str]] = []
    copper = metadata.get('front_copper', []) + metadata.get('back_copper', [])
    if len(metadata.get('front_copper', [])) == 1 and len(metadata.get('back_copper', [])) == 1:
        a, b = metadata['front_copper'][0], metadata['back_copper'][0]
        if a.get('sha256') == b.get('sha256'):
            findings.append({'code': 'IDENTICAL_COPPER_EXPORTS', 'severity': 'review',
                             'message': 'Front and back copper files are byte-identical; inspect intended board layers.'})
    units = {item['units'] for items in metadata.values() for item in items if item.get('units')}
    if len(units) > 1:
        findings.append({'code': 'MIXED_CAM_UNITS', 'severity': 'review',
                         'message': 'Gerber/Excellon headers report differing units; verify coordinate interpretation.'})
    for cat, items in metadata.items():
        if cat not in {'front_copper', 'back_copper'}:
            continue
        for item in items:
            desc = (item.get('file_function') or '').lower()
            side = 'top' if cat == 'front_copper' else 'bot'
            opposite = 'bot' if side == 'top' else 'top'
            if desc.startswith('copper,') and opposite in desc:
                findings.append({'code': 'COPPER_X2_LAYER_MISMATCH', 'severity': 'review',
                                 'message': cat + ' contradicts Gerber X2 FileFunction: ' + desc})
    return findings