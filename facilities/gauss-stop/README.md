# 高斯S05候車棚

使用者於2026-11-16確認：高斯門口面S05，過門口往南的人行道有遮陽／雨棚與等車長椅，棚南端有上車刷卡機。

`layout.json`保存模型尺寸與位置關係；執行`python scripts/build-building-catalog.py`會自動呼叫`node scripts/build-gauss-stop.mjs`，以高斯入口及S05路線生成`campus.gaussStop`。約21.3m棚長從入口南緣留1m開始，到S05立面與南牆轉角收尾，保留既有南側支路。若修改S05線形也需重跑生成。

寬3.2m、淨高3.05m、3張2.4m長椅、柱距及機器尺寸為模型近似，不是現場測量。長椅、立柱靠建築側，刷卡機在最南端靠路側，朝向人行通道。刷卡機為場景模型，不實作付費或驗票；建築入口為外觀模型，不代表開放室內。

`renderer.js`共用白磚實際高度供屋頂／柱腳／椅腳／機器及碰撞定位；屋頂完整在人行道上，不伸入馬路或建築，中間可通行。空中觀察時棚頂淡化便於檢視。

驗證：`node tests/gauss-stop.mjs`、`PYTHONPATH=<Shapely目錄> python tests/gauss-stop-geometry.py`、`python tests/gauss-stop-browser.py`（本機網站8127、Chromium及Playwright）。
