"""Move 詠絮樓 to its orthophoto position (user instruction 2026-11-22/23).

Fit: IoU of the user-sketch outline against the roof traced on the 2023 NLSC orthophoto: rotate +3.0 deg about the
building centroid, then shift [-10.0, -7.0] m (IoU 0.31 -> 0.75). Only the BUILDING moves: the forecourt asphalt and the
west lawn were already drawn where the real car park / garden are, so they stay and are clipped by the new footprint.
Idempotent: original values are kept as before* keys and always used as the source.
What follows the building: beforeSatelliteSketch, frontHint, yongxuAccess door, platform ring (via the swallow script).
What is re-routed: the S21 approach extension (it ran into the new footprint) and the P02/P03 ends.
The pad anchor (platformAnchor) is NOT moved, so the shared platform height stays identical.
Run before build-building-catalog.py / build-campus-plazas.py (this script also runs relocate-swallow-quarter.py last).
"""
import json, math, runpy
from pathlib import Path
from shapely.geometry import Polygon
from shapely.affinity import rotate, translate
root = Path(__file__).resolve().parents[1]
TH, SHIFT = 3.0, (-10.0, -7.0)
def load(p): return json.loads((root / p).read_text())
def save(p, o, indent=2): (root / p).write_text(json.dumps(o, ensure_ascii=False, indent=indent) + '\n')

bp = 'buildings/yongxu/building.json'; b = load(bp); g = b['geometry']
src = g.setdefault('beforeRelocationRing', g['ring'])
CEN = tuple(Polygon(src).centroid.coords[0])
def T(pt):
    q = translate(rotate(Polygon([pt, (pt[0] + 1e-9, pt[1]), (pt[0], pt[1] + 1e-9)]), TH, origin=CEN), *SHIFT)
    x, y = list(q.exterior.coords)[0]; return [round(x, 6), round(y, 6)]
Tm = lambda pts: [T(p) for p in pts]
ring0 = Tm(src)
# 2026-11-23 exterior from the floor plans (dormitory-plans.pdf p3/p4, cm): two 13.52 m wide arms, each 42.92 m on the outer side
# (24.57 m beyond the 18.35 m corner block), inner corner cut by the 6.45 m diagonal of the main entrance / lounge.
# Orientation and centroid follow the orthophoto-fitted ring0 (the plan is axis-aligned, ring0 is the placed L).
PW, PL, PC = 13.52, 42.92, ((13.52, 17.8), (18.35, 13.52))
plan = [(PL, 0), (0, 0), (0, PL), (PW, PL), PC[0], PC[1], (PL, PW)]          # A, B(outer corner), C, D, E, F, G = same order as before
a1 = math.atan2(ring0[0][1] - ring0[1][1], ring0[0][0] - ring0[1][0]); a2 = math.atan2(ring0[2][1] - ring0[1][1], ring0[2][0] - ring0[1][0])
mid = math.atan2(math.sin(a1 - math.pi / 2) + math.sin(a2), math.cos(a1 - math.pi / 2) + math.cos(a2))   # mean direction of arm 2 (arm 1 = arm 2 rotated +90 deg)
w2 = (math.cos(mid), math.sin(mid)); w1 = (-math.sin(mid), math.cos(mid))
raw = [(e * w1[0] + n * w2[0], e * w1[1] + n * w2[1]) for e, n in plan]
cr = Polygon(raw).centroid; c0 = Polygon(ring0).centroid
g['ring'] = [[round(x - cr.x + c0.x, 6), round(y - cr.y + c0.y, 6)] for x, y in raw]
sk = g.setdefault('beforeRelocationSatelliteSketch', g['beforeSatelliteSketch']); g['beforeSatelliteSketch'] = list(g['ring'])
a = b['appearance']; a.setdefault('beforeRelocationFrontHint', a['frontHint']); a['frontHint'] = [round((g['ring'][3][j] + g['ring'][4][j]) / 2, 6) for j in (0, 1)]
note = '2026-11-23依國土測繪中心2023正射影像移動詠絮樓（繞重心轉3.0°、平移[-10,-7]m，吻合度0.31→0.75）；前庭瀝青與草皮原本就在真實停車場／花園位置，保留並扣除新輪廓；平台錨點與共同平台高度不變。'
b['relocation'] = note; a['reference'] = a['reference'].split('；2026-11-23')[0] + '；' + note + '；2026-11-23外型改依平面圖（一至五樓）：兩翼寬13.52m、外側各長42.92m、內角為6.45m斜邊（大門／交誼廳），方位與位置沿用正射影像擬合。'
save(bp, b)
New = Polygon(g['ring'])

# --- user sketch: building ring follows, forecourt is clipped by the new footprint
sp = 'facilities/yongxu-access/satellite-sketch.json'; s = load(sp)
s.setdefault('beforeRelocationBuildingRing', s['buildingRing']); s['buildingRing'] = list(g['ring'])
road0 = s.setdefault('beforeRelocationRoadRing', s['roadRing'])
# The sketch brought the forecourt up to the north wing's inner wall ("空地向北補至北橫翼外牆"). The wall moved ~5 m north-west, so the
# strip between the old forecourt edge and the new wall is added; the cut along the new footprint is exact, so the wall edge stays shared.
A, B = (-153.2, -84.1), (-167.9, -87.9)      # old forecourt north edge (= old north wing inner wall)
C, D = tuple(g['ring'][5]), tuple(g['ring'][6])  # new north wing inner wall
road_all = Polygon(road0).union(Polygon([A, B, D, C]).buffer(0))
clip = road_all.difference(New)
clip = max(getattr(clip, 'geoms', [clip]), key=lambda q: q.area).simplify(.02)
s['roadRing'] = [[round(x, 6), round(z, 6)] for x, z in list(clip.exterior.coords)[:-1]]
save(sp, s)

# --- door + approach road: the old extension ran into the new footprint
ap = 'facilities/yongxu-access/layout.json'; y = load(ap)
for k in ('door', 'roadEnd', 'approachExtension'): y.setdefault('beforeRelocation_' + k, y[k])
y['door'] = [round((g['ring'][3][j] + g['ring'][4][j]) / 2, 6) for j in (0, 1)]   # middle of the inner wall facing the forecourt
from shapely.geometry import Point
_p, _q = (-169.410224, -55.673698), (-159.010, -56.040)                       # trim the last leg until the 7 m road is >=1.5 m from the new footprint
_t = max(i / 400 for i in range(401) if New.distance(Point(_p[0] + (_q[0] - _p[0]) * i / 400, _p[1] + (_q[1] - _p[1]) * i / 400)) >= 5.0)
y['approachExtension'] = [[-181.008312, -59.668693], list(_p), [round(_p[0] + (_q[0] - _p[0]) * _t, 6), round(_p[1] + (_q[1] - _p[1]) * _t, 6)]]
y['roadEnd'] = y['approachExtension'][-1]
y['reference'] += '；2026-11-23詠絮樓依正射影像移動，入口道路延伸改到新建築西南側（離建築≥1.5m）停止，再由步道P07通往新門位。'
save(ap, y)

# --- walkways: P02/P03 end next to the new access, P07 leads to the door along the lawn's east strip
lp = 'facilities/campus-plazas/layout.json'; L = load(lp); links = {x['id']: x for x in L['pedestrianLinks']}
door = y['door']
links['P02']['relocatedEnd'] = [-163.8, -58.7]
links['P03']['relocatedEnd'] = y['roadEnd']
links['P02']['line'] = links['P02']['line'][:-1] + [links['P02']['relocatedEnd']]   # swallow script re-derives it on every run
links['P03']['line'] = links['P03']['line'][:-1] + [links['P03']['relocatedEnd']]
L['pedestrianLinks'] = [x for x in L['pedestrianLinks'] if x['id'] != 'P07']   # earlier draft: forecourt asphalt already reaches the door
save(lp, L)
print('詠絮樓 relocated; door', door, 'new ring', g['ring'])
# shared platform + P01..P04 are recomputed by the swallow script, which now also reads this building's ring
runpy.run_path(str(root / 'scripts/relocate-swallow-quarter.py'), run_name='__main__')
