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
# 2026-11-23 revision: the straight side (diameter) is parallel to the building's easternmost wall.
# Axis = the building's easternmost wall (ring (-143.129,-64.132) -> (-138.018,-79.864)); user 2026-11-23.
wa, we = (-143.129, -64.132), (-138.018, -79.864)
ux, uz = wa[0] - we[0], wa[1] - we[1]; L = math.hypot(ux, uz); ux, uz = ux / L, uz / L
if uz < 0: ux, uz = -ux, -uz                                          # north -> south
vx, vz = -uz, ux                                                      # perpendicular
if vx < 0: vx, vz = -vx, -vz                                          # points east, towards the building
N0 = (-179.0, -92.0)                                                  # earlier north end of the diameter
# 2026-11-23: slide the D east (along the perpendicular) until its straight WEST side (wrect from the diameter) passes through the
# building's westmost vertex, i.e. the straight side lines up with the building's left edge.
W = min(ring0 := rd('buildings/yongxu/building.json')['geometry']['ring'], key=lambda q: q[0])
wrect, gap = 6.5, 3.0
slide = wrect + ((W[0] - N0[0]) * vx + (W[1] - N0[1]) * vz)
N = (N0[0] + vx * slide, N0[1] + vz * slide)
def shape(D):
    P = lambda s, t: (N[0] + ux * s + vx * t, N[1] + uz * s + vz * t)
    c = P(D / 2, 0); disc = Point(*c).buffer(D / 2, quad_segs=24)
    half = Polygon([P(-1, 0), P(D + 1, 0), P(D + 1, D + 1), P(-1, D + 1)]) if False else Polygon([P(-D, 0), P(2 * D, 0), P(2 * D, D), P(-D, D)])
    east = Polygon([P(0, 0), P(D, 0), P(D, D), P(0, D)])
    east = Polygon([P(-1, 0), P(D + 1, 0), P(D + 1, D), P(-1, D)])
    disc = disc.intersection(Polygon([P(-1, 0), P(D + 1, 0), P(D + 1, D / 2 + 2), P(-1, D / 2 + 2)]))
    rect = Polygon([P(0, -wrect), P(D, -wrect), P(D, 0), P(0, 0)])
    return unary_union([disc, rect]), c
D = 26.0   # diameter; the user asked to lengthen it southwards toward the building (3 m) - see docs/next-chat.md: not reachable along the S06 axis without covering S21
plaza, center = shape(D); r = D / 2
# door apron: the part of the previous road that hugs the facade, kept so the door still meets paving
door = Point(ya['door'])
apron = Polygon(old['roadRing']).buffer(0).intersection(door.buffer(9)).intersection(B.buffer(6))
link = LineString([[center[0] + vx * (r - 2), center[1] + vz * (r - 2)], [ya['door'][0] - 4, ya['door'][1] + 2.5]]).buffer(2.0, cap_style=2)
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
sk['plaza'] = dict(center=[round(center[0], 3), round(center[1], 3)], radius=round(r, 3), diameter=round(D, 3), axisSouth=[round(ux, 4), round(uz, 4)], northEnd=list(N), straightWidth=wrect, facing='east')
sk['reference'] = sk['reference'].split('；2026-11-23詠絮前廣場')[0] + '；2026-11-23詠絮前廣場依使用者指示與2023正射影像重畫為朝東半圓廣場（西側接S21，圓弧面向建築）。'
(root / lp).write_text(json.dumps(ya, ensure_ascii=False, indent=2) + '\n'); (root / sp).write_text(json.dumps(sk, ensure_ascii=False, indent=2) + '\n')
print('plaza D', round(D, 2), 'axis', round(ux, 3), round(uz, 3), 'area', round(plaza.area), 'roadRing', round(ring.area), 'lawn', round(lawn.area), 'gap to building', round(B.distance(ring), 2), 'roadEnd', ya['roadEnd'])
