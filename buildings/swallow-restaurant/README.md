# 歸燕食巢

修改 `building.json` 的 geometry 與 appearance 後，於專案根目錄執行 `python scripts/build-building-catalog.py`。

使用者提供之照片；依牆色、構架、入口及招牌重建，尺寸為近似值。

## 平面圖外型（2026-11-23）

`source/floor-B1.pdf`、`floor-1F…4F.pdf` 為使用者提供的向量 CAD 平面圖。主體 57.6×20.6m（A–C軸 7+13m 加牆厚）；D軸外另有拱廊／陽台及約13m寬門廊、核心突出約3m，**尚未建模**（renderer 僅單一輪廓）。目前外型為主體矩形，位置依正射影像，由 `scripts/relocate-swallow-quarter.py` 產生。
