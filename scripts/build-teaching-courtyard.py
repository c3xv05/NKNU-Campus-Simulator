"""One shared floor plan for the two flat plaza levels and the stairwell opening."""
import json
from pathlib import Path
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());layout=json.loads((root/'facilities/teaching-courtyard/layout.json').read_text());court=c['courtyard'];lookup={b['osm']:b for b in c['places']};layout['ring']=[lookup[p['building']]['ring'][p['vertex']] if isinstance(p,dict) else p for p in layout['boundary']];buildings=unary_union([Polygon(a['ring']).buffer(.01,join_style=2) for a in c['places']+c['buildings'] if a.get('height')]);shape=unary_union([Polygon(layout['ring']),Polygon(c['levelLink']['ring'])]).difference(buildings)
def triangles(p):return [[[round(x,7),round(z,7)] for x,z in list(t.exterior.coords)[:-1]] for t in constrained_delaunay_triangles(p).geoms if t.area>1e-7]
def regions(p):return [[[[round(x,7),round(z,7)] for x,z in list(r.coords)[:-1]] for r in [a.exterior,*a.interiors]] for a in (list(p.geoms) if hasattr(p,'geoms') else [p]) if a.area>1e-7]
plan=layout['upperPlan'];huanyu=lookup[444867694]
wall=LineString([huanyu['ring'][i] for i in plan['huanyuEdges']]);narrow=wall.buffer(plan['huanyuWalkWidth'],cap_style=2,join_style=2).intersection(shape)
band=Polygon([lookup[p['building']]['ring'][p['vertex']] if isinstance(p,dict) else p for p in plan['zhiliBandBoundary']])
upper=unary_union([narrow,band.intersection(shape)])
# Stair sits entirely within the broad arm, linking the original lower floor.
stair=court['stairs'][0];stair['line']=layout['centralStair']['line'];stair['width']=layout['centralStair']['width'];a,b=stair['line'];dx=b[0]-a[0];dz=b[1]-a[1];length=(dx*dx+dz*dz)**.5;nx=-dz/length*stair['width']/2;nz=dx/length*stair['width']/2;stair['ring']=[[a[0]+nx,a[1]+nz],[b[0]+nx,b[1]+nz],[b[0]-nx,b[1]-nz],[a[0]-nx,a[1]-nz]]
# Keep a small landing around both staircase ends.
upper=upper.union(LineString(stair['line']).buffer(2.6,cap_style=2).intersection(shape))
for s in c['levelLink']['stairs']+court.get('stairs',[]):upper=upper.difference(Polygon(s['ring']))
ramp=LineString(court['ramp']).buffer(court['width']/2,cap_style=2);court['rampTargetFloor']=1;court['accessRampRing']=[[round(x,7),round(z,7)] for x,z in list(ramp.exterior.coords)[:-1]]
lower=shape.difference(Polygon(c['levelLink']['stairs'][0]['ring'])).difference(ramp)
if c.get('zhiliLoweredTiles'):
 mask=Polygon(c['zhiliLoweredTiles']['ring']);lower=lower.difference(mask);upper=upper.difference(mask)
court.update(name=layout['name'],ring=layout['ring'],floors=2,floorHeight=layout['floorHeight'],floorRegions={'lower':regions(lower),'upper':regions(upper)},floorTriangles={'lower':triangles(lower),'upper':triangles(upper)},footprints=triangles(shape),pillars=[p for p in layout['pillars'] if upper.contains(Point(p))],upperShape='L',huanyuWalkWidth=plan['huanyuWalkWidth'],desc=layout['reference']);(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('Built two-level tiled courtyard',round(shape.area,1),'m² and central stair opening')
