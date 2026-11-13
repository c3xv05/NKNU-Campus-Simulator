from pathlib import Path
import json,shutil,os
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];base='http://127.0.0.1:8000/'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 for mobile in [False,True]:
  c=b.new_context(viewport={'width':390 if mobile else 1100,'height':844},is_mobile=mobile,has_touch=mobile)
  c.route('https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js',lambda r:r.fulfill(path=os.environ.get('THREE_MODULE_PATH','/tmp/three.module.js'),content_type='text/javascript'))
  c.route('https://api.github.com/**',lambda r:r.fulfill(json=[]))
  hook="""window.__view={state:()=>({enabled:aerial.enabled,height:aerial.height,center:aerial.center.toArray(),player:player.position.toArray(),camera:cam.position.toArray(),up:cam.getWorldDirection(new THREE.Vector3()).y,pitch,ride:motion.riding}),enable:()=>setAerial(true),ride:()=>toggleRide(),teleport:()=>teleport('zhili')};let previous=performance.now();"""
  html=(root/'index.html').read_text().replace('let previous=performance.now();',hook)
  c.route(base,lambda r:r.fulfill(body=html,content_type='text/html'))
  page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base);page.wait_for_function('window.__view',timeout=180000)
  page.get_by_role('button',name='開始探索',exact=True).click();assert page.locator('#aerialControls').is_hidden();page.evaluate('window.__view.enable()');assert not page.evaluate('window.__view.state().enabled')
  # Real drag raises the viewing direction for every visitor.
  page.mouse.move(700 if not mobile else 220,700);page.mouse.down();page.mouse.move(700 if not mobile else 220,200,steps=15);page.mouse.up();page.wait_for_timeout(500)
  state=page.evaluate('window.__view.state()');assert state['pitch']<0 and state['up']>.8,state
  page.screenshot(path=f'/tmp/nknu-look-up-{mobile}.png')
  page.evaluate("async()=>{const a=await import('./developer-auth.js');a.loginDeveloper('0315')}")
  assert page.locator('#aerialControls').is_visible();before=page.evaluate('window.__view.state().player');page.locator('#aerialToggle').click();assert page.evaluate('window.__view.state().enabled')
  for height in [10,200,80]:
   page.locator('#aerialHeight').evaluate('(e,h)=>{e.value=h;e.dispatchEvent(new Event("input"))}',height);page.wait_for_function('(h)=>Math.abs(window.__view.state().camera[1]-window.__view.state().player[1]-h)<1',arg=height);assert page.evaluate('window.__view.state().height')==height
  page.keyboard.down('w');page.wait_for_function('(before)=>window.__view.state().center.some((v,i)=>Math.abs(v-before[i])>.1)',arg=before);page.keyboard.up('w');state=page.evaluate('window.__view.state()');assert state['player']==before and state['center']!=before,state
  page.keyboard.down('e');page.wait_for_function('window.__view.state().height>80');page.keyboard.up('e');assert page.evaluate('window.__view.state().height')>80
  page.screenshot(path=f'/tmp/nknu-aerial-{mobile}.png');page.locator('#aerialToggle').click();assert page.evaluate('window.__view.state().player')==before
  page.evaluate('window.__view.ride();window.__view.enable()');page.evaluate("async()=>{const a=await import('./developer-auth.js');a.logoutDeveloper()}");assert page.locator('#aerialControls').is_hidden();state=page.evaluate('window.__view.state()');assert not state['enabled'] and state['ride'] and state['player']==before
  page.evaluate("async()=>{const a=await import('./developer-auth.js');a.loginDeveloper('0315')}");page.evaluate('window.__view.enable();window.__view.teleport()');assert not page.evaluate('window.__view.state().enabled')
  assert not errors,errors;c.close();print(json.dumps({'result':'PASS','mobile':mobile,'checks':['visitor upward view','developer-only aerial','height slider','pan without moving player','keyboard altitude','return to original position','logout while riding','teleport exits aerial','no JS errors']}))
 b.close()
