# 籃球場地下停車層：最新S11出口

## 2026-11-17：S11東南角停車場出口、露出地下層東南外牆；接續Issue #78

使用者要求今後更新最新開發紀錄Issue，不再持續累加#9。本輪最新[Issue #78](https://github.com/c3xv05/NKNU-Campus-Simulator/issues/78)，#9只留歷史。後續先列出含nknu-dev-record標記的Issues（排除PR），以最新編號接續；新工作可建立新紀錄Issue，發布結果回寫該輪最新紀錄。AGENTS、新對話模板與網站開發者入口同步；網站依讀取到的最新標記Issue更新連結與送出／複製內容，無網路時本版保底#78。

籃球場下方停車場出口由原左下改東南（右下）角，朝S11=218881799，portalAcross=-146；仍4.8m寬、5.6m門洞，保留原3.6m地下層與球場高程。新線約25m，接路前4.5m留平順穿越段，人行道與路緣精確裁出新開口；舊出口白磚由完整道路人行道來源重建補回。白磚簡化後再次扣車道，防毫米級薄片伸回入口。beforeS11Relocation僅留舊線歷史，不作現況恢復。

移除籃球東側／南側接到球場頂面的土坡，改garage-ground接地面：牆邊2m近停車層地坪，外側沿共用三角面平順接原道路／白磚／地形；西南、東北轉角平順融回保留的西／北土坡，不能產生新斷層。停車場南牆與東側基牆／通風帶露出，移除會遮牆的球場土色裙邊，保留天花樓板及柱。原球場獨立步行出入口及東側原6階短梯保留，後續沿牆斜坡改直接向路邊的18階（模型配置），避免再遮住東側停車場外牆；新車道內側一根柱位往牆側退2m以保留完整通行淨寬。尺寸、出口線位與接地帶寬為模型近似，非測量；原始高程、道路坡度、四籃球場、網球、生科32階與其餘已確認／撤回決定保留。

來源basketball-parking/layout.json與entrance.json；build-garage-access→pedestrian-patches→sidewalk-plan→motor-pavement-plan→court-access→road-regions→r04-vegetation。渲染與通行同用sports-courts/access-surface，地形依footprints裁切，外牆由parking/renderer負責，不再用高土坡遮住。

驗證：`python tests/garage-s11-geometry.py`、`python tests/garage-s11-browser.py`（CAMPUS_TEST_URL可指定本機站）；另跑arrival-landscape、court-garage-grade與sidewalk-level回歸。

---
以下為舊版說明，舊左下入口已取代。

# 籃球場地下停車層

使用者確認球場下方一層停車地下室，入口在左下角朝南側道路；這取代原入口未定位狀態。layout.json保留層高3.6m等模型結構，entrance.json定義4.8m入口與路徑。入口寬度、坡長、柱位、格位均為模型配置非實測工程成果。

先有最新球場／道路資料與motor-pavement-plan，再執行build-garage-access.py定位南側路緣並生成campus.courtParking.entrance的三角面及地形裁切；接著重建人行道、motor-plan及court-access。入口不新增成平面馬路以免抬升地下層；access.js、surface.js供步行／騎車／渲染共用高度，接路端連完整入口寬度都取道路同一高度場。

南側人行道在入口切出開口；先保留4.5m接路前坪以供橫越，再下坡到地下層。擋土牆留門洞、球場裙邊避門洞、坡面支撐不重複建側牆；避免露空或閃爍。驗證arrival-landscape.mjs／geometry.py／browser.py。
