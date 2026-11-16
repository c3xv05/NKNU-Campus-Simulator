# 和平校區初版

和平入口：[/heping.html](../../heping.html)。燕巢入口仍為 `/index.html`，兩頁封面與遊戲內提供明確校區切換。切換會重建場景及重設位置／速度，和平探索進度使用獨立鍵 `nknu-heping-visited-v1`，不修改燕巢資料。燕巢原有探索進度僅在當頁記憶體，離頁依原行為重設；本次未改其儲存規則。

## 可核對來源

- 2026-11-16下載 [OpenStreetMap 地圖API](https://www.openstreetmap.org/api/0.6/map.json?bbox=120.3190,22.6228,120.3238,22.6282)，原始回應保存在 `source/osm.json`，© OpenStreetMap contributors，ODbL 1.0。
- [和平校界 way 113740778](https://www.openstreetmap.org/way/113740778)；包含19棟校內建築、道路／步道與10處運動／泳池區。[附中校界 179137001](https://www.openstreetmap.org/way/179137001)已扣除，附中建築／球場不冒充大學設施。
- [操場跑道 relation 8274064](https://www.openstreetmap.org/relation/8274064)保留外圈及內孔。
- 建築名稱、輪廓及OSM明載的層數是圖資記載，非現場確認或官方測繪。各棟 `buildings/<OSM id>/building.json` 保存來源網址與精度。

## 模型近似與待校正

目前為可遊走的圖資量體初版。未使用燕巢地形或將燕巢建築改名。沒有可靠細部高程，採共同水平基準 y=0；這不代表和平校區實際完全平坦。地面、道路、步道、球場共高，地面依鋪面邊界裁除。之後調高低必須同步鄰側地形及支撐，檢查接縫、懸空與斷層。

未記載層數暫作3層、層高3.6m；牆色、樓層線、道路5m／步道2.4m、綠地樹木位置是示意。尚未查證立面、門位、人行道側別／路緣、階梯、通廊、室內或停車格；不將OSM階梯直接宣稱為已可上下的樓梯。路線投影在初版共同地面，穿堂先保守封閉。泳池不可走入。傳送點是可通行的鄰近道路／步道位置，不宣稱實際大門。

後續建議先核對校方和平校區圖、主要入口與教育／行政／圖書館外觀，再依使用者現場回饋逐棟細修。校方 `hp_01_map.pdf`、`hp_map.pdf` 查詢均為404，未引用為已核實來源。

## 開發

修改各棟 JSON 或來源後：

```sh
python scripts/build-heping.py  # Shapely 2.1.2
node tests/heping.mjs
python tests/heping-geometry.py
python tests/heping-browser.py
```

`campus.json`為生成檔。生成器只寫和平資料，不重建燕巢鋪面。`heping-world.js`共用渲染水平高度與通行基準，步行／騎車採小步碰撞；`heping.js`重用avatar、scooter、開發者登入／紀錄／座標介面。開發者座標與草稿附 `campus: heping`，便於後續定位。主頁切換器為獨立小模組，不導入和平場景或圖資。
