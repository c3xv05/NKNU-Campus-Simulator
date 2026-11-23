# 生科 B 館（生物教學大樓）

修改 `building.json` 的 geometry 與 appearance 後，於專案根目錄執行 `python scripts/build-building-catalog.py`。

使用者提供之照片；依牆色、構架、入口及招牌重建，尺寸為近似值。

## 2026-11-23：依平面圖重繪外框與兩棟連接處

- 來源：`source/floor-1.pdf`～`floor-3.pdf`（使用者提供；A＝生物科技館，B＝生物教學大樓，約9.40 pt／m）。圖面座標與判讀集中在 `scripts/biology_drawing.py`。
- 外框：1F向量圖描出的直角外框（略去冷氣窗台、A 1F北端戶外梯與小凸出），由 `python scripts/build-biology-layout.py` 放置；舊地圖草圖外框保留在 `beforeDrawingFootprint`（只作歷史）。地形台地改用新外框，platformAnchor 不變。
- 樓高：圖面1F +520→2F +970→3F +1370，故1F 4.5m、2F以上4.0m（`floorLevels`），5層共20.5m（三樓以上樓層數／高度沿用模型，未驗證）。二樓＝原S05 T平台高度（使用者指定為基準），因此 `platformOffset` −0.9m 讓1F下移。
- 名稱與說明依使用者確認對調：A＝生物科技館（生物科技系），B＝生物教學大樓（生命科學系）。
- 只有1F、2F與連接處相通（使用者確認）。室內、立面依照片細節尚未建置。
- 連接處說明見 `facilities/biology-link/README.md`。重建順序見 `facilities/campus-corridors/README.md` 最上方。
