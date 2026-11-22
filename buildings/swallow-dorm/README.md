# 燕窩

修改 `building.json` 的 geometry／appearance 後，執行 `python scripts/build-building-catalog.py`。

第三學生宿舍施工單位公開專案及校方宿舍資料核對位置用途；窗組、色彩與外廊採保守近似，未當成測量結果。

來源：

- https://shinjou.com.tw/?act=project&ad_id=201909050018780&cmd=detail
- https://sso.nknu.edu.tw/Services/Web/Default.aspx?cMenuId=522&cWebIdx=595

可信程度：`provisional`；精確門位與尺寸待現場校正。

## 2026-11-22 平面圖外框與位置

依使用者提供的宿舍逃生動線圖（`source/dormitory-escape-plans.pdf` 第5–8頁）重描二至六樓外框為36頂點對稱輪廓（中央男舍塊、兩側廊翼、兩端旋轉約27°的女舍／男舍端棟；兩翼間缺口為花園）。比例取圖上4.0m房間模數（約0.0727m／像素），旋轉-8°與平移由正射影像擬合（`scripts/place-drawn-buildings.py`）。舊20頂點OSM輪廓保留為`beforeRelocationRing`，地形台地沿用`terrainRing`。

待補：一樓／地下一樓不同於二樓外框（地下一樓餐廳／K書中心延伸到花園下方）、七樓縮小、屋頂樓層、外觀與細節；樓層仍沿用原設定。
