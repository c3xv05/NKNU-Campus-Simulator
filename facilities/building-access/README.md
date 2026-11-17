# 致理／高斯連接處階梯

2026-11-17：致理外殼改為平面圖塔樓後，`compactAccess.frontLine` 固定原致理 frontEdge=1（北→南）線段作階梯定位，不再讀新外殼頂點，因此兩組階梯位置不變。中央廣場中央小樓梯依使用者要求移除，`courtyardStairs` 為空，原資料存於 `removedCourtyardStairs`，不得恢復。

「便利商店」僅為溝通位置代稱，不建立店家、招牌或地圖標記。

2026-11-16最新要求：靠S05的第一組大階梯為8階→歇腳平台→再8階（共16階），上方小梯維持8階。補平高斯側剩餘人行道凹口。這取代PR71的第一組單跑8階；不恢復舊40／24階、七階、B1車道或下沉磁磚。

來源layout.json的compactAccess取致理frontEdge=1南端為定位原點；梯跑正面仍朝S05。下梯兩段各8階、各2.56m梯跑，中間1.6m水平歇腳平台，總深6.72m；上方小梯仍8階／3.2m。寬12m與4.5m沿用；北端留0.15m、梯腳退入立面0.12m及上梯定位為模型近似，非實測。建築原基準與原兩層關係保留，階高隨既有高差決定。beforeEightStepLayout及beforeRestLanding保留歷史來源，不作現況。

下梯底邊共用白磚原高度場，按1.25m格線與對角線交點分帶；渲染與通行共用底邊插值，讓整個12m寬度接上原縱坡。stair-layout.js保存此計算，connections.js依相同分帶繪製，第一組現為8＋平台＋8。歇腳平台及上段踏面以中央高度保持橫向水平，只有下段逐步接入白磚原縱坡；移除分帶內部重複側面以避免細紋。下層休息平台接回原兩層廣場，新增部分補實心接地基座；原樓板孔重建，避免空洞／舊梯殘留。

frontApron、舊大梯reclaimedFootprint以及延至高斯北牆的gapFootprint送入campus-plazas生成白磚，聯集後扣道路、建物、平台及新梯，避免疊片。外側鄰地用teaching-access-ground.js依原道路高度場、3m平順融合；不變動道路高程、建築基準或原始高程檔。重建：

```sh
python scripts/build-building-access.py
python scripts/build-teaching-courtyard.py
python scripts/build-campus-plazas.py
python scripts/build-pedestrian-patches.py
python scripts/build-sidewalk-plan.py
python scripts/build-motor-pavement-plan.py
python scripts/build-court-access.py
python scripts/build-road-regions.py
python scripts/build-r04-vegetation.py
```

驗證：tests/eight-step-access.py、eight-step-ground.mjs、eight-step-access-browser.py及既有photo-access／sidewalk-level、候車棚、道路與圓弧回歸。模型近似尺寸後續可調，使用者確認的第一組8＋平台＋8、上方8階及對齊／不占人行道、完整補平凹口要求須保留。
