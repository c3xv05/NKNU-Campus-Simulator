"""Compile the 圖資大樓 floor plans (user upload 2026-11-25) into a walkable two-level building.

Sources: buildings/library/source/floor-1F.pdf / floor-2F.pdf, read by scripts/library_drawing.py (frame, scale,
orthophoto placement) and scripts/extract-library-walls.py (wall pairs, door swings, columns).
User answers 2026-11-25:
  - drawing 1F = game B1 (level 0 here), drawing 2F = game 1F (+4.5 m); nothing above; 4.5 m storeys.
  - 2F (game 1F) is the entrance level from the west plaza 204, lower than S04: 202 = steps up to S04,
    201 = flower beds, 203 = platform with short steps down to 204, 204 = plaza deck over the half-open 125.
  - G/H stairs run from the 1F ground at the fan corners up to the S04 side (1F sheet: break line + dashed top).
  - The big arc through 204 is a thin ㄇ-shaped wall: both ends stand on the ground, the dashed middle is a beam
    over an opening people walk through.
  - 2F voids (central rectangle, 216, atrium halves) open to 1F; pool 128 has water; 129 is outdoor paving.
  - E/F stairs as drawn, parking only painted, room numbers only (no names), empty rooms, doors open.
Output: buildings/library/interior.json (world coordinates; heights relative to data.base = B1 floor).
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np, cv2
from shapely.geometry import Polygon, MultiPolygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity
from shapely import constrained_delaunay_triangles

sys.path.insert(0, str(Path(__file__).resolve().parent))
import library_drawing as LD
import importlib.util
spec = importlib.util.spec_from_file_location('xlw', Path(__file__).resolve().parent / 'extract-library-walls.py')
XLW = importlib.util.module_from_spec(spec); spec.loader.exec_module(XLW)
ZW = XLW.ZW

root = LD.ROOT
B = root / 'buildings/library'
H = 4.5                     # storey height (user: default 4.5 m)
LEVEL = {'1F': 0.0, '2F': H}
LABEL = {'1F': 'B1', '2F': '1F'}   # game labels
SLAB = .3
C = .025                    # raster cell (m)
X0, Y0, X1, Y1 = 0.0, 38.0, 95.0, 142.0
NW, NH = int((X1 - X0) / C), int((Y1 - Y0) / C)

# ------------------------------------------------------------------ measured geometry (drawing metres)
NORTH_BLOCK = box(38.69, 47.82, 85.69, 80.80)
ATRIUM_C = (64.06, 89.3)
FAN_C = (46.9, 86.75)
# 2F voids: atrium halves either side of the bridge, central wing rectangle (minus the A-stair head / 210), 216.
LEFT_VOID = Polygon([(58.4, 77.9), (56.0, 79.0), (54.25, 80.25), (52.8, 81.8), (51.75, 83.5), (51.0, 86), (50.5, 88.5), (50.4, 91.25),
                     (50.6, 93.3), (51.1, 95.25), (52.3, 97.2), (54.6, 99.25), (56.3, 100.2), (58.0, 100.6), (60.8, 101.0), (63.5, 101.25)])
RIGHT_VOID = Polygon([(61.0, 77.4), (63.5, 77.3), (66.3, 78.6), (68.5, 79.6), (70.2, 80.3), (74.2, 80.3), (75.6, 83.5), (76.6, 87.0),
                      (76.7, 90.0), (76.2, 93.0), (75.0, 96.3), (73.0, 99.2), (70.3, 101.8), (65.4, 101.2)])
WING_VOID = Polygon([(42.34, 100.4), (64.03, 108.08), (58.69, 123.16), (37.0, 115.48)]).difference(
    Polygon([(48.3, 101.6), (57.2, 104.9), (56.0, 108.0), (47.6, 105.2)]))
U = (math.cos(math.radians(109.47)), math.sin(math.radians(109.47)))   # wing long axis (west facade direction)
def _inward(p, d): return (p[0] + U[1] * -d, p[1] - U[0] * -d)
V216 = Polygon([(73.31, 102.89), (79.6, 105.0), (72.2, 127.3), (65.3, 125.5)])
VOIDS_2F = unary_union([LEFT_VOID, RIGHT_VOID, WING_VOID, V216])
BRIDGE = Polygon([(58.4, 77.9), (61.0, 77.4), (65.4, 101.2), (63.5, 101.25)])
# 1F: everything east of the 1F glass arc (= right-void edge) between the north block and the wing is outdoor 129.
EAST_OUT_1F = Polygon([(74.2, 80.81), (95, 80.81), (95, 107.4), (81.5, 105.6), (73.31, 102.6), (70.3, 101.8), (73.0, 99.2), (75.0, 96.3),
                       (76.2, 93.0), (76.7, 90.0), (76.6, 87.0), (75.6, 83.5)])
VESTIBULE_152 = box(65.6, 45.9, 68.9, 47.9)
WEST_CUT = Polygon([(0, 40), (38.75, 40), (38.75, 80.5), (37.0, 89.8), (34.3, 97.8), (0, 112)])
EAST_STAIR_CUT = box(86.0, 40, 100, 80)

# Stairs (all B1 -> 1F, rise 4.5). Switchbacks: start corner, long axis u, width axis w (unit vectors), length, width.
def switchback(o, u, w, L, Wd, per=13, landing=1.5, name=''):
    """Two flights: up along u on the first half-width, landing at the far end, back along -u on the second half."""
    run = (L - landing) / per; h = H / (2 * per); out = []
    P = lambda a, b: [o[0] + u[0] * a + w[0] * b, o[1] + u[1] * a + w[1] * b]
    quad = lambda a0, a1, b0, b1: [P(a0, b0), P(a1, b0), P(a1, b1), P(a0, b1)]
    for i in range(per): out.append({'q': quad(i * run, (i + 1) * run, 0, Wd / 2), 'h': round((i + 1) * h, 4)})
    out.append({'q': quad(L - landing, L, 0, Wd), 'h': round(per * h, 4)})
    for i in range(per): out.append({'q': quad(L - landing - (i + 1) * run, L - landing - i * run, Wd / 2, Wd), 'h': round((per + 1 + i) * h, 4)})
    return {'id': name, 'treads': out, 'foot': quad(0, L, 0, Wd), 'divider': quad(0, L - landing, Wd / 2 - .07, Wd / 2 + .07),
            'hole': quad(0, L, 0, Wd), 'top': quad(-.05, -1.2, Wd / 2 + .05, Wd - .05), 'start': quad(-.05, -1.2, .05, Wd / 2 - .05)}

N = (U[1] * -1, U[0])   # not used directly
WU = (-U[0], -U[1])     # wing axis pointing north (up the west facade)
WW = (math.cos(math.radians(19.47)), math.sin(math.radians(19.47)))   # across the wing (west -> east)
STAIRS = [
    # D 安全梯 (north block 132/222, x 39.5–42.6, y 65–70): from the lobby on the south, up north on the east half, back south.
    switchback((42.6, 70.0), (0, -1), (-1, 0), 5.0, 3.1, per=13, landing=1.4, name='D'),
    # A 樓梯 (108/209, in the wing void): starts at the north end (hatched start) on the west half, rises south.
    switchback((49.75, 102.55), U, WW, 6.6, 2.7, name='A'),
    # B 安全梯 (115/215, south-east corner): starts at the north end west half, rises south.
    switchback((67.75, 129.25), U, WW, 6.0, 3.3, name='B'),
]

def c_stair():
    """C 樓梯 (127): imperial stair in the left atrium void. Central flight west->east (1F sheet: solid lower part
    from x 47.6, arrow east) to a landing by the void, then north and south flights back west to the 2F lobby arc."""
    t = []; h1n, h2n = 19, 10; hm = h1n * .158
    x0, x1 = 47.6, 53.4
    for i in range(h1n):
        a = x0 + (x1 - x0) * i / h1n; b = x0 + (x1 - x0) * (i + 1) / h1n
        t.append({'q': [[a, 86.3], [b, 86.3], [b, 89.3], [a, 89.3]], 'h': round((i + 1) * .158, 4)})
    t.append({'q': [[53.4, 83.6], [55.5, 83.6], [55.5, 92.0], [53.4, 92.0]], 'h': round(hm, 4)})
    for (y0, y1, xe) in ((83.6, 86.25, 51.7), (89.35, 92.0, 50.5)):
        for i in range(h2n):
            a = 53.4 - (53.4 - xe) * i / h2n; b = 53.4 - (53.4 - xe) * (i + 1) / h2n
            t.append({'q': [[b, y0], [a, y0], [a, y1], [b, y1]], 'h': round(hm + (i + 1) * (H - hm) / h2n, 4)})
    return {'id': 'C', 'treads': t, 'foot': [[47.6, 83.6], [55.5, 83.6], [55.5, 92.0], [47.6, 92.0]], 'hole': None, 'divider': None}
STAIRS.append(c_stair())
ELEVATORS = [box(43.3, 67.4, 45.1, 70.0),                                   # B電梯 (north block)
             Polygon([(54.7, 100.1), (55.9, 100.5), (55.6, 101.4), (54.4, 101.0)])]  # A電梯 beside 217
POOL = Point(ATRIUM_C).buffer(2.9, 64)
DOME_R = 8.0

# Exterior entrances (drawing point on the outline, width, floor)
ENTRANCES = [('1F', (67.25, 45.9), 2.0, '152 北側門廳'), ('1F', (37.9, 85.2), 2.4, '125→126'),
             ('1F', (76.68, 90.6), 2.0, '129 東側'), ('2F', (37.9, 85.2), 3.0, '218 大廳主入口'), ('2F', (85.69, 56.9), 1.4, 'F梯')]

LABELS = json.loads((B / 'labels.json').read_text())

# ------------------------------------------------------------------ helpers
def to_px(p): return [int(round((p[0] - X0) / C)), int(round((p[1] - Y0) / C))]
def mask_of(geoms):
    m = np.zeros((NH, NW), np.uint8)
    for g in geoms if isinstance(geoms, (list, tuple)) else [geoms]:
        for p in ([g] if g.geom_type == 'Polygon' else list(getattr(g, 'geoms', []))):
            if p.is_empty or p.geom_type != 'Polygon': continue
            cv2.fillPoly(m, [np.array([to_px(q) for q in p.exterior.coords], np.int32)], 1)
            for h in p.interiors: cv2.fillPoly(m, [np.array([to_px(q) for q in h.coords], np.int32)], 0)
    return m
def polys_of(mask, simplify=.02, min_area=.02):
    cs, hier = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    if hier is None: return out
    for i, c in enumerate(cs):
        if hier[0][i][3] != -1 or len(c) < 3: continue
        ext = c.reshape(-1, 2) * C + [X0, Y0]
        holes = [cs[j].reshape(-1, 2) * C + [X0, Y0] for j in range(len(cs)) if hier[0][j][3] == i and len(cs[j]) >= 3]
        P = Polygon(ext, holes).buffer(0).simplify(simplify)
        for g in ([P] if P.geom_type == 'Polygon' else list(P.geoms)):
            if g.area >= min_area: out.append(g)
    return out
def parts(g): return [] if g.is_empty else [g] if g.geom_type == 'Polygon' else [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon']
W = LD.to_world
def wring(p): return [W(q) for q in list(p.exterior.coords)[:-1]]
def wpoly(p): return [wring(p)] + [[W(q) for q in list(h.coords)[:-1]] for h in p.interiors]
def tris(g):
    out = []
    for p in parts(g):
        for t in constrained_delaunay_triangles(p).geoms:
            if t.area > 1e-5: out += [c for q in list(t.exterior.coords)[:3] for c in W(q)]
    return [round(v, 3) for v in out]

prisms, walks, glass, leaves = [], [], [], []
def prism(g, y0, y1, m, block=True):
    for p in parts(g.buffer(0) if not g.is_valid else g):
        if p.area < 1e-3 or y1 - y0 < 1e-3: continue
        prisms.append({'p': wpoly(p.simplify(.005)), 'y0': round(y0, 3), 'y1': round(y1, 3), 'm': m, 'b': 1 if block else 0})
def walk(g, y, m, render=True, kind=''):
    t = tris(g)
    if t: walks.append({'t': t, 'y': round(y, 4), 'm': m if render else None, 'k': kind})

# ------------------------------------------------------------------ enclosures
def envelope(fl):
    s = LD.segments(fl); ink = np.zeros((NH, NW), np.uint8)
    for q in s: cv2.line(ink, tuple(to_px(q[:2])), tuple(to_px(q[2:])), 1, 1)
    k = int(1.5 / C) | 1
    cl = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    ff = cl.copy(); mm = np.zeros((NH + 2, NW + 2), np.uint8); cv2.floodFill(ff, mm, (0, 0), 2); filled = (ff != 2).astype(np.uint8)
    k2 = int(3 / C) | 1
    op = cv2.morphologyEx(filled, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k2, k2)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(op); i = 1 + int(np.argmax(st[1:, 4]))
    return max(polys_of((lab == i).astype(np.uint8), .25), key=lambda p: p.area)

E2 = envelope('2F').difference(WEST_CUT).difference(EAST_STAIR_CUT)
E2 = max(parts(E2.buffer(-.05).buffer(.05)), key=lambda p: p.area)
E1 = unary_union([E2.difference(EAST_OUT_1F), VESTIBULE_152]).buffer(0)
E1 = max(parts(E1), key=lambda p: p.area)
ENC = {'1F': E1, '2F': E2}

# ------------------------------------------------------------------ walls
def stair_zone(fl):
    z = [Polygon(s['foot']).buffer(.08) for s in STAIRS]
    return unary_union(z + [e.buffer(.02) for e in ELEVATORS])

def walls_of(fl):
    raw, s, arcs, quads = XLW.extract(fl)
    long_ = mask_of([q for q, lg, d in quads if lg]); short = mask_of([q for q, lg, d in quads if not lg]) & (1 - long_)
    n_, lab, st, _ = cv2.connectedComponentsWithStats(short, 8)
    touch = np.unique(lab[(cv2.dilate(long_, np.ones((3, 3), np.uint8)) > 0) & (lab > 0)])
    wall = long_ | np.isin(lab, touch).astype(np.uint8)
    # curved walls: thin bands between closely drawn lines (closing), long and narrow
    ink = np.zeros((NH, NW), np.uint8)
    for q in raw: cv2.line(ink, tuple(to_px(q[:2])), tuple(to_px(q[2:])), 1, 1)
    cl = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
    op = cv2.morphologyEx(cl, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4)))
    n_, lab, st, _ = cv2.connectedComponentsWithStats(op, 8)
    curved = np.zeros_like(wall)
    for c in range(1, n_):
        x, y, w_, h_, a = st[c]
        if max(w_, h_) * C < 2.0: continue
        comp = (lab[y:y + h_, x:x + w_] == c).astype(np.uint8)
        cs, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        per = sum(cv2.arcLength(q, True) for q in cs) * C / 2
        width = a * C * C / max(per, 1e-6)
        if width < .4 and per > 2.0: curved[y:y + h_, x:x + w_] |= comp
    wall |= curved
    inner = mask_of(ENC[fl].buffer(-.32))
    wall &= inner
    # keep a clear approach inside each exterior entrance (mullion pairs of the glazing read as walls)
    for f, p, w, name in ENTRANCES:
        if f == fl: wall &= 1 - mask_of(Point(p).buffer(w / 2 + 1.3))
    wall &= 1 - mask_of(stair_zone(fl))
    wall &= 1 - mask_of([box(l['at'][0] - .45, l['at'][1] - .85, l['at'][0] + .45, l['at'][1] + .85) for l in LABELS[fl]])   # room-number boxes
    if fl == '2F':
        wall &= 1 - mask_of(Point(ATRIUM_C).buffer(8.3).difference(Point(ATRIUM_C).buffer(6.3)))   # dome ring (drawn above)
        wall &= 1 - mask_of(VOIDS_2F.buffer(-.15))
        wall &= 1 - mask_of(BRIDGE.buffer(-.12))
    else:
        wall &= 1 - mask_of(Point(ATRIUM_C).buffer(8.6))                    # pool rings / dashed 2F edges
    # door swings: cut the sector and the strip through the wall
    doors = []
    dw = cv2.distanceTransform((1 - wall).astype(np.uint8), cv2.DIST_L2, 3) * C
    for a in arcs:
        R = a['r']; span = a['a1'] - a['a0']
        if not (.6 <= R <= 1.4) or not (math.radians(55) <= span <= math.radians(110) or math.radians(150) <= span <= math.radians(200)): continue
        cx, cy = a['c']; hp = to_px((cx, cy))
        if not (0 <= hp[0] < NW and 0 <= hp[1] < NH) or dw[hp[1], hp[0]] > .45: continue
        if not ENC[fl].buffer(.3).contains(Point(cx, cy)): continue
        c = np.array([cx, cy]); e0 = c + R * np.array([math.cos(a['a0']), math.sin(a['a0'])]); e1 = c + R * np.array([math.cos(a['a1']), math.sin(a['a1'])])
        def behind(e):
            v = (e - c) / R; cnt = 0
            for t in np.arange(.08, .5, .04):
                q = to_px(c - v * t)
                if 0 <= q[0] < NW and 0 <= q[1] < NH and wall[q[1], q[0]]: cnt += 1
            return cnt
        closed, open_ = (e0, e1) if behind(e0) >= behind(e1) else (e1, e0)
        if span > math.radians(140): am = (a['a0'] + a['a1']) / 2; closed = c + R * np.array([math.cos(am), math.sin(am)])
        sector = Polygon([c] + [[cx + R * math.cos(t), cy + R * math.sin(t)] for t in np.linspace(a['a0'], a['a1'], 16)])
        nrm = (open_ - c) / R
        strip = Polygon([c - nrm * .4, closed - nrm * .4, closed + nrm * .06, c + nrm * .06])
        wall &= 1 - mask_of(unary_union([sector.buffer(.03), strip]))
        doors.append({'hinge': c.tolist(), 'closed': closed.tolist(), 'open': open_.tolist(), 'r': R})
    n_, lab, st, _ = cv2.connectedComponentsWithStats(wall, 8)
    for c in range(1, n_):
        if math.hypot(st[c, 2], st[c, 3]) * C < 1.2: wall[lab == c] = 0
    return polys_of(wall), doors, arcs

# ------------------------------------------------------------------ exterior wall, windows, entrances
def entrance_cut(fl):
    out = []
    for f, p, w, name in ENTRANCES:
        if f != fl: continue
        b = ENC[fl].exterior; d = b.project(Point(p)); a = b.interpolate(d - w / 2); c = b.interpolate(d + w / 2)
        out.append(LineString([a, c]).buffer(.6, cap_style=2))
    return unary_union(out) if out else Polygon()

CURVED_GLASS = {'1F': [LineString([(74.2, 80.3), (75.6, 83.5), (76.6, 87.0), (76.7, 90.0), (76.2, 93.0), (75.0, 96.3), (73.0, 99.2), (70.3, 101.8)]),
                       LineString([(38.69, 80.8), (37.1, 89.8)])],
                'west': None}
def exterior(fl, y):
    E = ENC[fl]; band = E.difference(E.buffer(-.3)); ent = entrance_cut(fl)
    band_solid = band.difference(ent)
    # glazing zones: straight edges get ribbon windows; the lobby glass (west, both floors) and the 1F east arc / 2F 220 arc are full-height glass.
    full = []
    full.append(LineString([(38.69, 80.9), (37.1, 89.8)]).buffer(.5))
    if fl == '1F': full.append(CURVED_GLASS['1F'][0].buffer(.5))
    else: full.append(LineString([(77.5, 80.9), (78.6, 85), (79.1, 90), (78.4, 95), (76.8, 99.5), (74.4, 103.2)]).buffer(1.2))
    full = unary_union(full).intersection(band_solid)
    rest = band_solid.difference(full)
    # ribbon windows on long straight runs: sill 0.9, head 3.4, mullions every 1.6 m; corners and short pieces solid
    coords = list(E.exterior.coords); win = []
    for (ax, ay), (bx, by) in zip(coords, coords[1:]):
        L = math.hypot(bx - ax, by - ay)
        if L < 2.4: continue
        tx, ty = (bx - ax) / L, (by - ay) / L
        seg = LineString([(ax + tx * .9, ay + ty * .9), (bx - tx * .9, by - ty * .9)]).buffer(.45, cap_style=2)
        win.append(seg)
    win = unary_union(win).intersection(rest) if win else Polygon()
    solid = rest.difference(win)
    prism(solid, y, y + H, 'outer')
    prism(win, y, y + .9, 'outer'); prism(win, y + 3.4, y + H, 'outer'); prism(win, y + .9, y + 3.4, 'glass')
    prism(full, y, y + .12, 'outer'); prism(full, y + .12, y + H - .2, 'glass'); prism(full, y + H - .2, y + H, 'trim')
    for e in parts(ent.intersection(band)): prism(e, y + 2.6, y + H, 'outer')
    # mullions on the glazing
    for g, top in ((win, 3.4), (full, H - .2)):
        for p in parts(g):
            r = p.minimum_rotated_rectangle; cs = list(r.exterior.coords)[:4]
            e1 = math.dist(cs[0], cs[1]); e2 = math.dist(cs[1], cs[2])
            a, b = (cs[0], cs[1]) if e1 >= e2 else (cs[1], cs[2]); L = max(e1, e2); n = int(L / 1.6)
            for i in range(1, n + 1):
                t = i / (n + 1); m = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                prism(Point(m).buffer(.06, 4).intersection(p.buffer(.02)), y + (.9 if g is win else .12), y + top, 'frame', False)

# ------------------------------------------------------------------ build floors
floors_meta = []
wall_review = {}
for fl in ['1F', '2F']:
    y = LEVEL[fl]; E = ENC[fl]
    wl, doors, arcs = walls_of(fl)
    wall_review[fl] = (wl, doors)
    for p in wl:
        if fl == '2F' and p.buffer(.05).intersects(VOIDS_2F.boundary) and p.difference(VOIDS_2F.boundary.buffer(.45)).area < .25 * p.area:
            prism(p, y, y + 1.1, 'rail')          # wall pieces drawn along a void edge are balustrades
        else:
            prism(p, y, y + H, 'inner')
    for d in doors:
        c = d['hinge']; o = d['open']; v = (o[0] - c[0], o[1] - c[1]); L = math.hypot(*v)
        leaf = LineString([c, (c[0] + v[0] * .96, c[1] + v[1] * .96)]).buffer(.025, cap_style=2)
        prism(leaf, y + .02, y + 2.15, 'wood', False)
    exterior(fl, y)
    # columns
    for col in XLW.columns(fl):
        P = Point(col['c']).buffer(col['r'], 20) if col['r'] else Polygon(col['ring'])
        if any(Polygon(s['foot']).contains(Point(col['c'])) for s in STAIRS): continue   # posts under a stair landing
        if not E.buffer(.4).contains(P.centroid) and fl == '2F': continue
        if fl == '1F' and not (E.buffer(.4).contains(P.centroid) or Polygon([(18, 60), (40, 60), (40, 100), (18, 100)]).contains(P.centroid)): continue
        top = y + H if E.buffer(.4).contains(P.centroid) else y + H - SLAB
        prism(P, y, top, 'column')
    # elevators: closed shafts
    for e in ELEVATORS: prism(e, y, y + H, 'steel')
    floors_meta.append({'key': fl, 'label': LABEL[fl], 'level': y, 'outline': wring(E)})

# slabs: B1 floor, 1F floor (minus voids and stair holes), roof
holes = unary_union([Polygon(s['hole']) for s in STAIRS if s['hole']] + list(ELEVATORS))
walk(E1, 0.0, 'floor', kind='floor')
F2 = E2.difference(VOIDS_2F).difference(holes).union(BRIDGE.intersection(E2)).difference(holes)
walk(F2, H, 'floor', kind='floor')
prism(F2.buffer(-.01), H - SLAB, H - .005, 'ceiling', False)
# 1F (drawing 2F) overhang above the 1F east outdoor 129: same slab, its underside is outdoor soffit
roof = E2
prism(roof, 2 * H - SLAB, 2 * H, 'ceiling', False)
walk(roof, 2 * H, 'roof', kind='roof')
# parapet
prism(roof.difference(roof.buffer(-.3)), 2 * H, 2 * H + 1.0, 'outer')
# skylights over the voids and the atrium dome
for v in parts(VOIDS_2F.difference(Point(ATRIUM_C).buffer(DOME_R))):
    prism(v.buffer(-.05), 2 * H - .05, 2 * H + .05, 'glass', False)
domes = [{'c': W(ATRIUM_C), 'r': DOME_R, 'y': 2 * H}]
prism(Point(ATRIUM_C).buffer(DOME_R + .3).difference(Point(ATRIUM_C).buffer(DOME_R)), 2 * H, 2 * H + .6, 'trim')
# void balustrades (1.1 m) wherever no wall stands on the edge
rail = VOIDS_2F.boundary.buffer(.06).intersection(E2.buffer(-.3)).difference(BRIDGE.buffer(-.1))
stair_tops = unary_union([Polygon(s['foot']).buffer(.3) for s in STAIRS])
rail = rail.difference(stair_tops)
prism(rail, H, H + 1.1, 'rail')
# bridge balustrades
for edge in (LineString([(58.4, 77.9), (63.5, 101.25)]), LineString([(61.0, 77.4), (65.4, 101.2)])):
    prism(edge.buffer(.06).intersection(E2.buffer(-.3)), H, H + 1.1, 'rail')

# stairs: treads (render + walk), side walls for the switchbacks
for s in STAIRS:
    for t in s['treads']:
        q = Polygon(t['q']); prism(q, t['h'] - .18 if s['id'] != 'C' else 0, t['h'], 'tread', False)
        walk(q, t['h'], None, render=False, kind='stair-' + s['id'])
    if s['divider']: prism(Polygon(s['divider']), 0, H + 1.0, 'inner')
    if s['id'] in ('D', 'B'):
        f = Polygon(s['foot']); ringw = f.buffer(.2, join_style=2).difference(f)
        # stairwell walls on both storeys, one door opening at the start (B1) and at the top (1F)
        prism(ringw.difference(Polygon(s['start']).buffer(.05)), 0, H, 'inner')       # B1: door at the first flight
        prism(ringw.difference(Polygon(s['top']).buffer(.05)), H, 2 * H, 'inner')       # 1F: door where the second flight arrives
# pool
walk(POOL, -.05, 'water', kind='water')
prism(POOL.buffer(.35).difference(POOL), 0, .45, 'trim')

# room numbers
labels = []
for fl in ['1F', '2F']:
    for l in LABELS[fl]:
        labels.append({'n': l['num'], 'at': W(l['at']), 'y': LEVEL[fl] + 2.6})

# ------------------------------------------------------------------ fan plaza (2F level) and outdoor works
# Heights: the S04 sidewalk beside the fan's outer edge fixes the plaza; B1 = sidewalk - (4.5 + 0.3 + ~1.0 of 202 steps).
_q = {'walk': {'s04': W((7.4, 86.8)), 's04n': W((8.6, 80.0)), 's04s': W((8.6, 93.5))}, 'raw': {'anchor': W(E1.centroid.coords[0])}}
SH = json.loads(subprocess.run(['node', str(root / 'scripts/library-heights.mjs'), json.dumps(_q)], capture_output=True, text=True, check=True).stdout)
SIDEWALK = round((SH['s04'] + SH['s04n'] + SH['s04s']) / 3, 3)
BASE = round(SIDEWALK - H - 1.3, 2)
top_rel = SIDEWALK - BASE                         # S04 sidewalk relative to B1
L203 = H + .3
fanC = Point(FAN_C)
def annulus(r0, r1): return fanC.buffer(r1, 128).difference(fanC.buffer(r0, 128))
def half(a, b, keep):      # half-plane on the side of line a->b that contains point keep
    a, b = np.array(a), np.array(b); d = b - a; n = np.array([-d[1], d[0]]); n /= np.linalg.norm(n)
    if (np.array(keep) - a) @ n < 0: n = -n
    P = [a - d * 10, b + d * 10]; return Polygon([P[0], P[1], P[1] + n * 200, P[0] + n * 200])
H_IN = ((26.76, 73.14), (15.95, 64.93)); H_OUT = ((24.09, 73.58), (14.76, 66.50))     # H stair sides
G_IN = ((21.01, 91.50), (9.86, 95.06)); G_OUT = ((23.65, 92.94), (10.51, 97.13))      # G stair sides
fan = annulus(25.6, 37.35).intersection(half(*H_OUT, (15, 82))).intersection(half(*G_IN, (15, 82)))
D1 = ((13.40, 69.93), (18.37, 72.56)); D2 = ((12.07, 73.21), (20.59, 76.64)); D4 = ((18.73, 87.45), (9.55, 87.83)); D5 = ((15.26, 90.37), (9.69, 91.16))
outer = annulus(28.6, 37.35).intersection(fan)
s202n = outer.intersection(half(*D1, (16, 75))).intersection(half(*D2, (16, 72)))
s202s = outer.intersection(half(*D4, (13, 89))).intersection(half(*D5, (13, 88)))
beds = outer.difference(s202n).difference(s202s)
wide = annulus(26.0, 37.35).intersection(fan)
gap202 = unary_union([wide.intersection(half(*D1, (16, 75))).intersection(half(*D2, (16, 72))), wide.intersection(half(*D4, (13, 89))).intersection(half(*D5, (13, 88)))])
pebble = annulus(27.95, 28.6).intersection(fan).difference(gap202.buffer(.1))
EDGE204 = [(23.5, 74.3), (21.3, 78.9), (20.7, 82.2), (20.15, 85.5), (20.6, 90.6)]
deck = Polygon(EDGE204 + [(34.3, 97.8), (37.0, 89.8), (38.69, 80.6), (38.69, 72.4)]).buffer(0)
deck = deck.intersection(half((38.70, 72.56), (23.87, 74.20), (30, 85))).intersection(half((20.80, 91.57), (34.18, 98.04), (30, 85)))
p203 = annulus(25.6, 28.6).intersection(fan).difference(pebble).difference(deck)   # from the 204 edge (drain line) to the pebble planter
fan = fan.difference(deck)
grate = LineString(EDGE204).buffer(.18, cap_style=2).intersection(deck.buffer(.2))
# 125 (half-open, B1 level) under the deck; the deck rests on the drawn columns and on the 203 structure
walk(deck, 0.0, 'paving', kind='plaza-b1')
prism(deck, H - .45, H, 'ceiling', False)
walk(deck, H, 'paving', kind='plaza-204')
prism(grate, H - .02, H + .005, 'steel', False)
nparapet = LineString([(38.70, 72.2), (23.9, 73.82)]).buffer(.18, cap_style=2)
sparapet = LineString([(20.9, 91.2), (34.3, 97.7)]).buffer(.18, cap_style=2)
for pp in (nparapet, sparapet): prism(pp, H - .6, H + 1.1, 'outer')
# 203 platform (two short risers up from 204), pebble planter, 202 steps up to S04, 201 beds
prism(p203, -.5, L203, 'trim'); walk(p203, L203, 'paving', kind='203')
walk(p203.intersection(LineString(EDGE204).buffer(.45)), H + .15, None, render=False, kind='203-step')
prism(p203.intersection(LineString(EDGE204).buffer(.45)).difference(deck), H - .3, H + .15, 'trim')
prism(pebble, -.5, L203 + .35, 'planter'); walk(pebble, L203 + .3, 'pebble', kind='pebble')
radii = [28.6, 30.35, 32.1, 33.85, 35.6, 37.35]; nst = len(radii); rise = (top_rel - L203) / nst
for k in range(nst):
    r0 = radii[k]; r1 = radii[k + 1] if k + 1 < nst else 37.35 + .01
    for st_ in (s202n, s202s):
        ring = annulus(r0, max(r1, r0 + .3)).intersection(st_) if k + 1 < nst else annulus(r0 - .0, 37.35).intersection(st_).difference(annulus(28.6, r0))
        hk = L203 + rise * (k + 1)
        prism(ring, -.5, hk, 'tread'); walk(ring, hk, None, render=False, kind='202')
# 201 beds step with the 202 flights beside them: each radial band is a raised planter 0.45 m above that step.
for k in range(nst):
    r0 = radii[k]; r1 = radii[k + 1] if k + 1 < nst else 37.35
    band = annulus(r0, r1 if r1 > r0 else r0 + .3).intersection(beds) if k + 1 < nst else Polygon()
    if band.is_empty: continue
    hk = L203 + rise * (k + 1) + .45
    prism(band, -.5, hk, 'planter'); walk(band.buffer(-.15), hk + .005, 'soil', kind='bed')
# Walk between the fan's top edge and the S04 sidewalk (orthophoto: curved paved strip), at sidewalk height;
# the G/H stair heads land on it.
H_N = ((26.76, 73.14), (15.95, 64.93)); G_S = ((23.65, 92.94), (10.51, 97.13))
approach = annulus(37.35, 41.4).intersection(half(*H_N, (15, 82)).buffer(1.2)).intersection(half(*G_S, (15, 82)).buffer(1.2))
# Sloped: the inner edge meets the fan top, the outer edge the live S04 roadside walking height.
_at = tris(approach); _pts = {f'p{i}': [_at[2 * i], _at[2 * i + 1]] for i in range(len(_at) // 2)}
_hw = json.loads(subprocess.run(['node', str(root / 'scripts/library-heights.mjs'), json.dumps({'walk': _pts})], capture_output=True, text=True, check=True).stdout)
def _inv(w):   # world -> drawing
    c, s = math.cos(LD.THETA), math.sin(LD.THETA); x, z = w[0] - LD.T[0], w[1] - LD.T[1]; return (c * x + s * z, -s * x + c * z)
_yv = []
for i in range(len(_at) // 2):
    d = _inv(_pts[f'p{i}']); r = math.dist(d, FAN_C); k = min(1, max(0, (r - 37.35) / 3.0))
    _yv.append(round(top_rel * (1 - k) + (_hw[f'p{i}'] - BASE) * k, 3))
walks.append({'t': _at, 'y': round(top_rel, 4), 'yv': _yv, 'm': 'paving', 'k': 'approach'})
prism(approach, -.5, min(_yv) - .02, 'trim')
# retaining face under 203 toward 125 and the colonnade drawn on 1F (123)
prism(LineString(EDGE204).buffer(.25, cap_style=2).difference(deck), -.3, H, 'outer')

# G / H stairs: from the B1 ground at the fan corner up to the S04 side (landings where the drawing breaks)
def straight_stair(inner_line, outer_line, name, rises):
    (a0, a1), (b0, b1) = inner_line, outer_line
    a0, a1, b0, b1 = map(np.array, (a0, a1, b0, b1))
    L = np.linalg.norm(a1 - a0); u = (a1 - a0) / L
    n = rises; run = L / n
    end = (a1 + b1) / 2; wv = W(tuple(end)); k = min(range(len(_yv)), key=lambda i: math.dist(wv, _pts[f'p{i}']))
    top = max(top_rel, _yv[k])                       # land on the approach walk at the stair head
    for i in range(n):
        q = Polygon([a0 + u * run * i, a0 + u * run * (i + 1), b0 + u * run * (i + 1) + (b0 - a0) * 0, b0 + u * run * i])
        q = Polygon([a0 + u * run * i, a0 + u * run * (i + 1), b0 + (a1 - a0) / L * run * (i + 1), b0 + (a1 - a0) / L * run * i])
        h = top * (i + 1) / n
        prism(q, -.5, h, 'tread'); walk(q, h, None, render=False, kind='stair-' + name)
    side = LineString([a0, a1]).buffer(.12, cap_style=2)
    for i in range(n):
        seg = LineString([a0 + u * run * i, a0 + u * run * (i + 1)]).buffer(.12, cap_style=2)
        prism(seg, -.5, top * (i + 1) / n + 1.0, 'outer')
    return top
# H: inner side line first point is the corner by the deck; G likewise
straight_stair(((24.09, 73.58), (14.76, 66.50)), ((26.76, 73.14), (15.95, 64.93)), 'H', 30)
straight_stair(((21.01, 91.50), (9.86, 95.06)), ((23.65, 92.94), (10.51, 97.13)), 'G', 29)

# ㄇ-shaped thin wall: two legs on the ground, beam over the plaza (dashed middle on the sheet)
MC, MR0, MR1 = (-11.2277, 76.74), 46.23, 46.55
def arcband(a0, a1):
    t = np.radians(np.linspace(a0, a1, 40))
    o = [(MC[0] + MR1 * math.cos(x), MC[1] + MR1 * math.sin(x)) for x in t]
    i = [(MC[0] + MR0 * math.cos(x), MC[1] + MR0 * math.sin(x)) for x in t[::-1]]
    return Polygon(o + i)
TOPW = 2 * H + .6
prism(arcband(-3.4, 8.6), -1.0, TOPW, 'portal')
prism(arcband(35.2, 41.65), -1.0, TOPW, 'portal')
prism(arcband(8.6, 35.2), H + 3.2, TOPW, 'portal')

# F stair (east, from the 1F door down to the B1 ground) and E stair (north, along the wall)
def flight(x0, x1, ya, yb, h0, h1, n, axis='y', name='F'):
    for i in range(n):
        if axis == 'y': q = box(x0, ya + (yb - ya) * i / n, x1, ya + (yb - ya) * (i + 1) / n)
        else: q = box(ya + (yb - ya) * i / n, x0, ya + (yb - ya) * (i + 1) / n, x1)
        q = Polygon(q.exterior.coords)
        h = h0 + (h1 - h0) * (i + 1) / n
        prism(q, min(h0, h1) - .5, h, 'tread'); walk(q, h, None, render=False, kind='stair-' + name)
flight(85.75, 88.2, 55.7, 58.6, H, H, 1, name='F')                    # top landing at the door
flight(86.4, 88.2, 58.6, 71.0, H, 0.0, 26, name='F')                   # straight run down to the B1 ground
prism(LineString([(88.25, 55.7), (88.25, 71.0)]).buffer(.06), 0, H + 1.1, 'rail')
flight(45.8, 47.8, 41.9, 52.3, 0.0, H - .1, 26, axis='x', name='E')   # E梯 along the north wall (rises east)
prism(box(41.5, 45.6, 52.6, 45.8), 0, H + 1.0, 'outer')


# Paved walk round the B1 facades (drawing: dashed perimeter path) and the north parking (bays painted).
PARK = box(66.0, 38.6, 88.6, 47.85)
apron = unary_union([E1.buffer(2.2, join_style=2).difference(E1), PARK]).difference(deck.buffer(.3)).difference(fan.buffer(.3))
apron = apron.difference(box(85.9, 55.4, 88.4, 71.2)).difference(box(41.4, 45.5, 52.7, 47.85))
walk(apron, .0, 'paving', kind='apron')
walk(EAST_OUT_1F.intersection(E2).difference(apron), .0, 'paving', kind='129')
walk(PARK, .012, 'asphalt', kind='parking')
paint = []
for i in range(10):
    x = 66.4 + i * 2.5
    paint.append(LineString([(x, 39.5), (x, 45.5)]).buffer(.06))
paint.append(LineString([(66.4, 45.5), (88.9, 45.5)]).buffer(.06))
prism(unary_union(paint).intersection(PARK), .0, .03, 'paint', False)

# ------------------------------------------------------------------ terrain / ground cut
ground = unary_union([E1, deck, fan, p203, apron, PARK, approach, EAST_OUT_1F.intersection(E2)]).buffer(.05)
site_ring = unary_union([E1.buffer(2.4), deck.buffer(1.0), box(41, 41, 86.0, 48), box(64, 37.5, 90, 48), box(85.6, 55, 89, 72)]).buffer(0)
site_ring = max(parts(site_ring), key=lambda p: p.area).simplify(.3)

out = {'version': 1, 'building': 381963953, 'key': 'library', 'signText': '圖資大樓', 'base': BASE, 'floorHeight': H, 'slab': SLAB,
       'transform': LD.transform(),
       'outline': wring(unary_union([E1, E2]).buffer(0) if unary_union([E1, E2]).geom_type == 'Polygon' else max(parts(unary_union([E1, E2])), key=lambda p: p.area)),
       'floors': floors_meta, 'prisms': prisms, 'walks': walks, 'domes': domes, 'labels': labels,
       'site': {'groundOutline': wring(ground if ground.geom_type == 'Polygon' else max(parts(ground), key=lambda p: p.area)),
                'cuts': [[W(q) for q in list(tr.exterior.coords)[:3]] for p in parts(ground.simplify(.05)) for tr in constrained_delaunay_triangles(p).geoms if tr.area > 1e-4],   # convex pieces (road-ground.js subtracts convex footprints)
                'outlineRings': [wring(p) for p in parts(ground)], 'terrainRing': wring(site_ring), 'anchor': W(E1.centroid.coords[0])},
       'source': {'drawings': ['buildings/library/source/floor-1F.pdf', 'buildings/library/source/floor-2F.pdf'],
                  'basis': '使用者2026-11-25提供之一層、二層平面圖（圖面1F＝遊戲B1、圖面2F＝遊戲1F，無其他樓層）；牆由向量雙線判讀，弧牆以細帶判讀，門弧開門洞；比例8m柱距，依NLSC 2023正射影像定位；層高4.5m為使用者確認之預設。'}}
geo = json.loads((B / 'building.json').read_text())
g = geo['geometry']
g.setdefault('beforeRelocationRing', g['ring'])
outline_poly = unary_union([E1, E2]).buffer(.01)
outline_poly = max(parts(outline_poly), key=lambda p: p.area).simplify(.2)
g['ring'] = [[round(v, 3) for v in W(q)] for q in list(outline_poly.exterior.coords)[:-1]]
g['terrainRing'] = [[round(v, 3) for v in q] for q in out['site']['terrainRing']]
g['platformAnchor'] = [round(v, 3) for v in out['site']['anchor']]
g['platformOffset'] = round(BASE - SH['anchor'], 3)
g.update(height=2 * H, floors=2, floorHeight=H, basementFloors=0)
g['drawingPlacement'] = {'source': 'buildings/library/source/floor-1F.pdf, floor-2F.pdf', 'metresPerPoint': LD.S, 'rotationDeg': math.degrees(LD.THETA), 'translation': list(LD.T),
                         'levels': '圖面1F＝遊戲B1（B1地面＝base），圖面2F＝遊戲1F（+4.5m，西側扇形廣場204入口）；使用者2026-11-25確認無其他樓層',
                         'base': BASE, 's04Sidewalk': SIDEWALK}
(B / 'building.json').write_text(json.dumps(geo, ensure_ascii=False, indent=2) + '\n')
(B / 'interior.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')))

# review image
k = 12
img = np.full((int((Y1 - Y0) * k), int((X1 - X0) * k) * 2, 3), 255, np.uint8)
for j, fl in enumerate(['1F', '2F']):
    off = j * int((X1 - X0) * k)
    P = lambda q: (int((q[0] - X0) * k) + off, int((q[1] - Y0) * k))
    for q in LD.segments(fl): cv2.line(img, P(q[:2]), P(q[2:]), (205, 205, 205), 1)
    cv2.polylines(img, [np.array([P(q) for q in ENC[fl].exterior.coords], np.int32)], True, (0, 140, 0), 2)
    wl, doors = wall_review[fl]
    for p in wl: cv2.fillPoly(img, [np.array([P(q) for q in p.exterior.coords], np.int32)], (40, 40, 220))
    for d in doors: cv2.line(img, P(d['hinge']), P(d['open']), (0, 160, 0), 2)
    if fl == '2F':
        for v in parts(VOIDS_2F): cv2.polylines(img, [np.array([P(q) for q in v.exterior.coords], np.int32)], True, (220, 120, 0), 2)
    for s in STAIRS:
        cv2.polylines(img, [np.array([P(q) for q in s['foot']], np.int32)], True, (200, 0, 200), 2)
cv2.imwrite(str(B / 'review/plan-review.png'), img)
print('library interior:', len(prisms), 'prisms', len(walks), 'walk surfaces', len(labels), 'labels; E1', round(E1.area), 'm² E2', round(E2.area), 'm²')
