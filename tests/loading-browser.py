"""Same-machine cold-start comparison; optional --baseline-ref <commit>."""
from pathlib import Path
import argparse,json,shutil,subprocess,os,urllib.request
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--baseline-ref');parser.add_argument('--output',default='/tmp/nknu-loading-results.json');args=parser.parse_args()
base=os.environ.get('CAMPUS_TEST_URL','http://127.0.0.1:8128/')
# Fail early if the local server was stopped between development sessions.
with urllib.request.urlopen(base,timeout=5) as response:assert response.status==200
changed=['index.html','planar.js','observed-landscape.js','r04-vegetation.js','roads.js']
hook='''
const hashData=data=>{let h=2166136261;const bytes=ArrayBuffer.isView(data)?new Uint8Array(data.buffer,data.byteOffset,data.byteLength):new TextEncoder().encode(JSON.stringify(data));for(const b of bytes)h=Math.imul(h^b,16777619);return (h>>>0).toString(16);};
window.__startup={signature:{ground:Object.fromEntries(['position','normal','color'].map(k=>[k,hashData(ground.geometry.attributes[k].array)])),sidewalk:hashData(scene.getObjectByName('attached-sidewalks').geometry.attributes.position.array),plants:hashData([landscapeLayout.trees,landscapeLayout.flowers,landscapeLayout.weeds]),counts:[landscapeLayout.trees.length,landscapeLayout.flowers.length,landscapeLayout.weeds.length]},getPosition:()=>({x:player.position.x,y:player.position.y,z:player.position.z})};
'''
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 variants=([('baseline',False)] if args.baseline_ref else [])+[('optimized',False),('optimized',True)]
 for variant,mobile in variants:
  context=browser.new_context(viewport={'width':390,'height':844} if mobile else {'width':1000,'height':800},has_touch=mobile,is_mobile=mobile)
  context.route('https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js',lambda r:r.fulfill(path=os.environ.get('THREE_MODULE_PATH','/tmp/three.module.js'),content_type='text/javascript'))
  context.route('https://api.github.com/**',lambda r:r.fulfill(json=[]))
  def source(path):
   return subprocess.check_output(['git','show',f'{args.baseline_ref}:{path}'],cwd=root,text=True) if variant=='baseline' else (root/path).read_text()
  for file in changed[1:]:
   if variant=='baseline':context.route(base+file,lambda r,request,path=file:r.fulfill(body=source(path),content_type='text/javascript'))
  html=source('index.html').replace("document.getElementById('play').disabled=false;",hook+"document.getElementById('play').disabled=false;")
  context.route(base,lambda r:r.fulfill(body=html,content_type='text/html'))
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' and 'Shader Error' in m.text else None)
  page.add_init_script("window.__loadingStages=[];new MutationObserver(()=>{const b=document.getElementById('play');if(b&&!__loadingStages.includes(b.textContent))__loadingStages.push(b.textContent);}).observe(document,{subtree:true,childList:true,characterData:true});")
  page.goto(base,wait_until='domcontentloaded',timeout=240000);page.get_by_role('button',name='開始探索',exact=True).wait_for(timeout=240000)
  result=page.evaluate("({readyMs:performance.now(),signature:__startup.signature,stages:__loadingStages})");result.update(variant=variant,mobile=mobile)
  print('READY '+json.dumps(result,ensure_ascii=False),flush=True)
  if variant=='optimized':
   assert all(s in result['stages'] for s in ['讀取校園資料…','整理校園地形…','準備道路…','準備校園設施…','準備路面…','整理地表…','準備建築…','準備植栽…']),result['stages']
   assert page.evaluate("performance.getEntriesByName('campus-load-ready').length")==1
  page.get_by_role('button',name='開始探索',exact=True).click();before=page.evaluate('__startup.getPosition()');page.keyboard.down('KeyW');page.wait_for_function('(p)=>{const q=__startup.getPosition();return Math.hypot(q.x-p.x,q.z-p.z)>.01;}',arg=before,timeout=20000);page.keyboard.up('KeyW')
  page.locator('#rideToggle').click();assert page.locator('#rideToggle').get_attribute('aria-pressed')=='true';page.locator('#rideToggle').click()
  (page.locator('#hudMenuButton').click() if page.locator('#hudMenuButton').is_visible() and page.locator('#hudMenuButton').get_attribute('aria-expanded')!='true' else None);page.locator('#travelMenu').evaluate('e=>e.open=true');page.locator('[data-travel=zhili]').click();page.locator('#mapOpen').click();assert page.locator('#mapDialog').is_visible();page.locator('#mapClose').click()
  page.screenshot(path=f'/tmp/nknu-loading-{variant}-{mobile}.png');assert not errors,errors
  results.append(result);context.close()
 browser.close()
assert all(r['signature']==results[0]['signature'] for r in results),'Scene geometry/terrain colors/vegetation changed'
if args.baseline_ref:
 for r in results[1:]:assert r['readyMs']<results[0]['readyMs']*.6,'Expected at least 40% shorter startup on this machine'
Path(args.output).write_text(json.dumps(results,ensure_ascii=False,indent=2));print('PASS: startup, visible real loading stages, identical rendered ground/sidewalk/plants, walk/ride/travel/map, no JS/Shader errors',flush=True)
