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
from shapely.geometry import Polygon, box, Point, LineString
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent)); from furnish import furnish_floor

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
HALL_OPEN_1F = [6.6, 20.7, 22.8, 40.3]   # no 1F slab or partitions over the seating; the stage void is the plan void (挑空). The current 1F sheet (2026-11-19) shows 演講廳空調機房 and 118 全家超商A區 as 1F rooms west of it.
HALL_CLEAR_B1 = [6.4, 20.8, 22.8, 40.2]  # seating volume on B1 (B05 rows, B04 under the rake)
FREE = {'classroom', 'office', 'library', 'hall', 'corridor', 'toilet', 'stair', 'service', 'mech', 'balcony', 'plaza', 'unknown', 'garage'}
OPEN_TO = {'corridor', 'plaza', 'garage'}
WINDOWED = {'classroom', 'office', 'library', 'hall', 'service', 'mech', 'unknown', 'corridor', 'toilet', 'stair'}
WALL_BAND = .25
# Stair cores: switchback entrance end and the door read from the drawings (side, position along it).
STAIR = {'甲梯': {'entrance': 'y1', 'door': ('y1', .5, 1.6)}, '乙梯': {'entrance': 'x0', 'door': ('x0', .5, 1.4)},
         '丙梯': {'entrance': 'x0', 'door': ('x0', .5, 1.4)}, '丁梯': {'entrance': 'y1', 'door': ('x0', .82, 1.1)}}
# 己梯 (user 2026-11-18 "己梯要蓋"): open straight stair from the 1F ±0 paving (y55.3) up to the 2F plaza (y48.7);
# the 2F floor is open over it and its top opens onto the plaza.
DRIVE_CLEAR_B1 = [1.76, 59.3, 7.04, 60.5]   # garage mouth: no wall across the driveway ramp (2026-11-22)
DRIVE_OPEN_B1 = [1.75, 59.62, 7.07, 62.3]   # driveway ramp aisle: open to the sky (no ceiling), 2026-11-22
OPEN_2F = [19.0, 46.3, 21.45, 55.4]     # walls cleared (top landing opens onto the plaza)
# Open (semi-outdoor) outline edges, no wall (user 2026-11-19): 2F west of 己梯 between the two columns opens onto
# the upper plaza walkway.
OPEN_EDGES = {'2': [[16.2, 46.85, 16.9, 55.05]]}
HOLE_2F = [19.0, 48.7, 21.45, 55.4]     # 2F slab open over the flight  # B05 演講廳 double door to the south 門廳
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
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location('zhili_walls', root / 'scripts/extract-zhili-walls.py'); EXTRACT = _ilu.module_from_spec(_spec); _spec.loader.exec_module(EXTRACT)
def line_raster(label):
    """Every drawn line of this floor's PDF on the generator grid (needs PyMuPDF)."""
    m = np.zeros((H, W), np.uint8)
    for q in EXTRACT.segments(label):
        cv2.line(m, tuple(to_px(q[:2])), tuple(to_px(q[2:])), 1, 1)
    return m
ROOMISH = {'classroom', 'office', 'service', 'mech', 'unknown', 'library'}
def relabel_rooms(k, spaces, closed, WF, O):
    """Rooms from the current sheet (user 2026-11-19, 1F): every region enclosed by the drawn walls and door leaves
    that holds a room number in the sheet's text becomes a room named by that text; the old plan's rooms (not
    corridors, halls, toilets, stairs) are replaced. Halls/corridors/toilets keep the plan's outlines."""
    import re
    m = closed.copy()
    for d in WF['doors']: m |= poly_mask(LineString([d['hinge'], d['closed']]).buffer(.06, cap_style=2))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, disk(8))   # doorway gaps without a drawn leaf (<= 1.6 m) close a room too
    n, lab_r, st, _ = cv2.connectedComponentsWithStats((O & (1 - m)).astype(np.uint8), 4)
    words = {}
    for w in WF['labels']:
        px = to_px(w['at'])
        if 0 <= px[0] < W and 0 <= px[1] < H and lab_r[px[1], px[0]] > 0: words.setdefault(int(lab_r[px[1], px[0]]), []).append(w)
    keep_masks = np.zeros((H, W), np.uint8)
    for s in spaces:
        if s['type'] in ('hall', 'toilet', 'stair', 'elevator', 'void'): keep_masks |= s['mask']
    rooms = []
    isnum = lambda t: re.fullmatch(r'\d{3}(-\d)?', t)
    pieces = []
    for i, ws in words.items():
        nums = [w for w in ws if isnum(w['text'])]
        area = st[i, 4] * CELL * CELL; comp = (lab_r == i).astype(np.uint8)
        if not nums and 3 <= area <= 400 and (keep_masks[comp > 0] > 0).mean() <= .5:   # 郵局, 全家超商 A–C 區, 營繕組儲藏室
            pieces.append((comp, ws)); continue
        if not nums:   # unnumbered label inside a leaking region: the old plan room under its first word
            w0 = ws[0]; old = next((s for s in spaces if s['type'] in ROOMISH and s['mask'][to_px(w0['at'])[1], to_px(w0['at'])[0]]), None)
            if old is not None:
                piece = (old['mask'] & comp).astype(np.uint8); nn, pl = cv2.connectedComponents(piece, connectivity=4); j = pl[to_px(w0['at'])[1], to_px(w0['at'])[0]]
                if j: pieces.append(((pl == j).astype(np.uint8), [w for w in ws if pl[to_px(w['at'])[1], to_px(w['at'])[0]] == j]))
            continue
        if len(nums) == 1 and 3 <= area <= 400 and (keep_masks[comp > 0] > 0).mean() <= .5:
            pieces.append((comp, ws)); continue
        # Region leaks into the corridor or holds several rooms: take the old plan room under each number, cut by the
        # new walls, and give it the text lines below that number.
        for nw in nums:
            old = next((s for s in spaces if s['type'] in ROOMISH and s['mask'][to_px(nw['at'])[1], to_px(nw['at'])[0]]), None)
            if old is None: continue
            piece = (old['mask'] & comp).astype(np.uint8)
            nn, pl = cv2.connectedComponents(piece, connectivity=4); px = to_px(nw['at'])
            j = pl[px[1], px[0]]
            if j == 0: continue
            mine = [w for w in ws if pl[to_px(w['at'])[1], to_px(w['at'])[0]] == j and (not isnum(w['text']) or w is nw)]
            pieces.append(((pl == j).astype(np.uint8), mine))
    for comp, ws in pieces:
        ws = sorted(ws, key=lambda w: (round(w['at'][1], 0), w['at'][0]))
        num = next((w['text'] for w in ws if isnum(w['text'])), None)
        text = ''.join(w['text'] for w in ws if w['text'] != num)   # the sheet breaks names over lines (鋼琴練／習教室)
        kind = 'classroom' if '教室' in text or '研討室' in text else 'office'
        cs, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); c = max(cs, key=cv2.contourArea)
        poly = [[round(ox + x * CELL, 3), round(oy + y * CELL, 3)] for x, y in c.reshape(-1, 2)]
        ys, xs = np.nonzero(comp)
        rooms.append({'name': f'{num} {text}' if num else text, 'num': num, 'type': kind, 'mask': comp, 'polys': [poly],
                      'anchor': [round(ox + xs.mean() * CELL, 3), round(oy + ys.mean() * CELL, 3)], 'source': 'current-sheet'})
    print(f'  {LABEL[k]} rooms from the current sheet:', ', '.join(r['name'] for r in rooms))
    return [s for s in spaces if s['type'] not in ROOMISH] + rooms
def fit_hall(rect, ink):
    """Fit a stair hall rect to this floor's drawn walls: march outward from inside the hall to the first wall on each
    side; a side with no wall nearby keeps the given edge."""
    x0, y0, x1, y1 = rect; out = list(rect); m = ink.copy()
    m[rect_mask([x0 + .45, y0 + .45, x1 - .45, y1 - .45]) > 0] = 0   # ignore the drawn divider / treads
    for i, (axis, sgn) in enumerate([(0, -1), (1, -1), (0, 1), (1, 1)]):
        hits = []
        for t in np.linspace(.25, .75, 7):
            p = [x0 + (x1 - x0) * t, y0 + (y1 - y0) * t]; p[axis] = rect[i] - sgn * .45
            for step in range(0, 12):
                q = list(p); q[axis] = p[axis] + sgn * step * CELL; px = to_px(q)
                if 0 <= px[0] < W and 0 <= px[1] < H and m[px[1], px[0]]: hits.append(q[axis] - sgn * CELL / 2); break
        if len(hits) >= 4: out[i] = round(float(np.median(hits)), 3)
    return out
WALLS = json.loads((root / 'buildings/zhili/walls.json').read_text())['floors']
# Manual wall / door / opening edits by the user (致理牆門編輯器), grouped by floor label.
OVERRIDES = {}
for _ed in json.loads((root / 'buildings/zhili/overrides.json').read_text()).get('edits', []): OVERRIDES.setdefault(_ed['floor'], []).append(_ed)
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
    # Hairlines drawn across one space (floor patterns, dashed lines) split it into pieces whose 0.1 m gap would
    # become a wall (user 2026-11-19: a wall across the 1F corridor). Close such gaps inside each space, without
    # growing into any other space.
    allm = np.zeros((H, W), np.uint8)
    for s in out: allm |= s['mask']
    for s in out:
        r = 5 if s['type'] in OPEN_TO else 3
        closed = cv2.morphologyEx(s['mask'], cv2.MORPH_CLOSE, np.ones((r, r), np.uint8)) & inner
        s['mask'] = closed & ~(allm & (1 - s['mask'])).astype(bool)
        s['mask'] = s['mask'].astype(np.uint8)
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
    # Walls and doors read straight from the drawing's line work (scripts/extract-zhili-walls.py -> walls.json):
    # every drawn double line is a wall, every swing arc is a door, gaps without a leaf stay open (user 2026-11-19).
    WF = WALLS[LABEL[k]]
    ink = np.zeros((H, W), np.uint8)
    for ring, holes in zip(WF['walls'], WF['wallHoles']):
        if len(ring) > 2: ink |= poly_mask(Polygon(ring, [h for h in holes if len(h) > 2]).buffer(.02, join_style=2))
    ink &= O
    walls = (ink | band | solid) & O
    doors = np.zeros((H, W), np.uint8); door_list = []
    if WF.get('labels'):
        spaces = relabel_rooms(k, spaces, ink | band | solid, WF, O)
    space_polys = [(sp, unary_union([Polygon(q).buffer(0) for q in sp['polys'] if len(q) > 2])) for sp in spaces if sp['type'] in FREE]
    def space_at(q):   # smallest plan space containing q (the corridor polygon wraps around the rooms)
        hits = [(g.area, i) for i, (sp, g) in enumerate(space_polys) if g.buffer(.15).contains(Point(*q))]
        return space_polys[min(hits)[1]][0] if hits else None
    toilet_polys = [g for sp, g in space_polys if sp['type'] == 'toilet']; toilet_doors = []
    for d in WF['doors']:
        h, c, o = np.array(d['hinge']), np.array(d['closed']), np.array(d['open'])
        mid = (h + c) / 2; nrm = (o - h) / max(np.hypot(*(o - h)), 1e-6)
        def side(sg):   # first room met walking 0.6–1.6 m into that side (plan outlines stop short of some walls)
            hits = [space_at(mid + sg * nrm * t) for t in (.6, 1.0, 1.6)]
            return next((sp for sp in hits if sp and sp['type'] not in OPEN_TO), None) or next((sp for sp in hits if sp), None)
        sides = [side(1), side(-1)]
        # User 2026-11-19: toilets are not built for now — their doors are walled up and the rooms sealed below.
        if any(sp and sp['type'] == 'toilet' for sp in sides) or (not any(sides) and any(g.buffer(1.0).contains(Point(*mid)) for g in toilet_polys)):
            toilet_doors.append((h, c)); continue
        room = next((sp for sp in sides if sp and sp['type'] not in OPEN_TO), None) or next((sp for sp in sides if sp), None)
        if room is None or not Pk.buffer(.3).contains(Point(*mid)): continue
        other = next((sp for sp in sides if sp is not room), None)
        # Opening: the full chord from hinge to the closed-leaf end, through the wall thickness (raster rounding of the
        # jambs must not narrow it).
        u_ = (c - h) / max(np.hypot(*(c - h)), 1e-6)   # 8 cm past each end: rasterised jambs must not pinch a 0.8 m leaf
        doors |= poly_mask(LineString([h - u_ * .08, c + u_ * .08]).buffer(.2, cap_style=2))
        label = str(room['num']) if room.get('num') is not None else room['name']
        door_list.append({'name': label, 'kind': room['type'], 'to': (other['type'] if other else 'outside'), 'double': d.get('double', False),
                          'line': [world(list(h)), world(list(c))], 'drawing': [d['hinge'], d['closed']]})
    walls &= 1 - (doors & (1 - solid) & (1 - band))
    # Stair halls: same rect on every floor, a 0.2 m wall all round, one door where the drawing puts it.
    prev = stairs_by_floor.get(ORDER[ORDER.index(k) - 1], []) if k != ORDER[0] else []
    stairs = []
    if k != ORDER[-1]:
        upper = {s['name'] for s in plans[ORDER[ORDER.index(k) + 1]]['spaces'] if s['type'] == 'stair'}
        for s in spaces:
            if s['type'] != 'stair' or s['name'] not in upper or s['name'] not in STAIR: continue
            ys, xs = np.nonzero(s['mask']); rect = cell_rect(xs.min(), ys.min(), xs.max(), ys.max())
            if k != 'B': rect = fit_hall(TYPICAL[s['name']], ink)
            treads, hole, run, land, divider = stair_layout(rect, STAIR[s['name']]['entrance'])
            stairs.append({'id': s['name'], 'rect': rect, 'entrance': STAIR[s['name']]['entrance'], 'treads': treads, 'hole': hole, 'divider': divider, 'run': round(run, 3), 'landing': round(land, 3)})
    halls = {st['id']: st['rect'] for st in prev + stairs if st['id'] in STAIR}
    lines = line_raster(LABEL[k])
    for sid, hr in halls.items():
        # Treads and the divider are generated. The hall's walls follow this floor's drawing (user 2026-11-19: 2F
        # halls were offset and 乙梯 lost its walls): the rect is fitted to the drawn walls, and every side except
        # the door side gets a wall wherever the drawing has a line along it; drawn doors stay open.
        x0, y0, x1, y1 = hr if sid in [st['id'] for st in stairs] else fit_hall(hr, ink)
        inside = rect_mask([x0, y0, x1, y1]); walls[inside > 0] = 0; doors[inside > 0] = 0
        for side, r in {'x0': [x0 - .2, y0 - .2, x0, y1 + .2], 'x1': [x1, y0 - .2, x1 + .2, y1 + .2],
                        'y0': [x0 - .2, y0 - .2, x1 + .2, y0], 'y1': [x0 - .2, y1, x1 + .2, y1 + .2]}.items():
            if side == STAIR[sid]['door'][0]: continue
            band_r = rect_mask([r[0] - .3, r[1] - .3, r[2] + .3, r[3] + .3]) & (1 - inside)
            along = (r[2] - r[0]) > (r[3] - r[1])
            cover = (band_r & lines).any(axis=0 if along else 1)
            span = (band_r.any(axis=0) if along else band_r.any(axis=1))
            if span.sum() and cover[span > 0].mean() >= .6: walls |= rect_mask(r) & O & (1 - doors)
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
    # Drawn exterior doors (swing arcs on the outline) not covered above: open when level with the ground
    # outside, otherwise glazed (runtime).
    manual_mid = [((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2) for a0, a1 in MANUAL_EXITS.get(k, [])]
    for d in WF['doors']:
        h, c = np.array(d['hinge']), np.array(d['closed']); mid = (h + c) / 2
        if d['r'] < .7 or Pk.exterior.distance(Point(*mid)) > .45 or any(np.hypot(mid[0] - q[0], mid[1] - q[1]) < 1.6 for q in manual_mid): continue
        u = (c - h) / max(np.hypot(*(c - h)), 1e-6); nrm = np.array([-u[1], u[0]])
        out_p = mid + nrm * .8
        if Pk.buffer(-.01).contains(Point(*out_p)): out_p = mid - nrm * .8
        if Pk.buffer(-.01).contains(Point(*out_p)): continue
        strip = LineString([h, c]).buffer(.45, cap_style=2)
        sel = poly_mask(strip) & (band | walls)
        if sel.sum() < 3: continue
        exits.append({'manual': False, 'drawn': True, 'rect': rects(sel), 'line': [world(list(h)), world(list(c))], 'outside': world(list(out_p)), 'inside': world(list(2 * mid - out_p))})
        manual_mid.append(tuple(mid))
    if k == '2': walls &= 1 - rect_mask(OPEN_2F); doors &= 1 - rect_mask(OPEN_2F)
    if k == 'B': walls &= 1 - rect_mask(DRIVE_CLEAR_B1); doors &= 1 - rect_mask(DRIVE_CLEAR_B1)
    # Seal the toilets (not built yet): wall up their doors, then clear the partitions and fixtures inside each
    # closed toilet room so it reads as one empty, unreachable room.
    sealed = np.zeros((H, W), np.uint8)
    for h, c in toilet_doors:
        shut = poly_mask(LineString([h, c]).buffer(.1, cap_style=2)); walls |= shut & O; doors &= 1 - shut
    tmask = np.zeros((H, W), np.uint8)
    for g in toilet_polys: tmask |= poly_mask(g)
    zone = cv2.dilate(tmask, disk(6))
    n_t, lab_t, st_t, _ = cv2.connectedComponentsWithStats((O & (1 - walls) & (1 - band)).astype(np.uint8), 4)
    for i in range(1, n_t):
        comp = lab_t == i
        if st_t[i, 4] * CELL * CELL < 20 and (zone[comp] > 0).mean() > .3: sealed[comp] = 1
    if sealed.any():
        room_t = cv2.morphologyEx(sealed, cv2.MORPH_CLOSE, disk(9)) & O
        cs_t, _ = cv2.findContours(room_t, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); room_t = np.zeros_like(room_t)
        cv2.drawContours(room_t, cs_t, -1, 1, -1); room_t &= O
        core = cv2.erode(room_t, np.ones((3, 3), np.uint8))
        walls &= 1 - (core & (1 - solid)); walls |= room_t & (1 - core); doors &= 1 - room_t
        near_t = cv2.dilate(room_t, disk(8))
        exits = [e for e in exits if not any(near_t[to_px(drawing(q))[1], to_px(drawing(q))[0]] for q in [e['inside']]) or e.get('manual')]
    # User edits from the 致理牆門編輯器 page (buildings/zhili/overrides.json) win over the automatic reading.
    for ed in OVERRIDES.get(LABEL[k], []):
        a_, b_ = np.array(ed['a'], float), np.array(ed['b'], float)
        if ed['kind'] == 'wall':
            strip = poly_mask(LineString([a_, b_]).buffer(.08, cap_style=2)) & O; walls |= strip; doors &= 1 - strip
        else:
            u_ = (b_ - a_) / max(np.hypot(*(b_ - a_)), 1e-6)
            cut = poly_mask(LineString([a_ - u_ * .05, b_ + u_ * .05]).buffer(.3, cap_style=2))
            walls &= 1 - (cut & (1 - solid))
            if ed['kind'] == 'door':
                doors |= poly_mask(LineString([a_, b_]).buffer(.2, cap_style=2))
                mid = (a_ + b_) / 2; n_ = np.array([-u_[1], u_[0]])
                sides = [space_at(mid + n_ * .8), space_at(mid - n_ * .8)]
                room = next((sp for sp in sides if sp and sp['type'] not in OPEN_TO), None) or next((sp for sp in sides if sp), None)
                label = (str(room['num']) if room.get('num') is not None else room['name']) if room else '門'
                door_list.append({'name': label, 'kind': room['type'] if room else 'unknown', 'to': 'manual', 'manual': True,
                                  'line': [world(list(a_)), world(list(b_))], 'drawing': [ed['a'], ed['b']]})
    doors &= 1 - walls   # lintel strips over drawn door openings
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
    for r in OPEN_EDGES.get(k, []):
        walls_final &= 1 - rect_mask(r)
        hit = lambda q: q[0] < r[2] and q[2] > r[0] and q[1] < r[3] and q[3] > r[1]
        sills = [s for s in sills if not hit(s['rect'])]; heads = [s for s in heads if not hit(s['rect'])]
        glass = [g for g in glass if not hit([min(g['a'][0], g['b'][0]), min(g['a'][1], g['b'][1]), max(g['a'][0], g['b'][0]), max(g['a'][1], g['b'][1])])]
    # Furniture from room names (scripts/furnish.py); 1.3 m kept clear around doors, exits and stair halls.
    keep = doors.copy()
    for dr in door_list:   # authoritative door positions (world) -> drawing
        (a, b) = [drawing(q) for q in dr['line']]
        keep |= rect_mask([min(a[0], b[0]) - .2, min(a[1], b[1]) - .2, max(a[0], b[0]) + .2, max(a[1], b[1]) + .2])
    for e in exits:
        for r in e['rect']: keep |= rect_mask(r)
    for st in stairs:
        if not st.get('tiers'): keep |= rect_mask(st['rect'])
    for sid, hr in halls.items(): keep |= rect_mask(hr)
    if k == '2': keep |= rect_mask(OPEN_2F)
    keep = cv2.dilate(keep.astype(np.uint8), disk(int(1.3 / CELL)))
    furniture, fblocks = furnish_floor(spaces, walls_final, keep, O, H, W, CELL, ox, oy, CELL)
    if k == 'B':  # 理學院階梯教室: fixed seats on each rake tier (aisles at both ends and down the middle)
        rk = next(st for st in stairs if st.get('tiers'))
        y0r, y1r = RAKE['rect'][1], RAKE['rect'][3]; ym = (y0r + y1r) / 2
        for t in rk['treads'][2:]:   # first two tiers: cross-aisle in front of the stage
            r = t['rect']; h = t['height']; xc = (r[0] + r[2]) / 2
            yy = y0r + 1.0
            while yy + .5 < y1r - 1.0:
                if abs(yy + .25 - ym) > .75 and not (rect_mask([xc - .25, yy, xc + .25, yy + .5]) & keep).any():
                    seat = [round(xc - .25, 3), round(yy, 3), round(xc + .25, 3), round(yy + .5, 3)]
                    furniture += [{'r': seat, 'y': [h, h + .45], 'm': 'fabric', 'room': '理學院階梯教室'},
                                  {'r': [round(r[0] + .02, 3), round(yy, 3), round(r[0] + .08, 3), round(yy + .5, 3)], 'y': [h + .45, h + .95], 'm': 'fabric', 'room': '理學院階梯教室'}]
                    fblocks.append(seat)
                yy += .55
    floors_out.append({'openAreas': [OPEN_2F] if k == '2' else ([DRIVE_OPEN_B1] if k == 'B' else []), 'key': k, 'label': LABEL[k], 'level': LEVEL[k], 'outline': ring_coords(Pk), 'walls': rects(walls_final.astype(np.uint8)), 'lintels': rects(doors.astype(np.uint8)),
                       'sills': sills, 'heads': heads, 'windows': glass, 'furniture': furniture, 'furnitureBlocks': fblocks, 'doors': door_list, 'exits': exits, 'stairs': stairs, 'voidMask': void,
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
    # Suspended T-bar ceiling (user 2026-11-19): over the floor, open over stair halls (this floor's flights and the
    # ones arriving from below), the 己梯 opening and the double-height lecture hall.
    ceil = slab
    for st in stairs_by_floor[fl['key']] + (stairs_by_floor[ORDER[i - 1]] if i > 0 else []):
        ceil = ceil.difference(box(*st['rect']).buffer(.05, join_style=2))
        if st.get('tiers'): ceil = ceil.difference(box(*HALL_OPEN_1F))
    for r in fl['openAreas']: ceil = ceil.difference(box(*r))
    ceil = ceil.buffer(0); cparts = [ceil] if ceil.geom_type == 'Polygon' else [g for g in ceil.geoms if g.geom_type == 'Polygon']
    fl['ceilingTriangles'] = [[world(q) for q in list(t.exterior.coords)[:-1]] for p in cparts if p.area > .5 for t in constrained_delaunay_triangles(p).geoms if t.area > 1e-6]
top = OUTLINE[ORDER[-1]]
out = {'version': 2, 'building': 444867693, 'floorHeight': FLOOR_H, 'slab': SLAB, 'transform': T,
       # Interior finish (user 2026-11-19): square floor tiles, off-white walls, black skirting, light-steel (T-bar)
       # suspended ceiling with recessed lights.
       'finish': {'tile': .6, 'wall': '#efe9da', 'skirting': '#1c1c1e', 'skirtingHeight': .1, 'ceilingHeight': 3.0, 'ceilingPanel': .6}, 'outline': ring_coords(unary_union([OUTLINE[k] for k in ORDER])),
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
