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
import json, math
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
# User 2026-11-24: the triangular bay east of 乙梯 is glazing from 1F to 8F (every sheet draws it), and the SE toilet
# block reaches the drawn east wall x64.79 and south wall y64.35 (the ring stopped at x63.8 / y63.9).
NO_WINDOWS = {'1': [box(21.2, 48.0, 21.7, 55.4), box(16.2, 47.9, 21.5, 48.4)]}   # user 2026-11-24: 己梯 side / top walls have no windows
BUILT_TOILETS = {'1': unary_union([box(58.6, 58.2, 64.8, 64.4), box(21.4, 46.2, 26.4, 55.3), box(35.5, 4.5, 42.1, 10.9)])}   # 1F SE toilets drawn from the sheet (overrides.json zt1-*), not sealed
BAY = Polygon([(64.3, 54.85), (65.72, 54.85), (65.72, 55.7), (66.97, 56.8), (65.72, 57.9), (65.72, 58.8), (64.3, 58.8)])
BAY_GLASS = [([65.86, 55.79], [66.88, 56.8], [.7, -.714]), ([66.88, 56.8], [65.86, 57.81], [.7, .714])]
TOILET_SE = box(63.7, 58.7, 64.79, 64.35)
TOWER = unary_union([TOWER.difference(box(64.4, 54.8, 66.0, 58.85)), BAY, TOILET_SE, box(58.6, 63.8, 64.79, 64.35)]).buffer(.01, join_style=2).buffer(-.01, join_style=2)
CELL, FLOOR_H, SLAB = .1, geom.get('floorHeight', 3.6), .2
ALL_FLOORS = ['B', '1', '2', '3', '4', '5', '6', '7', '8']
ORDER = ['B', '1', '2']  # user 2026-11-18: walkable interior for 2F and below; 3F+ solid
LEVEL = {k: (i - 1) * FLOOR_H for i, k in enumerate(ALL_FLOORS)}
LABEL = {'B': 'B1', **{k: k + 'F' for k in ALL_FLOORS[1:]}}
# 1F outline read from the 1F drawing: podium (lecture hall, west lobby, 戊梯) + tower + north lobby to x=64.4.
# The covered area under 2F at the south end (x<26.7, y>55.2) and the 己梯 corner stay outdoors.
# User 2026-11-24: the 1F wall beside 己梯 is the drawn toilet wall x21.35–21.5 (no windows), and the wall above it is
# the drawn y48.1 line (the strip x16.25–21.35, y46.3–48.15 is indoors).
OUTLINE_1F = Polygon([(1.2, 15.5), (33.1, 15.5), (33.1, 10.8), (35.4, 10.8), (35.4, 4.3), (48.4, 4.3), (48.4, 10.8), (53.2, 10.8),
                      (53.2, 20.3), (61.3, 20.3), (61.3, 25.8), (64.4, 25.8), (64.4, 54.9), (65.8, 54.9), (65.8, 58.8), (63.8, 58.8),
                      (63.8, 63.9), (58.6, 63.9), (58.6, 66.6), (26.7, 66.6), (26.7, 55.2), (21.35, 55.2), (21.35, 48.15), (16.25, 48.15), (16.25, 46.3), (6.3, 46.3),
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
# User 2026-11-23: B1 walls follow the drawing. B02/B03 and the strip below them (x7.07-26.8, y55-66.6) belong to the drawing's B1 even
# though the 1F outline / lower plaza stop short. Where the old south teaching stairs (STAIR_KEEP) overlap, the basement is NOT hollowed
# out: the outline keeps its notch there, so the stair mass stays solid ground and nobody can fall through it.
# The stepped planters beside the main steps (campus.courtyard.planters, source 'zhili') stand on the ground there: B1 must not
# cover them with its outer wall (user 2026-11-23), so the strip stops short of them.
PLANTERS_Z = unary_union([Polygon([drawing(q) for q in pl['ring']]) for pl in camp['courtyard'].get('planters', []) if pl.get('source') == 'zhili']).buffer(.1, join_style=2)
B1_SW = box(7.07, 55.0, 26.8, 66.6).difference(PLANTERS_Z)
# Current 1F sheet (user 2026-11-19: "以我後來上傳的平面圖為準"): 全家超商B區 extends south of the old west-lobby
# front to y≈50.2 (7.8 m wide, x 8.5–16.25); west of it is the open 學生休憩廣場.
OUTLINE_1F = unary_union([OUTLINE_1F, box(8.5, 46.2, 16.25, 50.25)]).buffer(.05, join_style=2).buffer(-.05, join_style=2)
OUTLINE_1F = unary_union([OUTLINE_1F.difference(box(64.4, 54.8, 66.0, 58.85)), BAY, TOILET_SE, box(58.6, 63.8, 64.79, 64.35),
                          box(16.26, 55.18, 21.4, 55.3), box(16.26, 54.89, 16.7, 55.59)])   # user 2026-11-24: drawn wall + column south of 己梯.buffer(.01, join_style=2).buffer(-.01, join_style=2)
OUTLINE_1F = OUTLINE_1F.difference(STAIR_KEEP.difference(box(21.35, 46.0, 22.5, 56.0)).difference(box(16.0, 55.15, 21.5, 55.33))).buffer(0)   # the 1F toilet wall stays on its drawn line x21.35 beside 己梯
B1_OUTLINE = B1_PLAN.intersection(unary_union([OUTLINE_1F, *covered, B1_SW]).buffer(.3).buffer(-.3)).intersection(box(-50, -50, 200, 66.6)).buffer(0)
if B1_OUTLINE.geom_type != 'Polygon': B1_OUTLINE = max(B1_OUTLINE.geoms, key=lambda g: g.area)
B1_OUTLINE = B1_OUTLINE.difference(STAIR_KEEP)
if B1_OUTLINE.geom_type != 'Polygon': B1_OUTLINE = max(B1_OUTLINE.geoms, key=lambda g: g.area)
# The old stair footprint (STAIR_KEEP) lies inside the basement outline at 己梯; punching it out left a walled-off box in the driveway
# (user 2026-11-22). The stairs rise from the plaza above B1, so the basement floor continues underneath: drop interior holes.
B1_OUTLINE = Polygon(B1_OUTLINE.exterior).buffer(0)
# B1 driveway (user 2026-11-19 "地下室加入車道以及停車格"): the drawing's 車道 loop and the ramp to the 車道入口 on the
# south edge. In the game the ground at the ramp mouth is ~0.16 m below B1, so the ramp is a level cutting open to the sky.
RAMP = box(1.76, 58.0, 7.07, 66.6)
# User 2026-11-22 (B1 SE corner): the 1F outline notches the basement here (toilet block x59.0-64.9 / y58.7-64.4 and the
# B01 east wall at x59.1 were clipped by 0.45-1 m). The drawing's B1 walls run to those lines, so restore them.
B1_SE_FIX = unary_union([box(58.6, 58.7, 64.9, 64.4), box(58.6, 64.0, 59.15, 66.6)])
B1_OUTLINE = unary_union([B1_OUTLINE, B1_SE_FIX.intersection(B1_PLAN.buffer(.3))]).buffer(0)
B1_OUTLINE = unary_union([B1_OUTLINE, RAMP.intersection(B1_PLAN.buffer(.2))]).buffer(.05, join_style=2).buffer(-.05, join_style=2)
if B1_OUTLINE.geom_type != 'Polygon': B1_OUTLINE = max(B1_OUTLINE.geoms, key=lambda g: g.area)
B1_OUTLINE = B1_OUTLINE.simplify(.05)
OUTLINE = {'B': B1_OUTLINE, '1': OUTLINE_1F, '2': TOWER, **{k: TOWER for k in ALL_FLOORS[3:]}}
# 理學院階梯教室 (user): one double-height hall over B1 and 1F; stage at B1 level, seating tiers rise to the 1F lobby.
# User 2026-11-24 (new B1/1F sheets): 11 tiers, 1.0 m deep, tier lines x11.24…21.24 (back wall of B04 at x21.3); the first tread starts x10.24.
RAKE = {'rect': [10.24, 20.9, 21.24, 40.1], 'tiers': 11}
# Seats from the sheet: columns on every tread against the next riser; y blocks 21.65–26.15 (10), 27.3–33.3 (13), 34.45–38.95 (10).
SEAT_BLOCKS = [(21.65, 26.15, 10), (27.3, 33.3, 13), (34.45, 38.95, 10)]
# 舞台 (+0.8 m, drawing −290 cm over the −370 cm hall floor) x1.4–6.74, y24.7–36.3 with a 4-step stair at each corner notch down to the hall.
# User 2026-11-24 (2nd pass): the 準備室 floors are the SAME raised platform (solid down to the B1 floor), joined to the stage by the doorway beside
# the west wall; the 戊梯 hall below the lower 準備室 climbs from the 門廳 (3 steps) to a landing at stage height (door to the 準備室), then 戊梯 up to 1F.
# A 0.2 m curb above the stage floor runs along the stage front and the sides of the corner stairs (not a full wall).
STAGE_H, STAGE_MIRROR, CURB_TOP = .8, 61.0, 1.0
STAGE_POLY = [(1.45, 24.7), (4.96, 24.7), (5.84, 25.68), (6.74, 26.52), (6.74, 34.48), (5.84, 35.32), (4.96, 36.3), (1.45, 36.3)]
PREP_TOP = [(1.45, 21.05), (6.8, 21.05), (6.8, 22.96), (4.96, 24.7), (1.45, 24.7)]
PREP_BOT = [(1.45, 36.3), (4.96, 36.3), (6.8, 38.04), (6.8, 40.8), (1.45, 40.8)]   # the lower room runs to its door wall y40.7
STAIR_QUAD = [(4.96, 24.68), (6.4, 23.4), (7.24, 24.34), (5.84, 25.68)]   # top corner stair (W, N, E, S); the bottom one is its mirror
STAGE_WALLS = [((6.8, 21.0), (6.8, 22.96), .07, None), ((2.4, 24.7), (4.96, 24.7), .05, None),
               ((6.8, 22.96), (4.96, 24.7), .07, None)]   # user 2026-11-25: the slanted 準備室 wall beside each corner stair is a real full-height wall (was only a 1 m curb)          # full-height room walls (rect walls, exact)
STAGE_CURBS = [((5.84, 25.68), (7.24, 24.34), .07, CURB_TOP), ((5.84, 25.68), (6.74, 26.52), .07, CURB_TOP),
               ((6.74, 26.52), (6.74, 34.48), .07, CURB_TOP)]   # diagonal ones are drawn as true rotated boxes (no raster teeth)
# 戊梯 (B1): small flight from the 門廳, landing at stage height, lower flight W, half landing, upper flight E up to the 1F floor (2.8 m over 14 risers)
WU_TREADS = [[6.5, 42.45, 6.75, 43.95, .2], [6.25, 42.45, 6.5, 43.95, .4], [6.0, 42.45, 6.25, 43.95, .6], [4.95, 40.7, 6.74, 42.45, .8], [4.95, 42.45, 6.0, 43.95, .8]]
WU_TREADS += [[round(4.95 - (i + 1) * 2.0 / 6, 3), 42.5, round(4.95 - i * 2.0 / 6, 3), 43.95, round(1.0 + .2 * i, 2)] for i in range(6)]
WU_TREADS += [[1.5, 41.0, 2.95, 43.95, 2.2]]
WU_TREADS += [[round(2.95 + i * 2.0 / 7, 3), 41.0, round(2.95 + (i + 1) * 2.0 / 7, 3), 42.45, round(2.4 + .2 * i, 2)] for i in range(7)]
WU_HOLE = [1.5, 41.0, 4.95, 43.95]
# 1F: the slanted walls round the stage void (挑空) were raster teeth; now true rotated boxes (user 2026-11-25). (a, b, half thickness)
FLOOR_DIAGS = {'1': [((6.78, 23.05), (5.0, 24.82), .07), ((5.89, 25.7), (6.54, 26.36), .05), ((5.03, 36.45), (6.55, 37.96), .07)]}
STAGE_VOID_1F = [1.45, 24.95, 6.5, 36.3]   # nothing stands inside the void between the stage and the 2F level except what the plan draws on its rim
RAMP_EAST_WALL = [7.15, 60.1, 7.45, 62.4]   # driveway east wall (user 2026-11-25): one continuous full-height wall, no gap above/between the old low sills
RAISED_DOOR_ZONE = unary_union([Polygon(PREP_BOT), Polygon(PREP_TOP), Polygon(STAGE_POLY), box(4.95, 40.7, 6.8, 42.5)]).buffer(.12)   # floors at stage height (+0.8): doors there are raised with the floor
HALL_OPEN_1F = [6.6, 20.7, 21.4, 40.3]   # no 1F slab or partitions over the seating; the stage void is the plan void (挑空). The current 1F sheet (2026-11-19) shows 演講廳空調機房 and 118 全家超商A區 as 1F rooms west of it.
HALL_CLEAR_B1 = [6.4, 20.8, 21.1, 40.2]  # seating volume on B1 (B05 rows, B04 under the rake)
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
# User 2026-11-23: the driveway floor is a real slope from the garage mouth (B1 floor) down to the sidewalk-tile pad at the road
# (y66.6). Measured in the running game: B1 floor top 35.449, pad top 35.129 -> drop 0.32 m (scripts/ + interior.js ramp mesh).
RAMP_SLOPE = {'rect': [1.76, 60.5, 7.07, 66.6], 'tileFrom': 99, 'drop': -1.05}   # default only: interior.js re-measures it from the live road height; negative = the ramp climbs to the road
DRIVE_OPEN_B1 = [1.75, 59.62, 7.07, 62.3]   # driveway ramp aisle: open to the sky (no ceiling), 2026-11-22
VOID_CLEAR_2F = [16.3, 58.2, 21.2, 66.8]   # 2F corner void (挑空): no outer walls on the west and south sides, only the corner column (user 2026-11-22 photo)
# 己梯 (stair x19.32-21.44, y48.65-53.08, fixed) against the wall north of it: 1F toilet wall at x21.95 and the 2F meeting-room wall at x21.45.
STAIR_WALL_FILL = {'2': [[21.45, 48.6, 21.5, 53.1]]}   # 1F: the drawn wall x21.35–21.5 already meets the stair (user 2026-11-24)
OPEN_2F = [19.0, 46.3, 21.45, 55.4]     # walls cleared (top landing opens onto the plaza)
# Open (semi-outdoor) outline edges, no wall (user 2026-11-19): 2F west of 己梯 between the two columns opens onto
# the upper plaza walkway.
OPEN_EDGES = {'2': [[16.2, 46.85, 16.9, 55.05]]}
HOLE_2F = [19.0, 48.7, 21.45, 55.4]     # 2F slab open over the flight  # B05 演講廳 double door to the south 門廳
# Entrances on the 1F outline (drawing metres): north lobby, corridor south end, east main lobby, two west-lobby doors.
MANUAL_EXITS = {'B': [[[1.9, 66.6], [6.95, 66.6]]],   # 車道入口 (ramp mouth)
                '1': [[[64.4, 26.6], [64.4, 29.4]], [[26.7, 55.4], [26.7, 57.5]], [[38.4, 66.6], [42.4, 66.6]],
                      [[6.7, 46.3], [8.45, 46.3]]],   # west lobby → 學生休憩廣場 (the other doors are inside 全家超商B區 now)
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
# Fine wall output (user 2026-11-24: wall thicknesses did not match the drawing). The 0.1 m raster above decides
# topology (doors, rooms, sealing, furniture); the emitted wall boxes are redrawn on a 0.025 m grid so every wall
# drawn on the sheet keeps the sheet's own thickness instead of growing to whole 0.1 m cells (+0.02 m buffer).
FS = 4; FINE = CELL / FS; fox, foy = ox - CELL / 2, oy - CELL / 2
def up(m): return np.repeat(np.repeat(m.astype(np.uint8), FS, 0), FS, 1)
def fine_poly(P, m=None):
    m = np.zeros((H * FS, W * FS), np.uint8) if m is None else m
    tf = lambda c: np.array([[int(round(((x - fox) / FINE - .5) * 16)), int(round(((y - foy) / FINE - .5) * 16))] for x, y in c], np.int32)
    for g in ([P] if P.geom_type == 'Polygon' else list(getattr(P, 'geoms', []))):
        if g.is_empty or g.geom_type != 'Polygon': continue
        cv2.fillPoly(m, [tf(g.exterior.coords)], 1, shift=4)
        for h in g.interiors: cv2.fillPoly(m, [tf(h.coords)], 0, shift=4)
    return m
def fine_rects(mask):
    out, active = [], {}
    Hf, Wf = mask.shape
    for y in range(Hf + 1):
        runs = set()
        if y < Hf:
            row = mask[y]; d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
            runs = set(zip(np.nonzero(d == 1)[0].tolist(), (np.nonzero(d == -1)[0] - 1).tolist()))
        nxt = {r: active.pop(r, y) for r in runs}
        for (s_, e_), y0 in active.items(): out.append([round(fox + s_ * FINE, 3), round(foy + y0 * FINE, 3), round(fox + (e_ + 1) * FINE, 3), round(foy + y * FINE, 3)])
        active = nxt
    return out
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
def snap_doors(doors, edits):
    """User 2026-11-25: doors sit square in their wall. Drawn swing arcs give hinge->closed chords a degree or three off axis (and two leaves of one
    double door, or doors side by side in one wall, disagree by a few cm), so every chord is made exactly axis-aligned, doors that share a wall line
    take one common wall coordinate, and a drawn door that sits on top of a hand-placed one (front and back of the same opening) is dropped."""
    out = []
    for d in doors:
        h, c = np.array(d['hinge'], float), np.array(d['closed'], float); v = c - h
        if abs(v[0]) < abs(v[1]): cross = (h[0] + c[0]) / 2; h[0] = c[0] = cross; axis = 'x'
        else: cross = (h[1] + c[1]) / 2; h[1] = c[1] = cross; axis = 'y'
        out.append({**d, 'hinge': h.tolist(), 'closed': c.tolist(), '_axis': axis})
    manual = [(np.array(e['a'], float), np.array(e['b'], float)) for e in edits if e['kind'] == 'door']
    def seg(d):
        i = 1 if d['_axis'] == 'x' else 0; lo, hi = sorted((d['hinge'][i], d['closed'][i])); j = 1 - i; return i, lo, hi, d['hinge'][j]
    keep = []
    for d in out:
        i, lo, hi, cross = seg(d); dup = False
        for a_, b_ in manual:   # a hand-placed door in the same wall line and overlapping span replaces the drawn one
            ax = 'x' if abs(b_[0] - a_[0]) < abs(b_[1] - a_[1]) else 'y'
            if ax != d['_axis']: continue
            l2, h2 = sorted((a_[i], b_[i])); c2 = a_[1 - i]
            if abs(c2 - cross) < .6 and min(hi, h2) - max(lo, l2) > .3 * min(hi - lo, h2 - l2): dup = True; break
        d['_dup'] = dup; keep.append(d)   # flagged, not removed: exterior-entrance detection still reads the drawn arc
    out = keep; par = list(range(len(out)))
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for a in range(len(out)):
        for b in range(a + 1, len(out)):
            if out[a]['_axis'] != out[b]['_axis']: continue
            i, la, ha, ca = seg(out[a]); _, lb, hb, cb = seg(out[b])
            if abs(ca - cb) < .35 and max(la, lb) - min(ha, hb) < .3: par[find(a)] = find(b)   # side by side (or overlapping) in one wall line
    groups = {}
    for a in range(len(out)): groups.setdefault(find(a), []).append(a)
    for g in groups.values():
        i0 = out[g[0]]['_axis']; ci = 0 if i0 == 'x' else 1; mean = float(np.mean([out[a]['hinge'][ci] for a in g]))
        for a in g: out[a]['hinge'][ci] = out[a]['closed'][ci] = round(mean, 3)
    return out
# Manual wall / door / opening edits by the user (致理牆門編輯器), grouped by floor label.
OVERRIDES = {}
for _ed in json.loads((root / 'buildings/zhili/overrides.json').read_text()).get('edits', []): OVERRIDES.setdefault(_ed['floor'], []).append(_ed)
for _fl in ('1F', '2F'):   # glazed bay beside 乙梯 (user 2026-11-24), same panes as the solid floors above
    for _i, (_a, _b, _n) in enumerate(BAY_GLASS): OVERRIDES.setdefault(_fl, []).append({'id': f'bay-{_fl}-{_i}', 'floor': _fl, 'kind': 'window', 'a': _a, 'b': _b, 'normal': _n, 'sill': .1, 'head': FLOOR_H - .3})
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
        facade[LABEL[k]] = [w for w in window_plan(k, O, [s for s in spaces if s['type'] != 'void'], []) if not BAY.buffer(.05).contains(Point((w['a'][0] + w['b'][0]) / 2, (w['a'][1] + w['b'][1]) / 2))] + \
                           []   # the bay glass of 3F–8F is cut into the hollowed 乙梯 hall (upperFloors)
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
    WF = {**WALLS[LABEL[k]], 'doors': snap_doors(WALLS[LABEL[k]]['doors'], OVERRIDES.get(LABEL[k], []))}
    ink = np.zeros((H, W), np.uint8)
    for ring, holes in zip(WF['walls'], WF['wallHoles']):
        if len(ring) > 2: ink |= poly_mask(Polygon(ring, [h for h in holes if len(h) > 2]).buffer(.02, join_style=2))
    ink &= O
    ink_fine = np.zeros((H * FS, W * FS), np.uint8)
    for ring, holes in zip(WF['walls'], WF['wallHoles']):
        if len(ring) > 2: fine_poly(Polygon(ring, [h for h in holes if len(h) > 2]).buffer(0), ink_fine)
    walls = (ink | band | solid) & O
    doors = np.zeros((H, W), np.uint8); door_list = []
    if WF.get('labels') and k != 'B':   # B1 (current sheet) labels are mostly curves; keep plan.json rooms
        spaces = relabel_rooms(k, spaces, ink | band | solid, WF, O)
    space_polys = [(sp, unary_union([Polygon(q).buffer(0) for q in sp['polys'] if len(q) > 2])) for sp in spaces if sp['type'] in FREE]
    def space_at(q):   # smallest plan space containing q (the corridor polygon wraps around the rooms)
        hits = [(g.area, i) for i, (sp, g) in enumerate(space_polys) if g.buffer(.15).contains(Point(*q))]
        return space_polys[min(hits)[1]][0] if hits else None
    toilet_polys = [g for sp, g in space_polys if sp['type'] == 'toilet']; toilet_doors = []
    for d in WF['doors']:
        if d.get('_dup'): continue   # a hand-placed door already stands in this opening
        h, c, o = np.array(d['hinge']), np.array(d['closed']), np.array(d['open'])
        mid = (h + c) / 2; nrm = (o - h) / max(np.hypot(*(o - h)), 1e-6)
        if any(e_['kind'] == 'nodoor' and e_['rect'][0] <= mid[0] <= e_['rect'][2] and e_['rect'][1] <= mid[1] <= e_['rect'][3] for e_ in OVERRIDES.get(LABEL[k], [])): continue   # user: drawn swing that is a stall front, not a room door
        def side(sg):   # first room met walking 0.6–1.6 m into that side (plan outlines stop short of some walls)
            hits = [space_at(mid + sg * nrm * t) for t in (.6, 1.0, 1.6)]
            return next((sp for sp in hits if sp and sp['type'] not in OPEN_TO), None) or next((sp for sp in hits if sp), None)
        sides = [side(1), side(-1)]
        # User 2026-11-19: toilets are not built for now — their doors are walled up and the rooms sealed below.
        if k != 'B' and not (k in BUILT_TOILETS and BUILT_TOILETS[k].contains(Point(*mid))) and (any(sp and sp['type'] == 'toilet' for sp in sides) or (not any(sides) and any(g.buffer(1.0).contains(Point(*mid)) for g in toilet_polys))):
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
            if k == '1' and s['name'] == '乙梯': rect = [rect[0], rect[1], min(rect[2], 65.72), rect[3]]   # east end on the bay's side walls
            treads, hole, run, land, divider = stair_layout(rect, STAIR[s['name']]['entrance'])
            extra = []
            if k == '1' and s['name'] == '乙梯':
                # User 2026-11-24: the half landing runs on into the glazed bay (drawn landing arc), up to the glass.
                lh = next(t['height'] for t in treads if t['flight'] == -1); inner = BAY.buffer(-.12, join_style=2)
                for xb in np.arange(rect[2], 66.9, .1):
                    sl = inner.intersection(box(xb, rect[1], xb + .1, rect[3]))
                    if sl.is_empty or sl.area < .005: continue
                    b_ = sl.bounds; extra.append([round(xb, 3), round(b_[1], 3), round(xb + .1, 3), round(b_[3], 3)])
                treads += [{'rect': r_, 'height': lh, 'flight': -1, 'bay': True} for r_ in extra]
            stairs.append({'id': s['name'], 'rect': rect, 'entrance': STAIR[s['name']]['entrance'], 'treads': treads, 'hole': hole, 'divider': divider, 'run': round(run, 3), 'landing': round(land, 3), 'extraHoles': extra})
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
        # Raised platform (stage + 準備室), corner stairs graded along the flight, 戊梯: all on the 2.5 cm grid so diagonal edges have no 10 cm teeth.
        Xf = (fox + (np.arange(W * FS) + .5) * FINE).astype(np.float32)[None, :]; Yf = (foy + (np.arange(H * FS) + .5) * FINE).astype(np.float32)[:, None]
        mir = lambda Q: [(x, STAGE_MIRROR - y) for x, y in Q]
        plat = unary_union([Polygon(STAGE_POLY), Polygon(PREP_TOP), Polygon(PREP_BOT)]); plat_m = fine_poly(plat); step_m = {}
        for sign in (1, -1):
            Q = STAIR_QUAD if sign == 1 else mir(STAIR_QUAD)
            qm = fine_poly(Polygon(Q)); Wq, Nq = np.array(Q[0]), np.array(Q[1]); u = (Nq - Wq) / np.hypot(*(Nq - Wq))
            a_ = (Xf - Wq[0]) * u[0] + (Yf - Wq[1]) * u[1]
            for lo, hi, h_ in ((-9, .68, STAGE_H), (.68, 1.03, .6), (1.03, 1.38, .4), (1.38, 9, .2)):
                m_ = qm & ((a_ >= lo) & (a_ < hi)).astype(np.uint8)
                if h_ == STAGE_H: plat_m |= m_
                else: step_m.setdefault(h_, np.zeros_like(plat_m)); step_m[h_] |= m_
        st_treads = [{'rect': r_, 'height': STAGE_H, 'flight': 0} for r_ in fine_rects(plat_m)]
        for h_, m_ in step_m.items(): st_treads += [{'rect': r_, 'height': h_, 'flight': 0} for r_ in fine_rects(m_)]
        stairs.append({'id': '舞台', 'rect': [1.4, 21.0, 7.3, 40.85], 'entrance': 'x0', 'tiers': True, 'mat': 'wood', 'hole': [0, 0, .001, .001], 'treads': st_treads, 'run': .3, 'landing': 0})
        stairs.append({'id': '戊梯', 'rect': [1.4, 40.75, 6.8, 44.0], 'entrance': 'x1', 'tiers': True, 'hole': WU_HOLE, 'treads': [{'rect': r_[:4], 'height': r_[4], 'flight': 0} for r_ in WU_TREADS], 'run': .3, 'landing': 0})
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
        exits.append({'manual': True, 'rect': rects(sel), 'line': [world(a0), world(a1)], 'outside': world(probe), 'inside': world([2 * p[0] - probe[0], 2 * p[1] - probe[1]])} | ({'header': False} if k == 'B' else {}))   # driveway mouth: no beam across the opening (user 2026-11-23)
    # Drawn exterior doors (swing arcs on the outline) not covered above: open when level with the ground
    # outside, otherwise glazed (runtime).
    manual_mid = [((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2) for a0, a1 in MANUAL_EXITS.get(k, [])]
    for d in WF['doors']:
        h, c = np.array(d['hinge']), np.array(d['closed']); mid = (h + c) / 2
        if d['r'] < .7 or Pk.exterior.distance(Point(*mid)) > .45 or any(np.hypot(mid[0] - q[0], mid[1] - q[1]) < 1.6 for q in manual_mid): continue
        if any(e_['kind'] == 'noexit' and e_['rect'][0] <= mid[0] <= e_['rect'][2] and e_['rect'][1] <= mid[1] <= e_['rect'][3] for e_ in OVERRIDES.get(LABEL[k], [])): continue   # user: a drawn door that is not an exterior exit
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
    if k == '2': walls &= 1 - rect_mask(VOID_CLEAR_2F); doors &= 1 - rect_mask(VOID_CLEAR_2F)
    if k == 'B': walls &= 1 - rect_mask(DRIVE_CLEAR_B1); doors &= 1 - rect_mask(DRIVE_CLEAR_B1)
    # Seal the toilets (not built yet): wall up their doors, then clear the partitions and fixtures inside each
    # closed toilet room so it reads as one empty, unreachable room.
    sealed = np.zeros((H, W), np.uint8)
    for h, c in toilet_doors:
        shut = poly_mask(LineString([h, c]).buffer(.1, cap_style=2)); walls |= shut & O; doors &= 1 - shut
    tmask = np.zeros((H, W), np.uint8)
    for g in toilet_polys: tmask |= poly_mask(g) if k != 'B' and not (k in BUILT_TOILETS and BUILT_TOILETS[k].intersects(g)) else 0   # B1 toilets and BUILT_TOILETS are hand-drawn (overrides.json)
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
    ov_sills, ov_fixtures, door_leaves = [], [], []; ov_fine = np.zeros((H * FS, W * FS), np.uint8); ov_wall = np.zeros((H, W), np.uint8)   # ov_wall: user wall strips survive the small-blob filter
    for ed in OVERRIDES.get(LABEL[k], []):
        if ed['kind'] in ('noexit', 'nodoor', 'window'): continue
        if ed['kind'] == 'clear':   # rect: drop generated walls inside (exterior band / solid cores stay)
            walls &= 1 - (rect_mask(ed['rect']) & (1 - solid) & (1 - band)); continue
        if ed['kind'] == 'fixture':   # rect, h (top above floor), m (material): sinks, toilets, urinals ...
            r_ = [round(float(v), 3) for v in ed['rect']]
            ov_fixtures.append({'r': r_, 'y': [float(ed.get('y0', 0)), float(ed['h'])], 'm': ed.get('m', 'white'), 'room': ed.get('room', '廁所')}); continue
        a_, b_ = np.array(ed['a'], float), np.array(ed['b'], float)
        if ed['kind'] == 'wall' and ed.get('top'):   # low partition (e.g. toilet stall, 'top' metres, half-thickness 'w')
            w_ = float(ed.get('w', .04)); L_ = LineString([a_, b_]).buffer(w_, cap_style=2)
            xs_, ys_ = L_.exterior.xy
            ov_sills.append({'rect': [round(min(xs_), 3), round(min(ys_), 3), round(max(xs_), 3), round(max(ys_), 3)], 'top': float(ed['top'])})
            walls &= 1 - poly_mask(L_); continue
        if ed['kind'] == 'wall':
            strip = poly_mask(LineString([a_, b_]).buffer(float(ed.get('w', .08)), cap_style=2)) & O; walls |= strip; doors &= 1 - strip; ov_wall |= strip; fine_poly(LineString([a_, b_]).buffer(float(ed.get('w', .08)), cap_style=2), ov_fine)
        else:
            u_ = (b_ - a_) / max(np.hypot(*(b_ - a_)), 1e-6)
            cut = poly_mask(LineString([a_ - u_ * .05, b_ + u_ * .05]).buffer(.3, cap_style=2))
            # A long stroke along a wall (user: 以平面圖為準) clears the generated blobs but keeps the exterior wall band.
            keep_band = band if np.hypot(*(b_ - a_)) >= 2.5 else 0
            walls &= 1 - (cut & (1 - solid) & (1 - keep_band))
            if ed['kind'] == 'door' and ed.get('closed'):   # closed leaf standing in the opening (wooden, blocks)
                nn_ = np.array([-u_[1], u_[0]])   # leaf fills the whole opening (the door mask clears 0.2 m beyond each end of the drawn line), thicker than any wall (user: could see through)
                lf = Polygon([a_ - u_ * .22 - nn_ * .16, b_ + u_ * .22 - nn_ * .16, b_ + u_ * .22 + nn_ * .16, a_ - u_ * .22 + nn_ * .16]).bounds
                door_leaves.append([round(lf[0], 3), round(lf[1], 3), round(lf[2], 3), round(lf[3], 3)])
            if ed['kind'] == 'door':
                doors |= poly_mask(LineString([a_, b_]).buffer(.2, cap_style=2))
                mid = (a_ + b_) / 2; n_ = np.array([-u_[1], u_[0]])
                sides = [space_at(mid + n_ * .8), space_at(mid - n_ * .8)]
                room = next((sp for sp in sides if sp and sp['type'] not in OPEN_TO), None) or next((sp for sp in sides if sp), None)
                label = (str(room['num']) if room.get('num') is not None else room['name']) if room else '門'
                door_list.append({'name': label, 'kind': room['type'] if room else 'unknown', 'to': 'manual', 'manual': True,
                                  'line': [world(list(a_)), world(list(b_))], 'drawing': [ed['a'], ed['b']]})
    diag_walls, block_only, curb_sills = [], [], []
    if k == 'B':   # 準備室 room walls (exact rects) and the stage curbs; diagonal ones are rotated boxes at runtime (diagWalls) with a collision-only fine raster
        walls &= 1 - (rect_mask([1.5, 21.05, 6.95, 40.6]) & (1 - solid) & (1 - band))
        walls &= 1 - (rect_mask([1.5, 41.0, 4.95, 43.95]) & (1 - solid) & (1 - band))   # 戊梯 well: generated lines are not walls
        m_ = poly_mask(LineString([(6.8, 40.0), (6.8, 40.7)]).buffer(.07, cap_style=2)) & O; walls |= m_; doors &= 1 - m_; ov_wall |= m_   # east wall of the lower 準備室 down to its door wall
        for lst in (STAGE_WALLS, STAGE_CURBS):
            for (pa, pb, w_, top_) in lst:
                for (qa, qb) in (((pa[0], pa[1]), (pb[0], pb[1])), ((pa[0], STAGE_MIRROR - pa[1]), (pb[0], STAGE_MIRROR - pb[1]))):
                    axis = abs(qa[0] - qb[0]) < 1e-6 or abs(qa[1] - qb[1]) < 1e-6
                    g_ = LineString([qa, qb]).buffer(w_, cap_style=2)
                    if axis and top_ is None:
                        m_ = poly_mask(g_) & O; walls |= m_; doors &= 1 - m_; ov_wall |= m_
                    elif axis:
                        b_ = g_.bounds; curb_sills.append({'rect': [round(v, 3) for v in b_], 'top': top_})
                    else:
                        diag_walls.append({'a': [round(qa[0], 3), round(qa[1], 3)], 'b': [round(qb[0], 3), round(qb[1], 3)], 'w': w_, 'top': top_})
                        block_only += fine_rects(fine_poly(g_))
    for (pa, pb, w_) in FLOOR_DIAGS.get(k, []):   # slanted walls drawn as true rotated boxes (collision keeps a fine raster); the raster teeth are cleared first
        g_ = LineString([pa, pb]).buffer(w_, cap_style=2)
        walls &= 1 - (poly_mask(LineString([pa, pb]).buffer(.24, cap_style=2)) & (1 - solid) & (1 - band))
        ux, uy = (pb[0] - pa[0]), (pb[1] - pa[1]); ln_ = math.hypot(ux, uy); ex, ey = ux / ln_ * .06, uy / ln_ * .06   # 6 cm overlap into the straight walls it meets
        diag_walls.append({'a': [round(pa[0] - ex, 3), round(pa[1] - ey, 3)], 'b': [round(pb[0] + ex, 3), round(pb[1] + ey, 3)], 'w': w_, 'top': None})
        block_only += fine_rects(fine_poly(g_))
    if k == '1': walls &= 1 - (rect_mask(STAGE_VOID_1F) & (1 - solid) & (1 - band))   # stage void: no leftover wall bits or beams inside it
    doors &= 1 - walls   # lintel strips over drawn door openings
    walls_final = walls & (1 - doors)
    for e in exits:
        for r in e['rect']: walls_final &= 1 - rect_mask(r)
    # 2026-11-24 (user): the 己梯 must touch the wall on its north side; the wall is thickened toward the stair, the stair stays put.
    for r in STAIR_WALL_FILL.get(k, []): walls_final |= rect_mask(r)
    # Weld hairline slits (< 0.2 m) between wall pieces so no sliver of daylight shows between them (user 2026-11-24); doors/exits stay open.
    weld = cv2.morphologyEx(walls_final.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) & (1 - doors)
    for e in exits:
        for r in e['rect']: weld &= 1 - rect_mask(r)
    walls_final = weld.astype(np.uint8)
    n, cl, st, _ = cv2.connectedComponentsWithStats(walls_final.astype(np.uint8), 8)
    for i in range(1, n):
        if st[i, 4] * CELL * CELL < .3 and not (band & (cl == i)).any() and not (solid & (cl == i)).any() and not (ov_wall & (cl == i)).any(): walls_final[cl == i] = 0
    # Window openings cut through the outer band: sill below, head above, glass in between.
    exit_polys = [[[r[0], r[1]], [r[2], r[1]], [r[2], r[3]], [r[0], r[3]]] for e in exits for r in e['rect']]
    wins = window_plan(k, O, [s for s in spaces if s['type'] != 'void'], exit_polys) if k != 'B' else []
    wins = [w for w in wins if not any(g.contains(Point((w['a'][0] + w['b'][0]) / 2, (w['a'][1] + w['b'][1]) / 2)) for g in NO_WINDOWS.get(k, []))]
    sills, heads, glass = list(ov_sills) + curb_sills, [], []
    for w in wins:
        a, b = w['a'], w['b']; r = [min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])]
        r = [r[0] - (.4 if abs(w['normal'][0]) > .5 else 0), r[1] - (.4 if abs(w['normal'][1]) > .5 else 0), r[2] + (.4 if abs(w['normal'][0]) > .5 else 0), r[3] + (.4 if abs(w['normal'][1]) > .5 else 0)]
        cut = rect_mask(r) & band & walls_final
        if cut.sum() < 5: continue
        walls_final &= 1 - cut; rr = rects(cut); sills += [dict(rect=q, top=w['sill']) for q in rr]; heads += [dict(rect=q, bottom=w['head']) for q in rr]
        glass.append({'a': a, 'b': b, 'normal': w['normal'], 'sill': w['sill'], 'head': w['head']})
    # Hand-placed windows (overrides.json kind 'window': a, b along the wall, outward normal, sill, head): cut through any wall, not just the outer band.
    for ed in OVERRIDES.get(LABEL[k], []):
        if ed['kind'] != 'window': continue
        a, b, nrm = ed['a'], ed['b'], ed['normal']
        r = [min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])]
        r = [r[0] - (.45 if abs(nrm[0]) > .5 else 0), r[1] - (.45 if abs(nrm[1]) > .5 else 0), r[2] + (.45 if abs(nrm[0]) > .5 else 0), r[3] + (.45 if abs(nrm[1]) > .5 else 0)]
        cut = rect_mask(r) & walls_final
        if cut.sum() < 5: continue
        walls_final &= 1 - cut; rr = rects(cut); sills += [dict(rect=q, top=ed['sill']) for q in rr]; heads += [dict(rect=q, bottom=ed['head']) for q in rr]
        glass.append({'a': a, 'b': b, 'normal': nrm, 'sill': ed['sill'], 'head': ed['head']})
    garage_poly, stall_lines, garage_lights = None, [], []
    if k == 'B':
        # Ramp cutting: its side walls are retaining walls standing ~1 m above the outside ground (low walls, not full height).
        rr = rect_mask([1.4, 60.2, 7.45, 66.9]); rw = (walls_final & rr).astype(np.uint8); walls_final &= 1 - rr
        sills += [dict(rect=q, top=2.5) for q in rects(rw)]
        # User 2026-11-25: the driveway's east side must be one sealed wall. The drawn wall x7.15-7.45 stopped at y60.16, the low sills after it left a
        # 0.9 m gap above B03 and a hole at y61.26-62.16; it now runs full height to the B03 corner, and the west end of the ramp wall is closed too.
        sills = [q for q in sills if not (q['rect'][0] >= 7.0 and q['rect'][1] < 62.0 and q['rect'][3] <= 62.4)]
        walls_final |= rect_mask(RAMP_EAST_WALL)
        sills += [dict(rect=[6.95, 62.16, 7.15, 62.4], top=2.5), dict(rect=[1.75, 65.96, 1.95, 66.66], top=2.5)]
        # Garage: concrete floor, painted stalls and tube lights instead of tiles and a T-bar ceiling.
        gm = np.zeros((H, W), np.uint8)
        for s in spaces:
            if s['type'] == 'garage': gm |= s['mask']
        gm |= rect_mask([1.76, 58.0, 7.07, 66.6]) & O
        gm = cv2.morphologyEx(gm & O, cv2.MORPH_CLOSE, disk(3))
        # User 2026-11-25: no concrete wedges where a door opens into a tiled room. Split the floor at walls and doorways; a pocket that is mostly tile
        # (rooms behind a door) loses any garage cells that leaked in, and the doorway itself takes the room's tile so the pattern runs through the door.
        barrier = (walls_final | doors).astype(np.uint8)
        n_c, lab_c = cv2.connectedComponents((O & (1 - barrier)).astype(np.uint8), connectivity=4)
        tile_pocket = np.zeros((H, W), np.uint8)
        for i_c in range(1, n_c):
            comp = lab_c == i_c
            if gm[comp].mean() < .5 or (comp.sum() * CELL * CELL < 80 and not (comp & rect_mask([1.5, 56.0, 7.2, 66.7])).any()): gm[comp] = 0; tile_pocket |= comp.astype(np.uint8)   # rooms behind doors are tile
        gm &= 1 - (cv2.dilate(tile_pocket, disk(3)) & doors)
        for dr_ in door_list:   # whatever is left: on the room side of each door the doorway and the swing area are tile
            a_, b_ = [np.array(drawing(q)) for q in dr_['line']]; u_ = (b_ - a_) / max(np.hypot(*(b_ - a_)), 1e-6); n_ = np.array([-u_[1], u_[0]]); m_ = (a_ + b_) / 2
            if any((space_at(m_ + n_ * .8 * sg) or {}).get('type') not in (None, 'garage') for sg in (1, -1)) or dr_['kind'] != 'garage':   # the doorway itself takes the room's tile
                gm &= 1 - poly_mask(Polygon([a_ - u_ * .2 - n_ * .45, b_ + u_ * .2 - n_ * .45, b_ + u_ * .2 + n_ * .45, a_ - u_ * .2 + n_ * .45]))
            for sg in (1, -1):
                tp_ = (space_at(m_ + n_ * .8 * sg) or {}).get('type')
                if tp_ not in (None, 'garage'):
                    side = Polygon([a_ - u_ * .15, b_ + u_ * .15, b_ + u_ * .15 + n_ * sg * 1.5, a_ - u_ * .15 + n_ * sg * 1.5])
                    gm &= 1 - (poly_mask(side) & (1 - walls_final))
        cs_g, hi_g = cv2.findContours(gm, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE); gp = []
        for i_g, c_g in enumerate(cs_g):
            if hi_g[0][i_g][3] != -1 or cv2.contourArea(c_g) < 50: continue
            holes_g = [[[ox + x * CELL, oy + y * CELL] for x, y in cs_g[j].reshape(-1, 2)] for j in range(len(cs_g)) if hi_g[0][j][3] == i_g and len(cs_g[j]) > 2]
            gp.append(Polygon([[ox + x * CELL, oy + y * CELL] for x, y in c_g.reshape(-1, 2)], holes_g).buffer(0))
        garage_poly = unary_union(gp).intersection(Pk).buffer(0)
        # User 2026-11-25: concrete must not leak through a doorway into a tiled room (grey door-swing wedges on the tiles): whatever the plan calls a
        # room, corridor or stair hall (anything but 車道／停車場) is tile, so the garage paint stops at the wall line.
        non_garage = unary_union([g for sp, g in space_polys if sp['type'] != 'garage' and sp['type'] not in ('plaza', 'unknown')])
        garage_poly = garage_poly.difference(non_garage.buffer(-.04)).buffer(0)
        for st_ in plans['B'].get('stalls', []):
            P_ = Polygon(st_)
            if not Pk.buffer(-.1).contains(P_.centroid): continue
            x0_, y0_, x1_, y1_ = P_.bounds; t_ = .06
            stall_lines += [[x0_ - t_, y0_ - t_, x1_ + t_, y0_ + t_], [x0_ - t_, y1_ - t_, x1_ + t_, y1_ + t_], [x0_ - t_, y0_ - t_, x0_ + t_, y1_ + t_], [x1_ - t_, y0_ - t_, x1_ + t_, y1_ + t_]]
        inner_g = garage_poly.buffer(-1.0)
        for gx in np.arange(Pk.bounds[0] + 2, Pk.bounds[2], 4.8):
            for gy in np.arange(Pk.bounds[1] + 2, Pk.bounds[3], 4.8):
                if inner_g.contains(Point(gx, gy)) and not RAMP.contains(Point(gx, gy)): garage_lights.append([round(gx, 2), round(gy, 2)])
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
    if k == 'B':   # doorways between the 準備室 and the stage beside the west wall stay clear of shelves
        for r_ in ([1.4, 23.2, 2.5, 25.2], [1.4, 35.4, 2.5, 37.4]): keep |= rect_mask(r_)
    keep = cv2.dilate(keep.astype(np.uint8), disk(int(1.3 / CELL)))
    furniture, fblocks = furnish_floor([sp for sp in spaces if not (k == 'B' and sp['name'].startswith('B04'))] , walls_final, keep, O, H, W, CELL, ox, oy, CELL)   # B04 is solid under the rake
    furniture += ov_fixtures; fblocks += [f['r'] for f in ov_fixtures if f['y'][1] > .3]
    if k == 'B':  # 理學院階梯教室: fixed seats on each rake tier (aisles at both ends and down the middle)
        rk = next(st for st in stairs if st.get('tiers'))
        y0r, y1r = RAKE['rect'][1], RAKE['rect'][3]; ym = (y0r + y1r) / 2
        for t in rk['treads']:   # one seat column per tier, seats against the next riser (sheet: 10 / 13 / 10 seats per column, aisles 1.15 m)
            r = t['rect']; h = t['height']; xb = r[2]
            for ya, yb, cnt in SEAT_BLOCKS:
                pitch = (yb - ya) / cnt
                for j in range(cnt):
                    y0s = ya + j * pitch + .035; y1s = ya + (j + 1) * pitch - .035
                    seat = [round(xb - .48, 3), round(y0s, 3), round(xb - .06, 3), round(y1s, 3)]
                    furniture += [{'r': seat, 'y': [h, h + .45], 'm': 'fabric', 'room': '理學院階梯教室'},
                                  {'r': [round(xb - .12, 3), round(y0s, 3), round(xb - .06, 3), round(y1s, 3)], 'y': [h + .45, h + .95], 'm': 'fabric', 'room': '理學院階梯教室'}]
                    fblocks.append(seat)
        for it in furniture:   # lectern, 準備室 shelves: standing on the raised platform
            if it['room'].startswith('舞台') or it['room'] == '準備室': it['y'] = [round(it['y'][0] + STAGE_H, 3), round(it['y'][1] + STAGE_H, 3)]
    # Fine walls: cells that came from the drawn line work or a user wall strip are replaced by those exact shapes;
    # everything else (exterior band, cores, stair-hall walls, welds) keeps its cell outline.
    protect = (band | solid).astype(np.uint8)
    for r in STAIR_WALL_FILL.get(k, []): protect |= rect_mask(r)
    exact = (ink | ov_wall).astype(np.uint8)
    wf = up(walls_final) & (up(protect) | ink_fine | ov_fine | up(1 - exact))
    # Re-weld hairlines (< 0.2 m) between pieces on the fine grid; doors, openings and exits stay open.
    shut = up(doors)
    for e in exits:
        for r in e['rect']: shut |= up(rect_mask(r))
    wf = (cv2.morphologyEx(wf, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) & up(walls_final | (exact & (1 - doors)))) | wf
    wf &= 1 - shut | up(walls_final)
    # Lintels: one box per door, as thick as the wall at its jambs (was the 0.4 m door clearance strip).
    lint = np.zeros_like(wf); lint_up = np.zeros_like(wf)
    for dr in door_list:
        a2, b2 = [np.array(drawing(q)) for q in dr['line']]; L2 = np.hypot(*(b2 - a2))
        if L2 < .3: continue
        if k == 'B' and RAISED_DOOR_ZONE.contains(Point(*((a2 + b2) / 2))): dr['raise'] = STAGE_H   # user 2026-11-25: doors on the stage-height floor rise with it (frame head and lintel were 0.8 m too low)
        u2 = (b2 - a2) / L2; n2 = np.array([-u2[1], u2[0]]); lo, hi = [], []
        for pnt in (a2 - u2 * .12, b2 + u2 * .12, a2 - u2 * .2, b2 + u2 * .2):
            ts = [t for t in np.arange(-.4, .401, FINE / 2) if (lambda q: 0 <= q[1] < wf.shape[0] and 0 <= q[0] < wf.shape[1] and wf[q[1], q[0]])([int((pnt[0] + n2[0] * t - fox) / FINE), int((pnt[1] + n2[1] * t - foy) / FINE)])]
            if ts: lo.append(min(ts)); hi.append(max(ts))
        t0, t1 = (float(np.median(lo)), float(np.median(hi))) if lo else (-.1, .1)
        if t1 - t0 < .08: t0, t1 = -.1, .1
        dr['frame'] = [round(t1 - t0, 3), round((t0 + t1) / 2, 3)] if t1 - t0 <= .45 else [.25, 0.0]   # thicker readings (door beside a solid core) fall back to a 0.25 m frame   # user 2026-11-24: every door gets a frame (jambs + head) as thick as the wall at its jambs; centre offset along the normal
        fine_poly(Polygon([a2 - u2 * .08 + n2 * t0, b2 + u2 * .08 + n2 * t0, b2 + u2 * .08 + n2 * t1, a2 - u2 * .08 + n2 * t1]), lint_up if dr.get('raise') else lint)
    lint &= 1 - wf; lint_up &= 1 - wf
    floors_out.append({'garagePoly': garage_poly, 'stallLines': [[round(v, 3) for v in r] for r in stall_lines], 'garageLights': garage_lights, 'openAreas': [OPEN_2F] if k == '2' else ([DRIVE_OPEN_B1] if k == 'B' else []), 'key': k, 'label': LABEL[k], 'level': LEVEL[k], 'outline': ring_coords(Pk), 'walls': fine_rects(wf), 'diagWalls': diag_walls, 'blockOnly': block_only, 'lintels': fine_rects(lint) + [r_ + [STAGE_H] for r_ in fine_rects(lint_up)],
                       'sills': sills, 'heads': heads, 'windows': glass, 'furniture': furniture, 'furnitureBlocks': fblocks, 'doors': door_list, 'doorLeaves': door_leaves, 'exits': exits, 'stairs': stairs, 'voidMask': void,
                       'spaces': [{'name': s['name'], 'num': s.get('num'), 'type': s['type'], 'anchor': world(s['anchor']) if s.get('anchor') else None} for s in spaces]})

for i, fl in enumerate(floors_out):
    slab = OUTLINE[fl['key']]
    if fl['key'] == 'B': slab = slab.difference(box(*RAMP_SLOPE['rect'])); fl['ramp'] = RAMP_SLOPE
    if i > 0:
        for st in stairs_by_floor[ORDER[i - 1]]:
            slab = slab.difference(box(*st['hole']))
            for r_ in st.get('extraHoles', []): slab = slab.difference(box(*r_).buffer(.01, join_style=2))
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
        for r_ in st.get('extraHoles', []): ceil = ceil.difference(box(*r_).buffer(.05, join_style=2))
        if st.get('tiers'): ceil = ceil.difference(box(*HALL_OPEN_1F))
    for r in fl['openAreas']: ceil = ceil.difference(box(*r))
    gpoly = fl.pop('garagePoly')
    if gpoly is not None and not gpoly.is_empty:
        ceil = ceil.difference(gpoly)
        tp = slab.difference(gpoly).buffer(0); gp2 = slab.intersection(gpoly).buffer(0)
        tri = lambda P: [[world(q) for q in list(t.exterior.coords)[:-1]] for g in ([P] if P.geom_type == 'Polygon' else [x for x in getattr(P, 'geoms', []) if x.geom_type == 'Polygon']) if g.area > .2 for t in constrained_delaunay_triangles(g).geoms if t.area > 1e-6]
        fl['tileTriangles'] = tri(tp); fl['garageTriangles'] = tri(gp2)
        # Dashed lane curves from the drawing (scripts/extract-zhili-lanes.py): white paint on the garage floor, user 2026-11-23.
        lane_f = root / 'buildings/zhili/lanes.json'
        if fl['key'] == 'B' and lane_f.exists():
            lanes = unary_union([Polygon(q).buffer(0) for q in json.loads(lane_f.read_text()).get('B1', []) if len(q) > 2]).intersection(gp2).buffer(0)
            fl['laneTriangles'] = [[world(q) for q in list(t.exterior.coords)[:-1]] for g in (list(lanes.geoms) if hasattr(lanes, 'geoms') else [lanes]) if g.geom_type == 'Polygon' and g.area > .005 for t in constrained_delaunay_triangles(g).geoms if t.area > 1e-7]
    ceil = ceil.buffer(0); cparts = [ceil] if ceil.geom_type == 'Polygon' else [g for g in ceil.geoms if g.geom_type == 'Polygon']
    fl['ceilingTriangles'] = [[world(q) for q in list(t.exterior.coords)[:-1]] for p in cparts if p.area > .5 for t in constrained_delaunay_triangles(p).geoms if t.area > 1e-6]
# ---- 乙梯 stacked up to 8F (user 2026-11-24: 3F and above are hollowed out and the stair is built) ----
# The upper floors stay a solid brick volume (facade windows only) except this stair hall: the same two-flight stair as 1F
# (same rect and treads, landing running on into the glazed bay) on every floor, band walls round the hall, the bay glass
# as real window openings. Only 乙梯 climbs; its hall is closed off from the rest of each solid floor.
HALL_O = Polygon([(60.8, 55.01), (65.72, 55.01), (65.72, 55.7), (66.97, 56.8), (65.72, 57.9), (65.72, 59.11), (60.8, 59.11)]).intersection(TOWER).buffer(0)
st_ji = next(st for st in stairs_by_floor['1'] if st['id'] == '乙梯')
def stair_holes(st): return [box(*st['hole'])] + [box(*r_).buffer(.01, join_style=2) for r_ in st.get('extraHoles', [])]
def tris(P): return [[world(q) for q in list(t.exterior.coords)[:-1]] for g in ([P] if P.geom_type == 'Polygon' else [x for x in P.geoms if x.geom_type == 'Polygon']) if g.area > .05 for t in constrained_delaunay_triangles(g).geoms if t.area > 1e-6]
def regions(P): return [[ring_coords(g), *[[[round(x, 3), round(y, 3)] for x, y in h.coords][:-1] for h in g.interiors]] for g in ([P] if P.geom_type == 'Polygon' else [x for x in P.geoms if x.geom_type == 'Polygon']) if g.area > .05]
upper_floors = []
hall_mask = poly_mask(HALL_O); hall_band = hall_mask & (1 - cv2.erode(hall_mask, np.ones((2 * int(WALL_BAND / CELL) + 1,) * 2, np.uint8)))
for k in ('2', '3', '4', '5', '6', '7', '8'):
    ent = {'key': k, 'label': LABEL[k], 'level': LEVEL[k], 'hall': True, 'outline': ring_coords(HALL_O), 'walls': [], 'lintels': [], 'sills': [], 'heads': [], 'windows': [], 'doors': [], 'doorLeaves': [], 'exits': [],
           'furniture': [], 'furnitureBlocks': [], 'openAreas': [], 'spaces': [], 'slab': [], 'slabTriangles': [], 'stairs': [], 'stallLines': [], 'garageLights': []}
    if k != '8': ent['stairs'] = [{**st_ji, 'treads': [dict(t) for t in st_ji['treads']]}]
    if k != '2':
        wm = hall_band.copy(); sills_, heads_, glass_ = [], [], []
        for a_, b_, n_ in BAY_GLASS:
            r = [min(a_[0], b_[0]), min(a_[1], b_[1]), max(a_[0], b_[0]), max(a_[1], b_[1])]
            r = [r[0] - (.45 if abs(n_[0]) > .5 else 0), r[1] - (.45 if abs(n_[1]) > .5 else 0), r[2] + (.45 if abs(n_[0]) > .5 else 0), r[3] + (.45 if abs(n_[1]) > .5 else 0)]
            cut = rect_mask(r) & wm
            if cut.sum() < 5: continue
            wm &= 1 - cut; rr = rects(cut); sills_ += [dict(rect=q, top=.1) for q in rr]; heads_ += [dict(rect=q, bottom=FLOOR_H - .3) for q in rr]
            glass_.append({'a': a_, 'b': b_, 'normal': n_, 'sill': .1, 'head': FLOOR_H - .3})
        sl = HALL_O
        for h_ in stair_holes(st_ji): sl = sl.difference(h_)   # flight arriving from the floor below
        sl = sl.buffer(0)
        ent.update({'walls': fine_rects(up(wm)), 'sills': sills_, 'heads': heads_, 'windows': glass_, 'slab': regions(sl), 'slabTriangles': tris(sl)})
    upper_floors.append(ent)
roof_hole = unary_union(stair_holes(st_ji))
solid_ring = TOWER.difference(HALL_O); assert solid_ring.geom_type == 'Polygon' and not list(solid_ring.interiors), solid_ring.geom_type
hall_roof = HALL_O
top = OUTLINE[ORDER[-1]].difference(roof_hole).buffer(0)
out = {'version': 2, 'building': 444867693, 'floorHeight': FLOOR_H, 'slab': SLAB, 'transform': T,
       # Interior finish (user 2026-11-19): square floor tiles, off-white walls, black skirting, light-steel (T-bar)
       # suspended ceiling with recessed lights.
       'finish': {'tile': .6, 'wall': '#efe9da', 'skirting': '#1c1c1e', 'skirtingHeight': .1, 'ceilingHeight': 3.0, 'ceilingPanel': .6}, 'foundationRing': ring_coords(OUTLINE['B'].difference(box(*RAMP_SLOPE['rect']))), 'outline': ring_coords(unary_union([OUTLINE[k] for k in ORDER])),
       'towerOutline': ring_coords(TOWER), 'solidRing': ring_coords(solid_ring), 'upperFloors': upper_floors, 'hallRoofTriangles': tris(hall_roof), 'hallRoofLevel': LEVEL[ALL_FLOORS[-1]] + FLOOR_H, 'podiumRoofLevel': LEVEL['2'],
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
