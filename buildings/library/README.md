# 圖資大樓

修改 `building.json` 的 geometry／appearance 後，執行 `python scripts/build-building-catalog.py`。

校方圖資大樓工程資料：地上2層、地下1層；行政工作報告記載0與1的外牆設計。

來源：

- https://c.nknu.edu.tw/affair/fckeditor/ckfinder/userfiles/maintain/files/%E5%BB%BA%E7%AF%89%E5%B7%A5%E7%A8%8B.pdf
- https://fm.nknu.edu.tw/up/105-4%E8%A1%8C%E6%94%BF%E6%9C%83%E8%AD%B0%E5%B7%A5%E4%BD%9C%E5%A0%B1%E5%91%8A.pdf
- 使用者2026-11-25上傳之一層、二層平面圖：`source/floor-1F.pdf`、`source/floor-2F.pdf`

## 2026-11-25：依平面圖重建（可走的 B1／1F、西側扇形廣場）

使用者確認（2026-11-25）：
- **樓層**：圖面「一層」＝遊戲 **B1**、圖面「二層」＝遊戲 **1F**（入口層），上面沒有其他樓層（＝官方「地上2層、地下1層」的另一種讀法：西側埋在坡裡）。層高 4.5m（預設）。
- **入口**：1F（圖面2F）大廳 218 從西側廣場 204 進出，比 S04 低，要下階梯。
- **扇形區**：201＝花圃；202＝樓梯（往外上到 S04）；203＝平台，接 204 處有較短的小階梯；204＝平台（圖面1F 125 的屋頂）；125＝半戶外；G／H 梯照圖（1F 圖：從扇形兩角的 1F 地面往外上升，有折斷線、上段虛線）。
- **ㄇ字薄牆**：穿過 204 的大圓弧是一道薄牆，兩端（圖上實線段）落地，中段（虛線）是上方橫樑，底下挑空可通過。
- 其餘照預設：2F 中央矩形、216、圓形中庭兩塊為挑空；中央水池有水面；129 為戶外鋪面；E／F 梯照圖；停車格只畫標線；房間只標編號（不標名稱）；空房間、門開啟、家具不做；外觀先依圖面窗位、屋頂太陽能板與「0／1」外牆圖案未做。

### 檔案與流程

- `scripts/library_drawing.py`：圖面框架與定位。圖面公尺＝1F 圖頁座標 × S（S＝8m／112.8pt，柱距8m，約1:200 A1）；2F 圖頁＝1F 平移 (68.09, 37.06)pt（72 根柱位重合誤差 <0.25pt）。依 NLSC 2023 正射影像（中央圓頂中心＋南翼方向；扇形廣場邊緣核對）定位：旋轉 2.0°、平移 (-16.661, -143.445)。屋頂（含屋簷、空拍傾斜）比牆線略大，屬正常。
- `scripts/extract-library-walls.py`：沿用致理的向量雙線配對、門弧偵測（`scripts/extract-zhili-walls.py` 的函式），柱子由 300dpi 圖面實心塊取得。
- `scripts/build-library-interior.py`：產生 `interior.json`（世界座標棱柱＋行走面，高度相對 B1 地面）並更新 `building.json`（ring＝新外框、`beforeRelocationRing`＝舊 OSM 外框、`terrainRing`／`platformAnchor`／`platformOffset`＝新地台，使地台高度＝B1 地面）。高度以 `scripts/library-heights.mjs` 量 S04 人行道：B1＝人行道 −5.8m（4.5m 層高＋203 平台 0.3m＋202 約 1.0m），目前 B1 約 10.58、1F 約 15.08、S04 人行道約 16.38。
- 執行端：`buildings/library/interior.js`（`addLibraryInterior` 渲染、`createLibrarySurface` 支撐／碰撞），透過 `buildings/zhili/interior.js` 的 `planSurfaces` 接入移動與 `site-physics`；`buildings/renderer.js` 以 `interiorKind: 'library'` 取代通用外殼；`index.html` 以 `site.cuts`（凸三角形，road-ground.js 只能減凸多邊形）挖除地形與步道。
- 房號：`labels.json`（OCR 讀圖面編號框，誤讀已依圖面人工更正）。
- 檢視圖：`review/plan-review.png`（左 1F、右 2F；紅＝牆、綠＝外框／門、藍＝挑空、紫＝樓梯）。
- 重建：`python scripts/build-library-interior.py` → `python scripts/build-building-catalog.py`；測試 `node tests/library-interior.mjs`。

### 模型判讀（近似處）

- 牆：雙線配對（直牆）＋細帶閉運算（弧牆），外牆另以外框內 0.3m 帶生成，直段為帶狀窗（窗台0.9、窗頂3.4）、大廳西側玻璃、1F 東側弧形玻璃、2F 220 外弧玻璃為落地玻璃。
- 樓梯：A（南翼挑空內）、B（東南角）、D（北棟西側，梯間封牆、B1 由第一跑開門、1F 由第二跑開門）為兩跑折返；C 為帝王式（中央一跑由西往東上到中庭旁平台，再分南北兩跑折回大廳弧牆）；G／H 為扇形兩側直梯（1F 地面→S04 側）；F 為東側戶外梯（1F 門→B1 地面）；E 為北側沿牆直梯（終點高度圖面不明，暫做到接近 1F 高度）。
- 扇形：圓心 (46.9, 86.75)、外緣 R37.35；202 六級（每級徑向約 1.75m），201 花圃隨 202 逐階抬高 0.45m；204 西緣為排水溝蓋；扇形外緣到 S04 人行道間補一圈坡面鋪面（空拍上的弧形步道），G／H 梯頂接在其上。
- ㄇ字牆：圓心 (-11.23, 76.74)、R46.23–46.55，角度 -3.4°～8.6° 與 35.2°～41.65° 為落地牆腳，中段為 1F＋3.2m 以上的橫樑。
- 待確認／未做：E 梯上端去向；廁所器具（目前器具的雙線部分被判為小牆塊或忽略）；北側停車場的實際範圍（目前只畫 17–23 號一帶）；1F SW 角外側往上的坡道／階梯（102 外）；屋頂太陽能板、外牆 0／1 圖案；門扇樣式（目前全開）。
