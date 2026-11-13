# S23 南北向長條車棚

來源：使用者於 2026-11-11 確認 S23 無人行道，過道連接南北向長條型車棚。
沿既有 S23 末端向南配置，長 42m、寬 9m、淨高 3.2m、棚頂配色與柱距皆為模型近似，並非現場量測；未虛構車種、停車數量或停車格。

修改 `carport.json` 後依序執行：

```sh
python scripts/build-carports.py
python scripts/build-road-regions.py
```

第二步需 Shapely；網站執行不需 Python。配置同步至 campus.carports 與 pavedAreas，避免棚架、可通行地坪及地圖各存一套輪廓。兩端開放，中央通道無柱；支柱、橫樑以 InstancedMesh 合批。柱子阻擋人物／機車，棚內中央通道不設實體牆碰撞，西側新圍牆另由s24-sidegate/west-wall.json管理。

驗證：`node tests/carport.mjs`，以及 `python tests/map-mobile-browser.py`。

2026-11-13使用者更正：北端保持，總長向南擴為1.5倍（42→63m），增加21m；西側有圍牆並接大門西側。11跨支架為模型配置。重建車棚後重新build-motor-pavement-plan，確保新增區有完整鋪面。
