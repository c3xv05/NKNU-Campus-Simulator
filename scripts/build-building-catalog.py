"""Build one small runtime catalog and synchronize the OSM spatial index."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
c=json.loads((root/'data/campus.json').read_text());profiles={};records={}
for path in sorted((root/'buildings').glob('*/building.json')):
 d=json.loads(path.read_text());a=d['geometry'];p=d['appearance'];assert a['osm']==p['osm'];assert p['id']==path.parent.name
 records[a['osm']]=a;profiles[str(a['osm'])]=p
for section in ['places','buildings']:
 c[section]=[records.get(a['osm'],a) for a in c[section]]
guard=records.get(397467187)
if guard and c.get('gatehouse'):
 xs=[p[0] for p in guard['ring']];zs=[p[1] for p in guard['ring']]
 c['gatehouse'].update(ring=guard['ring'],center=[(min(xs)+max(xs))/2,(min(zs)+max(zs))/2],width=max(xs)-min(xs),depth=max(zs)-min(zs),height=guard['height'])
if c.get('sideGate'):c['sideGate']['tanks']=profiles['397467191']['tanks']
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':')))
(root/'buildings/catalog.json').write_text(json.dumps(profiles,ensure_ascii=False,separators=(',',':')))
print(f'Built {len(profiles)} independent building definitions')
