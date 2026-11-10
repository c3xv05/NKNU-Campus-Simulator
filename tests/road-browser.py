"""Road rendering smoke test; run with a local server on port 8000."""
from pathlib import Path
import os,shutil,json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 context=browser.new_context(viewport={'width':960,'height':720})
 if os.environ.get('THREE_MODULE_PATH'):
  context.route('https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js',lambda r:r.fulfill(path=os.environ['THREE_MODULE_PATH'],content_type='text/javascript'))
 html=(ROOT/'index.html').read_text().replace('let previous=performance.now();', '''window.__road={show:()=>{player.position.set(-22,walkHeight(-22,-70),-70);cam.position.copy(player.position).add(new THREE.Vector3(0,22,28));},inspect:()=>{
 const p=ground.geometry.attributes.position.array;let area=0;
 for(let i=0;i<p.length;i+=9)area+=Math.abs((p[i+3]-p[i])*(p[i+8]-p[i+2])-(p[i+5]-p[i+2])*(p[i+6]-p[i]))/2;
 return{remainingGround:area/((terrain.mesh.columns-1)*(terrain.mesh.rows-1)*terrain.mesh.step**2),meshes:roadRendering.group.children.map(m=>m.name),roadHeight:roadNetwork.surfaceHeight(player.position.x,player.position.z),playerHeight:player.position.y};}};let previous=performance.now();''')
 context.route('http://127.0.0.1:8000/',lambda r:r.fulfill(body=html,content_type='text/html'))
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/');page.wait_for_function('window.__road',timeout=60000)
 page.get_by_role('button',name='開始探索').click();page.evaluate('window.__road.show()');page.wait_for_timeout(300)
 result=page.evaluate('window.__road.inspect()')
 assert .9<result['remainingGround']<.99,result
 assert {'road-asphalt','road-concrete','road-yellow','road-white'}.issubset(result['meshes'])
 assert abs(result['playerHeight']-result['roadHeight']-.035)<1e-6
 page.screenshot(path='/tmp/nknu-road-desktop.png')
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path='/tmp/nknu-road-mobile.png')
 assert not errors,errors
 print(json.dumps({'result':'PASS','checks':['asphalt/concrete and white/yellow road meshes','ground cutout coverage','player follows pavement','desktop/mobile screenshots','no JavaScript errors'],'remainingGround':result['remainingGround']}))
 browser.close()
