"""Actual controller and rendered surfaces, desktop + touch viewport; no production hooks."""
from pathlib import Path
import shutil,json,os
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];base=os.environ.get('CAMPUS_TEST_URL','http://127.0.0.1:8131/')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 for mobile in ([False] if os.environ.get('CAMPUS_DESKTOP_ONLY') else [False,True]):
  c=b.new_context(viewport={'width':390,'height':844} if mobile else {'width':1100,'height':850},has_touch=mobile,is_mobile=mobile)
  if os.environ.get('THREE_MODULE_PATH'):c.route('https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js',lambda r:r.fulfill(path=os.environ['THREE_MODULE_PATH'],content_type='text/javascript'))
  c.route('https://api.github.com/**',lambda r:r.fulfill(json=[]))
  html=(root/'index.html').read_text().replace('let previous=performance.now();',(root/'tests/campus-corridors-browser-hook.js').read_text()).replace('cam.position.lerp(target,','if(!window.__freeze)cam.position.lerp(target,').replace('else cam.lookAt(player.position.x,player.position.y+1.1,player.position.z);','else if(!window.__freeze)cam.lookAt(player.position.x,player.position.y+1.1,player.position.z);');c.route(base,lambda r:r.fulfill(body=html,content_type='text/html'))
  page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' and 'Shader Error' in m.text else None);page.goto(base);page.wait_for_function('window.__corr',timeout=180000);page.get_by_role('button',name='開始探索',exact=True).click(timeout=90000)
  result=page.evaluate('__corr.test()');print(json.dumps({'mobile':mobile,**result}),flush=True);assert not result['failures'],result
  page.evaluate('__corr.cameraBelow()');page.wait_for_function('__corr.cameraState().frames>=8',timeout=30000);camera=page.evaluate('__corr.cameraState()');assert camera['lower']+1.5<camera['y']<camera['ceiling'],camera;print('camera',camera,flush=True)
  page.locator('#map').click();page.wait_for_function("document.getElementById('mapDialog').open");assert page.locator('#mapDialog svg text').filter(has_text='中央廣場').count()==0;assert page.locator('#mapDialog svg [aria-label="courtyard-s32"]').count()>0
  page.keyboard.press('Escape')
  for mode in (['court-air','court-ground','court-inside','bio-air','bio-road','bio-lower'] if not mobile else ['court-ground','bio-road']):
   page.evaluate('(m)=>__corr.view(m)',mode);page.wait_for_timeout(300);page.screenshot(path=f'/tmp/nknu-corridors-{mobile}-{mode}.png')
  assert not errors,errors;c.close()
 b.close();print('PASS: desktop/mobile three lanes bidirectional walk/ride, open two-floor corridor, level gallery, rendered support, S05 arrival and hidden courtyard map label')
