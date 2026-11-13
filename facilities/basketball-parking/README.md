# 籃球場地下停車層

使用者確認球場下方一層停車地下室，入口在右下角朝南側道路；這取代原入口未定位狀態。layout.json保留層高3.6m等模型結構，entrance.json定義4.8m入口與路徑。入口寬度、坡長、柱位、格位均為模型配置非實測工程成果。

先有最新球場／道路資料與motor-pavement-plan，再執行build-garage-access.py定位南側路緣並生成campus.courtParking.entrance的三角面及地形裁切；接著重建人行道、motor-plan及court-access。入口不新增成平面馬路以免抬升地下層；access.js、surface.js供步行／騎車／渲染共用高度，接路端連完整入口寬度都取道路同一高度場。

南側人行道在入口切出開口；先保留10m接路前坪以供橫越，再下坡到地下層。擋土牆留門洞、球場裙邊避門洞、坡面支撐不重複建側牆；避免露空或閃爍。驗證access-corrections.mjs／access-corrections-browser.py，並保留arrival-landscape回歸。
