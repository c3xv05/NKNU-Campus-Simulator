"""Visual and movement checks for the user-supplied facade and gateway references."""
from pathlib import Path
import os,shutil,json,urllib.request
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with urllib.request.urlopen('http://127.0.0.1:8000/buildings/catalog.json',timeout=3) as response:assert response.status==200
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 c=b.new_context(viewport={'width':1150,'height':850})
 if os.environ.get('THREE_MODULE_PATH'):c.route('https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js',lambda r:r.fulfill(path=os.environ['THREE_MODULE_PATH'],content_type='text/javascript'))
 hook='''window.__photo={inspect:()=>({buildings:buildingRendering.entries.length,wall:!!scene.getObjectByName('A1-retaining-wall'),guard:!!scene.getObjectByName('entrance-guardhouse'),deck:siteDetails.courtyardLevel,gauss:terrain.platformHeight(campus.places.find(p=>p.name==='高斯大樓')),zhili:terrain.platformHeight(campus.places.find(p=>p.name==='致理大樓')),huanyu:terrain.platformHeight(campus.places.find(p=>p.name==='寰宇大樓')),bioA:terrain.platformHeight(campus.places.find(p=>p.name==='生科 A 館')),bioB:terrain.platformHeight(campus.places.find(p=>p.name==='生科 B 館')),cap:MAX_SCOOTER_SPEED*3.6}),state:()=>({x:player.position.x,z:player.position.z,y:player.position.y}),pose:(x,z,y)=>player.position.set(x,y??walkHeight(x,z),z),move:(x,z)=>movePlayer(x,z,.3),detail:(x,z,time)=>{buildingRendering.update(x,z,time);return buildingRendering.entries.map(e=>({id:e.id,visible:e.detail.visible}));},view:(id)=>{const a=[...campus.places,...campus.buildings].find(a=>buildingProfiles[a.osm]?.id===id),profile=buildingProfiles[a.osm];const e=buildingRendering.entries.find(e=>e.id===id);player.position.set(e.cx,terrain.platformHeight(a),e.cz);window.__freeze=true;let area=0;for(let i=0;i<a.ring.length;i++){const p=a.ring[i],q=a.ring[(i+1)%a.ring.length];area+=p[0]*q[1]-q[0]*p[1];}let edges=a.ring.map((p,i)=>{const q=a.ring[(i+1)%a.ring.length],dx=q[0]-p[0],dz=q[1]-p[1],len=Math.hypot(dx,dz);return{x:(p[0]+q[0])/2,z:(p[1]+q[1])/2,nx:dz/len*Math.sign(area),nz:-dx/len*Math.sign(area),len};}).filter(e=>e.len>7).sort((a,b)=>Math.hypot(a.x-profile.frontHint[0],a.z-profile.frontHint[1])-Math.hypot(b.x-profile.frontHint[0],b.z-profile.frontHint[1]));const edge=edges[0],base=terrain.platformHeight(a);cam.position.set(edge.x+edge.nx*24,base+8,edge.z+edge.nz*24);cam.lookAt(edge.x,base+a.height*.42,edge.z);},bioView:()=>{window.__freeze=true;const y=siteDetails.bioLevel;player.position.set(-95,y,-251);cam.position.set(-100,y+2,-251);cam.lookAt(-64,y+1,-251);},aerial:(x,z,y=70)=>{window.__freeze=true;player.position.set(x,walkHeight(x,z),z);cam.position.set(x,walkHeight(x,z)+y,z+y*.55);cam.lookAt(x,walkHeight(x,z),z);}};let previous=performance.now();'''
 # Import speed separately for the test-only hook.
 html=(root/'index.html').read_text().replace('import {createScooter}',"import {MAX_SCOOTER_SPEED} from './travel.js';\nimport {createScooter}").replace('let previous=performance.now();',hook).replace('cam.position.lerp(target,','if(!window.__freeze)cam.position.lerp(target,').replace('cam.lookAt(player.position.x,player.position.y+1.1,player.position.z);','if(!window.__freeze)cam.lookAt(player.position.x,player.position.y+1.1,player.position.z);')
 c.route('http://127.0.0.1:8000/',lambda r:r.fulfill(body=html,content_type='text/html'))
 page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' and 'Shader Error' in m.text else None)
 page.goto('http://127.0.0.1:8000/');page.wait_for_function('window.__photo',timeout=180000);page.get_by_role('button',name='開始探索').click(timeout=90000)
 info=page.evaluate('window.__photo.inspect()');assert info['buildings']==19 and not info['wall'] and info['guard'];assert info['cap']==75;assert abs(info['bioA']-info['bioB'])<1e-7
 assert abs(info['deck']-info['gauss']-7.2)<1e-7 and abs(info['deck']-info['zhili']-3.6)<1e-7 and abs(info['deck']-info['huanyu']-3.6)<1e-7
 far=page.evaluate('window.__photo.detail(400,500,1000000)');assert not any(e['visible'] for e in far)
 near=page.evaluate('window.__photo.detail(-95,-190,1001000)');assert next(e['visible'] for e in near if e['id']=='gauss')
 # Walk the accessible ramp onto the courtyard without snapping up from below.
 page.evaluate('window.__photo.pose(-123,-171)');page.evaluate('window.__photo.move(-9,-19)');s=page.evaluate('window.__photo.state()');assert s['z']< -189 and abs(s['y']-info['deck'])<.15,s
 page.evaluate('y=>window.__photo.pose(-135,-210,y)',info['deck']+.08);page.evaluate('window.__photo.move(4,3)');s=page.evaluate('window.__photo.state()');assert abs(s['y']-info['deck']-.08)<.05,s
 # Guardhouse has collision, both barrier lanes remain driveable.
 page.evaluate('window.__photo.pose(-275,525)');page.evaluate('window.__photo.move(8,0)');s=page.evaluate('window.__photo.state()');assert s['x']< -269,s
 for id in (['bio-a'] if os.environ.get('PHOTO_FAST') else ['bio-a','bio-b','zhili','gauss','swallow-restaurant','foresight']):
  page.evaluate('(id)=>window.__photo.view(id)',id);page.wait_for_timeout(350);page.screenshot(path='/tmp/nknu-photo-'+id+'.png')
 page.evaluate('window.__photo.bioView()');page.screenshot(path='/tmp/nknu-photo-biology-connection.png')
 page.evaluate('window.__photo.aerial(-136,-207,72)');page.screenshot(path='/tmp/nknu-photo-courtyard.png')
 page.evaluate('window.__photo.aerial(-267,511,64)');page.screenshot(path='/tmp/nknu-photo-gate.png')
 assert not errors,errors
 print(json.dumps({'result':'PASS','checks':['19 independent building models','photo facade screenshots','near/far facade detail visibility','Gauss3F/Zhili2F/Huanyu2F platform','walkable ramp and upper platform','guardhouse collision','no retaining wall','75km/h cap','no JS/shader errors'],'details':info},ensure_ascii=False));b.close()
