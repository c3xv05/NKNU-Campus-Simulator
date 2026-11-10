# 校園位置與地形資料

## 建築、道路與校區輪廓

- OpenStreetMap contributors，ODbL 1.0。原模型保留既有 OSM 幾何；本次未改動建築位置。
  https://www.openstreetmap.org/copyright
- 高師大官方燕巢校區平面圖（核對校門、建築與道路相對位置，非高程來源）：
  https://w3.nknu.edu.tw/images/files/yt_01_map.pdf
- 模型局部座標：原點 WGS84 (120.407°E, 22.7865°N)，X 向東、Z 向南，
  每緯度 111195 公尺、每經度 111195 × cos(22.7865°) 公尺。
  以現有 OSM 道路 218881805 兩端點反算核對，局部座標四捨五入至 0.1 公尺。

## 本次實際採用的高程來源

2026-11-10 擷取 Mapzen Terrain Tiles on AWS，Terrarium 格式，zoom 14：

- https://s3.amazonaws.com/elevation-tiles-prod/terrarium/14/13671/7126.png
- https://s3.amazonaws.com/elevation-tiles-prod/terrarium/14/13672/7126.png
- 資料目錄：https://registry.opendata.aws/terrain-tiles/
- 格式：https://github.com/tilezen/joerd/blob/master/docs/formats.md
- 資料來源：https://github.com/tilezen/joerd/blob/master/docs/data-sources.md
- 標示與授權：https://github.com/tilezen/joerd/blob/master/docs/attribution.md
- SRTM terrain data courtesy of the U.S. Geological Survey.

Terrarium 以 R × 256 + G + B / 256 − 32768 解碼為公尺高程。
此地區採全球 SRTM 高程資料（約 30 公尺級）；zoom 14 圖磚像素約 8.8 公尺，
只是重取樣，不代表取得 8.8 公尺精度。衛星資料可能包含植被或建築表面影響，
也可能與今日整地不同。此版本不可視為校園實測高程。

`scripts/sample-terrain.py`（Python + Pillow）可重現 `data/elevation.json`：
將圖磚像素中心雙線性取樣至 20 公尺局部格網，保留兩位小數（非精度宣稱）。
遊戲將格網內插成 5 公尺網格，在建築、運動場、水面與球場輪廓內平整，外側
3–15 公尺平滑接回坡面；這些人工平台是可玩性近似，未取得竣工整地資料。
地面渲染與角色高度使用相同三角網內插，沒有垂直誇張。
道路以約 2 公尺間距貼合地面；建築加入地下基座，水面與操場保持平台。
校門高程作為遊戲局部 Y=0 基準；大地圖中的數字為衛星估計高程／近似高差。

## 已調查但未採用

- 內政部數值地形模型平台：https://dtm.moi.gov.tw/
  網站說明 20 公尺資料開放；目前 Swagger 的高程 API 參數仍要求服務認證碼。
  https://dtm-openapi.colife.org.tw/swagger/index.html
- 2025 年版 20 公尺 DTM 目錄：https://data.gov.tw/dataset/176927
  成功取得官方 CSV 目錄，但 TGOS 高雄市分幅 ZIP 的 HEAD 與 GET 請求皆回傳 HTTP 403，
  因此未把該資料冒稱為本模型的來源。日後取得可用官方 DTM 或測量點可替換此格網。

## 操作參考

政大學生作品 https://wenzhotw.github.io/nccu100/ 僅作左手搖桿、右手視角的操作參考。
搖桿、地圖及地形程式皆自行實作，未使用其程式碼、美術或地圖素材。
