# NKNU 燕巢校園模擬器

靜態 Three.js 校園探索，手機搖桿移動、右側拖曳視角；點小地圖或按 M 展開校園圖。
大地圖可點建築或清單，顯示位置、探索狀態、直線距離及近似高差。

## 本機執行

```sh
python -m http.server 8000
```

開啟 http://localhost:8000/ 。Three.js 由 jsDelivr 載入；地形格網隨網站提供，遊戲中不需呼叫高程 API。
部署時需一併提供 `index.html`、`map.js`、`terrain.js`、`zones.js`、`zones.html`、`roads.js`、`road-renderer.js`、`road-ground.js` 與 `data/` 內的 JSON 檔案。

## 驗證

```sh
node tests/terrain.mjs
node tests/zones.mjs
node tests/roads.mjs
python tests/browser.py
python tests/zones-browser.py
python tests/road-browser.py
```

瀏覽器測試需啟動上述伺服器，並安裝 Python Playwright 與 Chromium。
可用 `CHROMIUM_PATH` 指定瀏覽器；`THREE_MODULE_PATH` 可指定本地 Three.js 0.160.1
模組檔案，在測試時代替 CDN。測試的狀態讀取介面僅注入測試回應，不包含於正式頁面。

## 地形來源

見 [SOURCES.md](SOURCES.md)。資料為公開衛星高程近似重建，建築與運動場平台經簡化平整，
未宣稱為校園實測成果。以 `python scripts/sample-terrain.py` 可重取樣原始公開圖磚（需 Pillow）。

## 植被分區回饋

`zones.html` 提供不必啟動 3D 的分區圖，A 靠校門、D 靠科技大樓，共 12 區。
遊戲大地圖也能切換「植被分區」。所有植被初始皆為待確認，分區底色只供定位。
使用者可填寫分類與備註，草稿僅存於瀏覽器 localStorage；需複製文字貼回對話，
不會自動傳送或套用到模擬器。植被分區功能本身不會改動地形。

## 道路整平與標線

道路沿共享路網平滑縱坡，橫向維持平整，路口共用高程；路肩以近似挖填方接回地形。
地面三角形依道路範圍裁切，避免草地穿出路面；角色使用鋪面高程行走。
保留山坡走勢，並非把全校道路改成水平。原始衛星高程格網未改寫，實際道路坡度仍待實地校正。

鋪面及標線為自行繪製的台灣道路示意樣式。依 OSM 單行及步道資訊，分別使用
白色單行箭頭、雙黃線、白色邊線與不同步道鋪面；現場標線位置並未逐條測繪。
