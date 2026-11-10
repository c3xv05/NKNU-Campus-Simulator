import json,os,shutil
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
 context=b.new_context(viewport={'width':1280,'height':1000})
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/zones.html');page.wait_for_function("document.querySelectorAll('#zoneList button').length===12")
 assert page.locator('#zoneList button').count()==12
 assert page.locator('#vegetation').input_value()=='待確認'
 page.get_by_role('button',name='B1 霽遠樓、文萃樓與歸燕食巢周邊',exact=True).click()
 assert 'B1' in page.locator('#zoneTitle').inner_text()
 page.locator('#vegetation').select_option('草地與樹林混合');page.locator('#zoneNote').fill('靠道路是草地，後方是樹林。')
 assert 'B1' in page.locator('#replyText').input_value()
 assert '靠道路是草地' in page.locator('#replyText').input_value()
 page.reload();page.wait_for_function("document.querySelectorAll('#zoneList button').length===12")
 page.get_by_role('button',name='B1 霽遠樓、文萃樓與歸燕食巢周邊',exact=True).click()
 assert page.locator('#vegetation').input_value()=='草地與樹林混合'
 assert '後方是樹林' in page.locator('#zoneNote').input_value()
 # Direct SVG interaction must select the matching zone.
 page.locator('#zoneMap [aria-label="C1 教學區西側山坡，植被待確認"]').focus();page.keyboard.press('Enter')
 assert 'C1' in page.locator('#zoneTitle').inner_text()
 assert page.locator('#vegetation').input_value()=='待確認'
 # Capture the default map without implying any classification.
 page.evaluate('localStorage.clear()');page.reload();page.wait_for_function("document.querySelectorAll('#zoneList button').length===12")
 page.screenshot(path='/tmp/nknu-zones-desktop.png',full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path='/tmp/nknu-zones-mobile.png',full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors
 print('PASS: 12-zone rendering, no prefilled classification, region selection, feedback text, draft persistence, SVG keyboard selection and mobile layout')
 b.close()
