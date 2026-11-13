import json
from pathlib import Path
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text())
def plan(name):
 p=json.loads((root/('data/'+name+'-plan.js')).read_text().split('=',1)[1].rstrip(';\n'));return unary_union([Polygon(r[0],r[1:])for r in p['regions']])
road=plan('motor-pavement');walk=plan('sidewalk');guard=Polygon(next(a for a in c['buildings']if a['osm']==-2401)['ring']);wall=LineString(c['perimeterWalls'][0]['line']).buffer(.14,join_style=2);shed=Polygon(c['carports'][0]['ring'])
assert guard.intersection(road).area<1e-6;assert guard.distance(road)<.02;assert guard.intersection(walk).area<1e-6
assert wall.intersection(road).area<1e-5;assert wall.intersection(walk).area<1e-5
assert wall.distance(shed)<.32
for b in c['buildings']+c['places']:
 if b.get('height'):assert wall.intersection(Polygon(b['ring'])).area<1e-5,b['osm']
assert shed.difference(road).area<.001
print('PASS: guardhouse within 2cm of road without overlap; west wall avoids all actual asphalt/sidewalk/buildings; extended shed fully paved')
