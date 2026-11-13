"""Fit complete courts inside existing facilities, with a shared tennis datum."""
import json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());a=json.loads((root/'facilities/sports-courts/layout.json').read_text());u=a['axis'];v=[-u[1],u[0]]
def point(along,across):return [round(u[i]*along+v[i]*across,7)for i in range(2)]
def rectangle(center,length,width):
 x,z=center;return [[round(x+u[0]*d+v[0]*w,7),round(z+u[1]*d+v[1]*w,7)]for d,w in [(-length/2,-width/2),(length/2,-width/2),(length/2,width/2),(-length/2,width/2)]]
# Source bounds are in the Xiangyang-aligned frame; retain original footprints for history.
for kind in ['basketball','tennis']:
 config=a[kind];ids=config.get('osms',[config.get('osm')]);zones=[r for r in c['courts']if r['osm']in ids];lo,hi,left,right=config['bounds'];mid=(left+right)/2
 for zone in zones:
  zone.setdefault('sourceRing',zone['ring']);l,r=(left,right)if kind=='basketball'else((left,mid)if zone['osm']==ids[0]else(mid,right));zone['ring']=[point(x,z)for x,z in[(lo,l),(hi,l),(hi,r),(lo,r)]]
  zone['platformAnchor']=config.get('platformAnchor',a['tennisAnchor']);zone['roofMargin']=a['perimeter']['roofMargin']
for kind in ['basketball','tennis']:
 config=a[kind];ids=config.get('osms',[config.get('osm')]);zones=[r for r in c['courts']if r['osm']in ids];points=[p for r in zones for p in r['ring']];along=[sum(p[i]*u[i]for i in range(2))for p in points];across=[sum(p[i]*v[i]for i in range(2))for p in points];midU=(min(along)+max(along))/2;midV=(min(across)+max(across))/2;spacing=config['width']+config['gap']
 for z in zones:z['playingCourts']=[];z['layoutReference']='facilities/sports-courts/layout.json'
 for j in range(config['count']):
  offset=midV+(j-(config['count']-1)/2)*spacing;center=point(midU,offset);zone=min(zones,key=lambda r:abs(sum(sum(p[i]*v[i]for i in range(2))for p in r['ring'])/len(r['ring'])-offset))
  zone['playingCourts'].append({'id':kind+'-'+str(j+1),'sport':kind,'center':center,'axis':u,'length':config['length'],'width':config['width'],'ring':rectangle(center,config['length'],config['width'])})
 for z in zones:
  if kind=='tennis':z['platformAnchor']=a['tennisAnchor'];z['levelGroup']='tennis-four-courts'
c['sportsPerimeter']=a['perimeter'];c['sportsPerimeter']['axis']=u;c['sportsZones']=[{'id':kind,'ring':[point(x,z)for x,z in[(config['bounds'][0],config['bounds'][2]),(config['bounds'][1],config['bounds'][2]),(config['bounds'][1],config['bounds'][3]),(config['bounds'][0],config['bounds'][3])]],'bounds':config['bounds'],'courtIds':config.get('osms',[config.get('osm')])}for kind in ['basketball','tennis']for config in[a[kind]]]
# A source alias never enters the public names or map labels.
c['levelLink']['communicationAlias']=json.loads((root/'facilities/building-access/layout.json').read_text())['communicationAlias']
g=a['terracedGarden'];g={**g,'axis':u,'id':'sports-terraced-flowerbed','ring':[point(x,z)for x,z in [(g['along'][0],g['across'][0]),(g['along'][1],g['across'][0]),(g['along'][1],g['across'][1]),(g['along'][0],g['across'][1])]],'upperCourt':444902477,'lowerCourt':444902481};c['sportsGardens']=[g]
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('Built four full basketball and four tennis courts; one tennis datum and four garden tiers')
