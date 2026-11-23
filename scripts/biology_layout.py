"""Derive the Bio A/B connection from the user's floor-plan drawings (2026-11-23).

1F glazed hall + recess to the closed sewage room, open 2F deck (the S05 T deck
datum), +510 flower plaza, terraced ramp/stairs down to S01 (+0) and a flat
apron to the skew S01 edge. Drawing heights are in cm; at runtime they map
linearly from S01 (+0) to the hall floor (+510), i.e. the user-approved scaled
rises (2026-11-23 option 1) because the model's S01 is ~6 m lower than drawn.
"""
import math
import json
from pathlib import Path
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
import biology_drawing as D

root = Path(__file__).resolve().parents[1]


def frame():
    source = json.loads((root / 'facilities/biology-layout/layout.json').read_text())
    t = source['axis']
    return D.Frame(source['joint'], [-t[0], -t[1]], [t[1], -t[0]])


def ring(s):
    a, b = s['line']; dx = b[0] - a[0]; dz = b[1] - a[1]; length = math.hypot(dx, dz); n = [-dz / length, dx / length]
    return [[round(p[i] + side * n[i] * s['width'] / 2, 7) for i in range(2)] for p, side in [(a, 1), (b, 1), (b, -1), (a, -1)]]


def coords(poly):
    return [[round(x, 7), round(z, 7)] for x, z in list(poly.exterior.coords)[:-1]]


def lane_pieces(F, lane, stations, side):
    x0, x1 = D.LANES[lane]; xc = (x0 + x1) / 2; width = (x1 - x0) / D.A_SCALE; out = []
    for i, s in enumerate(stations):
        y0, y1 = s[1], s[2]
        if s[0] == 'landing':
            piece = {'id': f'biology-terrace-{lane}-landing-{i}', 'type': 'landing', 'line': [F.a(xc, y1), F.a(xc, y0)], 'width': width,
                     'steps': 1, 'hTop': s[3], 'hBottom': s[3]}
            if s[3] == 0:
                # Stays level where a ramp lands on it; only the S01 end follows the road.
                edge = x1 if lane == 'left' else x0
                ramps = [e[1] - D.RAMP_BAND / 2 - 1 for r in D.RAMPS for e in r[:2] if abs(e[0] - edge) < 1]
                level_to = min([y for y in ramps if y0 < y < y1], default=y1)
                piece['roadSlopeFrom'] = round((y1 - level_to) / (y1 - y0), 4)
            out.append(piece)
        else:
            out.append({'id': f'biology-terrace-{lane}-stair-{i}', 'type': 'stair', 'line': [F.a(xc, y1), F.a(xc, y0)], 'width': width,
                        'steps': s[5], 'hTop': s[4], 'hBottom': s[3]})
    return out


def terraces(F):
    pieces = lane_pieces(F, 'left', D.LEFT, -1) + lane_pieces(F, 'right', D.RIGHT, 1)
    fx0, fx1 = D.FIELD; ext = .25 * D.A_SCALE; bands = []
    for k, (p, q, h0, h1) in enumerate(D.RAMPS):
        dx, dy = q[0] - p[0], q[1] - p[1]; length = math.hypot(dx, dy); ux, uy = dx / length, dy / length
        # Exact parallelogram band between the two drawn stepped boundaries (vertical ends on the field edges).
        half = D.RAMP_BAND / 2
        # Extend past the field edges so no sliver of planter survives between a ramp end and its landing.
        p2 = (p[0] - ux * 3, p[1] - uy * 3); q2 = (q[0] + ux * 3, q[1] + uy * 3)
        band = Polygon([(p2[0], p2[1] - half), (q2[0], q2[1] - half), (q2[0], q2[1] + half), (p2[0], p2[1] + half)])
        bands.append(band)
        a = (q[0] + ux * ext, q[1] + uy * ext); b = (p[0] - ux * ext, p[1] - uy * ext); total = length + 2 * ext
        width = D.RAMP_BAND * abs(ux) / D.A_SCALE
        pieces.append({'id': f'biology-terrace-ramp-{k}', 'type': 'ramp', 'line': [F.a(*a), F.a(*b)], 'width': round(width, 4),
                       'steps': 1, 'hTop': h1, 'hBottom': h0, 'flat': [ext / total, 1 - ext / total]})
    bx0, by0, bx1, by1, bh = D.TOP_BAY
    bay = box(bx0, by0, bx1, by1)
    pieces.append({'id': 'biology-terrace-top-bay', 'type': 'landing', 'line': [F.a((bx0 + bx1) / 2, by1), F.a((bx0 + bx1) / 2, by0)],
                   'width': (bx1 - bx0) / D.A_SCALE, 'steps': 1, 'hTop': bh, 'hBottom': bh})
    for piece in pieces:
        piece['ring'] = ring(piece)
    # Stepped planters fill the rest of the ramp field: tiers follow the drawn 0.34 m tread lines.
    y0, y1 = D.TERRACE[1], D.TERRACE[3]
    field = box(fx0, y0, fx1, y1).difference(unary_union(bands + [bay])).buffer(-.02).buffer(.02)
    def average(y):  # drawing height of the ramp centre at this station
        return max(0, min(500, 40 + 80 * (y - 174.4) / 30.24))
    planters = []
    tier = 3.2
    n = math.ceil((y1 - y0) / tier)
    for j in range(n):
        strip = field.intersection(box(fx0 - 1, y0 + j * tier, fx1 + 1, min(y1, y0 + (j + 1) * tier)))
        for part in (list(strip.geoms) if hasattr(strip, 'geoms') else [strip]):
            if part.geom_type == 'Polygon' and part.area > .05:
                mid = part.centroid.y
                planters.append({'ring': D.ccw([F.a(x, y) for x, y in list(part.exterior.coords)[:-1]]), 'h': round(average(mid), 2), 'raise': .45})
    walls = []
    for wx0, wx1 in D.WALL_BOX:
        lane = 'left' if wx0 < D.AXIS_X else 'right'
        for s in (D.LEFT if lane == 'left' else D.RIGHT):
            h = s[3] if s[0] == 'landing' else max(s[3], s[4])
            walls.append({'ring': F.rect((wx0, s[1], wx1, s[2])), 'h': h, 'raise': .6})
    pits = [{'center': F.a(x, y), 'size': D.TREE_PIT_SIZE / D.A_SCALE, 'h': average(y)} for x, y in D.TREE_PITS]
    return pieces, planters, walls, pits


def derive_biology(c, source):
    F = frame(); bio = c['bioConnection']; cfg = source['biology']
    places = [Polygon(v['ring']) for v in c['places'] + c['buildings'] if v.get('height')]
    buildings = unary_union(places)
    hall = Polygon(F.rect(D.HALL)).union(Polygon(F.rect(D.HALL_RECESS)))
    line = [F.a(D.HALL_A_END, D.HALL_Y), F.a(D.HALL_B_END, D.HALL_Y)]
    width = (D.HALL[3] - D.HALL[1]) / D.A_SCALE
    north = F.north; east = F.east
    bio.update(line=line, width=width, ring=F.rect(D.HALL))
    for key in ['eastLanding', 'stairs']:
        bio.pop(key, None)
    sx0, sy0, sx1, sy1 = D.SEWAGE
    bio['corridor'] = {'floors': [1, 2], 'floorHeight': cfg['floorHeight'], 'slab': cfg['slab'], 'clearance': cfg['clearance'],
                       'lowerRetainingWalls': False, 'line': line, 'width': width, 'roof': False, 'joint': F.joint, 'axis': north, 'east': east,
                       'deckRing': F.rect(D.DECK),
                       'drawingReference': 'scripts/biology_drawing.py (buildings/bio-a/source/floor-1.pdf)'}
    # Glazed hall walls: (start, end) along each face, kinds glass / door-open / door-closed / column / wall.
    def seg(x0, y0, x1, y1, kind):
        return {'line': [F.a(x0, y0), F.a(x1, y1)], 'kind': kind}
    ny, sy = D.HALL[1], D.HALL[3]
    north_face = [seg(D.HALL_A_END, ny, D.PLAZA_DOORS[0][0], ny, 'glass'), seg(*(D.PLAZA_DOORS[0][0], ny, D.PLAZA_DOORS[0][1], ny), 'door-open'),
                  seg(D.PLAZA_DOORS[0][1], ny, D.PLAZA_DOORS[1][0], ny, 'glass'), seg(D.PLAZA_DOORS[1][0], ny, D.PLAZA_DOORS[1][1], ny, 'door-open'),
                  seg(D.PLAZA_DOORS[1][1], ny, D.HALL_B_END, ny, 'glass')]
    rx0, _, rx1, ry1 = D.HALL_RECESS
    south_face = [seg(D.HALL_A_END, sy, D.SOUTH_DOORS[0][0], sy, 'glass'), seg(D.SOUTH_DOORS[0][0], sy, D.SOUTH_DOORS[0][1], sy, 'door-open'),
                  seg(D.SOUTH_DOORS[0][1], sy, rx0, sy, 'wall'), seg(rx0, sy, rx0, ry1, 'wall'),
                  seg(rx0, ry1, D.SEWAGE_DOOR[0], ry1, 'wall'), seg(D.SEWAGE_DOOR[0], ry1, D.SEWAGE_DOOR[1], ry1, 'door-closed'),
                  seg(D.SEWAGE_DOOR[1], ry1, rx1, ry1, 'wall'), seg(rx1, ry1, rx1, sy, 'wall'),
                  seg(rx1, sy, D.SOUTH_DOORS[1][0], sy, 'wall'), seg(D.SOUTH_DOORS[1][0], sy, D.SOUTH_DOORS[1][1], sy, 'door-open'),
                  seg(D.SOUTH_DOORS[1][1], sy, D.HALL_B_END, sy, 'glass')]
    ends = [seg(D.HALL_A_END, D.END_DOORS['a'][0], D.HALL_A_END, D.END_DOORS['a'][1], 'door-closed'),
            seg(D.HALL_B_END, D.END_DOORS['b'][0], D.HALL_B_END, D.END_DOORS['b'][1], 'door-closed')]
    bio['corridor']['walls'] = north_face + south_face + ends
    bio['corridor']['columns'] = [F.a(x, y) for x in D.HALL_COLUMNS for y in (ny, sy)]
    # Closed sewage room between the inner walls of the two +505 side-stair lanes, minus the hall recess.
    left_in, right_in = D.SIDE_LANES['left'][1], D.SIDE_LANES['right'][0]
    under = box(left_in, sy, right_in, sy1).difference(box(*D.HALL_RECESS)).buffer(-.05 * D.A_SCALE, join_style=2)
    stem_half = cfg['accessWidth'] / 2 * D.A_SCALE
    dy0, dy1 = D.DECK[1], D.DECK[3]
    edge_l, edge_r = D.AXIS_X - stem_half, D.AXIS_X + stem_half
    bio['corridor']['deckRails'] = [[F.a(D.HALL_A_END, dy0), F.a(D.HALL_B_END, dy0)], [F.a(D.HALL_A_END, dy1), F.a(edge_l, dy1)],
                                    [F.a(edge_r, dy1), F.a(D.HALL_B_END, dy1)],
                                    # deck south edge over the open stair wells
                                    [F.a(edge_l, dy1), F.a(left_in, dy1)], [F.a(right_in, dy1), F.a(edge_r, dy1)]]
    # +505 side stairs (user 2026-11-23): door landing at 1F, one straight 32-riser flight up to the T stem,
    # whose floor is opened above them (stair wells), inner rails on the stem, solid outer walls to the stem edge.
    f0, f1 = D.SIDE_FLIGHT; side = []
    for lane, (x0, x1) in D.SIDE_LANES.items():
        xc = (x0 + x1) / 2; width = (x1 - x0) / D.A_SCALE
        landing = {'id': f'biology-side-{lane}-landing', 'type': 'landing', 'line': [F.a(xc, f0), F.a(xc, sy)], 'width': width, 'steps': 1, 'level': 'bio-lower'}
        flight = {'id': f'biology-side-{lane}-stair', 'type': 'stair', 'line': [F.a(xc, f1), F.a(xc, f0)], 'width': width, 'steps': D.SIDE_RISERS,
                  'level': 'stem', 'bottomLevel': 'bio-lower'}
        for piece in (landing, flight):
            piece['ring'] = ring(piece)
        outer, inner = (x0, x1) if lane == 'left' else (x1, x0)
        edge = edge_l if lane == 'left' else edge_r
        side.append({'lane': lane, 'pieces': [landing, flight],
                     # well = stem floor removed above the lane and the outer wall (0.5 m past the stem edge, no slivers)
                     'well': D.ccw(F.rect((min(inner, edge - .5 * D.A_SCALE), dy1, max(inner, edge + .5 * D.A_SCALE), f1))),
                     'outerWall': D.ccw(F.rect((min(outer, edge), dy1, max(outer, edge), f1))),
                     'outerWallLine': [F.a((outer + edge) / 2, dy1), F.a((outer + edge) / 2, f1)], 'outerWallWidth': abs(edge - outer) / D.A_SCALE,
                     'innerRail': [F.a(inner, dy1), F.a(inner, f1)]})
    bio['sideStairs'] = side
    bio['sewageRoom'] = {'name': '污水機房', 'ring': F.rect(D.SEWAGE), 'door': [F.a(D.SEWAGE_DOOR[0], sy0), F.a(D.SEWAGE_DOOR[1], sy0)],
                         'undercroft': D.ccw([F.a(x, y) for x, y in list(under.exterior.coords)[:-1]]),
                         'undercroftTriangles': [D.ccw([F.a(x, y) for x, y in list(tri.exterior.coords)[:-1]]) for tri in constrained_delaunay_triangles(under).geoms if tri.area > 1e-6],
                         'desc': '依生物科技館1F平面圖；門關閉、封閉量體，位於兩側+505小梯之間的T平台下方。'}
    px0, py0, px1, py1 = D.PLAZA
    bio['eastLanding'] = {'line': [F.a(D.AXIS_X, py1), F.a(D.AXIS_X, py0)], 'width': (px1 - px0) / D.A_SCALE, 'depth': (py1 - py0) / D.A_SCALE,
                          'ring': F.rect(D.PLAZA), 'targetFloor': 1, 'kind': 'flower-plaza',
                          'pattern': {'center': F.a(D.AXIS_X, (380.68 + 493.5) / 2), 'size': (523.68 - 410.9) / D.A_SCALE,
                                      'axis': [-north[0], -north[1]]},
                          'sidePlanters': [F.rect(r) for r in D.PLAZA_SIDE]}
    tx0, ty0, tx1, ty1 = D.TERRACE
    pieces, planters, walls, pits = terraces(F)
    stairs = {'kind': 'terraces', 'name': '生科東側坡道階梯', 'road': cfg['stairs']['road'],
              'line': [F.a(D.AXIS_X, ty1), F.a(D.AXIS_X, ty0)], 'width': (tx1 - tx0) / D.A_SCALE,
              'drawingTop': D.DRAWING_TOP, 'pieces': pieces, 'planters': planters, 'wallPlanters': walls, 'treePits': pits,
              'desc': '依生物科技館1F平面圖：之字形坡道、兩側直梯與階梯式花台（+0～+500）；平面照圖，高差依使用者2026-11-23選擇等比例放大以接上模型S01。'}
    stairs['ring'] = F.rect(D.TERRACE)
    bio['stairs'] = stairs
    # A flat ground apron fills the skew between the terraces' S01 end and the road edge.
    road = next(r for r in c['roads'] if r['osm'] == cfg['stairs']['road']); roadshape = LineString(road['line']).buffer(road['width'] / 2)
    bottom = stairs['line'][1]; half = stairs['width'] / 2; e = east
    def reach(offset):
        start = [bottom[i] + north[i] * offset for i in range(2)]
        ray = LineString([start, [start[i] + e[i] * 60 for i in range(2)]]); hit = ray.intersection(roadshape)
        return ray.project(Point(list(hit.coords)[0])) if not hit.is_empty else 0
    far = max(reach(v) for v in [-half, 0, half]) + .5
    apron = Polygon([[bottom[i] + north[i] * side * half + e[i] * d for i in range(2)] for side, d in [(1, 0), (-1, 0), (-1, far), (1, far)]])
    return hall, apron
