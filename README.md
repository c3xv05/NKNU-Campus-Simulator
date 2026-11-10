# NKNU 燕巢校園模擬器

靜態 Three.js 校園探索，手機搖桿移動、右側拖曳視角；點小地圖或按 M 展開校園圖。
大地圖可點建築或清單，顯示位置、探索狀態、直線距離及近似高差。

## 本機執行

```sh
python -m http.server 8000
```

開啟 http://localhost:8000/ 。Three.js 由 jsDelivr 載入；地形格網隨網站提供，遊戲中不需呼叫高程 API。
部署時需一併提供 `index.html`、`map.js`、`terrain.js` 與 `data/elevation.json`。

## 驗證

```sh
node tests/terrain.mjs
python tests/browser.py
```

瀏覽器測試需啟動上述伺服器，並安裝 Python Playwright 與 Chromium。
可用 `CHROMIUM_PATH` 指定瀏覽器；`THREE_MODULE_PATH` 可指定本地 Three.js 0.160.1
模組檔案，在測試時代替 CDN。測試的狀態讀取介面僅注入測試回應，不包含於正式頁面。

## 地形來源

見 [SOURCES.md](SOURCES.md)。資料為公開衛星高程近似重建，建築與運動場平台經簡化平整，
未宣稱為校園實測成果。以 `python scripts/sample-terrain.py` 可重取樣原始公開圖磚（需 Pillow）。
