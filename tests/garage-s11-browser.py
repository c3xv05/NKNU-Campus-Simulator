"""Three full-width routes, old/new sidewalk crossings and exposed garage walls."""
from pathlib import Path
import os,shutil,json
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];base=os.environ.get('CAMPUS_TEST_URL','http://127.0.0.1:8134/')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 for mobile in [False,True]:
  c=b.new_context(viewport={'width':390,'height':844}if mobile else {'width':1100,'height':850},is_mobile=mobile,has_touch=mobile)
  c.route('https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js',lambda r:r.fulfill(path='/tmp/three.module.js',content_type='text/javascript'));c.route('https://api.github.com/**',lambda r:r.fulfill(json=[]))
  html=(root/'index.html').read_text().replace('let previous=performance.now();',(root/'tests/garage-s11-browser-hook.js').read_text()).replace('cam.position.lerp(target,','if(!window.__freeze)cam.position.lerp(target,').replace('else cam.lookAt(player.position.x,player.position.y+1.1,player.position.z);','else if(!window.__freeze)cam.lookAt(player.position.x,player.position.y+1.1,player.position.z);');c.route(base,lambda r:r.fulfill(body=html,content_type='text/html'))
  page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base);page.wait_for_function('window.__garageS11',timeout=180000);page.get_by_role('button',name='開始探索',exact=True).click();result=page.evaluate('__garageS11.test()');print(json.dumps({'mobile':mobile,**result}),flush=True)
  for mode in ['air','south','east']:
   page.evaluate('(m)=>__garageS11.view(m)',mode);page.wait_for_timeout(300);page.screenshot(path=f'/tmp/nknu-garage-s11-{mobile}-{mode}.png')
  assert not result['failures'],result;assert not errors,errors;c.close()
 b.close();print('PASS: desktop/mobile S11 garage walking/riding, sidewalk crossings, basement wall visibility and shared ground rendering')
