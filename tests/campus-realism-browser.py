from pathlib import Path
import os,shutil,json,urllib.request
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with urllib.request.urlopen('http://127.0.0.1:8000/data/campus.json',timeout=3) as response:assert response.status==200
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 context=browser.new_context(viewport={'width':1100,'height':800})
 if os.environ.get('THREE_MODULE_PATH'):context.route('https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js',lambda r:r.fulfill(path=os.environ['THREE_MODULE_PATH'],content_type='text/javascript'))
 hook='''window.__site={state:()=>({x:player.position.x,y:player.position.y,z:player.position.z,riding:motion.riding,speed:motion.speed}),pose:(x,z,y)=>{player.position.set(x,y??walkHeight(x,z),z);},move:(dx,dz)=>movePlayer(dx,dz,.3),lake:(x,z)=>!!lakeAt(x,z,campus),inspect:()=>({height:avatar.height,white:roadRendering.group.getObjectByName('road-white').material.color.getHexString(),yellow:roadRendering.group.getObjectByName('road-yellow').material.color.getHexString(),basic:roadRendering.group.getObjectByName('road-white').material.isMeshBasicMaterial,bridge:siteDetails.bridgeLevel,gauss:terrain.platformHeight(campus.places.find(p=>p.name==='高斯大樓')),canopies:siteDetails.blockers.filter(m=>m.name.startsWith('canopy-')).length,waters:siteDetails.waterMeshes.length,sidewalks:siteDetails.sidewalks.length}),aerial:(x,z,dy=55)=>{window.__aerial=true;cam.position.set(x,walkHeight(x,z)+dy,z+dy*.55);cam.lookAt(x,walkHeight(x,z),z);},restore:()=>window.__aerial=false};let previous=performance.now();'''
 html=(ROOT/'index.html').read_text().replace('let previous=performance.now();',hook).replace('cam.position.lerp(target,','if(!window.__aerial)cam.position.lerp(target,').replace('cam.lookAt(player.position.x,player.position.y+1.1,player.position.z);','if(!window.__aerial)cam.lookAt(player.position.x,player.position.y+1.1,player.position.z);')
 context.route('http://127.0.0.1:8000/',lambda r:r.fulfill(body=html,content_type='text/html'))
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' and ('Shader Error' in m.text or 'VALIDATE_STATUS' in m.text) else None)
 page.goto('http://127.0.0.1:8000/');page.wait_for_function('window.__site',timeout=120000);page.get_by_role('button',name='開始探索').click(timeout=90000)
 inspect=page.evaluate('window.__site.inspect()');assert inspect['height']==1.76 and inspect['white']=='ffffff' and inspect['yellow']=='ffcc00' and inspect['basic'];assert abs(inspect['bridge']-inspect['gauss']-3.6)<1e-7;assert inspect['canopies']==4 and inspect['waters']==4 and inspect['sidewalks']>200
 # The blue lake has real exclusion, not an ordinary walkable plane.
 page.evaluate('window.__site.pose(-77,-25.6)');page.evaluate('window.__site.move(12,0)');state=page.evaluate('window.__site.state()');assert not page.evaluate('s=>window.__site.lake(s.x,s.z)',state);assert state['x']< -70
 # Traverse the actual bridge at the linked upper level.
 level=inspect['bridge'];page.evaluate('y=>window.__site.pose(-110.5,-234,y)',level+.08);page.evaluate('window.__site.move(5.5,20)');state=page.evaluate('window.__site.state()');assert abs(state['y']-level-.08)<.05 and state['z']> -216,state
 page.locator('#mapOpen').click();page.locator('#amenityList button').filter(has_text='詠絮樓').click();assert '詠絮樓' in page.locator('#mapSelection').inner_text();page.locator('#amenityList button').filter(has_text='風雨排球場').click();assert '遮雨棚' in page.locator('#mapSelection').inner_text();page.screenshot(path='/tmp/nknu-realism-map.png');page.keyboard.press('Escape')
 page.evaluate('window.__site.aerial(35,-242,90)');page.screenshot(path='/tmp/nknu-covered-courts.png')
 page.evaluate('window.__site.aerial(-115,-224,78)');page.screenshot(path='/tmp/nknu-connected-buildings.png')
 page.evaluate('window.__site.aerial(-267,497,65)');page.screenshot(path='/tmp/nknu-flush-entrance.png')
 page.evaluate('window.__site.restore()');page.keyboard.press('1');page.set_viewport_size({'width':390,'height':844});page.screenshot(path='/tmp/nknu-human-scale.png')
 assert not errors,errors
 print(json.dumps({'result':'PASS','checks':['Taiwan yellow/white paint colours','human scale','five-plus-storey building level link','walk across the connected level','lake blocks walking','covered courts','named dorm and facilities on map','attached sidewalks and entrance screenshots','no JavaScript errors'],'details':inspect},ensure_ascii=False));browser.close()
