"""Offline OSM import. Shapely 2.1; buildings remain independently editable."""
import json, math
from pathlib import Path
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
root=Path(__file__).resolve().parents[1]; base=root/'campuses/heping'
j=json.loads((base/'source/osm.json').read_text()); nodes={e['id']:e for e in j['elements'] if e['type']=='node'}
ways={e['id']:e for e in j['elements'] if e['type']=='way'}
origin=[120.3213,22.6255]
def xy(n):
 p=nodes[n];return [round((p['lon']-origin[0])*111320*math.cos(math.radians(origin[1])),3),round((origin[1]-p['lat'])*111320,3)]
def ring(w): return [xy(n) for n in w['nodes']][:-1]
boundary=Polygon(ring(ways[113740778])); school=Polygon(ring(ways[179137001])); area=boundary.difference(school)
def inside(w):return area.covers(Polygon(ring(w)).representative_point())
profiles=[]
for w in ways.values():
 t=w.get('tags',{})
 if not t.get('building') or w['nodes'][0]!=w['nodes'][-1] or not inside(w):continue
 path=base/'buildings'/str(w['id'])/'building.json';path.parent.mkdir(exist_ok=True)
 if not path.exists():
  levels=int(t.get('building:levels',3));d=dict(id=str(w['id']),osm=w['id'],name=t.get('name','未命名附屬建物'),ring=ring(w),height=levels*3.6,levels=levels,color='#d7c6b0',confidence='OSM輪廓與名稱；未標層數時暫用三層，層高3.6m及外觀為模型近似',source=f"https://www.openstreetmap.org/way/{w['id']}")
  path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 profiles.append(json.loads(path.read_text()))
obstacles=unary_union([Polygon(b['ring']) for b in profiles]);roads=[];paths=[];greens=[];courts=[]
for w in ways.values():
 t=w.get('tags',{});pts=[xy(n) for n in w['nodes']]
 if t.get('highway') in ['service','path','footway','steps'] and not t.get('tunnel') and LineString(pts).intersects(area):
  kind=t['highway'];width=5 if kind=='service' else 2.4
  shape=LineString(pts).buffer(width/2,quad_segs=6).intersection(area).difference(obstacles)
  (roads if kind=='service' else paths).append(shape)
 if w['nodes'][0]==w['nodes'][-1] and t.get('leisure') and inside(w):
  record=dict(osm=w['id'],name=t.get('name',t['leisure']),sport=t.get('sport'),ring=ring(w))
  (courts if t['leisure'] in ['pitch','swimming_pool'] else greens).append(record)
road=unary_union(roads);path=unary_union(paths).difference(road)
# All rendered/support surfaces share the initial flat height field y=0.
def triangles(g):
 return [[[round(x,3),round(y,3)] for x,y in list(t.exterior.coords)[:3]] for t in constrained_delaunay_triangles(g).geoms]
trackOuter=Polygon(ring(ways[179222454]));trackInner=Polygon(ring(ways[179222455]));track=trackOuter.difference(trackInner).intersection(area).difference(road.union(path).union(obstacles))
features=unary_union([obstacles,road,path,track,*[Polygon(c['ring']) for c in courts]])
ground=area.difference(features)
# Spawn at the west entrance, nearest safe service-road point to its OSM gate.
gate=xy(1895208616) if 1895208616 in nodes else [-130,0]
# Western main entrance road endpoints; choose closest road point to west boundary at central campus.
from shapely.ops import nearest_points
spawn=list(nearest_points(road,Point(-140,-20))[0].coords)[0]
places=[]
for b in profiles:
 p=Polygon(b['ring']);spot=nearest_points(road.union(path),p.representative_point())[0]
 if p.distance(spot)<1: spot=nearest_points(road.union(path).difference(p.buffer(1.2)),p.representative_point())[0]
 places.append(dict(id=b['id'],name=b['name'],position=[round(spot.x,3),round(spot.y,3)]))
data=dict(id='heping',name='和平校區',origin=origin,boundary=ring(ways[113740778]),campusTriangles=triangles(area),ground=triangles(ground),track=triangles(track),road=triangles(road),paths=triangles(path),buildings=profiles,courts=courts,greens=greens,spawn=list(spawn),places=places,sourceDate='2026-11-16',heightNote='初版採共同水平基準，尚未取得可核對的細部高程；非實測平坦度。',excludedSchool=179137001)
(base/'campus.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
print(f"Heping: {len(profiles)} buildings, {len(courts)} sports areas; road {road.area:.1f}m², path {path.area:.1f}m²; spawn {spawn}")
