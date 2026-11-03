"""Validate official EasyEDA Pro exported .enet JSON snapshots.

Netlist snapshots reflect the state *at export time*.  They are not an ERC,
proof of current schematic synchronization, or electrical safety approval.
Format: https://github.com/easyeda/easyeda-netlist-format
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MAX_NETLIST_BYTES = 30 * 1024 * 1024
MAX_COMPONENTS = 30000
MAX_PINS = 250000


class NetlistFormatError(ValueError):
    pass


def read_enet(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if path.suffix.lower() != '.enet':
        raise NetlistFormatError('Expected an EasyEDA Pro .enet file')
    if path.stat().st_size > MAX_NETLIST_BYTES:
        raise NetlistFormatError('Netlist exceeds size limit')
    return parse_enet(path.read_bytes(), path.name)


def parse_enet(data: bytes, name: str = 'design.enet') -> dict[str, Any]:
    if len(data) > MAX_NETLIST_BYTES:
        raise NetlistFormatError('Netlist exceeds size limit')
    try:
        document = json.loads(data.decode('utf-8-sig'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NetlistFormatError('Netlist must contain valid UTF-8 JSON') from exc
    if not isinstance(document, dict) or not isinstance(document.get('components'), dict):
        raise NetlistFormatError('Expected an object with a components object')
    if len(document['components']) > MAX_COMPONENTS:
        raise NetlistFormatError('Too many components in netlist')
    found: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    references: set[str] = set()
    seen_pins: set[tuple[str, str]] = set()
    component_count = 0
    for uuid, component in document['components'].items():
        if not isinstance(component, dict) or not isinstance(component.get('props'), dict) or not isinstance(component.get('pinInfoMap'), dict):
            warnings.append({'code': 'UNSUPPORTED_COMPONENT', 'detail': str(uuid)})
            continue
        props = component['props']
        ref = props.get('Designator')
        if not isinstance(ref, str) or not ref.strip():
            warnings.append({'code': 'MISSING_DESIGNATOR', 'detail': str(uuid)})
            continue
        ref = ref.strip()
        component_count += 1
        references.add(ref)
        for key, item in component['pinInfoMap'].items():
            if not isinstance(item, dict):
                warnings.append({'code': 'UNSUPPORTED_PIN', 'detail': f'{ref}:{key}'})
                continue
            number = item.get('number', key)
            net = item.get('net', '')
            if not isinstance(number, (str, int)) or isinstance(number, bool) or not isinstance(net, str):
                warnings.append({'code': 'UNSUPPORTED_PIN', 'detail': f'{ref}:{key}'})
                continue
            number = str(number)
            if not number:
                warnings.append({'code': 'UNSUPPORTED_PIN', 'detail': f'{ref}:{key}'})
                continue
            if (ref, number) in seen_pins:
                warnings.append({'code': 'DUPLICATE_PIN', 'detail': f'{ref}.{number}'})
                # Do not arbitrarily choose which net is right.
                found = [p for p in found if (p['ref'], p['pin']) != (ref, number)]
                continue
            seen_pins.add((ref, number))
            found.append({'ref': ref, 'pin': number, 'net': net,
                          'pin_name': item.get('name') if isinstance(item.get('name'), str) else ''})
            if len(found) > MAX_PINS:
                raise NetlistFormatError('Too many netlist pins')
    found.sort(key=lambda p: (p['ref'], p['pin']))
    nets: dict[str, list[str]] = {}
    for pin in found:
        if pin['net']:
            nets.setdefault(pin['net'], []).append(f"{pin['ref']}.{pin['pin']}")
    return {
        'file': name, 'format': 'EasyEDA Pro .enet JSON',
        'format_version': document.get('version'),
        'status': 'EXPORTED_NETLIST_SNAPSHOT',
        'component_count': component_count, 'reference_count': len(references),
        'pin_count': len(found), 'unconnected_pin_count': sum(not p['net'] for p in found),
        'net_count': len(nets),
        'nets': [{'name': name, 'pins': sorted(connected)} for name, connected in sorted(nets.items())],
        'pins': found, 'warnings': warnings,
        'note': 'Exported EasyEDA snapshot only: not ERC/DRC and not proof of current project synchronization.'
    }


def compare_geometry(netlist: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    """Compare exact reference/pin identifiers; never equate unnamed wire IDs with net names."""
    lookup = {(p['ref'], p['pin']): p for p in netlist['pins']}
    findings: list[dict[str, str]] = []
    checked: set[tuple[str, str]] = set()
    for entry in report.get('files', []):
        for page in entry.get('schematics', []):
            for pin in page.get('connectivity', {}).get('pins', []):
                key = (str(pin['ref']), str(pin['pin_number']))
                target = lookup.get(key)
                if not target:
                    findings.append({'code': 'PIN_NOT_IN_NETLIST', 'pin': '.'.join(key),
                                     'detail': 'Geometry pin not found in exported netlist; check export scope and revision.'})
                    continue
                checked.add(key)
                net = target['net']
                status = pin.get('connection_status')
                name = pin.get('net_name')
                if status == 'UNCONNECTED_CANDIDATE' and net:
                    findings.append({'code': 'GEOMETRY_MISSED_CONNECTION', 'pin': '.'.join(key),
                                     'detail': f'Exported netlist connects to {net!r}; geometry found no wire.'})
                elif status == 'ON_WIRE' and not net:
                    findings.append({'code': 'SNAPSHOT_DISAGREEMENT', 'pin': '.'.join(key),
                                     'detail': 'Geometry touches a wire, but exported pin has an empty net.'})
                elif status == 'ON_WIRE' and name and net and name != net:
                    findings.append({'code': 'NAMED_NET_DISAGREEMENT', 'pin': '.'.join(key),
                                     'detail': f'Geometry label {name!r}; exported net {net!r}.'})
    for key in sorted(set(lookup) - checked):
        findings.append({'code': 'NETLIST_PIN_NOT_IN_GEOMETRY', 'pin': '.'.join(key),
                         'detail': 'Netlist pin not present in geometric evidence (may be intentionally omitted or missing symbol).'})
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding['code']] = counts.get(finding['code'], 0) + 1
    return {'status': 'COMPARISON_REQUIRES_SAME_REVISION',
            'checked_matching_pins': len(checked), 'finding_counts': dict(sorted(counts.items())),
            'findings': findings,
            'note': 'Differences are review candidates; archives and netlist may represent different revisions.'}