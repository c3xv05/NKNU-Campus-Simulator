"""Run against python -m http.server 8000. Optional THREE_MODULE_PATH avoids CDN dependence."""
import json, os, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=1)
    if os.environ.get('THREE_MODULE_PATH'):
        context.route('https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js',lambda route:route.fulfill(path=os.environ['THREE_MODULE_PATH'],content_type='text/javascript'))
    # Inspection hook exists in the test response only, never production source.
    html=(ROOT/'index.html').read_text().replace('let previous=performance.now();', '''window.__test={getState:()=>({x:player.position.x,y:player.position.y,z:player.position.z,yaw,stick:{...stick}}),height:walkHeight,
    pose:(x,z)=>{player.position.set(x,walkHeight(x,z),z);cam.position.copy(player.position).add(new THREE.Vector3(0,22,30));},places,
    visited,terrain,scene};let previous=performance.now();''')
    context.route('http://127.0.0.1:8000/',lambda route:route.fulfill(body=html,content_type='text/html'))
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8000/');page.wait_for_function('!!window.__test',timeout=120000)
    page.get_by_role('button',name='開始探索').click(timeout=90000);page.wait_for_timeout(300)
    assert page.locator('#joystick').is_visible()
    assert page.locator('#joystick').evaluate("e=>getComputedStyle(e).touchAction")=='none'
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    session=context.new_cdp_session(page)
    box=page.locator('#joystick').bounding_box();cx=box['x']+box['width']/2;cy=box['y']+box['height']/2
    def touch(kind,points): session.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[{'id':i,'x':x,'y':y} for i,x,y in points]})
    state=lambda:page.evaluate('window.__test.getState()')
    start=state()
    touch('touchStart',[(1,cx,cy-42)])
    page.wait_for_timeout(250)
    touch('touchStart',[(1,cx,cy-42),(2,270,380)])
    touch('touchMove',[(1,cx+18,cy-42),(2,310,400)])
    page.wait_for_timeout(400)
    moving=state();assert moving['z']<start['z'];assert moving['yaw']<start['yaw'];assert moving['stick']['z']<0
    # Releasing the looking finger must leave movement active.
    touch('touchEnd',[(2,310,400)]);before=state();page.wait_for_timeout(800);after=state();assert after['z']<before['z']
    touch('touchEnd',[]);before=state();page.wait_for_timeout(200);after=state();assert before==after
    assert abs(after['y']-page.evaluate('s=>window.__test.height(s.x,s.z)',after))<1e-6
    # Full map has every place, labelled selection, player marker, modal input pause.
    page.locator('#mapOpen').click();assert page.locator('#mapDialog').evaluate('e=>e.open')
    assert page.locator('#buildingList button').count()==12
    page.locator('#buildingList button').filter(has_text='圖資大樓').click()
    assert '圖資大樓' in page.locator('#mapSelection').inner_text()
    assert page.locator('#buildingList button.selected').count()==1
    assert not page.locator('#zonesMode').is_visible();page.evaluate("async()=>{(await import('./developer-auth.js')).loginDeveloper('0315')}");page.locator('#zonesMode').click();assert page.locator('#buildingList button').count()==12
    page.locator('#buildingList button').filter(has_text='R04').click();assert '植被' in page.locator('#mapSelection').inner_text()
    page.locator('#buildingsMode').click();assert '圖資大樓' in page.locator('#mapSelection').inner_text()
    before=state();page.keyboard.down('w');page.wait_for_timeout(200);assert state()==before;page.keyboard.up('w')
    page.screenshot(path='/tmp/nknu-mobile-map.png')
    page.keyboard.press('Escape');assert not page.locator('#mapDialog').evaluate('e=>e.open')
    page.keyboard.press('m');assert page.locator('#mapDialog').evaluate('e=>e.open');page.keyboard.press('m')
    assert not page.locator('#mapDialog').evaluate('e=>e.open')
    # Cancel must reset the stick, even after holding off its visual edge.
    touch('touchStart',[(3,cx,cy-40)]);touch('touchMove',[(3,cx,cy-170)]);touch('touchCancel',[])
    assert state()['stick']=={'x':0,'z':0}
    # Verify platform heights, satellite relief and terrain-following actual movement.
    levels=page.evaluate('window.__test.places.map(p=>({name:p.name,height:window.__test.height(p.x,p.z)}))')
    assert max(p['height'] for p in levels)-min(p['height'] for p in levels)>20
    page.evaluate('window.__test.pose(-22,-70)');before=state();page.keyboard.down('w');page.wait_for_timeout(500);page.keyboard.up('w');after=state()
    assert abs(after['y']-page.evaluate('s=>window.__test.height(s.x,s.z)',after))<1e-6
    page.screenshot(path='/tmp/nknu-mobile-terrain.png')
    page.set_viewport_size({'width':844,'height':390});page.wait_for_timeout(100)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.locator('#mapOpen').click();page.screenshot(path='/tmp/nknu-landscape-map.png');page.locator('#mapClose').click()
    assert not errors,errors
    context.close()
    desktop=browser.new_context(viewport={'width':1280,'height':900})
    if os.environ.get('THREE_MODULE_PATH'):
        desktop.route('https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js',lambda route:route.fulfill(path=os.environ['THREE_MODULE_PATH'],content_type='text/javascript'))
    d=desktop.new_page();d.on('pageerror',lambda e:errors.append(str(e)));d.goto('http://127.0.0.1:8000/');d.get_by_role('button',name='開始探索').click(timeout=90000)
    assert not d.locator('#touch').is_visible()
    d.keyboard.press('m');assert d.locator('#mapDialog').evaluate('e=>e.open');d.locator('#buildingList button').first.click();d.screenshot(path='/tmp/nknu-desktop-map.png');d.keyboard.press('Escape')
    assert not errors,errors
    print(json.dumps({'result':'PASS','checks':['real multi-touch joystick + look','independent finger release','cancel/reset','terrain-following player','12-place map selection','map pauses keyboard movement','Escape/M modal handling','portrait/landscape/desktop layouts','no JavaScript errors'],'landmarkRelativeHeights':levels},ensure_ascii=False))
    browser.close()
