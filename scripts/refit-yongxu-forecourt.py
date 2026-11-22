"""Re-fit the Yongxu forecourt (S21 end, inner road/apron, lawn) to the drawing-based footprint (2026-11-22).
Idempotent: originals are kept under satellite-sketch.json['beforeDrawingPlacement'] / layout.json['beforeDrawingPlacement'].
Run after place-drawn-buildings.py + build-building-catalog.py, then build-campus-plazas.py and the usual chain."""
import json, math
from pathlib import Path
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
root = Path(__file__).resolve().parents[1]
rd = lambda p: json.loads((root / p).read_text())
b = rd('buildings/yongxu/building.json')
ring, i = b['geometry']['ring'], b['appearance']['frontEdge']
B = Polygon(ring).buffer(0)
a, c = ring[i], ring[(i + 1) % len(ring)]
dx, dz = c[0] - a[0], c[1] - a[1]; L = math.hypot(dx, dz)
n = (dz / L, -dx / L)
if n[0] > 0: n = (-n[0], -n[1])  # outward = towards the open forecourt (west / south)
door = [(a[0] + c[0]) / 2 + 0.3 * n[0], (a[1] + c[1]) / 2 + 0.3 * n[1]]  # just outside the wall, inside the forecourt
roadEnd = [door[0] + 3.3 * n[0], door[1] + 3.3 * n[1]]
lp, sp = 'facilities/yongxu-access/layout.json', 'facilities/yongxu-access/satellite-sketch.json'
ya, sk = rd(lp), rd(sp)
ya.setdefault('beforeDrawingPlacement', {k: ya[k] for k in ('door', 'roadEnd', 'approachExtension')})
sk.setdefault('beforeDrawingPlacement', {k: sk[k] for k in ('roadRing', 'lawnRing')})
ext = ya['beforeDrawingPlacement']['approachExtension']
ya['door'] = [round(v, 6) for v in door]; ya['roadEnd'] = [round(v, 6) for v in roadEnd]
ya['approachExtension'] = ext[:2] + [[-161.2, -58.5], [-161.0, -72.0], ya['roadEnd']]
road_poly = LineString(ya['approachExtension']).buffer(ya['width'] / 2 + .2)
oldRoad = Polygon(sk['beforeDrawingPlacement']['roadRing']).buffer(0)
notch = B.convex_hull.difference(B)
newRoad = unary_union([oldRoad, B.buffer(4).intersection(notch)]).difference(B.buffer(.05)).buffer(.3).buffer(-.3)
newRoad = max(getattr(newRoad, 'geoms', [newRoad]), key=lambda g: g.area).simplify(.15)
lawn = Polygon(sk['beforeDrawingPlacement']['lawnRing']).buffer(0).difference(road_poly).difference(B.buffer(1))
lawn = max(getattr(lawn, 'geoms', [lawn]), key=lambda g: g.area).simplify(.1)
R = lambda g: [[round(x, 6), round(y, 6)] for x, y in list(g.exterior.coords)[:-1]]
sk['roadRing'] = R(newRoad); sk['lawnRing'] = R(lawn)
sk['reference'] = sk['reference'].split('；2026-11-22')[0] + '；2026-11-22詠絮樓依平面圖重描外框並重新定位：內側道路外圍保留，改接新外牆；S21延伸段、草皮避開新建物。'
(root / lp).write_text(json.dumps(ya, ensure_ascii=False, indent=2) + '\n')
(root / sp).write_text(json.dumps(sk, ensure_ascii=False, indent=2) + '\n')
print('door', ya['door'], 'roadEnd', ya['roadEnd'], 'road/bld dist', round(B.distance(LineString(ya['approachExtension'])), 2),
      'roadRing area', round(newRoad.area), 'lawn area', round(lawn.area))
# shared platform: keep the old range, add the new footprint + 4 m (not into motor roads)
cp = 'facilities/campus-plazas/layout.json'
L = rd(cp)
qa = next(x for x in L['levelAreas'] if x['id'] == 'restaurant-quarter')
cam = rd('data/campus.json')
motor = unary_union([LineString(r['line']).buffer(r['width'] / 2 + .3) for r in cam['roads'] if r['width'] >= 4])
old = Polygon(qa.setdefault('beforeYongxuDrawing', qa['ring']))
area = unary_union([old, B.buffer(4)]).difference(motor.difference(old))
area = max(getattr(area, 'geoms', [area]), key=lambda g: g.area); area = Polygon(area.exterior).simplify(.1)
qa['ring'] = [[round(x, 6), round(y, 6)] for x, y in list(area.exterior.coords)[:-1]]
(root / cp).write_text(json.dumps(L, ensure_ascii=False, indent=2) + '\n')
print('restaurant-quarter', round(old.area), '->', round(area.area))
