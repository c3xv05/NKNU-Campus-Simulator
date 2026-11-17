# 籃球場西南路口局部降層

## 2026-11-17：籃球場西南路口降低半層，接續Issue #80

使用者確認其X約34.99／Y高度約13.67指籃球場西南側「向陽路×環手星月大道」交口，平面中心約[34.4,-136.6]，不是平面[34.99,13.67]。本輪最新紀錄[Issue #80](https://github.com/c3xv05/NKNU-Campus-Simulator/issues/80)，接續#78，#9仍只作歷史。

交口核心降低1.8m，依既有3.6m層高取半層；16m核心完整降1.8m，16–70m用端點一、二階導數為零的五次曲線平順接回原高度。核心與融合範圍是模型近似，非測量。此筆取代該路口原南端高程，不恢復撤回S05調坡；路線、路寬、路口圓弧、球場／建築平台與原始高程檔均保留。

來源facilities/southwest-junction/layout.json，build-local-junction-grade.py生成data/local-junction-grade.js。local-junction-grade.js提供共用修正，roads.js在既有高度網格後疊加同1.25m三角網上的修正；瀝青、白磚／15cm路緣、行走騎車與4m鄰側地形整平共用，建築與球場基準受保護。只對含三條指定道路的燕巢路網啟用，和平及合成路網不套用。修改來源跑python scripts/build-local-junction-grade.py；未改平面輪廓，不需重建整校鋪面或DEM。

與路口連動的籃球場南側人行道、球場接地帶及S11停車場出口接路高度會取新道路高度，地下停車層／球場水平面與出口位置不變。保留生科正交輪廓／T／小平台／32階、霽遠室內、候車棚、S05原坡度及其他撤回決定。

測試：node tests/junction-half-floor.mjs；CAMPUS_TEST_URL指定本機站後跑python tests/junction-half-floor-browser.py。來源重建後檢查核心1.8m、範圍外／S05不變、人行道15cm、三路雙向步行騎車，以及S11出口與球場接續。
