import json
from pathlib import Path
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());plan=lambda name:json.loads((root/('data/'+name+'-plan.js')).read_text().split('=',1)[1].rstrip(';\n'));roads=unary_union([Polygon(r[0],r[1:])for r in plan('motor-pavement')['regions']]);walk=unary_union([Polygon(r[0],r[1:])for r in plan('sidewalk')['regions']]);wall=LineString(c['perimeterWalls'][1]['line']).buffer(.14,join_style=2);assert wall.intersection(roads).area<.0001;assert wall.intersection(walk).area<.0001;assert wall.distance(roads)>1.3
b=Polygon(next(p for p in c['places']if p['osm']==381735221)['ring']);arrival=LineString(next(r for r in c['roads']if r['osm']==399908546)['line']).buffer(2.25);
if c.get('wencuiArrival'): assert arrival.intersection(b).area<.001
else: assert next(r for r in c['roads']if r['osm']==399908546)['line']==json.loads((root/'facilities/wencui-arrival/layout.json').read_text())['restoredLine']
fore=Polygon(next(p for p in c['pavedAreas']if p['id']=='yongxu-forecourt')['ring']);y=next(p for p in c['places']if p['osm']==381735423);north=LineString([y['ring'][5],y['ring'][6]]);assert fore.boundary.intersection(north.buffer(.00001)).length>15
entrance=Polygon(c['courtParking']['entrance']['ring']);assert entrance.is_valid;assert entrance.intersection(walk).area<.01;assert len(c['courtParking']['entrance']['groundCuts'])>1
print('PASS: boundary wall clear of asphalt/walks, Wencui service road restored, Yongxu north wing shared frontage, garage trench removes sidewalk and has explicit ground cutouts')
