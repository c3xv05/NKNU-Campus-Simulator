import json,subprocess
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());base=json.loads(subprocess.check_output(['git','show','232c6c3:data/campus.json'],cwd=root));assert c['roads']==base['roads'];assert c['junctionFillets']==base['junctionFillets'];roof=Polygon(c['gaussStop']['ring']);assert roof.is_valid
load=lambda name:json.loads((root/('data/'+name+'-plan.js')).read_text().split('=',1)[1].rstrip(';\n'));motor=unary_union([Polygon(r[0],r[1:])for r in load('motor-pavement')['regions']]);walk=unary_union([Polygon(r[0],r[1:])for r in load('sidewalk')['regions']]);assert roof.intersection(motor).area<.001;assert roof.difference(walk).area<.001
for b in c['places']:
 if b.get('height'):assert roof.intersection(Polygon(b['ring'])).area<.001,b['name']
assert not(root/'s05-grade.js').exists();print('PASS: entire shelter is above actual tiled sidewalk, no asphalt/building overlap, original S05 road geometry and grade retained')
