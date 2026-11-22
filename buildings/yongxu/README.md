# 詠絮樓

修改 `building.json` 的 geometry／appearance 後，執行 `python scripts/build-building-catalog.py`。

校方影藏歲月70期詠絮樓初貌：下部紅磚、上部淺色牆、外廊及欄杆。

來源：

- https://c.nknu.edu.tw/affair/Page.aspx?Kind=dbhp&PN=174&SN=150

可信程度：`historical-photo`；精確門位與尺寸待現場校正。

## 2026-11-22 平面圖外框與位置

依使用者提供的宿舍逃生動線圖（`source/dormitory-escape-plans.pdf` 第3、4頁，單位公分；L形兩翼各4292、翼寬1352）重描二至五樓外框為31頂點輪廓，內角斜邊（交誼廳）為主入口邊（`frontEdge`）。旋轉198°、平移由國土測繪中心2023正射影像擬合（`scripts/place-drawn-buildings.py`）。舊7角輪廓保留為`beforeRelocationRing`，地形台地沿用`terrainRing`（地形／道路高程資料未重算）。內側道路、草皮、S21延伸段依新外牆重配（`scripts/refit-yongxu-forecourt.py`）。

來源性質：外框為模型描圖，圖面尺寸與影像約差1成內；樓層（圖面為1–5層，模型仍6層19.2m）、外觀與細節待補。
