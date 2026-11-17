"""Actual movePlayer and rendered meshes on desktop / mobile, with test-only hooks."""
import os,json,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];base=os.environ.get('CAMPUS_TEST_URL','http://127.0.0.1:8139/')
html=(root/'index.html').read_text().replace('let previous=performance.now();',(root/'tests/jiyuan-interior-browser-hook.js').read_text()).replace('cam.position.lerp(target,','if(!window.__freeze)cam.position.lerp(target,').replace('else cam.lookAt(player.position.x,player.position.y+1.1,player.position.z);','else if(!window.__freeze)cam.lookAt(player.position.x,player.position.y+1.1,player.position.z);')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 for mobile in [False,True]:
  c=b.new_context(viewport={'width':390,'height':844} if mobile else {'width':1200,'height':900},has_touch=mobile,is_mobile=mobile);c.route(base,lambda r:r.fulfill(body=html,content_type='text/html'));c.route('https://api.github.com/**',lambda r:r.fulfill(json=[]))
  if os.environ.get('THREE_MODULE_PATH'):c.route('https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js',lambda r:r.fulfill(path=os.environ['THREE_MODULE_PATH'],content_type='text/javascript'))
  page=c.new_page();errors=[];page.on('pageerror',lambda e:(errors.append(str(e)),print(str(e),flush=True)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' and 'Shader Error' in m.text else None);page.goto(base);page.wait_for_function('window.__jiyuan',timeout=180000);page.get_by_role('button',name='開始探索',exact=True).click(timeout=90000)
  result=page.evaluate('__jiyuan.test()');print(json.dumps({'mobile':mobile,**result}),flush=True);assert not result['failures'],result
  level=page.evaluate('__jiyuan.camera()');page.wait_for_function('__jiyuan.cameraState().frame>=12',timeout=90000);camera=page.evaluate('__jiyuan.cameraState()');assert level+1.5<camera['y']<level+2.84*1.1,camera;print('camera',camera,flush=True)
  for mode in ['exterior','bath','stair-ground','stair-upper','cut'] if not mobile else ['exterior','bath','stair-ground','stair-upper']:
   page.evaluate('__jiyuan.view',mode);page.wait_for_timeout(300);page.screenshot(path=f'/tmp/nknu-jiyuan-{mobile}-{mode}.png')
  assert not errors,errors;c.close()
 b.close()
print('PASS: desktop and mobile actual controller, all room/public doors, 16 bidirectional stair links, slab/tread rays, indoor camera, no JS/Shader errors')
