"""Move 詠絮樓 to its orthophoto position (user instruction 2026-11-22/23).

Fit: IoU of the user-sketch outline against the roof traced on the 2023 NLSC orthophoto: rotate +3.0 deg about the
building centroid, then shift [-10.0, -7.0] m (IoU 0.31 -> 0.75). Only the BUILDING moves: the forecourt asphalt and the
west lawn were already drawn where the real car park / garden are, so they stay and are clipped by the new footprint.
Idempotent: original values are kept as before* keys and always used as the source.
What follows the building: beforeSatelliteSketch, frontHint, yongxuAccess door, platform ring (via the swallow script).
What is re-routed: the S21 approach extension (it ran into the new footprint) and the P02/P03 ends; new link P07 to the door.
The pad anchor (platformAnchor) is NOT moved, so the shared platform height stays identical.
Run before build-building-catalog.py / build-campus-plazas.py (this script also runs relocate-swallow-quarter.py last).
"""
import json, runpy
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
g['ring'] = Tm(src)
sk = g.setdefault('beforeRelocationSatelliteSketch', g['beforeSatelliteSketch']); g['beforeSatelliteSketch'] = Tm(sk)
a = b['appearance']; a['frontHint'] = T(a.setdefault('beforeRelocationFrontHint', a['frontHint']))
note = '2026-11-23依國土測繪中心2023正射影像移動詠絮樓（繞重心轉3.0°、平移[-10,-7]m，吻合度0.31→0.75）；前庭瀝青與草皮原本就在真實停車場／花園位置，保留並扣除新輪廓；平台錨點與共同平台高度不變。'
b['relocation'] = note; a['reference'] = a['reference'].split('；2026-11-23')[0] + '；' + note
save(bp, b)
New = Polygon(g['ring'])

# --- user sketch: building ring follows, forecourt is clipped by the new footprint
sp = 'facilities/yongxu-access/satellite-sketch.json'; s = load(sp)
s.setdefault('beforeRelocationBuildingRing', s['buildingRing']); s['buildingRing'] = Tm(s['beforeRelocationBuildingRing'])
road0 = s.setdefault('beforeRelocationRoadRing', s['roadRing'])
clip = Polygon(road0).difference(New.buffer(.3))
clip = max(getattr(clip, 'geoms', [clip]), key=lambda q: q.area).simplify(.02)
s['roadRing'] = [[round(x, 6), round(z, 6)] for x, z in list(clip.exterior.coords)[:-1]]
save(sp, s)

# --- door + approach road: the old extension ran into the new footprint
ap = 'facilities/yongxu-access/layout.json'; y = load(ap)
for k in ('door', 'roadEnd', 'approachExtension'): y.setdefault('beforeRelocation_' + k, y[k])
y['door'] = T(y['beforeRelocation_door'])
y['approachExtension'] = [[-181.008312, -59.668693], [-169.410224, -55.673698]]   # clear of the new footprint (>=1.5 m beside the 7 m road)
y['roadEnd'] = y['approachExtension'][-1]
y['reference'] += '；2026-11-23詠絮樓依正射影像移動，入口道路延伸改到新建築西南側（離建築≥1.5m）停止，再由步道P07通往新門位。'
save(ap, y)

# --- walkways: P02/P03 end next to the new access, P07 leads to the door along the lawn's east strip
lp = 'facilities/campus-plazas/layout.json'; L = load(lp); links = {x['id']: x for x in L['pedestrianLinks']}
door = y['door']
links['P02']['relocatedEnd'] = [-163.8, -58.7]
links['P03']['relocatedEnd'] = [-169.410224, -55.673698]
links['P02']['line'] = links['P02']['line'][:-1] + [links['P02']['relocatedEnd']]   # swallow script re-derives it on every run
links['P03']['line'] = links['P03']['line'][:-1] + [links['P03']['relocatedEnd']]
p07 = {'id': 'P07', 'name': '詠絮樓入口步道', 'line': [[-169.410224, -55.673698], [-163.8, -58.7], [-161.6, -64.6], [round(door[0] - 1.4, 3), round(door[1], 3)]],
       'width': 3, 'cornerRadius': 2, 'reference': '2026-11-23詠絮樓移動後，從入口道路末端沿草皮東側白磚帶通往新門位；路線為模型近似。'}
if 'P07' in links: L['pedestrianLinks'] = [p07 if x['id'] == 'P07' else x for x in L['pedestrianLinks']]
else: L['pedestrianLinks'].append(p07)
save(lp, L)
print('詠絮樓 relocated; door', door, 'new ring', g['ring'])
# shared platform + P01..P04 are recomputed by the swallow script, which now also reads this building's ring
runpy.run_path(str(root / 'scripts/relocate-swallow-quarter.py'), run_name='__main__')
