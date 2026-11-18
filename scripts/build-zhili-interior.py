"""Compile the reviewed Zhili floor-plan draft into a walkable empty-room interior.

Source: buildings/zhili/plan.json (drawing metres, user-confirmed room reading) and
buildings/zhili/building.json (tower ring + drawingFootprint placement).
Output: buildings/zhili/interior.json — per floor slab triangles, axis-aligned wall
rectangles (drawing frame), door/lintel rectangles, exterior openings and stair treads.
Walls are derived from the gaps between the plan's room regions inside the tower outline;
door positions are model approximations (centre of the shared wall), not surveyed.
Only the tower footprint is built (B1–8F); the podium and B1 garage outside it are pending.
"""
import json, math
from pathlib import Path
import numpy as np, cv2
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles

root = Path(__file__).resolve().parents[1]
plan = json.loads((root / 'buildings/zhili/plan.json').read_text())
geom = json.loads((root / 'buildings/zhili/building.json').read_text())['geometry']
T = geom['drawingFootprint']['transform']
outline = Polygon(geom['drawingFootprint']['drawingRing']).buffer(0)
CELL = .1
FLOOR_H = geom.get('floorHeight', 3.6)
ORDER = ['B', '1', '2', '3', '4', '5', '6', '7', '8']
LEVEL = {k: (i - 1) * FLOOR_H for i, k in enumerate(ORDER)}  # B1 = -3.6, 1F = 0
FREE = {'classroom', 'office', 'library', 'hall', 'corridor', 'toilet', 'stair', 'service', 'mech', 'balcony',
        'plaza', 'unknown', 'garage'}
OPEN_TO = {'corridor', 'plaza'}
WALL_BAND = .25
# Stair entrance ends read from the drawings (door / 上下 marks); one stacked stairwell per core.
STAIR_ENTRANCE = {'甲梯': 'y1', '乙梯': 'x0', '丙梯': 'x0', '丁梯': 'y1'}
TYPICAL_RECT = {}

minx, miny, maxx, maxy = outline.bounds
ox, oy = minx - 1, miny - 1
W, H = int((maxx - minx + 2) / CELL) + 1, int((maxy - miny + 2) / CELL) + 1

def to_px(p): return [int(round((p[0] - ox) / CELL)), int(round((p[1] - oy) / CELL))]
def mask_of(polys, evenodd=False):
    m = np.zeros((H, W), np.uint8)
    if evenodd:
        for p in polys:
            t = np.zeros_like(m); cv2.fillPoly(t, [np.array([to_px(q) for q in p], np.int32)], 1); m ^= t
    else:
        cv2.fillPoly(m, [np.array([to_px(q) for q in p], np.int32) for p in polys if len(p) > 2], 1)
    return m
def world(p): return [round(T['a'] * p[0] - T['b'] * p[1] + T['tx'], 4), round(T['b'] * p[0] + T['a'] * p[1] + T['tz'], 4)]
def cell_rect(x0, y0, x1, y1):  # inclusive cell indices -> drawing-metre rect
    return [round(ox + x0 * CELL - CELL / 2, 3), round(oy + y0 * CELL - CELL / 2, 3), round(ox + x1 * CELL + CELL / 2, 3), round(oy + y1 * CELL + CELL / 2, 3)]
def rects(mask):
    """Greedy rectangle cover: merge identical row runs downwards."""
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
        nxt = {}
        for r in runs:
            nxt[r] = active.pop(r, y)
        for (s, e), y0 in active.items(): out.append(cell_rect(s, y0, e, y - 1))
        active = nxt
    return out

O = mask_of([list(outline.exterior.coords)])
inner = cv2.erode(O, np.ones((2 * int(WALL_BAND / CELL) + 1,) * 2, np.uint8))
band = O & (1 - inner)
disk = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

def stair_layout(rect, entrance):
    """Two-flight switchback inside an axis-aligned rect; entrance = side ('x0','x1','y0','y1')."""
    x0, y0, x1, y1 = rect; along_x = entrance in ('x0', 'x1')
    L = (x1 - x0) if along_x else (y1 - y0); Wd = (y1 - y0) if along_x else (x1 - x0)
    risers = 22; per = 11; h = FLOOR_H / risers
    land = max(.9, min(1.4, (L - per * .26) / 2)); run = (L - 2 * land) / per
    def r(a0, a1, b0, b1):  # a = along from entrance, b = across
        if along_x:
            ax = (x0 + a0, x0 + a1) if entrance == 'x0' else (x1 - a1, x1 - a0)
            return [ax[0], y0 + b0, ax[1], y0 + b1]
        ay = (y0 + a0, y0 + a1) if entrance == 'y0' else (y1 - a1, y1 - a0)
        return [x0 + b0, ay[0], x0 + b1, ay[1]]
    treads = []
    for i in range(per):  # flight 0 on the first half, rising away from the entrance
        treads.append({'rect': r(land + i * run, land + (i + 1) * run, 0, Wd / 2), 'height': round((i + 1) * h, 4), 'flight': 0})
    treads.append({'rect': r(L - land, L, 0, Wd), 'height': round(per * h, 4), 'flight': -1})
    for i in range(per):  # flight 1 on the other half, rising back toward the entrance; last run meets the upper slab
        treads.append({'rect': r(L - land - (i + 1) * run, L - land - i * run, Wd / 2, Wd), 'height': round((per + 1 + i) * h, 4), 'flight': 1})
    hole = r(land, L, 0, Wd)  # upper slab opening; the entrance landing strip stays solid
    return treads, hole, run, land

# Typical-floor (4F) stair halls are reused for 1F–7F so every core stacks exactly.
for s in plans_pre['4']['spaces'] if (plans_pre := {f['key']: f for f in plan['floors']}) else []:
    if s['type'] == 'stair' and s['name'] in STAIR_ENTRANCE:
        m = mask_of(s['polys']) & inner; ys, xs = np.nonzero(m); TYPICAL_RECT[s['name']] = cell_rect(xs.min(), ys.min(), xs.max(), ys.max())
floors_out = []
stairs_by_floor = {}
plans = {f['key']: f for f in plan['floors']}
for k in ORDER:
    f = plans[k]; spaces = []
    for s in f['spaces']:
        if s['type'] in ('planter', 'steps', 'drive') or not s['polys']: continue
        poly = unary_union([Polygon(p).buffer(0) for p in s['polys'] if len(p) > 2]) if s['type'] != 'garage' else None
        m = mask_of(s['polys'], evenodd=s['type'] == 'garage') & inner
        if m.sum() < 30: continue
        spaces.append({**s, 'mask': m})
    free = np.zeros((H, W), np.uint8); solid = np.zeros((H, W), np.uint8); void = np.zeros((H, W), np.uint8)
    for s in spaces:
        if s['type'] == 'elevator':
            ys, xs = np.nonzero(s['mask']); solid[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = 1
        elif s['type'] == 'void': void |= s['mask']
        elif s['type'] in FREE: free |= s['mask']
    # Interfaces between two different spaces are partitions even where the traced regions touch.
    lab = np.zeros((H, W), np.int32)
    for i, sp in enumerate(spaces, 1):
        if sp['type'] in FREE: lab[sp['mask'] > 0] = i
    k3 = np.ones((3, 3), np.uint8)
    hi = cv2.dilate(lab.astype(np.float32), k3); lo = -cv2.dilate(-np.where(lab > 0, lab, 10**6).astype(np.float32), k3)
    corridor_ids = {i for i, sp in enumerate(spaces, 1) if sp['type'] in OPEN_TO}
    interface = ((lab > 0) & (hi != lo) & (lo < 10**6)).astype(np.uint8)
    same_open = np.isin(hi, list(corridor_ids) or [-1]) & np.isin(lo, list(corridor_ids) or [-1])
    interface[same_open] = 0
    gap = O & (1 - free) & (1 - void)
    # Thick leftovers (covered outdoor areas, shafts) become open floor; thin ones are partitions.
    thick = cv2.morphologyEx(gap, cv2.MORPH_OPEN, disk(4))
    walls = (gap & (1 - cv2.dilate(thick, disk(1)))) | band | solid | interface
    walls &= O
    # Doors: rooms open to a corridor at the centre of the shared wall; corridor pieces merge fully.
    def near(m, r=.35):
        return cv2.distanceTransform((1 - m).astype(np.uint8), cv2.DIST_L2, 3) * CELL <= r
    corridors = [s for s in spaces if s['type'] in OPEN_TO]
    corr_mask = np.zeros((H, W), np.uint8)
    for s in corridors: corr_mask |= s['mask']
    doors = np.zeros((H, W), np.uint8); door_list = []
    for i, a in enumerate(corridors):
        for b in corridors[i + 1:]:
            doors |= (walls & near(a['mask']) & near(b['mask']) & (1 - band) & (1 - solid)).astype(np.uint8)
    def carve(cand, width, name, kind, target):
        n, lab, st, cen = cv2.connectedComponentsWithStats(cand.astype(np.uint8), 8)
        if n < 2: return False
        i = 1 + int(np.argmax(st[1:, 4])); comp = (lab == i)
        ys, xs = np.nonzero(comp); horiz = (xs.max() - xs.min()) >= (ys.max() - ys.min())
        length = ((xs.max() - xs.min()) if horiz else (ys.max() - ys.min())) * CELL
        if length < .7: return False
        w = min(width, length - .2); cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2; half = w / 2 / CELL
        sel = comp & ((np.abs(np.arange(W)[None, :] - cx) <= half) if horiz else (np.abs(np.arange(H)[:, None] - cy) <= half))
        sel = cv2.dilate(sel.astype(np.uint8), np.ones((5, 1) if horiz else (1, 5), np.uint8)) & walls & (1 - solid)
        doors[sel > 0] = 1
        p = [ox + cx * CELL, oy + cy * CELL]; d = [w / 2, 0] if horiz else [0, w / 2]
        door_list.append({'name': name, 'kind': kind, 'to': target, 'line': [world([p[0] - d[0], p[1] - d[1]]), world([p[0] + d[0], p[1] + d[1]])]})
        return True
    for s in spaces:
        if s['type'] in OPEN_TO or s['type'] in ('elevator', 'void', 'garage', 'stair'): continue
        width = 1.6 if s['type'] == 'stair' else 1.0 if s['type'] in ('toilet', 'service', 'mech') else 1.2
        near_s = near(s['mask'], .4); cand = walls & near_s & (1 - band) & (1 - solid)
        label = str(s['num']) if s.get('num') is not None else s['name']
        if carve(cand & near(corr_mask, .4), width, label, s['type'], 'corridor'): continue
        others = np.zeros((H, W), np.uint8)
        for t in spaces:
            if t is not s and t['type'] in FREE: others |= t['mask']
        carve(cand & near(others, .4), width, label, s['type'], 'room')
    # Exterior openings where a corridor reaches the outline (runtime decides open vs glass).
    outside = (1 - O).astype(np.uint8)
    exits = []
    cand = (band & near(corr_mask, .5) & near(outside, .4)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(cand, 8)
    for i in range(1, n):
        comp = lab == i; ys, xs = np.nonzero(comp); horiz = (xs.max() - xs.min()) >= (ys.max() - ys.min())
        length = ((xs.max() - xs.min()) if horiz else (ys.max() - ys.min())) * CELL
        if length < 1.2: continue
        w = min(2.4, length - .2); cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2; half = w / 2 / CELL
        sel = comp & ((np.abs(np.arange(W)[None, :] - cx) <= half) if horiz else (np.abs(np.arange(H)[:, None] - cy) <= half))
        sel = cv2.dilate(sel.astype(np.uint8), np.ones((7, 1) if horiz else (1, 7), np.uint8)) & band
        p = [ox + cx * CELL, oy + cy * CELL]; d = [w / 2, 0] if horiz else [0, w / 2]
        # outward probe: the side of the band that is outside the outline
        probe = None
        for sgn in (1, -1):
            q = [p[0] + (0 if horiz else sgn * .6), p[1] + (sgn * .6 if horiz else 0)]
            if not outline.contains(Polygon([(q[0] - .01, q[1] - .01), (q[0] + .01, q[1] - .01), (q[0] + .01, q[1] + .01)])): probe = q
        exits.append({'rect': rects(sel.astype(np.uint8)), 'line': [world([p[0] - d[0], p[1] - d[1]]), world([p[0] + d[0], p[1] + d[1]])], 'outside': world(probe or p), 'inside': world([2 * p[0] - (probe or p)[0], 2 * p[1] - (probe or p)[1]])})
    # Stairs: switchbacks from this floor to the next, entrance on the short side facing the corridor.
    stairs = []
    if k != ORDER[-1]:
        upper = {s['name'] for s in plans[ORDER[ORDER.index(k) + 1]]['spaces'] if s['type'] == 'stair'}
        for s in spaces:
            if s['type'] != 'stair' or s['name'] not in upper or s['name'] not in STAIR_ENTRANCE: continue
            ys, xs = np.nonzero(s['mask']); rect = cell_rect(xs.min(), ys.min(), xs.max(), ys.max())
            if k != 'B' and s['name'] in TYPICAL_RECT: rect = TYPICAL_RECT[s['name']]
            entrance = STAIR_ENTRANCE[s['name']]
            treads, hole, run, land = stair_layout(rect, entrance)
            stairs.append({'id': s['name'], 'rect': rect, 'entrance': entrance, 'treads': treads, 'hole': hole, 'run': round(run, 3), 'landing': round(land, 3)})
    # Open the stair hall to the corridor along its entrance landing (and the arrival landing above).
    for st in stairs + [dict(x, arrival=True) for x in stairs_by_floor.get(ORDER[ORDER.index(k) - 1], [])] if k != 'B' else stairs:
        x0, y0, x1, y1 = st['rect']; e = st['entrance']; land = st['landing']
        strip = {'x0': [x0 - .45, y0 - .45, x0 + land, y1 + .45], 'x1': [x1 - land, y0 - .45, x1 + .45, y1 + .45], 'y0': [x0 - .45, y0 - .45, x1 + .45, y0 + land], 'y1': [x0 - .45, y1 - land, x1 + .45, y1 + .45]}[e]
        a = to_px(strip[:2]); b = to_px(strip[2:]); zone = np.zeros((H, W), np.uint8); zone[a[1]:b[1] + 1, a[0]:b[0] + 1] = 1
        doors |= (walls & zone & near(corr_mask, .5) & (1 - band) & (1 - solid)).astype(np.uint8)
    stairs_by_floor[k] = stairs
    # Nothing but the hall walls around a stairwell: clear traced leftovers inside every flight/landing.
    for st in stairs + (stairs_by_floor.get(ORDER[ORDER.index(k) - 1], []) if k != 'B' else []):
        a = to_px(st['rect'][:2]); b = to_px(st['rect'][2:]); walls[a[1]:b[1] + 1, a[0]:b[0] + 1] = 0; doors[a[1]:b[1] + 1, a[0]:b[0] + 1] = 0
    doors &= walls
    walls_final = walls & (1 - doors)
    for e in exits:
        for r in e['rect']: x0, y0, x1, y1 = to_px(r[:2]) + to_px(r[2:]); walls_final[y0:y1 + 1, x0:x1 + 1] = 0
    floors_out.append({'key': k, 'label': f['label'], 'level': LEVEL[k], 'walls': rects(walls_final.astype(np.uint8)), 'lintels': rects(doors.astype(np.uint8)),
                       'doors': door_list, 'exits': exits, 'stairs': stairs, 'voidMask': void,
                       'spaces': [{'name': s['name'], 'num': s.get('num'), 'type': s['type'], 'anchor': world(s['anchor']) if s.get('anchor') else None} for s in spaces]})

# Slabs: each floor's slab minus the stair openings arriving from below and the plan's voids.
for i, fl in enumerate(floors_out):
    slab = outline
    if i > 0:
        for st in stairs_by_floor[ORDER[i - 1]]: slab = slab.difference(box(*st['hole']))
    vm = fl.pop('voidMask')
    if vm.any():
        cs, _ = cv2.findContours(vm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cs:
            pts = [[ox + x * CELL, oy + y * CELL] for x, y in c.reshape(-1, 2)]
            if len(pts) > 2: slab = slab.difference(Polygon(pts).buffer(0))
    slab = slab.buffer(0)
    parts = [slab] if slab.geom_type == 'Polygon' else list(slab.geoms)
    fl['slab'] = [[[[round(x, 3), round(y, 3)] for x, y in p.exterior.coords][:-1], *[[[round(x, 3), round(y, 3)] for x, y in h.coords][:-1] for h in p.interiors]] for p in parts if p.area > .5]
    fl['slabTriangles'] = [[world(q) for q in list(t.exterior.coords)[:-1]] for p in parts for t in constrained_delaunay_triangles(p).geoms if t.area > 1e-6]
roof = [[world(q) for q in list(t.exterior.coords)[:-1]] for t in constrained_delaunay_triangles(outline).geoms if t.area > 1e-6]
out = {'version': 1, 'building': 444867693, 'floorHeight': FLOOR_H, 'transform': T, 'outline': [list(p) for p in list(outline.exterior.coords)[:-1]],
       'source': {'plan': 'buildings/zhili/plan.json', 'basis': '使用者確認的平面圖判讀草稿；牆由房間分區間隙推得，門位取共用牆中點，皆為模型近似。空房間，未放家具。',
                  'scope': '只建塔樓外框內的B1～8F；裙樓（1F階梯教室／門廳、2F屋頂廣場）與塔樓外B1停車場待處理。層高照遊戲每層3.6m（B1=-3.6m）。'},
       'floors': floors_out, 'roofTriangles': roof, 'roofLevel': LEVEL['8'] + FLOOR_H}
(root / 'buildings/zhili/interior.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
print('Zhili interior:', ', '.join(f"{f['label']} walls {len(f['walls'])} doors {len(f['doors'])} exits {len(f['exits'])} stairs {len(f['stairs'])}" for f in floors_out))
