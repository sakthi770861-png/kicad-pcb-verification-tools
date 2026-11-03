"""Generate permission-safe, fully fictional EasyEDA/ENET/CAM test inputs.

Usage: python3 examples/make_synthetic_regression.py /tmp/pcbverify-demo
"""
from __future__ import annotations
import io
import json
from pathlib import Path
from zipfile import ZipFile
import sys


def record(kind, data, **header):
    return json.dumps({'type': kind, **header}, sort_keys=True) + '||' + json.dumps(data) + '|\n'


def build(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    sch = record('DOCHEAD', {'docType': 'SCH_PAGE', 'uuid': 'test-sch'})
    sch += record('META', {'title': 'Synthetic schematic'}, id='meta-sch')
    sch += record('COMPONENT', {'x': 0, 'y': 0}, id='r1')
    sch += record('ATTR', {'parentId': 'r1', 'key': 'Designator', 'value': 'R1'}, id='attr-r1')
    pcb = record('DOCHEAD', {'docType': 'PCB', 'uuid': 'test-board'})
    pcb += record('META', {'title': 'Synthetic board'}, id='meta-pcb')
    pcb += record('COMPONENT', {'x': 0, 'y': 0}, id='r1')
    pcb += record('ATTR', {'parentId': 'r1', 'key': 'Designator', 'value': 'R1'}, id='attr-r1')
    pcb += record('LAYER', {'layerType': 'TOP', 'layerName': 'Top', 'use': True}, id='top')
    pcb += record('LAYER', {'layerType': 'BOTTOM', 'layerName': 'Bottom', 'use': True}, id='bottom')
    pcb += record('POLY', {'polyType': 'BOARD_OUTLINE'}, id='outline')
    with ZipFile(output / 'synthetic_easyeda.zip', 'w') as z:
        for name, contents in [('example-sch.epro2', sch), ('example-pcb.epro2', pcb)]:
            buffer = io.BytesIO()
            with ZipFile(buffer, 'w') as inner:
                inner.writestr('records.epru', contents)
            z.writestr(name, buffer.getvalue())
    netlist = {'version': '2.0.0', 'components': {'synthetic-r1': {
        'props': {'Designator': 'R1', 'Value': '10K'},
        'pinInfoMap': {'1': {'number': '1', 'name': 'IN', 'net': 'GND'},
                       '2': {'number': '2', 'name': 'OUT', 'net': 'PWR'}}}}}
    (output / 'synthetic.enet').write_text(json.dumps(netlist, indent=2) + '\n', encoding='utf-8')
    with ZipFile(output / 'synthetic-fab.zip', 'w') as z:
        for name in ('fixture-F_Cu.gbr', 'fixture-B_Cu.gbr', 'fixture-Edge_Cuts.gbr', 'fixture-PTH.drl'):
            z.writestr(name, 'SYNTHETIC PLACEHOLDER: THIS IS NOT A VALID CAM FILE\n')
    manifest = {'schema_version': 1, 'cases': [
        {'name': 'easyeda-inventory', 'kind': 'easyeda', 'input': 'synthetic_easyeda.zip',
         'expected': {'/summary/pcb_boards': 1, '/summary/schematic_pages': 1,
                      '/summary/schematic_references': 1, '/summary/pcb_references': 1,
                      '/status': 'STRUCTURAL_INSPECTION_ONLY'}},
        {'name': 'enet-two-pin', 'kind': 'enet', 'input': 'synthetic.enet',
         'expected': {'/component_count': 1, '/pin_count': 2, '/net_count': 2,
                      '/status': 'EXPORTED_NETLIST_SNAPSHOT'}},
        {'name': 'fabrication-manifest', 'kind': 'manufacturing', 'input': 'synthetic-fab.zip',
         'expected': {'/missing_required_categories': [], '/status': 'MANIFEST_REVIEW_ONLY'}}]}
    (output / 'regression-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return output / 'regression-manifest.json'


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 examples/make_synthetic_regression.py OUTPUT_DIR')
    print(build(Path(sys.argv[1])))