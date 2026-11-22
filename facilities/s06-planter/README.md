# S06 詠霽路東側花圃（人行道外移 100 cm）

使用者 2026-11-22 現場觀察：S06（293423729）從寰宇大樓T形平台往上到碰到 S21 為止，路邊有約 30 公分寬、內部只有草的花圃，所以人行道比原模型更遠離道路。

模型做法（尺寸為模型近似，非實測）：
- `layout.js`：里程 182.5 m（寰宇T橫段盡頭）起以 10 m 平滑漸進外移 100 cm，維持到 285 m（S21 路口瀝青內，S21 於 286.6 m 接入）；其後恢復原位。`setbackPair` 是唯一的外移來源。
- `site-physics.js` 的 `sidewalkSections(campus,network,band)`：`band='sidewalk'`（預設）人行道內緣依外移量往外推，寬度仍 3.6 m；`band='planter'` 回傳被讓出的路緣～人行道之間的條帶，用同一套瀝青／建築裁切，因此邊界與人行道、道路完全共邊。
- `surface.js`：純幾何。草面高度＝道路面＋ROAD_SURFACE_LIFT＋0.11 m（人行道高 0.15，路緣面露出約 4 cm）；`heightAt` 供行走（index.html 的 `planterAt`，與渲染共用同一高度函式），`footprints` 供 index.html 從地形裁掉。
- `renderer.js`：草面與靠道路側的水泥立緣。
- 周遭地形不改高度場：人行道外緣隨外移後，裁切邊界與路緣面（延伸到地面下 4 cm）照原方式貼合原連續高度場，沒有加階或開縫。
- 建置：`scripts/build-sidewalk-plan.py` → `scripts/build-motor-pavement-plan.py`（後者把花圃條帶排除在「路緣補瀝青」之外，並濾掉其旁的毫米級碎片）。修改範圍或寬度後須重跑這兩個腳本。
- 測試：`tests/s06-planter.mjs`。
