"""Replace the identified old path with a south sidewalk joined to S09's west side."""
import json,math,subprocess
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());a=json.loads((root/'facilities/sports-courts/south-sidewalk.json').read_text());sports=json.loads((root/'facilities/sports-courts/layout.json').read_text());u=sports['axis'];v=[-u[1],u[0]];lo,hi,left,right=sports['basketball']['bounds'];center=hi+a['offsetFromCourt']+a['width']/2
point=lambda x,z:[round(x*u[i]+z*v[i],7)for i in range(2)]
js="""import fs from 'node:fs';import{createRoadNetwork}from'./roads.js';import{sidewalkSections}from'./site-physics.js';const c=JSON.parse(fs.readFileSync('data/campus.json')),n=createRoadNetwork(c.roads,()=>0,JSON.parse(fs.readFileSync('data/road-tags.json')),{apron:c.entranceApron,pavedAreas:c.pavedAreas,junctionFillets:c.junctionFillets});process.stdout.write(JSON.stringify(sidewalkSections(c,n).filter(s=>s.road===218881793).map(s=>s.points)));"""
walk=unary_union([Polygon(r)for r in json.loads(subprocess.check_output(['node','--input-type=module','-e',js],cwd=root))]);line=LineString([point(center,left),point(center,left-30)]);intersection=line.intersection(walk);points=[]
def collect(g):
 if hasattr(g,'geoms'):
  for q in g.geoms:collect(q)
 elif hasattr(g,'coords'):points.extend(list(g.coords))
collect(intersection);contact=min(points,key=lambda p:line.project(Point(p)));across=sum(contact[i]*v[i]for i in range(2))-.8
ring=[point(x,z)for x,z in[(center-a['width']/2,right),(center-a['width']/2,across),(center+a['width']/2,across),(center+a['width']/2,right)]]
layoutPath=root/'facilities/campus-plazas/layout.json';layout=json.loads(layoutPath.read_text());layout['pedestrianAreas']=[p for p in layout['pedestrianAreas']if p['id']!=a['id']]+[{'id':a['id'],'name':a['name'],'ring':ring,'width':a['width'],'connection':'S09','connectionRoad':a['connectionRoad'],'reference':a['reference']}];layoutPath.write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n')
c['roads']=[r for r in c['roads']if r['osm']!=a['removeFootpath']['osm']];c['footpathRemovals']=[r for r in c.get('footpathRemovals',[])if r['osm']!=a['removeFootpath']['osm']]+[a['removeFootpath']];c['courtSouthSidewalk']={**a,'ring':ring,'centerAlong':center,'contact':contact};next(r for r in c['roads']if r['osm']==218881795)['gradeProfile']=json.loads((root/'facilities/xiangyang-grade/profile.json').read_text());(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('Built 3.6m south sidewalk touching S09, removed only path',a['removeFootpath']['osm'])
