# 致理／高斯連接處階梯

「便利商店」僅為溝通位置代稱，不建立店家、招牌或地圖標記。

2026-11-16使用者要求兩層各8階、縮小並對齊致理，補齊人行道。本筆取代舊40／24階，也不恢復PR58／59的七階、B1車道或下沉磁磚。

來源layout.json的compactAccess取致理frontEdge=1南端為定位原點；梯跑正面仍朝S05。兩組各8階／單梯跑，寬12m與4.5m沿用；梯深各3.2m、北端留0.15m、梯腳退入立面0.12m及上梯定位為模型近似，非實測。建築原基準與原兩層關係保留，階高隨既有高差決定。beforeEightStepLayout保留調整前40／24階來源供追蹤，不作現況。

下梯底邊共用白磚原高度場，按1.25m格線與對角線交點分帶；渲染與通行共用底邊插值，讓整個12m寬度接上原縱坡。stair-layout.js保存此計算，connections.js依相同分帶繪製，仍為八階。下層休息平台接回原兩層廣場，新增部分補實心接地基座；原樓板孔重建，避免空洞／舊梯殘留。

frontApron及舊大梯reclaimedFootprint送入campus-plazas生成白磚，聯集後扣道路、建物、平台及新梯，避免疊片。外側鄰地用teaching-access-ground.js依原道路高度場、3m平順融合；不變動道路高程、建築基準或原始高程檔。重建：

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

驗證：tests/eight-step-access.py、eight-step-ground.mjs、eight-step-access-browser.py及既有photo-access／sidewalk-level、候車棚、道路與圓弧回歸。模型近似尺寸後續可調，使用者確認的兩組八階與對齊／不占人行道要求須保留。
