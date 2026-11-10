# 獨立建築定義

各棟 `building.json` 為編輯來源；修改後執行 `python scripts/build-building-catalog.py`，同步校園空間索引與單份外觀索引，避免執行時逐棟下載。

`geometry` 存平面輪廓、樓高、樓層、介紹；`appearance` 存外觀類型、色彩、窗組、正面與研究依據。
`frontMode: main-road` 依外牆朝向及主要道路選取單一入口面。若需精確校正，可填 `frontEdge` 為 ring 中起點的索引值，指定該邊。
`showEntrance: false` 取消入口與招牌（未核對的附屬設施採此設定）。各棟來源及不確定部分見 `docs/research/buildings.md`。

連接多棟的基座、平台與樓梯屬共同場地配置，位於 `data/campus.json` 的 `levelLink`、`courtyard`、`bioConnection`；渲染及通行在 `connections.js`。
校門車道與花圃屬道路配置，不能用建築模型代替道路高程修正。
