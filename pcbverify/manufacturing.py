"""Conservative manifest checks for PCB manufacturing-export ZIP archives.

This module does NOT parse CAM geometry or validate manufacturability. It only
checks names and (optionally) tabular header/reference compatibility.
"""
from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path, PurePosixPath
import re
from typing import Any
from zipfile import BadZipFile, ZipFile
from .cam import scan_cam_header, cam_cross_checks, MAX_CAM_INSPECTION_BYTES

MAX_ENTRIES = 1000
MAX_ZIP_BYTES = 100 * 1024 * 1024
MAX_CSV_BYTES = 4 * 1024 * 1024


class ManufacturingArchiveError(ValueError):
    pass


def _classify(filename: str) -> str | None:
    """Heuristics for common KiCad/JLCPCB/RS-274X naming conventions."""
    name = PurePosixPath(filename).name.lower()
    # Check drill before Gerber: Excellon tools use .drl or .xln.
    if name.endswith(('.drl', '.xln', '.exc')) or re.search(r'(?:drill|pth|npth).*\.(?:txt)$', name):
        return 'drill'
    if name.endswith(('.gtl',)) or re.search(r'[-_.]f[_-]?cu\.(?:gbr|ger)$', name):
        return 'front_copper'
    if name.endswith(('.gbl',)) or re.search(r'[-_.]b[_-]?cu\.(?:gbr|ger)$', name):
        return 'back_copper'
    if name.endswith(('.gts',)) or re.search(r'[-_.]f[_-]?mask\.(?:gbr|ger)$', name):
        return 'front_mask'
    if name.endswith(('.gbs',)) or re.search(r'[-_.]b[_-]?mask\.(?:gbr|ger)$', name):
        return 'back_mask'
    if name.endswith(('.gto',)) or re.search(r'[-_.]f[_-]?(?:silks|silk|silkscreen)\.(?:gbr|ger)$', name):
        return 'front_silkscreen'
    if name.endswith(('.gbo',)) or re.search(r'[-_.]b[_-]?(?:silks|silk|silkscreen)\.(?:gbr|ger)$', name):
        return 'back_silkscreen'
    if name.endswith(('.gko', '.gm1')) or re.search(r'[-_.]edge[_-]?cuts\.(?:gbr|ger)$', name) or re.search(r'(?:outline|profile).*\.(?:gbr|ger)$', name):
        return 'outline'
    if name.endswith('.csv'):
        if any(n in name for n in ('bom', 'bill_of_material', 'bill-of-material')):
            return 'bom'
        if any(n in name for n in ('cpl', 'pos', 'placement', 'pick', 'centroid', 'pnp')):
            return 'placement'
    return None


def _csv_summary(data: bytes, kind: str) -> dict[str, Any]:
    try:
        decoded = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        return {'status': 'UNREADABLE_UTF8', 'row_count': None, 'fields': [], 'references': []}
    try:
        reader = csv.DictReader(StringIO(decoded))
        fields = reader.fieldnames or []
        if not fields:
            return {'status': 'EMPTY', 'row_count': 0, 'fields': [], 'references': []}
        # Standard JLCPCB BOM often groups designators like "R1,R2".
        names = {f.casefold().strip(): f for f in fields if f}
        ref_header = next((names[k] for k in ('designator', 'designators', 'reference', 'references', 'ref', 'refdes') if k in names), None)
        refs: set[str] = set()
        count = 0
        for row in reader:
            count += 1
            if count > 50000:
                return {'status': 'TOO_MANY_ROWS', 'row_count': count, 'fields': fields, 'references': []}
            if ref_header and row.get(ref_header):
                refs.update(p.strip() for p in re.split('[,;\\s]+', row[ref_header]) if p.strip())
        status = 'PARSED' if ref_header else 'MISSING_REFERENCE_COLUMN'
        return {'status': status, 'row_count': count, 'fields': fields, 'references': sorted(refs)}
    except (csv.Error, TypeError):
        return {'status': 'CSV_PARSE_ERROR', 'row_count': None, 'fields': [], 'references': []}


def inspect_manufacturing_zip(path: str | Path, assembly: bool = False) -> dict[str, Any]:
    path = Path(path)
    if path.suffix.lower() != '.zip' or not path.is_file():
        raise ManufacturingArchiveError('Expected existing manufacturing .zip archive')
    if path.stat().st_size > MAX_ZIP_BYTES:
        raise ManufacturingArchiveError('ZIP file exceeds archive limit')
    found: dict[str, list[str]] = {}
    csv_reports: dict[str, Any] = {}
    cam_metadata: dict[str, list[dict[str, Any]]] = {}
    try:
        with ZipFile(path) as z:
            entries = z.infolist()
            if len(entries) > MAX_ENTRIES:
                raise ManufacturingArchiveError('Too many ZIP entries')
            for info in entries:
                filename = info.filename
                if info.is_dir():
                    continue
                p = PurePosixPath(filename)
                if p.is_absolute() or '..' in p.parts or '\\' in filename:
                    raise ManufacturingArchiveError('Unsafe archive member path')
                kind = _classify(filename)
                if not kind:
                    continue
                found.setdefault(kind, []).append(filename)
                if kind in {'front_copper','back_copper','front_mask','back_mask',
                            'front_silkscreen','back_silkscreen','outline','drill'}:
                    # Bounded decompression; reject oversized or zip-bomb-style entries.
                    if info.file_size > MAX_CAM_INSPECTION_BYTES * 20 or (
                        info.compress_size and info.file_size / info.compress_size > 1000
                    ):
                        cam_metadata.setdefault(kind, []).append({'category':kind, 'status':'TOO_LARGE_OR_HIGH_RATIO',
                                                                   'file':filename, 'units':None})
                    else:
                        with z.open(info) as f:
                            contents = f.read(MAX_CAM_INSPECTION_BYTES * 20 + 1)
                        if len(contents) > MAX_CAM_INSPECTION_BYTES * 20:
                            cam_metadata.setdefault(kind, []).append({'category':kind, 'status':'TOO_LARGE',
                                                                       'file':filename, 'units':None})
                        else:
                            cam_metadata.setdefault(kind, []).append({'file':filename,
                                **scan_cam_header(contents,kind)})
                if kind in {'bom','placement'}:
                    if info.file_size > MAX_CSV_BYTES:
                        csv_reports[filename] = {'status': 'TOO_LARGE'}
                        continue
                    with z.open(info) as f:
                        data = f.read(MAX_CSV_BYTES + 1)
                    if len(data) > MAX_CSV_BYTES:
                        csv_reports[filename] = {'status': 'TOO_LARGE'}
                    else:
                        csv_reports[filename] = _csv_summary(data, kind)
    except BadZipFile as exc:
        raise ManufacturingArchiveError('Not a ZIP archive') from exc
    required = ['front_copper', 'back_copper', 'outline', 'drill']
    if assembly:
        required += ['bom','placement']
    missing = [key for key in required if not found.get(key)]
    info = []
    if not found.get('front_mask') or not found.get('back_mask'):
        info.append('Solder-mask Gerbers not found by filename heuristic; verify stackup and export choices.')
    for category, files in found.items():
        if category in ('front_copper','back_copper','outline') and len(files)>1:
            info.append(f'{category} has {len(files)} possible files; inspect for unrelated boards or duplicate exports.')
    bom = next((csv_reports[p] for p in found.get('bom',[]) if csv_reports[p]['status']=='PARSED'), None)
    pos = next((csv_reports[p] for p in found.get('placement',[]) if csv_reports[p]['status']=='PARSED'), None)
    ref_mismatch = {'bom_only': [], 'placement_only': []}
    if bom and pos:
        b, c = set(bom['references']), set(pos['references'])
        ref_mismatch = {'bom_only': sorted(b-c), 'placement_only': sorted(c-b)}
        if b != c:
            info.append('BOM/placement references differ; DNP, THT or manual assembly may explain differences.')
    header_findings = cam_cross_checks(cam_metadata)
    return {'input':path.name, 'status':'MANIFEST_REVIEW_ONLY', 'assembly_requested':bool(assembly),
            'detected_file_categories':{k:sorted(v) for k,v in sorted(found.items())},
            'missing_required_categories':missing,'csv_summary':csv_reports,
            'cam_header_metadata': cam_metadata, 'cam_header_findings': header_findings,
            'bom_placement_reference_differences':ref_mismatch,
            'notes':info + [
                'Filename detection and CAM header reading are heuristic. No Gerber geometry, Excellon coordinates, solderability, component purchasing, footprint orientation, electrical clearance, or panelization were validated.',
                'Treat all results as a preflight checklist, never a manufacturing release approval.'
            ]}