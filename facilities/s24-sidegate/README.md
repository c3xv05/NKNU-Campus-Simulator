# S24 圍牆側門

使用者確認：過 S23 後的 S24 是圍牆邊側門。用途與人行道皆已確認：此段沒有人行道。

`gate.json` 控制位置、開口、短段圍牆方向及尺寸；修改後執行 `python scripts/build-sidegate.py`。沿既有支路末端放置開放門口與局部圍牆，開口 5.2m、牆高 1.6m 等為模型近似，非現場量測；門扇暫以向側邊收起示意。圍牆不等同先前取消的擋土牆，不延伸成未確認的整圈校界。

場景與地圖共用 `sidegateWalls` 輪廓；只有牆及門柱阻擋通行，中央開口保留。更改配置後重建相應截圖及 `node tests/sidewalk-upgrade.mjs`。

2026-11-13最新使用者要求：警衛室西南移貼牆與道路，保留10×7m量體並沿牆轉向。北側短牆reach改10.6m，南側仍9m、門口5.2m保留。新增west-wall.json從南側短牆接車棚西緣，再沿既有西校界近似路徑至大門西側圍牆端；這是本次已確認的西段，並非整圈校界或恢復先前取消的擋土牆。

west-wall.js的薄牆依實際分片地形逐公尺採樣，牆底埋入地面，地形不為牆額外抬升；渲染、碰撞、地圖與植栽避讓共用線形。驗證見tests/sidegate-west-wall.mjs、sidegate-west-wall-geometry.py與sidegate-west-wall-browser.py。
