"""Fit the user-specified facades to the confirmed walkway, retaining source outlines."""
import json,math,sys
from pathlib import Path
from shapely.geometry import LineString,Point,Polygon
from shapely.ops import nearest_points,unary_union
root=Path(__file__).resolve().parents[1];path=root/'data/campus.json';c=json.loads(path.read_text());width=3.6
settings={'swallow-restaurant':([6,7],6,[293423729,382869349]),'gauss':([0],0,[218881800]),'zhili':([1],1,[218881800])}
frontages=[];deltas={};entrance_roads={};keep_buildings='--keep-buildings' in sys.argv
for name,(edges,entry,roadids) in settings.items():
 p=root/'buildings'/name/'building.json';d=json.loads(p.read_text());a=d['geometry'];appearance=d['appearance'];meta=d.setdefault('frontageAlignment',{});source=meta.setdefault('sourceRing',a['ring']);meta.update(edges=edges,entryEdge=entry,roadIds=roadids,reference='依使用者要求向指定道路人行道貼齊；平移與門前鋪面為模型近似，非實測')
 winding=sum(u[0]*v[1]-v[0]*u[1] for u,v in zip(source,source[1:]+source[:1]));v,q=source[entry],source[(entry+1)%len(source)];dx,dz=q[0]-v[0],q[1]-v[1];l=math.hypot(dx,dz);nx,nz=dz/l*math.copysign(1,winding),-dx/l*math.copysign(1,winding)
 roads=[r for r in c['roads'] if r['osm'] in roadids];lines=[LineString(r['line']) for r in roads];roadline=unary_union(lines);half=roads[0]['width']/2
 def safe(t):
  for edge in edges:
   a0,b0=source[edge],source[(edge+1)%len(source)];line=LineString([[a0[0]+nx*t,a0[1]+nz*t],[b0[0]+nx*t,b0[1]+nz*t]])
   if line.distance(roadline)<half+width:return False
   mid=line.centroid;r=nearest_points(mid,roadline)[1]
   if (r.x-mid.x)*nx+(r.y-mid.y)*nz<=0:return False
  return True
 lo,hi=-20.,40.
 for _ in range(55):
  mid=(lo+hi)/2
  if safe(mid):lo=mid
  else:hi=mid
 delta=[nx*lo,nz*lo];deltas[a['osm']]=delta
 if not keep_buildings:a['ring']=[[round(x+delta[0],6),round(z+delta[1],6)] for x,z in source]
 appearance.update(frontMode='main-road',frontEdge=entry,frontRoadIds=roadids);appearance['frontHint']=[sum(a['ring'][k][j] for k in [entry,(entry+1)%len(source)])/2 for j in range(2)]
 # Door on the confirmed street side; keep the teaching-building floor settings.
 if name=='swallow-restaurant':appearance['entranceAtSidewalk']=True
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');entrance_roads[str(a['osm'])]=roadids
 for edge in edges:
  a0,b0=a['ring'][edge],a['ring'][(edge+1)%len(source)];samples=[]
  for i in range(17):
   x=a0[0]+(b0[0]-a0[0])*i/16;z=a0[1]+(b0[1]-a0[1])*i/16;point=Point(x,z);r,rl=min(zip(roads,lines),key=lambda pair:pair[1].distance(point));distance=rl.project(point);near=rl.interpolate(distance);rw=r['width'];profile=r.get('widthTransition');
   if profile:
    length=min(profile.get('length',35),rl.length*.4);ease=lambda v:(lambda t:t*t*(3-2*t))(max(0,min(1,v/length)));rw+=(profile.get('start',r['width'])-r['width'])*(1-ease(distance))+(profile.get('end',r['width'])-r['width'])*(1-ease(rl.length-distance))
   dx,dz=x-near.x,z-near.y;length=math.hypot(dx,dz);outer=[near.x+dx/length*(rw/2+width),near.y+dz/length*(rw/2+width)];samples.append(([x-nx*.05,z-nz*.05],outer))
  for i in range(1,len(samples)):
   ring=[samples[i-1][0],samples[i][0],samples[i][1],samples[i-1][1]];poly=Polygon(ring).buffer(0)
   parts=list(poly.geoms) if hasattr(poly,'geoms') else [poly]
   for part in parts:
    if part.area>.0001:frontages.append(dict(building=a['osm'],road=roadids[0],ring=[[round(x,6),round(z,6)] for x,z in list(part.exterior.coords)[:-1]]))
 print(name,'position preserved' if keep_buildings else 'translation', [] if keep_buildings else delta)
if not keep_buildings:
 link=c['levelLink'];src=link.setdefault('sourceLine',link['line']);link['line']=[[p[0]+deltas[id][0],p[1]+deltas[id][1]] for p,id in zip(src,[link['from'],link['to']])];a,b=link['line'];dx,dz=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dz);nx,nz=-dz/l*link['width']/2,dx/l*link['width']/2;link['ring']=[[a[0]+nx,a[1]+nz],[b[0]+nx,b[1]+nz],[b[0]-nx,b[1]-nz],[a[0]-nx,a[1]-nz]]

c['sidewalkFrontages']=frontages;c['entranceRoadIds']=entrance_roads;path.write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
