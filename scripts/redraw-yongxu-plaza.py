"""Redraw the 詠絮樓 forecourt as a semicircular plaza (user 2026-11-23, traced from the NLSC 2023 orthophoto).
Walking from S21 toward the building, the road reaches the west end of the building's S06-parallel side and opens into a
'D' shaped plaza: a short straight west part and a half disc whose arc faces east (towards the building).
Photo-traced model approximation (approx +-1.5 m): half disc centre [-179,-75], radius 13, plus a 6.5 m rectangle to its west (x>=-185.5, clear of the S21 mouth blend).
Idempotent; originals kept under satellite-sketch.json / layout.json ['beforePlazaRedraw']. Run after refit-yongxu-forecourt.py,
then build-campus-plazas -> ... (see docs/next-chat.md rebuild order)."""
import json, math
from pathlib import Path
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
root = Path(__file__).resolve().parents[1]
rd = lambda p: json.loads((root / p).read_text())
lp, sp = 'facilities/yongxu-access/layout.json', 'facilities/yongxu-access/satellite-sketch.json'
ya, sk = rd(lp), rd(sp)
B = Polygon(rd('buildings/yongxu/building.json')['geometry']['ring']).buffer(0)
ya.setdefault('beforePlazaRedraw', {k: ya[k] for k in ('roadEnd', 'approachExtension')})
sk.setdefault('beforePlazaRedraw', {k: sk[k] for k in ('roadRing', 'lawnRing')})
old = sk['beforePlazaRedraw']
cx, cz, r, west, half = -179.0, -75.0, 13.0, -185.5, 12.5
disc = Point(cx, cz).buffer(r, quad_segs=24).intersection(box(cx, cz - r - 1, cx + r + 1, cz + r + 1))
plaza = unary_union([disc, box(west, cz - half, cx, cz + half)])
# door apron: the part of the previous road that hugs the facade, kept so the door still meets paving
door = Point(ya['door'])
apron = Polygon(old['roadRing']).buffer(0).intersection(door.buffer(9)).intersection(B.buffer(6))
link = LineString([[cx + r - 2, cz - 1.5], [ya['door'][0] - 4, ya['door'][1] + 2.5]]).buffer(2.0, cap_style=2)
ring = unary_union([plaza, apron, link]).difference(B.buffer(.05)).buffer(.2).buffer(-.2)
ring = max(getattr(ring, 'geoms', [ring]), key=lambda g: g.area).simplify(.08)
# The S21 extension keeps the first two vertices of the former route and stops south of the plaza (its north kerb meets the plaza's
# south-west corner). Candidate tree points of the frozen landscape seed pass must not newly fall inside the road (tests/jiyuan-interior.mjs).
ya['approachExtension'] = ya['beforePlazaRedraw']['approachExtension'][:2] + [[-166.0, -60.0]]
ya['roadEnd'] = ya['approachExtension'][-1]
lawn = Polygon(old['lawnRing']).buffer(0).difference(ring.buffer(.5)).difference(B.buffer(1))
R = lambda g: [[round(x, 6), round(y, 6)] for x, y in list(g.exterior.coords)[:-1]]
sk['roadRing'] = R(ring)
if lawn.area > 15:
    lawn = max(getattr(lawn, 'geoms', [lawn]), key=lambda g: g.area).simplify(.1); sk['lawnRing'] = R(lawn)
else:
    sk['lawnRing'] = R(Point(-161.5, -72).buffer(.01))  # no lawn left; keep a degenerate ring out of the way
sk['plaza'] = dict(center=[cx, cz], radius=r, westEdge=west, halfWidth=half, facing='east')
sk['reference'] = sk['reference'].split('；2026-11-23詠絮前廣場')[0] + '；2026-11-23詠絮前廣場依使用者指示與2023正射影像重畫為朝東半圓廣場（西側接S21，圓弧面向建築）。'
(root / lp).write_text(json.dumps(ya, ensure_ascii=False, indent=2) + '\n'); (root / sp).write_text(json.dumps(sk, ensure_ascii=False, indent=2) + '\n')
print('plaza', round(plaza.area), 'roadRing', round(ring.area), 'lawn', round(lawn.area), 'gap to building', round(B.distance(ring), 2), 'roadEnd', ya['roadEnd'])
