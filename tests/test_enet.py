import json
import unittest
from pcbverify.enet import parse_enet, compare_geometry, NetlistFormatError


def fixture():
    return json.dumps({'version':'2.0.0','components': {
        'gge1': {'props': {'Designator':'U1'}, 'pinInfoMap': {
            '1': {'number':'1','name':'VCC','net':'VCC'},
            '2': {'number':'2','name':'NC','net':''}}},
        'gge2': {'props': {'Designator':'R1'}, 'pinInfoMap': {
            '1': {'number':'1','net':'VCC'},'2': {'number':'2','net':'GND'}}}}
    }).encode()

class TestExportedNetlist(unittest.TestCase):
    def test_inventory(self):
        r=parse_enet(fixture())
        self.assertEqual(r['component_count'],2)
        self.assertEqual(r['net_count'],2)
        self.assertEqual(r['pin_count'],4)
        self.assertEqual(r['unconnected_pin_count'],1)
        self.assertEqual(r['nets'][1]['pins'],['R1.1','U1.1'])
    def test_invalid(self):
        for data in (b'garbage',b'[]',b'{}',b'{"components": []}'):
            with self.subTest(data=data):
                with self.assertRaises(NetlistFormatError): parse_enet(data)
    def test_malformed_pin_not_guessed(self):
        data=json.loads(fixture()); data['components']['gge1']['pinInfoMap']['9']={'number':{},'net':17}
        r=parse_enet(json.dumps(data).encode()); self.assertEqual(len(r['warnings']),1)
    def test_comparison(self):
        nl=parse_enet(fixture())
        geo={'files':[{'schematics':[{'connectivity':{'pins':[
            {'ref':'U1','pin_number':'1','connection_status':'ON_WIRE','net_name':'WRONG'},
            {'ref':'U1','pin_number':'2','connection_status':'UNCONNECTED_CANDIDATE','net_name':None},
            {'ref':'R1','pin_number':'1','connection_status':'UNCONNECTED_CANDIDATE','net_name':None},
            {'ref':'R1','pin_number':'2','connection_status':'ON_WIRE','net_name':'GND'},
            {'ref':'U7','pin_number':'1','connection_status':'ON_WIRE','net_name':None},
        ]}}]}]}
        r=compare_geometry(nl,geo)
        self.assertEqual(r['finding_counts']['NAMED_NET_DISAGREEMENT'],1)
        self.assertEqual(r['finding_counts']['GEOMETRY_MISSED_CONNECTION'],1)
        self.assertEqual(r['finding_counts']['PIN_NOT_IN_NETLIST'],1)
    def test_duplicate_pin_ambiguous(self):
        doc=json.loads(fixture());doc['components']['gge3']={'props':{'Designator':'U1'},'pinInfoMap':{'x':{'number':'1','net':'GND'}}}
        r=parse_enet(json.dumps(doc).encode())
        self.assertIn('DUPLICATE_PIN',[w['code'] for w in r['warnings']])
        self.assertFalse(any(p['ref']=='U1' and p['pin']=='1' for p in r['pins']))

if __name__=='__main__':unittest.main()