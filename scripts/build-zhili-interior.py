"""Compile the reviewed Zhili floor plans into a walkable B1–2F interior and a plan-driven facade.

Sources: buildings/zhili/plan.json (user-confirmed reading of the 1:250 drawings, drawing metres)
and buildings/zhili/building.json (tower ring, drawingFootprint placement).
Output: buildings/zhili/interior.json.

Every floor uses its own outline from the drawings (1F includes the podium / lecture hall and the
north lobby; 2F and 3F+ use the tower). Walls are the interfaces between the plan's room regions
plus a 0.25 m outer wall band; stair halls are fully walled with one door on the side shown in the
drawing; exterior walls get window openings where a room meets the facade. 3F+ is a solid volume
whose facade windows come from the same plan. Door/window positions and sizes are model
approximations read from the drawings, not survey data.
"""
import json
from pathlib import Path
import numpy as np, cv2
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles

root = Path(__file__).resolve().parents[1]
plan = json.loads((root / 'buildings/zhili/plan.json').read_text())
geom = json.loads((root / 'buildings/zhili/building.json').read_text())['geometry']
T = geom['drawingFootprint']['transform']
TOWER = Polygon(geom['drawingFootprint']['drawingRing']).buffer(0)
CELL, FLOOR_H, SLAB = .1, geom.get('floorHeight', 3.6), .2
ALL_FLOORS = ['B', '1', '2', '3', '4', '5', '6', '7', '8']
ORDER = ['B', '1', '2']  # user 2026-11-18: walkable interior for 2F and below; 3F+ solid
LEVEL = {k: (i - 1) * FLOOR_H for i, k in enumerate(ALL_FLOORS)}
LABEL = {'B': 'B1', **{k: k + 'F' for k in ALL_FLOORS[1:]}}
# 1F outline read from the 1F drawing: podium (lecture hall, west lobby, 戊梯) + tower + north lobby to x=64.4.
# The covered area under 2F at the south end (x<26.7, y>55.2) and the 己梯 corner stay outdoors.
OUTLINE_1F = Polygon([(1.2, 15.5), (33.1, 15.5), (33.1, 10.8), (35.4, 10.8), (35.4, 4.3), (48.4, 4.3), (48.4, 10.8), (53.2, 10.8),
                      (53.2, 20.3), (61.3, 20.3), (61.3, 25.8), (64.4, 25.8), (64.4, 54.9), (65.8, 54.9), (65.8, 58.8), (63.8, 58.8),
                      (63.8, 63.9), (58.6, 63.9), (58.6, 66.6), (26.7, 66.6), (26.7, 55.2), (22.0, 55.2), (22.0, 46.3), (6.3, 46.3),
                      (6.3, 43.9), (1.2, 43.9)]).buffer(0)
# B1 garage: only the part under the 1F building for now (parts under outdoor paving are pending).
B1_PLAN = unary_union([Polygon(p).buffer(0) for f in plan['floors'] if f['key'] == 'B' for p in f['footprint']])
# B1 (user 2026-11-18: build B1 too): the drawing's B1 wherever a 1F floor or the paved lower plaza / connection covers it.
camp = json.loads((root / 'data/campus.json').read_text())
def drawing(p):
    x, z = p[0] - T['tx'], p[1] - T['tz']; return (T['a'] * x + T['b'] * z, -T['b'] * x + T['a'] * z)
covered = [Polygon([drawing(q) for q in r[0]]).buffer(0) for r in camp['courtyard']['floorRegions']['lower']]
covered += [Polygon([drawing(q) for q in camp['levelLink']['ring']]).buffer(0), Polygon([drawing(q) for q in camp['teachingAccess']['lowerLanding']]).buffer(0)]
# The existing 便利商店 stairs (pre-drawing game layout) reach ~1.2 m past the drawing's south edge; keep 0.3 m clear of
# them on B1 and the 1F podium until the steps are redone from the Zhili drawing (pending user decision with Gauss).
STAIR_KEEP = unary_union([Polygon([drawing(q) for q in st['ring']]).buffer(.3, join_style=2) for st in camp['levelLink']['stairs']]
                       + [Polygon([drawing(q) for q in camp['teachingAccess'][k]]).buffer(.3, join_style=2) for k in ('frontApron', 'gapFootprint') if camp.get('teachingAccess', {}).get(k)])
OUTLINE_1F = OUTLINE_1F.difference(STAIR_KEEP).buffer(0)
B1_OUTLINE = B1_PLAN.intersection(unary_union([OUTLINE_1F, *covered]).buffer(.3).buffer(-.3)).intersection(box(-50, -50, 200, 66.6)).buffer(0)
if B1_OUTLINE.geom_type != 'Polygon': B1_OUTLINE = max(B1_OUTLINE.geoms, key=lambda g: g.area)
B1_OUTLINE = B1_OUTLINE.difference(STAIR_KEEP)
if B1_OUTLINE.geom_type != 'Polygon': B1_OUTLINE = max(B1_OUTLINE.geoms, key=lambda g: g.area)
B1_OUTLINE = B1_OUTLINE.simplify(.05)
OUTLINE = {'B': B1_OUTLINE, '1': OUTLINE_1F, '2': TOWER, **{k: TOWER for k in ALL_FLOORS[3:]}}
# 理學院階梯教室 (user): one double-height hall over B1 and 1F; stage at B1 level, seating tiers rise to the 1F lobby.
RAKE = {'rect': [6.5, 20.9, 22.8, 40.1], 'tiers': 12}
HALL_OPEN_1F = [1.3, 20.7, 22.8, 40.3]   # no 1F slab or partitions here (stage void + seating)
HALL_CLEAR_B1 = [6.4, 20.8, 22.8, 40.2]  # seating volume on B1 (B05 rows, B04 under the rake)
FREE = {'classroom', 'office', 'library', 'hall', 'corridor', 'toilet', 'stair', 'service', 'mech', 'balcony', 'plaza', 'unknown', 'garage'}
OPEN_TO = {'corridor', 'plaza', 'garage'}
WINDOWED = {'classroom', 'office', 'library', 'hall', 'service', 'mech', 'unknown', 'corridor', 'toilet', 'stair'}
WALL_BAND = .25
# Stair cores: switchback entrance end and the door read from the drawings (side, position along it).
STAIR = {'甲梯': {'entrance': 'y1', 'door': ('y1', .5, 1.6)}, '乙梯': {'entrance': 'x0', 'door': ('x0', .5, 1.4)},
         '丙梯': {'entrance': 'x0', 'door': ('x0', .5, 1.4)}, '丁梯': {'entrance': 'y1', 'door': ('x0', .82, 1.1)}}
# Interior doors whose drawn swing arcs would otherwise survive as wall fragments (drawing metres).
EXTRA_DOORS = {'B': [[7.0, 40.2, 9.1, 41.3]]}
# 己梯 (user 2026-11-18 "己梯要蓋"): open straight stair from the 1F ±0 paving (y55.3) up to the 2F plaza (y48.7);
# the 2F floor is open over it and its top opens onto the plaza.
OPEN_2F = [19.0, 46.3, 21.3, 55.4]     # walls cleared (top landing opens onto the plaza)
HOLE_2F = [19.0, 48.7, 21.3, 55.4]     # 2F slab open over the flight  # B05 演講廳 double door to the south 門廳
# Entrances on the 1F outline (drawing metres): north lobby, corridor south end, east main lobby, two west-lobby doors.
MANUAL_EXITS = {'1': [[[64.4, 26.6], [64.4, 29.4]], [[26.7, 55.4], [26.7, 57.5]], [[38.4, 66.6], [42.4, 66.6]],
                      [[7.9, 46.3], [10.9, 46.3]], [[13.2, 46.3], [16.0, 46.3]]],
                # 2F: balcony doors onto the plaza walkway, corridor west end onto the plaza.
                '2': [[[33.4, 26.6], [33.4, 29.8]], [[16.5, 55.4], [16.5, 57.5]]]}

allb = unary_union(list(OUTLINE.values())).bounds
ox, oy = allb[0] - 1, allb[1] - 1
W, H = int((allb[2] - allb[0] + 2) / CELL) + 1, int((allb[3] - allb[1] + 2) / CELL) + 1
xs_grid, ys_grid = np.arange(W)[None, :], np.arange(H)[:, None]
def to_px(p): return [int(round((p[0] - ox) / CELL)), int(round((p[1] - oy) / CELL))]
def mask_of(polys, evenodd=False):
    m = np.zeros((H, W), np.uint8)
    if evenodd:
        for p in polys:
            t = np.zeros_like(m); cv2.fillPoly(t, [np.array([to_px(q) for q in p], np.int32)], 1); m ^= t
    else: cv2.fillPoly(m, [np.array([to_px(q) for q in p], np.int32) for p in polys if len(p) > 2], 1)
    return m
def poly_mask(P):
    parts = [P] if P.geom_type == 'Polygon' else list(P.geoms)
    m = np.zeros((H, W), np.uint8)
    for p in parts:
        cv2.fillPoly(m, [np.array([to_px(q) for q in p.exterior.coords], np.int32)], 1)
        for h in p.interiors: cv2.fillPoly(m, [np.array([to_px(q) for q in h.coords], np.int32)], 0)
    return m
def rect_mask(r):
    m = np.zeros((H, W), np.uint8); a = to_px(r[:2]); b = to_px(r[2:]); m[max(a[1], 0):b[1] + 1, max(a[0], 0):b[0] + 1] = 1; return m
def world(p): return [round(T['a'] * p[0] - T['b'] * p[1] + T['tx'], 4), round(T['b'] * p[0] + T['a'] * p[1] + T['tz'], 4)]
def cell_rect(x0, y0, x1, y1): return [round(ox + x0 * CELL - CELL / 2, 3), round(oy + y0 * CELL - CELL / 2, 3), round(ox + x1 * CELL + CELL / 2, 3), round(oy + y1 * CELL + CELL / 2, 3)]
def rects(mask):
    out, active = [], {}
    for y in range(H + 1):
        runs = set()
        if y < H:
            row = mask[y]; x = 0
            while x < W:
                if row[x]:
                    s = x
                    while x < W and row[x]: x += 1
                    runs.add((s, x - 1))
                else: x += 1
        nxt = {r: active.pop(r, y) for r in runs}
        for (s, e), y0 in active.items(): out.append(cell_rect(s, y0, e, y - 1))
        active = nxt
    return out
def near(m, r=.35): return cv2.distanceTransform((1 - m).astype(np.uint8), cv2.DIST_L2, 3) * CELL <= r
disk = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
def ring_coords(P): return [[round(x, 3), round(y, 3)] for x, y in list(P.exterior.coords)[:-1]]

def stair_layout(rect, entrance):
    x0, y0, x1, y1 = rect; along_x = entrance in ('x0', 'x1')
    L = (x1 - x0) if along_x else (y1 - y0); Wd = (y1 - y0) if along_x else (x1 - x0)
    per = 11; h = FLOOR_H / (2 * per)
    land = max(.9, min(1.4, (L - per * .26) / 2)); run = (L - 2 * land) / per
    def r(a0, a1, b0, b1):
        if along_x:
            ax = (x0 + a0, x0 + a1) if entrance == 'x0' else (x1 - a1, x1 - a0); return [ax[0], y0 + b0, ax[1], y0 + b1]
        ay = (y0 + a0, y0 + a1) if entrance == 'y0' else (y1 - a1, y1 - a0); return [x0 + b0, ay[0], x0 + b1, ay[1]]
    treads = [{'rect': r(land + i * run, land + (i + 1) * run, 0, Wd / 2), 'height': round((i + 1) * h, 4), 'flight': 0} for i in range(per)]
    treads.append({'rect': r(L - land, L, 0, Wd), 'height': round(per * h, 4), 'flight': -1})
    treads += [{'rect': r(L - land - (i + 1) * run, L - land - i * run, Wd / 2, Wd), 'height': round((per + 1 + i) * h, 4), 'flight': 1} for i in range(per)]
    return treads, r(land, L, 0, Wd), run, land, r(land, L - land, Wd / 2 - .06, Wd / 2 + .06)

plans = {f['key']: f for f in plan['floors']}
TYPICAL = {}
for s in plans['4']['spaces']:
    if s['type'] == 'stair' and s['name'] in STAIR:
        m = mask_of(s['polys']) & poly_mask(TOWER.buffer(-WALL_BAND)); ys, xs = np.nonzero(m); TYPICAL[s['name']] = cell_rect(xs.min(), ys.min(), xs.max(), ys.max())

def floor_spaces(k, inner):
    out = []
    for s in plans[k]['spaces']:
        if s['type'] in ('planter', 'steps', 'drive', 'void') and s['type'] != 'void' or not s['polys']: continue
        m = mask_of(s['polys'], evenodd=s['type'] == 'garage') & inner
        if m.sum() >= 30: out.append({**s, 'mask': m})
    return out

def window_plan(k, O, spaces, skip):
    """Windows along outline edges where a windowed room meets the facade (drawing metres)."""
    lab = np.zeros((H, W), np.int32)
    for i, s in enumerate(spaces, 1): lab[s['mask'] > 0] = i
    P = OUTLINE[k]; coords = list(P.exterior.coords); orient = 1 if P.exterior.is_ccw else -1
    wins = []
    for (ax, ay), (bx, by) in zip(coords, coords[1:]):
        L = abs(bx - ax) + abs(by - ay)
        if L < 1.6: continue
        tx, ty = (bx - ax) / L, (by - ay) / L; nx, ny = ty * orient, -tx * orient  # outward normal
        probe = []
        for t in np.arange(.3, L - .3, .1):
            q = [ax + tx * t - nx * .6, ay + ty * t - ny * .6]; px = to_px(q)
            i = lab[px[1], px[0]] if 0 <= px[0] < W and 0 <= px[1] < H else 0
            probe.append((t, i))
        runs = []
        for t, i in probe:
            if runs and runs[-1][2] == i and abs(t - runs[-1][1] - .1) < 1e-6: runs[-1][1] = t
            else: runs.append([t, t, i])
        for t0, t1, i in runs:
            if not i: continue
            s = spaces[i - 1]
            if s['type'] not in WINDOWED: continue
            span = t1 - t0
            small = s['type'] in ('toilet', 'stair')
            if span < (1.2 if small else 1.8): continue
            n = max(1, int(round((span - .6) / (2.4 if small else 3.2))))
            pitch = span / n; width = min(.9 if small else 2.0, pitch - .7)
            for j in range(n):
                c = t0 + pitch * (j + .5); a = [ax + tx * (c - width / 2), ay + ty * (c - width / 2)]; b = [ax + tx * (c + width / 2), ay + ty * (c + width / 2)]
                mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
                if any(Polygon(e).buffer(.6).contains(Polygon([(mid[0] - .01, mid[1] - .01), (mid[0] + .01, mid[1] - .01), (mid[0], mid[1] + .01)])) for e in skip): continue
                sill, head = (1.5, 2.3) if s['type'] == 'toilet' else (.9, 2.4)
                wins.append({'a': [round(v, 3) for v in a], 'b': [round(v, 3) for v in b], 'normal': [nx, ny], 'sill': sill, 'head': head})
    return wins

floors_out, stairs_by_floor, facade = [], {}, {}
for k in ALL_FLOORS:
    Pk = OUTLINE[k]; O = poly_mask(Pk); inner = cv2.erode(O, np.ones((2 * int(WALL_BAND / CELL) + 1,) * 2, np.uint8)); band = O & (1 - inner)
    spaces = floor_spaces(k, inner)
    if k not in ORDER:  # solid floors: facade windows only
        facade[LABEL[k]] = window_plan(k, O, [s for s in spaces if s['type'] != 'void'], [])
        continue
    free = np.zeros((H, W), np.uint8); solid = np.zeros((H, W), np.uint8); void = np.zeros((H, W), np.uint8)
    for s in spaces:
        if s['type'] == 'elevator': ys, xs = np.nonzero(s['mask']); solid[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = 1
        elif s['type'] == 'void': void |= s['mask']
        elif s['type'] in FREE: free |= s['mask']
    lab = np.zeros((H, W), np.int32)
    for i, sp in enumerate(spaces, 1):
        if sp['type'] in FREE: lab[sp['mask'] > 0] = i
    k3 = np.ones((3, 3), np.uint8)
    hi = cv2.dilate(lab.astype(np.float32), k3); lo = -cv2.dilate(-np.where(lab > 0, lab, 10 ** 6).astype(np.float32), k3)
    open_ids = [i for i, sp in enumerate(spaces, 1) if sp['type'] in OPEN_TO] or [-1]
    interface = ((lab > 0) & (hi != lo) & (lo < 10 ** 6)).astype(np.uint8)
    interface[np.isin(hi, open_ids) & np.isin(lo, open_ids)] = 0
    gap = O & (1 - free) & (1 - void)
    thick = cv2.morphologyEx(gap, cv2.MORPH_OPEN, disk(4))
    walls = ((gap & (1 - cv2.dilate(thick, disk(1)))) | band | solid | interface) & O
    corr_mask = np.zeros((H, W), np.uint8)
    for s in spaces:
        if s['type'] in OPEN_TO: corr_mask |= s['mask']
    doors = np.zeros((H, W), np.uint8); door_list = []
    def carve(cand, width, name, kind, target):
        n, cl, st, _ = cv2.connectedComponentsWithStats(cand.astype(np.uint8), 8)
        if n < 2: return False
        i = 1 + int(np.argmax(st[1:, 4])); comp = cl == i
        ys, xs = np.nonzero(comp); horiz = (xs.max() - xs.min()) >= (ys.max() - ys.min())
        length = ((xs.max() - xs.min()) if horiz else (ys.max() - ys.min())) * CELL
        if length < .7: return False
        w = min(width, length - .2); cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2; half = w / 2 / CELL
        sel = comp & ((np.abs(xs_grid - cx) <= half) if horiz else (np.abs(ys_grid - cy) <= half))
        sel = cv2.dilate(sel.astype(np.uint8), np.ones((5, 1) if horiz else (1, 5), np.uint8)) & walls & (1 - solid) & (1 - band)
        doors[sel > 0] = 1
        p = [ox + cx * CELL, oy + cy * CELL]; d = [w / 2, 0] if horiz else [0, w / 2]
        door_list.append({'name': name, 'kind': kind, 'to': target, 'line': [world([p[0] - d[0], p[1] - d[1]]), world([p[0] + d[0], p[1] + d[1]])]})
        return True
    for s in spaces:
        if s['type'] in OPEN_TO or s['type'] in ('elevator', 'void', 'stair'): continue
        width = 1.0 if s['type'] in ('toilet', 'service', 'mech') else 1.2
        cand = walls & near(s['mask'], .4) & (1 - band) & (1 - solid)
        label = str(s['num']) if s.get('num') is not None else s['name']
        if carve(cand & near(corr_mask, .4), width, label, s['type'], 'corridor'): continue
        others = np.zeros((H, W), np.uint8)
        for t in spaces:
            if t is not s and t['type'] in FREE: others |= t['mask']
        carve(cand & near(others, .4), width, label, s['type'], 'room')
    # Stair halls: same rect on every floor, a 0.2 m wall all round, one door where the drawing puts it.
    prev = stairs_by_floor.get(ORDER[ORDER.index(k) - 1], []) if k != ORDER[0] else []
    stairs = []
    if k != ORDER[-1]:
        upper = {s['name'] for s in plans[ORDER[ORDER.index(k) + 1]]['spaces'] if s['type'] == 'stair'}
        for s in spaces:
            if s['type'] != 'stair' or s['name'] not in upper or s['name'] not in STAIR: continue
            ys, xs = np.nonzero(s['mask']); rect = cell_rect(xs.min(), ys.min(), xs.max(), ys.max())
            if k != 'B': rect = TYPICAL[s['name']]
            treads, hole, run, land, divider = stair_layout(rect, STAIR[s['name']]['entrance'])
            stairs.append({'id': s['name'], 'rect': rect, 'entrance': STAIR[s['name']]['entrance'], 'treads': treads, 'hole': hole, 'divider': divider, 'run': round(run, 3), 'landing': round(land, 3)})
    halls = {st['id']: st['rect'] for st in prev + stairs if st['id'] in STAIR}
    for sid, (x0, y0, x1, y1) in halls.items():
        inside = rect_mask([x0, y0, x1, y1]); ring = rect_mask([x0 - .2, y0 - .2, x1 + .2, y1 + .2]) & (1 - inside) & O
        walls[inside > 0] = 0; doors[inside > 0] = 0; walls |= ring
        side, pos, width = STAIR[sid]['door']
        if side in ('x0', 'x1'):
            xx = x0 - .2 if side == 'x0' else x1; c = y0 + (y1 - y0) * pos; c = min(max(c, y0 + width / 2), y1 - width / 2); r = [xx - .05, c - width / 2, xx + .25, c + width / 2]
        else:
            yy = y0 - .2 if side == 'y0' else y1; c = x0 + (x1 - x0) * pos; c = min(max(c, x0 + width / 2), x1 - width / 2); r = [c - width / 2, yy - .05, c + width / 2, yy + .25]
        doors |= rect_mask(r) & walls & (1 - band)
        # Keep a clear 1.2 m approach outside the stair door (drawing door swings / leftover partition pieces).
        ap = {'x0': [r[0] - 1.2, r[1] - .15, r[0], r[3] + .15], 'x1': [r[2], r[1] - .15, r[2] + 1.2, r[3] + .15],
              'y0': [r[0] - .15, r[1] - 1.2, r[2] + .15, r[1]], 'y1': [r[0] - .15, r[3], r[2] + .15, r[3] + 1.2]}[side]
        walls &= 1 - (rect_mask(ap) & (1 - band) & (1 - ring))
        door_list.append({'name': sid, 'kind': 'stair', 'to': 'corridor', 'line': [world([r[0], r[1]]), world([r[2], r[3]])]})
    if k == '1': walls &= 1 - rect_mask(HALL_OPEN_1F); doors &= 1 - rect_mask(HALL_OPEN_1F)
    if k == 'B':
        walls &= 1 - rect_mask(HALL_CLEAR_B1); doors &= 1 - rect_mask(HALL_CLEAR_B1)
        x0, y0, x1, y1 = RAKE['rect']; n = RAKE['tiers']; d = (x1 - x0) / n
        stairs.append({'id': '理學院階梯教室', 'rect': RAKE['rect'], 'entrance': 'x0', 'tiers': True, 'hole': HALL_OPEN_1F,
                       'treads': [{'rect': [round(x0 + i * d, 3), y0, round(x0 + (i + 1) * d, 3), y1], 'height': round(FLOOR_H * (i + 1) / n, 4), 'flight': 0} for i in range(n)],
                       'run': round(d, 3), 'landing': 0})
    stairs_by_floor[k] = stairs
    # Exterior entrances (drawing positions); runtime decides open, stepped or glazed from the ground outside.
    exits = []
    for (a0, a1) in MANUAL_EXITS.get(k, []):
        horiz = abs(a1[1] - a0[1]) < 1e-6; p = [(a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2]
        r = [min(a0[0], a1[0]) - (0 if horiz else .45), min(a0[1], a1[1]) - (.45 if horiz else 0), max(a0[0], a1[0]) + (0 if horiz else .45), max(a0[1], a1[1]) + (.45 if horiz else 0)]
        sel = rect_mask(r) & (band | walls); probe = None
        for sgn in (1, -1):
            q = [p[0] + (0 if horiz else sgn * .8), p[1] + (sgn * .8 if horiz else 0)]
            if not Pk.buffer(-.01).contains(Polygon([(q[0] - .01, q[1] - .01), (q[0] + .01, q[1] - .01), (q[0], q[1] + .01)])): probe = q
        exits.append({'manual': True, 'rect': rects(sel), 'line': [world(a0), world(a1)], 'outside': world(probe), 'inside': world([2 * p[0] - probe[0], 2 * p[1] - probe[1]])})
    if k == '2': walls &= 1 - rect_mask(OPEN_2F); doors &= 1 - rect_mask(OPEN_2F)
    for r in EXTRA_DOORS.get(k, []):
        doors |= rect_mask(r) & walls & (1 - band); walls &= 1 - (rect_mask(r) & (1 - band)); walls |= doors
    doors &= walls
    walls_final = walls & (1 - doors)
    for e in exits:
        for r in e['rect']: walls_final &= 1 - rect_mask(r)
    n, cl, st, _ = cv2.connectedComponentsWithStats(walls_final.astype(np.uint8), 8)
    for i in range(1, n):
        if st[i, 4] * CELL * CELL < .3 and not (band & (cl == i)).any() and not (solid & (cl == i)).any(): walls_final[cl == i] = 0
    # Window openings cut through the outer band: sill below, head above, glass in between.
    exit_polys = [[[r[0], r[1]], [r[2], r[1]], [r[2], r[3]], [r[0], r[3]]] for e in exits for r in e['rect']]
    wins = window_plan(k, O, [s for s in spaces if s['type'] != 'void'], exit_polys) if k != 'B' else []
    sills, heads, glass = [], [], []
    for w in wins:
        a, b = w['a'], w['b']; r = [min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])]
        r = [r[0] - (.4 if abs(w['normal'][0]) > .5 else 0), r[1] - (.4 if abs(w['normal'][1]) > .5 else 0), r[2] + (.4 if abs(w['normal'][0]) > .5 else 0), r[3] + (.4 if abs(w['normal'][1]) > .5 else 0)]
        cut = rect_mask(r) & band & walls_final
        if cut.sum() < 5: continue
        walls_final &= 1 - cut; rr = rects(cut); sills += [dict(rect=q, top=w['sill']) for q in rr]; heads += [dict(rect=q, bottom=w['head']) for q in rr]
        glass.append({'a': a, 'b': b, 'normal': w['normal'], 'sill': w['sill'], 'head': w['head']})
    floors_out.append({'openAreas': [OPEN_2F] if k == '2' else [], 'key': k, 'label': LABEL[k], 'level': LEVEL[k], 'outline': ring_coords(Pk), 'walls': rects(walls_final.astype(np.uint8)), 'lintels': rects(doors.astype(np.uint8)),
                       'sills': sills, 'heads': heads, 'windows': glass, 'doors': door_list, 'exits': exits, 'stairs': stairs, 'voidMask': void,
                       'spaces': [{'name': s['name'], 'num': s.get('num'), 'type': s['type'], 'anchor': world(s['anchor']) if s.get('anchor') else None} for s in spaces]})

for i, fl in enumerate(floors_out):
    slab = OUTLINE[fl['key']]
    if i > 0:
        for st in stairs_by_floor[ORDER[i - 1]]: slab = slab.difference(box(*st['hole']))
    vm = fl.pop('voidMask')
    if vm.any():
        cs, _ = cv2.findContours(vm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cs:
            pts = [[ox + x * CELL, oy + y * CELL] for x, y in c.reshape(-1, 2)]
            if len(pts) > 2: slab = slab.difference(Polygon(pts).buffer(0))
    if fl['key'] == '2': slab = slab.difference(box(*HOLE_2F))
    slab = slab.buffer(0); parts = [slab] if slab.geom_type == 'Polygon' else list(slab.geoms)
    fl['slab'] = [[ring_coords(p), *[[[round(x, 3), round(y, 3)] for x, y in h.coords][:-1] for h in p.interiors]] for p in parts if p.area > .5]
    fl['slabTriangles'] = [[world(q) for q in list(t.exterior.coords)[:-1]] for p in parts for t in constrained_delaunay_triangles(p).geoms if t.area > 1e-6]
top = OUTLINE[ORDER[-1]]
out = {'version': 2, 'building': 444867693, 'floorHeight': FLOOR_H, 'slab': SLAB, 'transform': T, 'outline': ring_coords(unary_union([OUTLINE[k] for k in ORDER])),
       'towerOutline': ring_coords(TOWER), 'podiumRoofLevel': LEVEL['2'],
       'source': {'plan': 'buildings/zhili/plan.json', 'basis': '使用者確認的平面圖判讀；各層外框依圖面（1F含裙樓與北側門廳），牆為房間分區交界與0.25m外牆，梯間四周封牆、門依圖面方位，外牆依房間開窗；門窗尺寸為模型近似。空房間。',
                  'scope': '使用者2026-11-18：先做2樓以下（B1～2F可走），3F以上為實心量體但外牆窗依圖面；B1只含1F建物下方，室外鋪面下方的停車場待做。'},
       'floors': floors_out, 'facade': facade, 'roofTriangles': [[world(q) for q in list(t.exterior.coords)[:-1]] for t in constrained_delaunay_triangles(top).geoms if t.area > 1e-6],
       'roofLevel': LEVEL[ORDER[-1]] + FLOOR_H, 'solidAbove': {'from': LEVEL[ORDER[-1]] + FLOOR_H, 'to': LEVEL[ALL_FLOORS[-1]] + FLOOR_H}}
p2 = plans['2']; plaza = unary_union([Polygon(q).buffer(0) for sp in p2['spaces'] if sp['type'] == 'plaza' for q in sp['polys']] + [OUTLINE_1F.difference(TOWER)]).buffer(.05).buffer(-.05)
def wrings(P): return [[world(q) for q in list(g.exterior.coords)[:-1]] for g in ([P] if P.geom_type == 'Polygon' else P.geoms) if g.area > 1]
out['site'] = {'groundOutline': [world(q) for q in list(OUTLINE_1F.exterior.coords)[:-1]], 'tower': [world(q) for q in list(TOWER.exterior.coords)[:-1]], 'plaza': wrings(plaza.difference(TOWER)),
               'reference': '1F外框（含裙樓）作中央廣場下層的建物範圍；2F中央廣場＝致理2F圖面廣場＋裙樓屋頂，扣塔樓。'}
(root / 'buildings/zhili/interior.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
print('Zhili interior:', ', '.join(f"{f['label']} walls {len(f['walls'])} doors {len(f['doors'])} windows {len(f['windows'])} exits {len(f['exits'])} stairs {len(f['stairs'])}" for f in floors_out), '| facade windows', {k: len(v) for k, v in facade.items()})
