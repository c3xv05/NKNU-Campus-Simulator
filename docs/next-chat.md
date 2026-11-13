# 新對話接續摘要

專案：`c3xv05/NKNU-Campus-Simulator`，分支 `main`。本機目錄 `/workspace/NKNU-Campus-Simulator`。

- 正式網站：https://c3xv05.github.io/NKNU-Campus-Simulator/
- 開發紀錄及回報索引：https://github.com/c3xv05/NKNU-Campus-Simulator/issues/9
- 新對話先讀 `AGENTS.md`、本摘要與 `docs/developer-journal.md`，再讀索引Issue及相關建築資料。使用者最新指示優先。

## 最新完成（2026-11-13）

- **最新球場與詠絮／R04更正**：籃球南側3.6m人行道改沿南側道路218881799北緣，約64m邊線直接貼路、右端接S09；取代前版離道路有草帶的獨立直條，場緣到步道仍用坡面銜接。左下出口改在西側（沿向陽路218881795），面朝向陽路，取消南側出口缺口；西網分兩段、南網完整、東網兩段，仍五段，東短梯保留。
- 詠絮樓依本次俯瞰白框重描7轉角L形：北橫翼較薄、東縱翼及內側斜角，非原6角輪廓。附圖黑斜線為內側／南側道路，藍斜線為西凸半圓草皮；取消原半徑28m整片半圓路面與舊入口補片，改約631m²道路、163m²草皮。來源yongxu-access/satellite-sketch.json保存手繪像素輪廓與定位換算，不作材質。輪廓、比例是圖片近似，非實測。
- S21原西段／路寬保留，前庭段改從草皮南側繞到新內側門前；8cm額外道路微調上限維持，詠絮／食巢共同平台仍64.285704m。原64地形fixture有61點不變，僅3點受新建築基座局部融合影響（最大約0.738m），限制在基座附近20m網格插值範圍，沒有整片抬升、原始高程檔不變。凹形路面必須保留triangles，供路緣／步道／地形裁切使用。
- R04細分7區：R04-L1詠絮草皮，R04-O1食巢／飛燕／詠絮前庭，R04-O2高斯／致理／寰宇教學區，R04-O3其他建築，R04-F1北側教學外圍林、F2宿舍詠絮周邊林、F3大門西側山坡林。非鋪面／非開放區皆為茂密樹林，種植格距6.5m，確定性生成1,348棵R04樹。分區避開實際道路、白磚、建築與草皮；不把整個共同平台都當草地。內部分界為便於定位的模型線，可在開發者分區頁各自選取回報，訪客維持一般地圖。
- R04來源facilities/r04-vegetation/layout.json，生成data/r04-vegetation.js；r04-vegetation.js供分類，landcover／landscape套用，zones／road-review列7個子區。重建鋪面與court-access後再跑build-road-regions及build-r04-vegetation；父R01–R12編號維持。
- 新回歸tests/court-yongxu-r04.mjs、-geometry.py、-browser.py；既有照片／坡度／S21路寬與實走測試改讀最新輪廓及實際繞行線，不再要求被本次取消的28m半圓。


- **側門最新更正**：警衛室-2401往西南移並沿牆轉向，保留10×7m量體，西側貼北短牆、南端距實際路緣約1.6cm且零重疊。取代前版約10.4m道路退縮；回收場／水塔不動。北短牆reach10.6m，南短牆仍9m，門口5.2m不變。
- S23南北車棚北端／接路固定，總長按使用者「1.5倍」由42→63m，南加21m至z72.7；寬9m、淨高3.2m維持，中央步行騎車通道開放，支架改11跨。carport.json及pavedAreas同步，重建瀝青mesh。
- 新西側圍牆：facilities/s24-sidegate/west-wall.json，從側門南短牆接車棚西側，再依既有西校界近似線至大門西側牆端[-280,525.8]。這次已確認的西段才新增，不是整圈牆、也不是恢復擋土牆。高1.6m厚0.28m、校界西偏避讓為模型近似。與實際車道／白磚／建築零重疊，兩門開口保留。
- west-wall.js共用圍牆線形供渲染／碰撞／地圖／植栽避讓；每公尺依實際地形採樣，底部埋入，不為牆抬升地形。來源改後跑build-building-catalog、build-carports、build-sidegate，再重建pedestrian-patches／sidewalk-plan／motor-pavement-plan／court-access。
- 新回歸：sidegate-west-wall.mjs、sidegate-west-wall-geometry.py、sidegate-west-wall-browser.py。舊sidewalk-upgrade曲線冪等檢查排除有明確entryExtensionReference的詠絮延伸路，另核對其門前端點，保留其他路重建檢查。


- **最新南側縮退與道路坡度**：籃球南緣向北縮7.2m（兩個3.6m人行道），四座標線與八籃框整體向北移7.2m；新外圍32.8×49.5m，仍水平、矩形且不與車道／人行道重疊。保留兩出口、東短梯與東南西鐵網。
- 移除使用者指定舊南側2m步道445696824，其他非W步道36條保留。新南側3.6m白磚人行道接S09；和南場緣留4.2m坡面過渡，不擅自刪別條步道。來源sports-courts/south-sidewalk.json。
- 籃球下方增加約一層地下停車場結構：模型層高3.6m，樓板、頂板、柱與格線；來源basketball-parking/layout.json，車道入口尚未定位，未新增推測車行入口，24格僅模型配置。地下樓層支撐獨立，地上球場仍在原高程。
- 向陽路218881795保留路線／路寬與原剖面端點，整路平滑持續南降，過長型建築後仍下降；1,250點坡度約3.4%–11.9%。road-grade-profile.js與xiangyang-grade/profile.json共用連續高度場，帶動路旁地形平滑衰減並保護建築基座，原始高程檔不改。
- 使用者強調未來所有修改都要配合鄰側地形微調、避免斷層；已寫入AGENTS.md永久要求。檢查地面／空中接縫、渲染／支撐一致，不可只補一片懸空鋪面。
- 重建新增順序：build-sports-courts → build-court-south-sidewalk → build-campus-plazas → build-pedestrian-patches → build-sidewalk-plan → build-motor-pavement-plan → build-court-access。南側連接生成只取S09原人行道，避免重跑時自我截短。
- 新回歸：tests/court-garage-grade.mjs與court-garage-grade-browser.py。


- **最新球場外圍**：籃球區、網球區均改成沿向陽路方向的嚴格矩形，與實際道路／白磚人行道交集為零。球場地坪為水平面，網球兩半仍同高；地形在場下完整裁除，避免草地穿出。舊不規則輪廓留在各court.sourceRing，不再用作現況。
- 球場外緣以獨立坡面接回道路、人行道與草地，坡面不覆蓋既有鋪面；與出口坡道分割成不重疊幾何。保留四籃球全場、四網球場、平行向陽路、遮棚及中間階梯花圃。
- 籃球左下（西南）出入口用坡道接外路；右上（東北）出入口先下東側六階短梯（模型0.9m），再沿場邊坡道接東側道路。兩入口寬4m，東側沿邊坡道模型寬2.4m；不可用鐵網封掉入口。
- 東、南、西三邊為3m模型防球鐵網；東／南各切一入口，西側完整，共五段網。網與柱合批，具防穿越碰撞，北側維持通往花圃的開放配置。
- 新生成流程：build-sports-courts.py之後跑build-court-access.py（Shapely2.1，讀實際sidewalk-plan與motor-pavement-plan邊界）。通行與坡面渲染共用facilities/sports-courts/access-surface.js；外圍渲染在access-renderer.js。若重建鋪面，最後重跑build-court-access。

- **取代前版詠絮2.4m抬升**：已取消整片新增平台並恢復與食巢／飛燕同一原始平台，周邊64個地形基準點與PR #50相同；只對S21原自然坡做最多8cm局部修整。門前道路延伸仍保留，不能再恢復大幅抬升。
- 高斯／致理連接處的「便利商店」僅為使用者與開發者的溝通代稱，存`levelLink.communicationAlias`及building-access來源。不要做店家模型、招牌或地圖標籤。地圖「致理1F ↔ 高斯2F」文字已移除；實際樓層連接與通行保留。
- 籃球四個完整全場（八籃框），網球四場（四張網），全部長軸平行向陽路。外圍以最新矩形為準並保留遮棚；籃球22×約11.79m為配合既有範圍的模型示意、非FIBA標準或實測；網球23.77×10.97m採常用標線尺寸但位置非測量。
- 網球兩原輪廓共用`platformAnchor=[36.5,-220]`，左右同高；中間設四階花圃並留3.6m通行間隙。高於遮棚時棚面淡化，便於空中觀察；地面仍保留遮棚。
- 球場來源`facilities/sports-courts/layout.json`，生成`python scripts/build-sports-courts.py`；渲染在同資料夾renderer.js。每個外圍court的`playingCourts`列實際標線／球網／籃框，不再將一個外圍直接當成一個全場。

- 寰宇3F門廳為中空穿堂，直通中央廣場2F。3F樓面對齊廣場2F，因此寰宇基準相對前版另降3.6m；致理／高斯基準不變。通道寬6m、淨高3.2m為模型近似，只切開該樓層，底層及樓上仍實心；步行可雙向通過，機車不開放穿堂。
- 中央廣場1F保留；2F改連通L型，寰宇內牆側一個人行道寬（3.6m），致理側由致理高斯連接處南端至致理內牆。中央小樓梯移到L型寬臂內。上層約1495m²、下層約2770m²，取代前版全面鋪滿的二層。
- S21原路寬、接點與續延至門前保留；瀝青與外牆共邊約21m。前版2.4m平台抬升及3.89m坡道已被使用者取消，現為原地形上的局部微坡。
- 側門北側從西向東為警衛室（-2401）、回收場（397467190）、雙圓水塔（397467191）；由使用者本次衛星圖辨識，距車道約10.4／13.9／15.2m為圖片近似。三處與所有車道、步道均無重疊，沿用原三棟ID。
- 新來源：`facilities/yongxu-access/layout.json`、`facilities/s24-sidegate/north-facilities.json`、各棟building.json的passage／tanks。通道修改後先build-building-passages，再build-building-catalog；廣場build-teaching-courtyard、T廣場build-huanyu-platform；鋪面依既有流程重建。

- 開發者登入後左上「空中觀察」：離地高度滑桿10–200m，預設60m；WASD／手機搖桿平移、拖曳環看，Q／E降低／升高。角色留原地，返回時保留原步行／騎車模式；登出立即退出，傳送先退出再落地。
- 所有人可拖曳視角向上仰視，地面相機保留避障與樓層支撐。空中模式的建築細節／照明跟隨觀察中心，手機工具區可捲動。慢載入首幀負時間差已限制為0。
- 視角入口：`index.html`；回歸：`tests/aerial-browser.py`。

- 一般訪客維持五個傳送點：大門、歸燕食巢、致理、圖資、科技。數字鍵1–5不變。
- 開發者登入後可傳送全部20棟建築：原公開四棟加16個額外建築，另保留大門，共21個選項。登出即移除額外按鈕，傳送函式也會重新檢查登入，不能用登出前的選項繼續傳送。
- 落點在建築附近安全道路／可通行前庭，避開建築、湖與障礙，步行／騎車均可用；未命名建物以編號區分。手機選單可捲動。
- 歸燕門前缺口連同靠路緣的一段補齊：`facilities/campus-plazas/layout.json` 的 `swallow-entrance-infill`；先合併白磚再扣車道／建築，維持15cm高差，無重疊貼片。

## 已確認、請保留的現況

- 高斯取消削角，恢復原轉角。418049575／495017564支路原寬4.5m繞外牆；742398750原步道接點順接。其他道路保持；原輪廓及繞行來源在各建築與道路備註。
- 高斯、致理、寰宇共同降半層（模型1.8m）。保留致理1F＝高斯2F，採樣錨點與offset已分開，局部退縮不能順帶改道路高度。
- 中央廣場為兩層白磚，1F保留廣場，2F已收成L型；中央24階小樓梯連通。北側坡面接1F。分層支撐、坡面邊界與相機已處理，避免跳層／抬上樓。
- 寰宇入口是3F，T形廣場的橫段沿S06詠霽路人行道，直段通門前。不要恢復成2F入口或把T橫段放回門前。
- 食巢與飛燕約兩個現有人行道寬（模型7.2m）；詠絮樓前半圓模型半徑28m、圓弧朝東且接入口。食巢／飛燕／詠絮已恢復原共同平面。
- 基本人行道寬3.6m、高於路面15cm；白色磁磚、灰邊。側別已逐段確認，不能擅加整段人行道。
- W01–W18全刪，保留36條非W步道（最新另依指示移除籃球南側445696824）。僅S06、S12、S05、S09、S02、S03、S04、S13加寬至模型10.5m，各側加1.75m並平滑收束。
- S06西側為向西上升的森林陡坡；高程是現場回饋模型近似，非實測。原始高程檔未改。
- 手機搖桿與調視角可同時使用；小地圖可雙指縮放。植被分區只供開發者。
- 新聞／Dcard故事只在 `docs/research/story-seeds.md` 備忘，尚未實作NPC／事件；避免腥羶色及仇恨題材。

## 工作入口

- 傳送：`travel.js`、`index.html`；登入狀態：`developer-auth.js`。原五點與開發者額外點分開，實際呼叫也須檢查登入。
- 每棟外觀：`buildings/<id>/building.json`；修改後執行 `python scripts/build-building-catalog.py`。
- 兩層廣場：`facilities/teaching-courtyard/`，生成 `scripts/build-teaching-courtyard.py`。
- 寰宇T廣場：`facilities/huanyu-platform/`，生成 `scripts/build-huanyu-platform.py`。
- 樓梯：`facilities/building-access/layout.json`、`stair-layout.js`、`connections.js`。
- 新增／修補步道：修改campus-plazas來源後，依序build-campus-plazas、build-pedestrian-patches、build-sidewalk-plan、build-motor-pavement-plan。需Shapely 2.1。
- 新增回歸：`tests/developer-travel.mjs`、`tests/developer-travel-browser.py`；原有貼路、15cm鋪面、樓梯與手機測試仍須依變更範圍驗證。

使用者偏好完成驗證後直接合併並發布，再回報結果；同時更新開發日誌及Issue #9，方便後續對話接續。新指示優先。
