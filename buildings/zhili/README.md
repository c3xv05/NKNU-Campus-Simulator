# 致理大樓

修改 `building.json` 的 geometry 與 appearance 後，於專案根目錄執行 `python scripts/build-building-catalog.py`。

## 2026-11-17：外殼改依平面圖、北側路距貼近現實

- `source/floor-B1.pdf`～`floor-8F.pdf`：使用者提供的理學大樓（致理）B1～8F平面圖。圖面比例推定為1:250 A3縮印A4（B1車格2.5m、踏階約26cm、走廊約2.7m反推），主塔約49×63m、標準層每層約1,790m²。
- `plan.json`：使用者確認的平面判讀草稿（各層房號、房名、走廊、樓梯甲～庚、廁所、陽台、B1車位50格），座標為圖面公尺，`placement`可換算世界座標。房間外框由向量線稿自動分區後人工標註；201／203無隔間先合併、1F左上一間未標房名、層高、牆厚／門寬仍待確認。**室內尚未建構。**
- `geometry.ring`：四樓標準層外牆（22頂點）。東立面沿用原S05臨路立面線（frontEdge=0），北側依1F圖面路緣弧線與遊戲瀝青邊界最小平方套合，比沿用原南端再往北13.75m，殘差約±1m。使用者要求「與北側道路的距離貼近現實」。
- `geometry.beforeDrawingFootprint` 保存舊OSM／退縮輪廓；`terrainRing` 沿用舊輪廓讓地形墊底完全不變，`platformAnchor`／`platformOffset`及1F=高斯2F的樓層關係不變。
- 舊輪廓扣掉新外殼的範圍併入中央廣場下層（1F同高），即「中央廣場與連接處跟著延伸」；臨S05面為實心磚基座加矮牆，西側坡地高出約2.6～4.7m處為擋土牆，兩側均不可穿越、無懸空或縫隙。廣場上層L型、裙樓（1F階梯教室、2F屋頂廣場）、B1停車場與東南角車道入口依使用者指示留待日後處理。
- 便利商店兩組階梯固定在原致理frontEdge=1線段（building-access `compactAccess.frontLine`），不隨新外殼移動；中央廣場中央小樓梯依使用者要求移除（歷史存於 `removedCourtyardStairs`）。

外觀仍為原照片推定的磚紅外牆與構架；尺寸以圖面為準，位置為套合近似，非實測。
