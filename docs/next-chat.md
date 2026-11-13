# 新對話接續摘要

專案：`c3xv05/NKNU-Campus-Simulator`，分支 `main`。本機目錄 `/workspace/NKNU-Campus-Simulator`。

- 正式網站：https://c3xv05.github.io/NKNU-Campus-Simulator/
- 開發紀錄及回報索引：https://github.com/c3xv05/NKNU-Campus-Simulator/issues/9
- 新對話先讀 `AGENTS.md`、本摘要與 `docs/developer-journal.md`，再讀索引Issue及相關建築資料。使用者最新指示優先。

## 最新完成（2026-11-13）

- 寰宇3F門廳為中空穿堂，直通中央廣場2F。3F樓面對齊廣場2F，因此寰宇基準相對前版另降3.6m；致理／高斯基準不變。通道寬6m、淨高3.2m為模型近似，只切開該樓層，底層及樓上仍實心；步行可雙向通過，機車不開放穿堂。
- 中央廣場1F保留；2F改連通L型，寰宇內牆側一個人行道寬（3.6m），致理側由致理高斯連接處南端至致理內牆。中央小樓梯移到L型寬臂內。上層約1495m²、下層約2770m²，取代前版全面鋪滿的二層。
- S21詠霽路到詠絮樓為連續斜坡，保留原路寬與接點，中心線續延至門前；瀝青與門前外牆共邊約21m，無建築重疊。詠絮樓及前庭比食巢／飛燕平台追加2.4m模型高差，實際S21模型爬升約3.89m，非測量。
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
- 食巢與飛燕約兩個現有人行道寬（模型7.2m）；詠絮樓前半圓模型半徑28m、圓弧朝東且接入口。食巢／飛燕仍共平面，詠絮樓與門前平台依最新斜坡需求追加模型高差。
- 基本人行道寬3.6m、高於路面15cm；白色磁磚、灰邊。側別已逐段確認，不能擅加整段人行道。
- W01–W18全刪，保留37條非W步道。僅S06、S12、S05、S09、S02、S03、S04、S13加寬至模型10.5m，各側加1.75m並平滑收束。
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
