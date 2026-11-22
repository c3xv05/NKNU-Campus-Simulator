# 科技大樓

修改 `building.json` 的 geometry／appearance 後，執行 `python scripts/build-building-catalog.py`。

校方影藏歲月70期科技大樓照片：淺粉磁磚、橫向窗組、圓角樓梯塔；以原始幾何近似重建。

來源：

- https://c.nknu.edu.tw/affair/Page.aspx?Kind=dbhp&PN=174&SN=150

可信程度：`historical-photo`；精確門位與尺寸待現場校正。

## 2026-11-22 平面圖外框與位置

依使用者提供的工教大樓平面圖（`source/` 內B1、1F–5F、屋頂；圖幅A4、標示1/300，實際約0.1m／110dpi像素）以屋頂平面圖描出外框：中庭塊（含北端半圓梯間）、D形翼、扇形太陽能實驗室與旋梯、東南塊、西南長翼與兩端圓弧梯間，共88頂點。旋轉70°、平移由正射影像擬合（`scripts/place-drawn-buildings.py`），舊24頂點OSM輪廓保留為`beforeRelocationRing`，地形台地沿用`terrainRing`。

待補：各層不同外框、樓層數（圖面1–5層，模型6層21.6m）、外觀與細節。
