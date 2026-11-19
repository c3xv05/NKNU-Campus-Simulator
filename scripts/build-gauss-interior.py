"""Compile the confirmed Gauss (物理館) 1F–3F floor-plan reading into a walkable interior and a plan-driven facade.

Sources: buildings/gauss/plan.json (user-confirmed reading of the 1:200 drawings, Zhili drawing metres)
and buildings/zhili/building.json (shared drawing-frame transform). Output: buildings/gauss/interior.json.
User 2026-11-18: 1F–3F walkable empty rooms like Zhili; 4F–7F solid with plan windows. Gauss 1F stays at its
game level; 2F meets the lower plaza (Zhili 1F) and 3F the upper-plaza level (not connected).
"""
import json
from pathlib import Path
import numpy as np, cv2
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union, nearest_points
from shapely import constrained_delaunay_triangles

root = Path(__file__).resolve().parents[1]
plan = json.loads((root / 'buildings/gauss/plan.json').read_text())
geom = json.loads((root / 'buildings/gauss/building.json').read_text())['geometry']
T = json.loads((root / 'buildings/zhili/building.json').read_text())['geometry']['drawingFootprint']['transform']
CELL, FLOOR_H, SLAB = .1, geom.get('floorHeight', 3.6), .2
ALL_FLOORS = ['1', '2', '3', '4', '5', '6', '7']
ORDER = ['1', '2', '3']
LEVEL = {k: (int(k) - 1) * FLOOR_H for k in ALL_FLOORS}
LABEL = {k: k + 'F' for k in ALL_FLOORS}
plan_floors = {f['key']: f for f in plan['floors']}
OUTLINE = {k: Polygon(plan_floors[k]['outline']).buffer(0) for k in ORDER}
OUTLINE.update({k: OUTLINE['3'] for k in ALL_FLOORS[3:]})
TOWER = OUTLINE['3']
DECK = Polygon(plan['deck2F']['ring']).buffer(0)
FREE = {'classroom', 'office', 'library', 'hall', 'corridor', 'toilet', 'stair', 'service', 'unknown'}
OPEN_TO = {'corridor'}
WINDOWED = {'classroom', 'office', 'library', 'hall', 'service', 'unknown', 'corridor', 'toilet', 'stair'}
WALL_BAND = .25
# Stair cores (stacked, read from the 1F drawing): switchback entrance end and the corridor door.
STAIR = {'甲梯': {'entrance': 'x1', 'door': ('x1', .5, 1.2)}, '乙梯': {'entrance': 'y0', 'door': ('y0', .5, 1.2)},
         '丙梯': {'entrance': 'y0', 'door': ('y0', .5, 1.2)}, '丁梯': {'entrance': 'y1', 'door': ('y1', .5, 1.2)}}
TYPICAL = plan['stairCores']['rects']
EXTRA_DOORS = {}
OPEN_2F = None
off = plan['floorOffsets']['v']; MP = 0.0817 * 200 / 250
def dz(k, dx, dy):  # 1F-drawing display px (2000-wide preview) -> Zhili drawing metres for floor k
    ox, oy = off[k]; return ((dx * 1.28 / 2 + ox - 1084.5) * MP - 6.17, (dy * 1.28 / 2 + oy - 611) * MP + 66.6)
# Exterior doors (drawing positions; snapped onto the floor outline): east main 玄關, west entrance, west-court door;
# 2F doors onto the 接未來廣場 deck (lower plaza).
# Exterior doors read from the drawings: (point, width, wall) where wall 'x' = the door lies on a wall of constant x
# (passage along x), 'y' = constant y. The door is cast onto the floor outline along that axis.
EXIT_POINTS = {'1': [(dz('1', 1119, 1058), 3.0, 'y'), (dz('1', 428, 872), 1.8, 'x'), (dz('1', 1130, 690), 1.6, 'y')],
               '2': [(dz('2', 588, 535), 1.6, 'x'), (dz('2', 1068, 632), 1.6, 'y')]}
from shapely.geometry import LineString
def cast_exit(P, pt, width, wall):
    px, py = pt
    ray = LineString([(px - 40, py), (px + 40, py)]) if wall == 'x' else LineString([(px, py - 40), (px, py + 40)])
    hit = P.exterior.intersection(ray); pts = [hit] if hit.geom_type == 'Point' else list(getattr(hit, 'geoms', []))
    q = min(pts, key=lambda h: h.distance(Point(pt)))
    if wall == 'x': return [[round(q.x, 3), round(py - width / 2, 3)], [round(q.x, 3), round(py + width / 2, 3)]]
    return [[round(px - width / 2, 3), round(q.y, 3)], [round(px + width / 2, 3), round(q.y, 3)]]
MANUAL_EXITS = {k: [cast_exit(OUTLINE[k], p, w, wl) for p, w, wl in v] for k, v in EXIT_POINTS.items()}

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

plans = {k: plan_floors[k if k in plan_floors else '3'] for k in ALL_FLOORS}

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
        upper = set(STAIR)
        for s in spaces:
            if s['type'] != 'stair' or s['name'] not in STAIR or any(q['id'] == s['name'] for q in stairs): continue
            ys, xs = np.nonzero(s['mask']); rect = cell_rect(xs.min(), ys.min(), xs.max(), ys.max())
            rect = TYPICAL[s['name']]
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
    stairs_by_floor[k] = stairs
    # Exterior entrances (drawing positions); runtime decides open, stepped or glazed from the ground outside.
    exits = []
    for (a0, a1) in MANUAL_EXITS.get(k, []):
        horiz = abs(a1[1] - a0[1]) < abs(a1[0] - a0[0]); p = [(a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2]
        r = [min(a0[0], a1[0]) - (0 if horiz else .45), min(a0[1], a1[1]) - (.45 if horiz else 0), max(a0[0], a1[0]) + (0 if horiz else .45), max(a0[1], a1[1]) + (.45 if horiz else 0)]
        sel = rect_mask(r) & (band | walls); probe = None
        ex, ey = a1[0] - a0[0], a1[1] - a0[1]; el = (ex * ex + ey * ey) ** .5; nx, ny = -ey / el, ex / el
        for sgn in (1, -1):
            q = [p[0] + sgn * nx * .8, p[1] + sgn * ny * .8]
            if not Pk.contains(Point(q)): probe = q; break
        exits.append({'manual': True, 'rect': rects(sel), 'line': [world(a0), world(a1)], 'outside': world(probe), 'inside': world([2 * p[0] - probe[0], 2 * p[1] - probe[1]])})
    for r in EXTRA_DOORS.get(k, []):
        doors |= rect_mask(r) & walls & (1 - band); walls &= 1 - (rect_mask(r) & (1 - band)); walls |= doors
    # Clear a 1.2 m approach inside each exterior door (drawn door-swing arcs would otherwise block it).
    for (a0, a1) in MANUAL_EXITS.get(k, []):
        ex, ey = a1[0] - a0[0], a1[1] - a0[1]; el = (ex * ex + ey * ey) ** .5; nx, ny = -ey / el, ex / el; mx, my = (a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2
        if Pk.contains(Point(mx - nx * .8, my - ny * .8)): nx, ny = -nx, -ny   # (nx,ny) now points inward
        quad = Polygon([(a0[0] - ex / el * .15, a0[1] - ey / el * .15), (a1[0] + ex / el * .15, a1[1] + ey / el * .15),
                        (a1[0] + ex / el * .15 + nx * 1.4, a1[1] + ey / el * .15 + ny * 1.4), (a0[0] - ex / el * .15 + nx * 1.4, a0[1] - ey / el * .15 + ny * 1.4)])
        walls &= 1 - poly_mask(quad)
    doors &= walls
    walls_final = walls & (1 - doors)
    for e in exits:
        for r in e['rect']: walls_final &= 1 - rect_mask(r)
    n, cl, st, _ = cv2.connectedComponentsWithStats(walls_final.astype(np.uint8), 8)
    for i in range(1, n):
        if st[i, 4] * CELL * CELL < .3 and not (band & (cl == i)).any() and not (solid & (cl == i)).any(): walls_final[cl == i] = 0
    # Window openings cut through the outer band: sill below, head above, glass in between.
    exit_polys = [[[r[0], r[1]], [r[2], r[1]], [r[2], r[3]], [r[0], r[3]]] for e in exits for r in e['rect']]
    wins = window_plan(k, O, [s for s in spaces if s['type'] != 'void'], exit_polys)
    sills, heads, glass = [], [], []
    for w in wins:
        a, b = w['a'], w['b']; r = [min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])]
        r = [r[0] - (.4 if abs(w['normal'][0]) > .5 else 0), r[1] - (.4 if abs(w['normal'][1]) > .5 else 0), r[2] + (.4 if abs(w['normal'][0]) > .5 else 0), r[3] + (.4 if abs(w['normal'][1]) > .5 else 0)]
        cut = rect_mask(r) & band & walls_final
        if cut.sum() < 5: continue
        walls_final &= 1 - cut; rr = rects(cut); sills += [dict(rect=q, top=w['sill']) for q in rr]; heads += [dict(rect=q, bottom=w['head']) for q in rr]
        glass.append({'a': a, 'b': b, 'normal': w['normal'], 'sill': w['sill'], 'head': w['head']})
    floors_out.append({'key': k, 'label': LABEL[k], 'level': LEVEL[k], 'outline': ring_coords(Pk), 'walls': rects(walls_final.astype(np.uint8)), 'lintels': rects(doors.astype(np.uint8)),
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
    slab = slab.buffer(0); parts = [slab] if slab.geom_type == 'Polygon' else list(slab.geoms)
    fl['slab'] = [[ring_coords(p), *[[[round(x, 3), round(y, 3)] for x, y in h.coords][:-1] for h in p.interiors]] for p in parts if p.area > .5]
    fl['slabTriangles'] = [[world(q) for q in list(t.exterior.coords)[:-1]] for p in parts for t in constrained_delaunay_triangles(p).geoms if t.area > 1e-6]
top = OUTLINE[ORDER[-1]]
def tris(P): return [[world(q) for q in list(t.exterior.coords)[:-1]] for g in ([P] if P.geom_type == 'Polygon' else list(P.geoms)) for t in constrained_delaunay_triangles(g).geoms if t.area > 1e-6]
# Roofs of lower floors not covered by the floor above (the 2F deck is lower plaza and rendered by the courtyard).
exposed = []
for a, b in zip(ORDER, ORDER[1:]):
    R = OUTLINE[a].difference(OUTLINE[b]).difference(DECK.buffer(.05)).buffer(0)
    if R.area > 1: exposed.append({'level': LEVEL[b], 'triangles': tris(R)})
out = {'version': 2, 'building': 444867692, 'key': 'gauss', 'signText': '高斯大樓', 'floorHeight': FLOOR_H, 'slab': SLAB, 'transform': T, 'outline': ring_coords(unary_union([OUTLINE[k] for k in ORDER])),
       'towerOutline': ring_coords(TOWER), 'exposedRoofs': exposed,
       'source': {'plan': 'buildings/gauss/plan.json', 'basis': '使用者確認的物理館1F～3F平面判讀；外框由室內房間合成，牆為房間分區交界與0.25m外牆，四座梯間封牆、門朝走廊；門窗尺寸為模型近似。空房間。',
                  'scope': '使用者2026-11-18：1F～3F可走，4F～7F實心量體、外牆窗依3F圖面。'},
       'floors': floors_out, 'facade': facade, 'roofTriangles': tris(top),
       'roofLevel': LEVEL[ORDER[-1]] + FLOOR_H, 'solidAbove': {'from': LEVEL[ORDER[-1]] + FLOOR_H, 'to': LEVEL[ALL_FLOORS[-1]] + FLOOR_H},
       'site': {'groundOutline': [world(q) for q in list(OUTLINE['1'].exterior.coords)[:-1]]}}
(root / 'buildings/gauss/interior.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
print('Gauss interior:', ', '.join(f"{f['label']} walls {len(f['walls'])} doors {len(f['doors'])} windows {len(f['windows'])} exits {len(f['exits'])} stairs {len(f['stairs'])}" for f in floors_out), '| facade windows', {k: len(v) for k, v in facade.items()})
