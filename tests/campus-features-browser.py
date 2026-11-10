from pathlib import Path
import os,shutil,json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 c=b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=1)
 if os.environ.get('THREE_MODULE_PATH'):c.route('https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js',lambda r:r.fulfill(path=os.environ['THREE_MODULE_PATH'],content_type='text/javascript'))
 html=(ROOT/'index.html').read_text().replace('let previous=performance.now();', '''window.__game={state:()=>({x:player.position.x,y:player.position.y,z:player.position.z,yaw,heading:motion.heading,riding:motion.riding,speed:motion.speed,visible:scooter.visible,visited:visited.size}),destinations,layout:()=>({trees:landscapeLayout.trees.length,flowers:landscapeLayout.flowers.length,weeds:landscapeLayout.weeds.length}),overlook:()=>{window.__overview=true;cam.position.set(-267,walkHeight(-267,500)+65,550);cam.lookAt(-267,walkHeight(-267,500),495);renderer.render(scene,cam);}};let previous=performance.now();''').replace('cam.position.lerp(target,','if(!window.__overview)cam.position.lerp(target,').replace('cam.lookAt(player.position.x,player.position.y+1.1,player.position.z);','if(!window.__overview)cam.lookAt(player.position.x,player.position.y+1.1,player.position.z);')
 c.route('http://127.0.0.1:8000/',lambda r:r.fulfill(body=html,content_type='text/html'))
 page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' and ('Shader Error' in m.text or 'VALIDATE_STATUS' in m.text) else None)
 page.goto('http://127.0.0.1:8000/');page.wait_for_function('window.__game',timeout=90000)
 page.get_by_role('button',name='開始探索').click()
 assert page.locator('#joystick').is_visible();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 state=lambda:page.evaluate('window.__game.state()')
 def travel(id):
  page.locator('#travelMenu summary').click();page.locator('[data-travel="'+id+'"]').click()
  target=page.evaluate('id=>window.__game.destinations.find(d=>d.id===id)',id);actual=state()
  assert abs(actual['x']-target['x'])<.01 and abs(actual['z']-target['z'])<.01
 travel('canteen');page.wait_for_function("document.querySelector('#info').textContent.includes('歸燕食巢')")
 page.locator('#interact').click();page.wait_for_function('window.__game.state().visited===1')
 travel('zhili');page.wait_for_function("document.querySelector('#info').textContent.includes('致理大樓')")
 assert state()['visited']==1
 page.keyboard.press('1');assert abs(state()['z']-page.evaluate("window.__game.destinations.find(d=>d.id==='gate').z"))<.01
 page.locator('#rideToggle').click();assert state()['riding'] and state()['visible']
 before=state();page.keyboard.down('w');page.wait_for_function('window.__game.state().speed>1')
 page.keyboard.down('d');page.wait_for_function('window.__game.state().heading<-.02');page.keyboard.up('d')
 # Camera view remains independent from the scooter heading while accelerating.
 session=c.new_cdp_session(page)
 session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'id':1,'x':280,'y':400}]})
 session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'id':1,'x':315,'y':420}]})
 session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
 assert state()['yaw']<before['yaw'];page.keyboard.up('w')
 page.locator('#mapOpen').click();assert state()['speed']==0
 stopped=state();page.wait_for_timeout(200);assert state()==stopped
 page.keyboard.press('Escape');page.keyboard.press('1')
 box=page.locator('#joystick').bounding_box();cx=box['x']+box['width']/2;cy=box['y']+box['height']/2
 session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'id':3,'x':cx,'y':cy-40}]})
 page.wait_for_function('window.__game.state().speed>1')
 session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'id':3,'x':cx,'y':cy-40},{'id':4,'x':280,'y':400}]})
 oldYaw=state()['yaw'];session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'id':3,'x':cx+15,'y':cy-40},{'id':4,'x':310,'y':410}]})
 assert state()['yaw']<oldYaw
 session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
 travel('canteen');assert state()['riding'] and state()['speed']==0
 page.screenshot(path='/tmp/nknu-scooter-mobile.png')
 page.locator('#rideToggle').click();assert not state()['visible'] and not state()['riding']
 page.screenshot(path='/tmp/nknu-forest-mobile.png')
 page.keyboard.press('1');page.screenshot(path='/tmp/nknu-gate-mobile.png')
 page.set_viewport_size({'width':1100,'height':800});page.evaluate('window.__game.overlook()');page.screenshot(path='/tmp/nknu-entrance-overview.png')
 assert not errors,errors
 print(json.dumps({'result':'PASS','checks':['three safe teleports','nearby landmark interaction','progress preserved','scooter toggle acceleration steering','independent camera while riding','map brakes and pauses','riding state preserved through teleport','forest and flowerbed screenshots','no JavaScript errors'],'landscape':page.evaluate('window.__game.layout()')},ensure_ascii=False))
 b.close()
