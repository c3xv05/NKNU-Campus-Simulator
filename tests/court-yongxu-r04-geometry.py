import json
from pathlib import Path
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text())
def plan(name):return json.loads((root/('data/'+name+'.js')).read_text().split('=',1)[1].split(';',1)[0])
road=unary_union([Polygon(r[0],r[1:])for r in plan('motor-pavement-plan')['regions']]);walk=unary_union([Polygon(r[0],r[1:])for r in plan('sidewalk-plan')['regions']]);south=Polygon(c['courtSouthSidewalk']['ring']);assert south.intersection(road).area<.01;assert south.boundary.intersection(road.boundary.buffer(.002)).length>55;assert south.difference(walk).area<.01
b=Polygon(next(p for p in c['places']if p['osm']==381735423)['ring']);lawn=Polygon(c['yongxuLandscape']['lawn']['ring']);apron=Polygon(next(p for p in c['pavedAreas']if p['id']=='yongxu-forecourt')['ring']);assert b.is_valid and apron.is_valid and lawn.is_valid;assert b.intersection(road).area<.001;assert apron.boundary.intersection(b.boundary.buffer(.00001)).length>25;assert 140<lawn.area<180;assert 3.5<apron.area/lawn.area<4.5
r04=plan('r04-vegetation')['regions'];parts=[unary_union([Polygon(p[0],p[1:])for p in r['regions']])for r in r04];assert sum(p.area for p in parts)-unary_union(parts).area<.001
for r,shape in zip(r04,parts):
 assert shape.intersection(road.union(walk)).area<.03
 if r['category']=='forest':
  assert shape.intersection(lawn).area<.001
  for a in c['places']+c['buildings']:
   if a.get('height'):assert shape.intersection(Polygon(a['ring'])).area<.001
print('PASS: >55m sidewalk/road shared edge, no paving overlap, L building and road share inner facade, sketch lawn/asphalt ratio, seven R04 non-overlapping parts excluding roads/buildings/lawn')
