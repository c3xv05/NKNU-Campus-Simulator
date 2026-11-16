from pathlib import Path
import json,shutil
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];base='http://127.0.0.1:8127/'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 for mobile in [False,True]:
  c=b.new_context(viewport={'width':390,'height':844} if mobile else {'width':1280,'height':900},has_touch=mobile,is_mobile=mobile)
  c.route('https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js',lambda r:r.fulfill(path='/tmp/three.module.js',content_type='text/javascript'))
  c.route('https://api.github.com/**',lambda r:r.fulfill(json=[]))
  js=(root/'heping.js').read_text().replace('drawMaps();requestAnimationFrame(animate);',"window.__heping={data,world,player,travel,get state(){return {riding,aerial,speed,yaw,pitch,orbit:{x:orbit.x,z:orbit.z},visits:[...visits]};}};drawMaps();requestAnimationFrame(animate);")
  c.route(base+'heping.js',lambda r:r.fulfill(body=js,content_type='text/javascript'))
  page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' and 'Shader Error' in m.text else None)
  page.goto(base+'heping.html')
  page.get_by_role('button',name='開始探索',exact=True).click(timeout=90000);page.wait_for_function('window.__heping')
  assert page.locator('#top [aria-current=page]').inner_text()=='和平校區'
  assert not page.locator('#developerCoordinates').is_visible()
  page.evaluate("async()=>{const auth=await import('./developer-auth.js');auth.loginDeveloper('0315');}")
  page.locator('#developerCoordinates').wait_for(state='visible');assert page.evaluate('campusDeveloperContext().campus')=='heping'
  page.evaluate("async()=>{const auth=await import('./developer-auth.js');auth.logoutDeveloper();}");assert not page.locator('#developerCoordinates').is_visible()
  original=page.evaluate('({x:__heping.player.position.x,z:__heping.player.position.z})')
  page.keyboard.down('KeyW');page.wait_for_timeout(450);page.keyboard.up('KeyW');moved=page.evaluate('({x:__heping.player.position.x,z:__heping.player.position.z})');assert moved!=original
  page.locator('#ride').click();assert page.evaluate('__heping.state.riding');page.locator('#ride').click()
  page.locator('#aerial').click();assert page.evaluate('__heping.state.aerial');page.screenshot(path=f'/tmp/heping-{mobile}-air.png');page.locator('#aerial').click()
  page.locator('#mapOpen').click();page.get_by_role('button',name='教育大樓',exact=True).last.click();page.locator('#mapTravel').click();assert not page.locator('#mapDialog').is_visible()
  result=page.evaluate('''()=>{const r=[];for(const p of __heping.data.places){__heping.travel(p.id);if(__heping.world.blocked(__heping.player.position.x,__heping.player.position.z,.8))r.push(p.name);}return r;}''');assert not result,result
  if mobile:
   page.locator('#aerial').click();before=page.evaluate('__heping.state');stick=page.locator('#joystick').bounding_box();x=stick['x']+stick['width']/2;y=stick['y']+stick['height']/2
   cdp=c.new_cdp_session(page)
   cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1},{'x':280,'y':440,'id':2}]})
   cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-30,'id':1},{'x':320,'y':445,'id':2}]})
   page.wait_for_timeout(450);cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
   after=page.evaluate('__heping.state');assert before['orbit']!=after['orbit'];assert before['yaw']!=after['yaw'];page.locator('#aerial').click()
  page.evaluate("__heping.travel('gate')");page.screenshot(path=f'/tmp/heping-{mobile}-ground.png');page.locator('#mapOpen').click();page.screenshot(path=f'/tmp/heping-{mobile}-map.png');page.locator('#mapClose').click()
  # Return to Yanchao through the in-game campus control; existing scene still loads.
  page.locator('#top').get_by_role('link',name='燕巢校區',exact=True).click();page.get_by_role('button',name='開始探索',exact=True).click(timeout=180000);page.screenshot(path=f'/tmp/yanchao-switch-{mobile}.png')
  switch=page.locator('#tools .campus-switcher').bounding_box();assert switch and switch['width']>100
  page.locator('#tools').get_by_role('link',name='和平校區',exact=True).click();page.get_by_role('button',name='開始探索',exact=True).click(timeout=90000)
  assert not errors,errors
  print('PASS:', 'mobile' if mobile else 'desktop','campus round-trip, walking, riding, aerial, map travel, safe arrivals, no JS/Shader errors',flush=True);c.close()
 b.close()
