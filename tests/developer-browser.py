from pathlib import Path
import json,shutil
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright
base='http://127.0.0.1:8000'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
 c=b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
 fixture='''<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="./developer.css"><style>body{margin:0;background:#102a3b;color:white;font-family:system-ui}#panel{padding:20px}button{font:inherit;padding:10px}</style><div id="panel"><h1>校園封面</h1></div><script>window.campusDeveloperContext=()=>({position:{x:-275.3,y:0,z:525.8},mode:'步行'});</script><script type="module" src="./developer.js"></script>'''
 c.route(base+'/developer-fixture.html',lambda r:r.fulfill(body=fixture,content_type='text/html'))
 issues=[{'title':'已保存的校門回報','body':'<!-- nknu-dev-record -->\n校門已修正 <script>window.bad=true</script>','html_url':'https://github.com/c3xv05/NKNU-Campus-Simulator/issues/9'},{'title':'一般議題','body':'ordinary','html_url':'https://github.com/example'},{'title':'不列出的 PR','body':'<!-- nknu-dev-record -->','pull_request':{},'html_url':'https://github.com/example'}]
 c.route('https://api.github.com/repos/c3xv05/NKNU-Campus-Simulator/issues?*',lambda r:r.fulfill(json=issues))
 c.route('https://github.com/c3xv05/NKNU-Campus-Simulator/issues/new?*',lambda r:r.fulfill(body='GitHub handoff test',content_type='text/html'))
 page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/developer-fixture.html')
 page.locator('#developerEntry').click();page.locator('#devPass').fill('wrong');page.get_by_role('button',name='進入開發者介面',exact=True).click();assert '不正確' in page.locator('#devLoginStatus').inner_text();assert not page.locator('#devOrb').is_visible()
 page.locator('#devPass').fill('0315');page.get_by_role('button',name='進入開發者介面',exact=True).click();assert page.locator('#devOrb').is_visible()
 page.locator('#devOrb').click();page.locator('#devReport').click();page.locator('#devRecordTitle').fill('校門測試');page.locator('#devRecordBody').fill('靠花圃的路面需要再調整。')
 page.wait_for_function("JSON.parse(localStorage.getItem('nknu-developer-drafts-v1')).length===1")
 page.wait_for_function("document.getElementById('devCloudList').textContent.includes('已保存的校門回報')")
 assert '一般議題' not in page.locator('#devCloudList').inner_text();assert '不列出的 PR' not in page.locator('#devCloudList').inner_text();assert not page.evaluate('window.bad')
 with page.expect_popup() as info:page.locator('#devSend').click()
 popup=info.value;popup.wait_for_load_state();q=parse_qs(urlparse(popup.url).query);assert q['title'][0]=='[問題回報] 校門測試';assert 'local-id:' in q['body'][0] and '-275.3' in q['body'][0];popup.close()
 assert '請在該頁完成送出' in page.locator('#devStatus').inner_text()
 page.locator('#devRecordBody').fill('修改後的本機草稿');page.reload();page.locator('#devOrb').click();page.locator('#devReport').click();assert page.locator('#devRecordBody').input_value()=='修改後的本機草稿'
 with page.expect_download() as info:page.locator('#devExport').click()
 download=info.value;download.save_as('/tmp/nknu-developer-records-test.json');d=json.load(open('/tmp/nknu-developer-records-test.json'));assert d['records'][0]['body']=='修改後的本機草稿'
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.screenshot(path='/tmp/nknu-developer-mobile.png')
 page.locator('#devBack').click();page.locator('#devLogout').click();assert not page.locator('#devOrb').is_visible();page.reload();assert not page.locator('#devOrb').is_visible()
 # GitHub failure preserves editing and draft access.
 page.locator('#developerEntry').click();page.locator('#devPass').fill('0315');page.get_by_role('button',name='進入開發者介面',exact=True).click();page.locator('#devOrb').click();page.locator('#devJournal').click()
 c.unroute('https://api.github.com/repos/c3xv05/NKNU-Campus-Simulator/issues?*');c.route('https://api.github.com/repos/c3xv05/NKNU-Campus-Simulator/issues?*',lambda r:r.fulfill(status=403,json={'message':'rate limit'}));page.locator('#devRefresh').click();page.wait_for_function("document.getElementById('devStatus').textContent.includes('暫時無法讀取')")
 assert not errors,errors
 print('PASS: password gate, developer orb/menu, autosave/reload, GitHub handoff is not falsely marked sent, remote records/XSS safety, metadata/export, logout, mobile layout and offline fallback');b.close()
