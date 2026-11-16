# 中央廣場／S32 與生科雙層走廊

使用者 2026-11-16 現場補充為空間關係來源：廣場內不要斜面、補缺口，S32 東端須緩坡過渡；生科兩棟的一、二樓都有走廊，S05 接成 T 字。道路輪廓、原坡度、建築高程與樓層沿用原資料；線位、寬度、坡長、樓板厚度、柱與擋土牆均為模型近似，沒有新增實測高程或獨立立面圖資。

`layout.json` 是本次可編輯來源。`build-teaching-courtyard.py` 會自動執行 `build-campus-corridors.py`，生成 `campus.campusTransitions`、`bioConnection.corridor` 及廣場二樓平面連廊。舊 courtyard.ramp / accessRampRing 保留歷史資料；exteriorAccess 啟用後不再渲染、支撐或挖掉舊內部坡道。

- 廣場兩層各水平，樓層與原 L 型主步道、中央樓梯保留；新水平連廊和整個 3.6m 坡口都接上二樓。舊內坡開孔補回平面，移除沿建物邊的 1cm 緩衝縫。
- S32=495017564，接到其實際東端／S28 接點附近；坡道在廣場外，最後 6m 水平，入廣場前已達二樓基準。不是把 S32 或 S05 道路重新調坡。
- 生科上下兩層樓板、天花、頂棚與側柱取代舊實心連接量體。一樓在 S05 路面下，兩側擋土牆封住土體切口；牆面向內退 3cm，避免和既有階梯／坡道基座共面。兩端不封牆，東側原照片寬階梯、花台及門楣保留，縱向走線從其西側通過。
- S05=218881800，主支線接生科二樓。6m 通道／入口兩側各 2m 展寬是模型尺寸；起點從實際車道邊緣貼路，替換局部白磚成無階差坡口。支線在最早碰到二樓樓板之前 0.75m 已達平面高度；主坡中段近直線，兩端 0.75m 平順變坡，避免舊版在坡與樓板間垂直落差。

`surface.js` 將平滑高度場採樣成共用三角網，渲染與角色支撐共用 Float32 頂點與重心內插。坡道口按原道路高度接地，核心縱坡測得約 14.6% 以下（模型量，不是現場測量）；一、二樓依角色當前高度選層，不會從底下吸到上層。S05 入口側翼平順銜接原 15cm 白磚邊。`renderer.js` 做實體樓板、基座與擋土面；土體沿同一高度場在外側 3m 融合，保護車道、建築與樓梯，且不把一樓空間填到二樓。原致理階梯補磚的 gradeTeachingAccess 最後套用，避免廣場外緣的土體融合抬高高斯側舊補磚。

坡道先扣精確原車道包絡、建築、廣場／生科平面；白磚與舊步道再扣坡道／走廊，瀝青只刪其重疊補角。地形裁切使用簡單三角 footprint，不用細分渲染格網重複裁切。植栽避讓新通道，小地圖與展開地圖顯示新鋪面，中央廣場文字隱藏，建物及路號標籤保留。

高斯入口本來已設定 S05，但開發者全棟傳送忽略 entranceRoadIds。本次 `travel.js` 把候選點附道路 ID，依指定道路及入口立面中點挑安全車道落點並面向入口；五個原公開傳送不變。

重建（Shapely 2.1.2、Node）：

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
python scripts/build-building-catalog.py
```

局部改本資料可從 build-teaching-courtyard 開始。若改樓層／原樓梯仍須從 building-access 開始；不要回復歷史階梯或撤回的 S05 調坡。

驗證：

```sh
python tests/campus-corridors-geometry.py
node tests/campus-corridors.mjs
CAMPUS_TEST_URL=http://127.0.0.1:8131/ THREE_MODULE_PATH=/tmp/three.module.js python tests/campus-corridors-browser.py
```

瀏覽器檢查桌面及 390px 觸控 viewport：兩坡各三條走線雙向步行／騎車、兩層生科走廊、完整水平連廊、渲染射線、高斯 S05 落點、地圖標籤，以及地面／空中畫面；另跑原廣場、階梯／歇腳平台、路幅／圓弧、候車棚及和平回歸。瀏覽器 hook 只由測試攔截 HTML 注入，正式站不暴露測試控制。
