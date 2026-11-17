"""Derive the S05-parallel connector, lower landing and east staircase."""
import math
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union

def ring(s):
    a,b=s['line'];dx=b[0]-a[0];dz=b[1]-a[1];length=math.hypot(dx,dz);n=[-dz/length,dx/length]
    return [[round(p[i]+side*n[i]*s['width']/2,7)for i in range(2)]for p,side in [(a,1),(b,1),(b,-1),(a,-1)]]

def derive_biology(c,source):
    cfg=source['biology'];bio=c['bioConnection'];lookup={b['osm']:b for b in c['places']};a=lookup[bio['from']];b=lookup[bio['to']]
    p,q=[b['ring'][i]for i in cfg['northEndVertices']];width=math.dist(p,q);east=[(p[i]-q[i])/width for i in range(2)];north=[east[1],-east[0]];start=[(p[i]+q[i])/2 for i in range(2)]
    path=LineString([start,[start[i]+north[i]*100 for i in range(2)]])
    hit=path.intersection(Polygon(a['ring']));contact=list(hit.coords)[0];length=path.project(Point(contact));joint=[start[i]+north[i]*length/2 for i in range(2)]
    # Continue a little into the wing shells so all of the constant-width strip meets them.
    raw=Polygon([[v[i]+north[i]*d for i in range(2)]for v,d in [(p,-.2),(q,-.2),(q,length+3),(p,length+3)]])
    bio.update(line=[list(contact),start],width=width,ring=[[round(x,7),round(z,7)]for x,z in list(raw.exterior.coords)[:-1]])
    bio['corridor']={**{k:cfg[k]for k in ['floors','floorHeight','slab','clearance','lowerRetainingWalls']},'line':bio['line'],'width':width,'roof':False,'northEndVertices':cfg['northEndVertices'],'joint':joint,'axis':north,'east':east}
    # The stairs leave the connector's lower floor at its east face, centred on the span.
    edge=[joint[i]+east[i]*width/2 for i in range(2)];depth=cfg['stairs'].get('topLandingDepth',0);top=[edge[i]+east[i]*depth for i in range(2)];requested=cfg['stairs']['width'];road=next(r for r in c['roads']if r['osm']==cfg['stairs']['road']);roadshape=LineString(road['line']).buffer(road['width']/2)
    def road_distance(offset):
        begin=[top[i]+north[i]*offset for i in range(2)];ray=LineString([begin,[begin[i]+east[i]*100 for i in range(2)]]);hit=ray.intersection(roadshape)
        return ray.project(Point(list(hit.coords)[0]))
    buildings=unary_union([Polygon(v['ring']).buffer(cfg['stairs']['buildingClearance'])for v in c['places']+c['buildings']if v.get('height')])
    def stair_for(w):
        run=min(road_distance(v)for v in [-w/2,0,w/2])-.05
        stair={**bio['stairs'],'line':[top,[top[i]+east[i]*run for i in range(2)]],'width':w,'topWidth':w,'topLevel':'biology-lower','bottomProfile':'road','landingSidewalls':False}
        stair['ring']=ring(stair);return stair
    lo,hi=1,requested
    for _ in range(40):
        mid=(lo+hi)/2
        candidate=stair_for(mid);landing=Polygon(ring({'line':[edge,top],'width':mid})) if depth else Polygon()
        if Polygon(candidate['ring']).union(landing).intersection(buildings).area>1e-6:hi=mid
        else:lo=mid
    stair=stair_for(math.floor(lo*1000)/1000);stair['desc']='使用者更正：向陽路側樓梯接生科連接處下層，等寬矩形；寬度依兩翼空隙推導，階數／尺寸仍為模型近似。';bio['stairs']=stair
    if depth:bio['eastLanding']={'line':[edge,top],'width':stair['width'],'depth':depth,'ring':ring({'line':[edge,top],'width':stair['width']}),'targetFloor':1}
    # A ground-level apron fills the skew between a rectangular stair and S01's road edge.
    bottom=stair['line'][1];reach=max(road_distance(v)for v in [-stair['width']/2,0,stair['width']/2])-math.dist(top,bottom)+.5
    apron=Polygon([[bottom[i]+north[i]*side*stair['width']/2+east[i]*d for i in range(2)]for side,d in [(1,0),(-1,0),(-1,reach),(1,reach)]])
    return raw,apron
