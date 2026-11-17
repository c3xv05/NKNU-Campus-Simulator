# 廣場下層入口與生科 T 通廊（最新更正）

使用者 2026-11-16 最新更正取代 PR73：**撤回中央廣場內部補平，S32 接下層，L 要直角，便利商店上方與寰宇／致理角落長邊平行 S05。生科通廊由 B 北側細長翼等寬延伸至 A，上層沒有棚頂；T 支線加倍並置中，向陽路樓梯接下層且為矩形。**

樓層、道路原坡度與兩棟生科輪廓沿用原資料。位置關係為使用者確認，寬度、坡長、結構與淨距仍為模型近似，未取得新的實測高程／完整室內圖。beforeAlignmentCorrection、beforeRightAngleUpperPlan 與 beforeBiologyLowerRectangle 僅保存已取代的舊版來源，不能當現況恢復。

## 廣場

- `facilities/teaching-courtyard/layout.json` 的 alignment 以 S05=218881800 鄰接直線段（near 指定點）推導共同正交軸；建築外殼不動。寰宇側內邊及便利商店上方長邊平行 S05，致理側前緣垂直於此軸，轉角恰為90°。寰宇／致理外角改成同軸直角接續。
- 撤回 PR73 的斜向二樓連廊與整片廣場土體拉平，恢復內部下層坡口。既有上下兩層樓板基準（約39.045／42.645m）、中央樓梯與寰宇穿堂保留。
- S32=495017564 從東端[-124,-147.5]附近沿既有步道742398750通道降至**下層**，終點取靠近[-132,-190]的步道位置。走線按寰宇外牆留0.8m模型淨距局部向東避讓；保留原道路資料，替換該段舊步道渲染，不留高低不同的殘面，沒有獨立疊加舊坡。坡面、土體與角色共用高度場，末端水平接下層；不再接二樓。
- 地形只修新坡與輪廓變更的鄰地，不對廣場內部作全面高度覆寫。S32外側3m另外使用共用土坡三角面，外緣依原4m地形對角線銜接、內緣貼坡；土體裁切封口避開坡道／建物共面，渲染與步行共用高度，不只以立面遮洞。terrain.js、原始高程與 S05 道路基準不變；gradeTeachingAccess 最後套用，保護前次已完成的便利商店階梯補磚。

## 生科

- `layout.json / biology / northEndVertices=[5,7]` 取 B 北端輪廓，寬約7.071m，沿其法線等寬延伸到 A。T 支線的 joint 是 A/B 接觸點之間的中點，方向垂直通廊；支線寬12m，明確為前次6m的兩倍。
- 上層露天：沒有上層遮雨棚，也沒有高出上層的棚柱。原入口門楣／標示改在下層，最高不越過二樓樓面；一樓有上層樓板天花、必要側柱與擋土面。
- `scripts/biology_layout.py` 同時供 building-access 及 campus-corridors 生成使用，確保重建不會回到舊28/14m梯形。向陽路樓梯 topLevel=biology-lower，接約30.400m下層，而不是約34.000m上層。固定寬度約20.285m由兩翼間隙與0.25m模型淨距推得，上下等寬、四角直角，避免碰撞建築；保留96階／四梯跑及三休息平台的既有模型配置。
- 樓梯口避開側柱與擋土牆；第一層通廊可直接走上東梯。梯腳逐帶使用 S01 原路面高度，原花台依實際踏面落地。矩形梯腳與斜交的 S01 之間另補貼地鋪面；這是地面接縫，沒有把樓梯改回梯形。
- S05 支線仍接上層。入口逐個橫向 station 從精確車道邊取高度，再平順過渡到上層，整段12m都置中；兩側原各2m展寬只是銜接白磚側翼。S05與S01車道、寬度、坡度不動。

## 共用幾何及重建

`surface.js` 的 Float32 三角網與重心內插供渲染／行走共用，依目前高度選層。細網格只用於坡面；裁地形仍用粗三角 footprint，保留載入優化。舊白磚、步道、瀝青補角及植栽避讓新設施；白磚輪廓簡化後再扣一次精確坡口，避免微小重疊。上下層、樓梯、坡道與鄰地各有連續的支撐面，不以新增重疊面遮住孔洞。

步行時樓梯優先於下方樓板取得支撐，避免還原下層後中央樓梯或便利商店小梯被平面搶走高度；騎車仍不使用階梯支撐。高斯傳送修正與地圖隱藏中央廣場文字保留。所有原建築、S05坡度、教學大梯8＋平台＋8／上梯8、候車棚、路口圓弧、地下車道及和平校區保持。

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

build-teaching-courtyard 自動呼叫 build-campus-corridors；只改本資料可從前者開始，改原階梯來源時由 building-access 開始。這些生成器共享生科推導，不需手動修改 campus.json。

```sh
python tests/campus-corridors-geometry.py
node tests/campus-corridors.mjs
CAMPUS_TEST_URL=http://127.0.0.1:8132/ THREE_MODULE_PATH=/tmp/three.module.js python tests/campus-corridors-browser.py
```

檢查實際邊線平行／直角、下層入口、B端同寬、支線12m／置中／垂直、露天上層、矩形下層樓梯及鋪面不重疊。瀏覽器在桌面及390px觸控 viewport 測坡道三走線雙向步行／騎車、上下兩層、完整 L、樓梯全寬／轉入下層、渲染射線、相機與地圖；測試 hook 只由測試攔截 HTML 注入。

## 2026-11-17：生科雙棟南移，T支線垂直S05

依使用者最新更正，生科A／B整體沿世界南向（+Z）移14.723923m，兩棟各頂點X、輪廓、相對位置與樓層不變。中央通廊中點與致理／高斯levelLink中點沿S05法線對齊；T支線保持12m與置中，改垂直S05共同軸，而非沿生科原通廊法線。這筆取代前輪「生科建築不動、支線垂直通廊」；其餘撤回決定維持。距離為現有模型推導，非實測。

來源buildings/bio-a、bio-b/building.json保留beforeSouthAlignment及原platformAnchor，避免平移導致樓層高程漂移。campus-corridors/layout.json的southAlignment記錄偏移、對齊目標及道路軸；build-campus-corridors依該軸推導坡口方向，向陽路東梯／梯腳鋪面跟隨新接點重建，保留矩形下層樓梯、露天上層與B端等寬通廊。原共用地形融合依新建物基座、通廊及坡口重新計算；白磚、車道裁切、植栽避讓同步重建，原始高程與道路坡度不動。

重建時白磚差集出現零面積LineString，build-sidewalk-plan僅接收Polygon以消除無面積邊線，不刪除有效鋪面。依campus-corridors/README既有生成鏈重建。
