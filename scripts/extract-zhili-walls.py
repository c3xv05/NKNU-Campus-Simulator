"""Read walls and doors straight from the vector line work of the Zhili floor-plan PDFs.

User 2026-11-19: the walkable interior treated many drawn doors as walls and missed many walls, because
walls were inferred from room-region boundaries and doors were guessed at the middle of shared walls.
This script reads the drawing itself:

- Wall  = the band between two parallel drawn lines 0.05–0.42 m apart that overlap along their length
          (the drawings draw every wall / partition as a double line), plus columns (small closed squares
          attached to walls). Repeating parallel patterns (stair treads, seat rows, paving) are excluded.
- Door  = a swing arc (a chain of short segments fitting a circle, R 0.46–1.4 m, a 76–110 deg quarter arc (urinals and basins draw shallower bowls), or 150–200 deg for double-acting leaves). The hinge is
          the circle centre; the opening is the chord along the wall; the whole swing sector is kept clear.
- Openings without a leaf are simply gaps in the drawn double lines and stay open.

Output (drawing metres, plan.json frame): buildings/zhili/walls.json and review images
buildings/zhili/review/walls-<floor>.png (walls red, doors green with the swing, openings visible).
Requires PyMuPDF (pip install pymupdf), OpenCV, Shapely 2.
"""
import json, sys, math
from pathlib import Path
import numpy as np, cv2
import pymupdf as fitz
from shapely.geometry import Polygon, box, Point, LineString
from shapely.ops import unary_union

root = Path(__file__).resolve().parents[1]
B = root / 'buildings/zhili'
plan = json.loads((B / 'plan.json').read_text())
FLOORS = ['B1', '1F', '2F', '3F', '4F', '5F', '6F', '7F', '8F']
KEY = {'B1': 'B', **{f: f[:-1] for f in FLOORS[1:]}}
S = 0.0817 * 110 / 72            # metres per PDF point (1:250 A3 printed on A4)
# Page -> drawing frame (plan.json): x = -page_y*S + tx, y = page_x*S + ty; offsets fitted per page against plan.json.
OFFSET = {'B1': (90.06, -0.68), '1F': (91.86, 1.3), '2F': (89.32, -1.8), '3F': (97.58, 1.3), '4F': (104.96, -0.02),
          '5F': (98.74, -0.24), '6F': (103.4, 0.52), '7F': (101.64, -1.32), '8F': (99.66, 1.36)}
PAIR_MIN, PAIR_MAX, OVERLAP_MIN = .05, .42, .12
C = .025                          # raster cell for components / images


def segments(fl):
    page = fitz.open(B / f'source/floor-{fl}.pdf')[0]; tx, ty = OFFSET[fl]
    out = []
    for d in page.get_drawings():
        for it in d['items']:
            pts = []
            if it[0] == 'l': pts = [it[1], it[2]]
            elif it[0] == 'qu': q = it[1]; pts = [q.ul, q.ur, q.lr, q.ll, q.ul]
            elif it[0] == 're': r = it[1]; pts = [r.tl, r.tr, r.br, r.bl, r.tl]
            elif it[0] == 'c': pts = [it[1], it[4]]
            for a, b in zip(pts, pts[1:]):
                out.append((-a.y * S + tx, a.x * S + ty, -b.y * S + tx, b.x * S + ty))
    s = np.array(out)
    L = np.hypot(s[:, 2] - s[:, 0], s[:, 3] - s[:, 1])
    return s[L > 1e-4]


def geometry(s):
    d = s[:, 2:] - s[:, :2]; L = np.hypot(d[:, 0], d[:, 1]); u = d / L[:, None]
    th = np.mod(np.arctan2(u[:, 1], u[:, 0]), np.pi)
    u = np.stack([np.cos(th), np.sin(th)], 1); n = np.stack([-u[:, 1], u[:, 0]], 1)
    t1 = (s[:, :2] * u).sum(1); t2 = (s[:, 2:] * u).sum(1)
    return L, th, u, n, (s[:, :2] * n).sum(1), np.minimum(t1, t2), np.maximum(t1, t2)


def pairs(s, minlen=.1, exclude=()):
    """Parallel overlapping pairs: returns list of (i, j, signed distance from i, t0, t1)."""
    L, th, u, n, o, ta, tb = geometry(s)
    idx = np.nonzero(L >= minlen)[0]
    if len(exclude): idx = np.setdiff1d(idx, np.fromiter(exclude, int))
    step = math.radians(.5); bk = np.round(th / step).astype(int) % 360
    res = []
    for b in np.unique(bk[idx]):
        A = idx[bk[idx] == b]
        Bc = idx[np.isin(bk[idx], [(b - 1) % 360, b, (b + 1) % 360])]
        ref = b * step; ur = np.array([math.cos(ref), math.sin(ref)]); nr = np.array([-ur[1], ur[0]])
        def proj(I):
            # reference frame of this bucket (handles wrap at 0/180 by using the actual endpoints)
            m = (s[I, :2] + s[I, 2:]) / 2; t1 = s[I, :2] @ ur; t2 = s[I, 2:] @ ur
            return m @ nr, np.minimum(t1, t2), np.maximum(t1, t2)
        oa, a0, a1 = proj(A); ob, b0, b1 = proj(Bc)
        order = np.argsort(ob); ob, b0, b1, Bs = ob[order], b0[order], b1[order], Bc[order]
        lo = np.searchsorted(ob, oa - PAIR_MAX); hi = np.searchsorted(ob, oa + PAIR_MAX, 'right')
        for k in range(len(A)):
            if hi[k] <= lo[k]: continue
            sl = slice(lo[k], hi[k]); d = ob[sl] - oa[k]; j = Bs[sl]
            t0 = np.maximum(a0[k], b0[sl]); t1 = np.minimum(a1[k], b1[sl])
            ok = (np.abs(d) >= PAIR_MIN) & (t1 - t0 >= OVERLAP_MIN) & (np.abs(np.sin(th[j] - th[A[k]])) < math.sin(math.radians(.8)))
            ok &= (j > A[k]) | ~np.isin(j, A)
            for jj, dd, x0, x1 in zip(j[ok], d[ok], t0[ok], t1[ok]):
                res.append((int(A[k]), int(jj), float(dd), float(x0), float(x1), ur, nr))
    return res


def pattern_lines(s, prs):
    """Lines with parallel overlapping partners at a similar 0.15–0.6 m spacing on both sides (stair treads,
    seat rows, hatching)."""
    side = {}
    L = np.hypot(s[:, 2] - s[:, 0], s[:, 3] - s[:, 1])
    for i, j, d, t0, t1, *_ in prs:
        a, b = L[i], L[j]
        if min(a, b) < .55 * max(a, b) or t1 - t0 < .7 * min(a, b): continue   # columns / stubs beside a wall are not a pattern
        if .15 <= abs(d) <= .6:
            side.setdefault(i, []).append(d); side.setdefault(j, []).append(-d)
    out = set()
    for i, ds in side.items():
        pos = [d for d in ds if d > 0]; neg = [-d for d in ds if d < 0]
        if pos and neg and any(abs(a - b) / max(a, b) < .3 for a in pos for b in neg): out.add(i)
    return out


def find_arcs(s):
    """Door swings: clusters of short connected segments (the drawings trace curves as tiny steps, often doubled)
    in which RANSAC finds circles R 0.46–1.4 m spanning 50–110 deg; a double door's two arcs touch and are split."""
    L = np.hypot(s[:, 2] - s[:, 0], s[:, 3] - s[:, 1])
    short = np.nonzero((L < .3) & (L > 1e-3))[0]
    # Group by touching ink on a 2 cm raster (endpoint snapping alone splits the traced curves).
    G = .02; lo = s[short, :2].min(0) - .1
    shp = tuple((np.ceil((np.maximum(s[short, :2].max(0), s[short, 2:].max(0)) - lo) / G) + 3).astype(int))[::-1]
    r = np.zeros(shp, np.uint8)
    for i in short: cv2.line(r, tuple(np.round((s[i, :2] - lo) / G).astype(int)), tuple(np.round((s[i, 2:] - lo) / G).astype(int)), 1, 1)
    _, comp = cv2.connectedComponents(r, connectivity=8)
    mids = np.round(((s[short, :2] + s[short, 2:]) / 2 - lo) / G).astype(int)
    starts = np.round((s[short, :2] - lo) / G).astype(int)
    groups = {}
    for i, q in zip(short, starts): groups.setdefault(int(comp[q[1], q[0]]), []).append(i)
    rng = np.random.default_rng(1); arcs = []
    for segs in groups.values():
        P = np.concatenate([s[segs, :2], s[segs, 2:], (s[segs, :2] + s[segs, 2:]) / 2])
        P = np.unique(np.round(P, 3), axis=0)
        ext = np.ptp(P, axis=0)
        if len(P) < 10 or max(ext) < .35 or max(ext) > 15: continue
        rest = P
        for _ in range(16):
            if len(rest) < 10: break
            best = None
            for _ in range(400):
                a, b, c = rest[rng.choice(len(rest), 3, replace=False)]
                M = np.array([[b[0] - a[0], b[1] - a[1]], [c[0] - a[0], c[1] - a[1]]]) * 2
                if abs(np.linalg.det(M)) < 1e-6: continue
                cx, cy = np.linalg.solve(M, [b @ b - a @ a, c @ c - a @ a]); R = math.hypot(a[0] - cx, a[1] - cy)
                if not (.46 <= R <= 1.4): continue
                inl = np.abs(np.hypot(rest[:, 0] - cx, rest[:, 1] - cy) - R) < .04
                if best is None or inl.sum() > best[0].sum(): best = (inl, cx, cy, R)
            if best is None or best[0].sum() < 10: break
            inl, cx, cy, R = best
            Q = P[np.abs(np.hypot(P[:, 0] - cx, P[:, 1] - cy) - R) < .04]   # judge continuity on all points (touching arcs share some)
            ang = np.sort(np.mod(np.arctan2(Q[:, 1] - cy, Q[:, 0] - cx), 2 * np.pi))
            gaps = np.diff(np.r_[ang, ang[0] + 2 * np.pi]); k = int(np.argmax(gaps)); span = 2 * np.pi - gaps[k]
            # continuous: no internal gap larger than 12 deg; enough points along it
            internal = np.delete(gaps, k)
            rest = rest[~inl]
            if internal.size and internal.max() > math.radians(12): continue
            if span > math.radians(300) and len(Q) >= 2 * np.pi * R / .06:
                # two double-acting leaves on one mullion: split the circle along the drawn leaf line through it
                Ls = np.hypot(s[:, 2] - s[:, 0], s[:, 3] - s[:, 1]); mid = (s[:, :2] + s[:, 2:]) / 2
                d = np.abs((s[:, 2] - s[:, 0]) * (cy - s[:, 1]) - (s[:, 3] - s[:, 1]) * (cx - s[:, 0])) / np.maximum(Ls, 1e-9)
                cand = np.nonzero((d < .05) & (np.abs(Ls - 2 * R) < .3 * R) & (np.hypot(mid[:, 0] - cx, mid[:, 1] - cy) < .15))[0]
                if len(cand):
                    th = math.atan2(s[cand[0], 3] - s[cand[0], 1], s[cand[0], 2] - s[cand[0], 0])
                    for t0 in (th, th + np.pi):
                        arcs.append({'c': [float(cx), float(cy)], 'r': float(R), 'a0': float(t0), 'a1': float(t0 + np.pi), 'segs': segs, 'leaf': True})
                continue
            # single swing (quarter arc) or double-acting leaf drawn as a half circle
            if not (math.radians(50) <= span <= math.radians(110) or math.radians(150) <= span <= math.radians(200)): continue
            if len(Q) < span * R / .06: continue
            a0 = ang[(k + 1) % len(ang)]
            arcs.append({'c': [float(cx), float(cy)], 'r': float(R), 'a0': float(a0), 'a1': float(a0 + span), 'segs': segs})
    # de-duplicate (doubled line work)
    out = []
    for a in arcs:
        if not any(math.hypot(a['c'][0] - b['c'][0], a['c'][1] - b['c'][1]) < .08 and abs(a['r'] - b['r']) < .08 and abs((a['a0'] + a['a1'] - b['a0'] - b['a1']) / 2 % (2 * np.pi)) < .5 for b in out): out.append(a)
    return out


def mask_from(geoms, shape, org):
    m = np.zeros(shape, np.uint8)
    for g in geoms:
        for p in ([g] if g.geom_type == 'Polygon' else getattr(g, 'geoms', [])):
            if p.is_empty: continue
            cv2.fillPoly(m, [np.round((np.array(p.exterior.coords) - org) / C).astype(np.int32)], 1)
            for h in p.interiors: cv2.fillPoly(m, [np.round((np.array(h.coords) - org) / C).astype(np.int32)], 0)
    return m


def extract(fl):
    s = segments(fl)
    key = KEY[fl]; fp = [Polygon(p).buffer(0) for f in plan['floors'] if f['key'] == key for p in f['footprint']]
    region = unary_union(fp).buffer(1.5)
    import shapely
    keep = shapely.intersects(region, shapely.linestrings(s.reshape(-1, 2, 2))); s = s[keep]
    arcs = find_arcs(s)
    # Door leaves: straight lines from a swing's hinge to one arc end (length ~R). They are not wall faces.
    leaves = set()
    for a in arcs:
        c = np.array(a['c']); R = a['r']
        for t in (a['a0'], a['a1'], (a['a0'] + a['a1']) / 2):
            e = c + R * np.array([math.cos(t), math.sin(t)])
            for P, Q in ((s[:, :2], s[:, 2:]), (s[:, 2:], s[:, :2])):
                hit = (np.hypot(*(P - c).T) < .08) & (np.hypot(*(Q - e).T) < .12)
                leaves.update(np.nonzero(hit)[0].tolist())
                if hit.any(): a['leaf'] = True
    prs = pairs(s, exclude=leaves); pat = pattern_lines(s, prs)
    arc_segs = set()
    quads = []
    for i, j, d, t0, t1, u, n in prs:
        if i in pat or j in pat or i in arc_segs or j in arc_segs: continue
        mi = (s[i, :2] + s[i, 2:]) / 2; base = n * (mi @ n)
        p0 = base + u * t0; p1 = base + u * t1
        Lmin = min(np.hypot(*(s[i, 2:] - s[i, :2])), np.hypot(*(s[j, 2:] - s[j, :2])))
        quads.append((Polygon([p0, p1, p1 + n * d, p0 + n * d]).buffer(.012, join_style=2), Lmin >= .95))
    minx, miny, maxx, maxy = region.bounds; org = np.array([minx, miny])
    shape = (int((maxy - miny) / C) + 2, int((maxx - minx) / C) + 2)
    # Short pairs (both lines < 0.95 m: jambs, returns, but also text strokes) count only where they touch a long wall.
    wall = mask_from([q for q, long_ in quads if long_], shape, org)
    short = mask_from([q for q, long_ in quads if not long_], shape, org) & (1 - wall)
    n_, lab, st, _ = cv2.connectedComponentsWithStats(short, 8)
    touch = np.unique(lab[(cv2.dilate(wall, np.ones((3, 3), np.uint8)) > 0) & (lab > 0)])
    # Inside toilets the short pairs are fixtures and the room-name text: keep only the partitions (long pairs).
    toilets = [Polygon(q).buffer(0).buffer(-.25) for f in plan['floors'] if f['key'] == key for sp in f['spaces'] if sp['type'] == 'toilet' for q in sp['polys']]
    toil = mask_from(toilets, shape, org) if toilets else np.zeros(shape, np.uint8)
    wall |= np.isin(lab, touch).astype(np.uint8) & (1 - toil)
    # Columns / solid blocks: small fully enclosed empty cells (0.04–1.2 m²) touching a wall.
    ink = np.zeros(shape, np.uint8)
    for q in s:
        a = np.round((q[:2] - org) / C).astype(int); b = np.round((q[2:] - org) / C).astype(int)
        cv2.line(ink, tuple(a), tuple(b), 1, 1)
    inv = (1 - (ink | wall)).astype(np.uint8)
    n_, lab, st, _ = cv2.connectedComponentsWithStats(inv, 4)
    near_wall = cv2.dilate(wall, np.ones((3, 3), np.uint8))
    for c in range(1, n_):
        area = st[c, 4] * C * C; w_, h_ = st[c, 2] * C, st[c, 3] * C
        if .08 <= area <= .9 and max(w_, h_) <= 1.1 and area >= .6 * w_ * h_ and max(w_, h_) <= 2.5 * min(w_, h_):
            comp = lab == c
            border = cv2.dilate(comp.astype(np.uint8), np.ones((5, 5), np.uint8)) & (1 - comp)
            if (near_wall[border > 0]).mean() > .12 and toil[comp].mean() < .5: wall[comp] = 1
    wall = cv2.morphologyEx(wall, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    # Fixed seating rows (lecture halls): the row edges are drawn as double lines but are not walls.
    seats = [Polygon(q).buffer(0).buffer(-.5) for f in plan['floors'] if f['key'] == key for sp in f['spaces']
             if any(w in sp['name'] for w in ('階梯教室', '演講廳')) for q in sp['polys']]
    if seats: wall &= 1 - mask_from(seats, shape, org)
    # Drop isolated pieces (text glyphs, furniture symbols): keep components with extent >= 1.6 m.
    n_, lab, st, _ = cv2.connectedComponentsWithStats(wall, 8)
    for c in range(1, n_):
        if math.hypot(st[c, 2], st[c, 3]) * C < 1.6: wall[lab == c] = 0
    # Doors: keep each swing sector clear and record the opening chord along the wall.
    doors = []
    toilet_zone = [Polygon(q).buffer(0).buffer(1.5) for f in plan['floors'] if f['key'] == key for sp in f['spaces'] if sp['type'] == 'toilet' for q in sp['polys']]
    def has_leaf(a):
        c = np.array(a['c']); R = a['r']
        for t in (a['a0'], a['a1']):
            v = np.array([math.cos(t), math.sin(t)]); A, Bq = s[:, :2] - c, s[:, 2:] - c; ta, tb = A @ v, Bq @ v
            da = np.abs(A[:, 0] * v[1] - A[:, 1] * v[0]); db = np.abs(Bq[:, 0] * v[1] - Bq[:, 1] * v[0])
            if ((da < .05) & (db < .05) & (np.abs(np.minimum(ta, tb)) < .12) & (np.maximum(ta, tb) > .6 * R)).any(): return True
        return bool(a.get('leaf'))
    stair_cores = [Polygon(q).buffer(0).buffer(-.6) for f in plan['floors'] if f['key'] == key for sp in f['spaces'] if sp['type'] == 'stair' for q in sp['polys']]
    wall0 = wall.copy()
    dwall = cv2.distanceTransform((1 - wall).astype(np.uint8), cv2.DIST_L2, 3) * C
    dink = cv2.distanceTransform((1 - ink).astype(np.uint8), cv2.DIST_L2, 3) * C
    for a in arcs:
        cx, cy = a['c']; R = a['r']
        hp = np.round((np.array([cx, cy]) - org) / C).astype(int)
        if not (0 <= hp[0] < shape[1] and 0 <= hp[1] < shape[0]) or (dwall[hp[1], hp[0]] > .6 and not a.get('leaf')): continue   # a swing hinges on a wall (or has its drawn leaf)
        if any(sp.contains(Point(cx, cy)) for sp in stair_cores): continue   # stair arrows / handrail ends
        # User 2026-11-19: urinals / basins were read as doors. Inside toilets a swing must be a full quarter arc
        # or have its straight leaf drawn from the hinge; urinal bowls are shallow arcs with no leaf.
        # Urinal symbols (angular bowls) also fit circles but their 'hinge' floats in open floor: in toilets the hinge
        # must sit on a wall.
        if any(t.contains(Point(cx, cy)) for t in toilet_zone):
            if dwall[hp[1], hp[0]] > .2: continue
            if a['a1'] - a['a0'] < math.radians(76) and not has_leaf(a): continue
        e0 = np.array([cx + R * math.cos(a['a0']), cy + R * math.sin(a['a0'])]); e1 = np.array([cx + R * math.cos(a['a1']), cy + R * math.sin(a['a1'])])
        c = np.array([cx, cy])
        # The closed-leaf end lies on the wall line: the wall continues behind the hinge in the opposite direction.
        def wall_behind(e):
            v = (e - c) / R; cnt = 0
            for t in np.arange(.08, .5, .04):
                q = np.round((c - v * t - org) / C).astype(int)
                if 0 <= q[0] < shape[1] and 0 <= q[1] < shape[0] and wall0[q[1], q[0]]: cnt += 1
            return cnt
        if a['a1'] - a['a0'] > math.radians(140):   # double-acting: closed leaf at the middle of the half circle
            am = (a['a0'] + a['a1']) / 2; closed, open_ = np.array([cx + R * math.cos(am), cy + R * math.sin(am)]), e1
        else:
            # The drawn leaf is a straight line from the hinge to the open end; fall back to the wall behind the hinge.
            def leaf(e):
                v = (e - c) / R; A, Bq = s[:, :2] - c, s[:, 2:] - c
                ta, tb = A @ v, Bq @ v; da = np.abs(A[:, 0] * v[1] - A[:, 1] * v[0]); db = np.abs(Bq[:, 0] * v[1] - Bq[:, 1] * v[0])
                ok = (da < .05) & (db < .05) & (np.abs(np.maximum(ta, tb) - R) < .15 * R) & (np.minimum(ta, tb) > -.1 * R) & (np.minimum(ta, tb) < .25 * R)
                return int(ok.sum())
            l0, l1 = leaf(e0), leaf(e1)
            if l0 != l1: closed, open_ = (e1, e0) if l0 > l1 else (e0, e1)
            else: closed, open_ = (e0, e1) if wall_behind(e0) >= wall_behind(e1) else (e1, e0)
        sector = Polygon([c] + [[cx + R * math.cos(t), cy + R * math.sin(t)] for t in np.linspace(a['a0'], a['a1'], 16)])
        v = (closed - c) / R; nrm = (open_ - c) / R
        # opening strip through the wall thickness (both faces), from hinge to the closed-leaf end
        strip = Polygon([c - nrm * .35, closed - nrm * .35, closed + nrm * .05, c + nrm * .05])
        clear = unary_union([sector.buffer(.03), strip])
        wall &= 1 - mask_from([clear], shape, org)
        doors.append({'hinge': [round(cx, 3), round(cy, 3)], 'r': round(R, 3), 'closed': [round(v, 3) for v in closed], 'open': [round(v, 3) for v in open_],
                      'line': [[round(v, 3) for v in c], [round(v, 3) for v in closed]]})
    # Merge double doors (two hinges facing each other on one opening).
    for d in doors: d['double'] = any(o is not d and np.hypot(*(np.array(o['closed']) - d['closed'])) < .25 for o in doors)
    cs, hier = cv2.findContours(wall, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    polys = []
    if hier is not None:
        for i, c in enumerate(cs):
            if hier[0][i][3] != -1: continue
            ext = (c.reshape(-1, 2) * C + org)
            holes = [(cs[j].reshape(-1, 2) * C + org) for j in range(len(cs)) if hier[0][j][3] == i]
            if len(ext) < 3: continue
            P = Polygon(ext, [h for h in holes if len(h) >= 3]).buffer(0).simplify(.02)
            for g in ([P] if P.geom_type == 'Polygon' else P.geoms):
                if g.area > .01: polys.append(g)
    return s, polys, doors, (org, shape, wall)


def render(fl, s, polys, doors, org, shape):
    sc = 2  # px per raster cell
    img = np.full((shape[0] * sc, shape[1] * sc, 3), 255, np.uint8)
    P = lambda p: tuple(np.round((np.array(p) - org) / C * sc).astype(int))
    for q in s: cv2.line(img, P(q[:2]), P(q[2:]), (190, 190, 190), 1, cv2.LINE_AA)
    over = img.copy()
    for g in polys:
        cv2.fillPoly(over, [np.array([P(q) for q in g.exterior.coords], np.int32)], (40, 40, 220))
        for h in g.interiors: cv2.fillPoly(over, [np.array([P(q) for q in h.coords], np.int32)], (255, 255, 255))
    img = cv2.addWeighted(over, .85, img, .15, 0)
    for d in doors:
        c = np.array(d['hinge']); R = d['r']
        a0 = math.degrees(math.atan2(d['closed'][1] - c[1], d['closed'][0] - c[0])); a1 = math.degrees(math.atan2(d['open'][1] - c[1], d['open'][0] - c[0]))
        da = (a1 - a0 + 540) % 360 - 180
        cv2.ellipse(img, P(c), (int(R / C * sc),) * 2, 0, a0, a0 + da, (30, 160, 30), 2, cv2.LINE_AA)
        cv2.line(img, P(c), P(d['open']), (30, 160, 30), 2, cv2.LINE_AA)
        cv2.line(img, P(d['line'][0]), P(d['line'][1]), (0, 200, 0), 6, cv2.LINE_AA)
    # 10 m grid ticks in drawing metres
    for gx in range(int(org[0]) // 10 * 10, int(org[0] + shape[1] * C) + 1, 10):
        cv2.putText(img, f'x{gx}', (P((gx, org[1]))[0] + 3, 30), cv2.FONT_HERSHEY_SIMPLEX, .9, (120, 120, 120), 2)
        cv2.line(img, (P((gx, 0))[0], 0), (P((gx, 0))[0], 12), (120, 120, 120), 2)
    for gy in range(int(org[1]) // 10 * 10, int(org[1] + shape[0] * C) + 1, 10):
        cv2.putText(img, f'y{gy}', (3, P((org[0], gy))[1] - 4), cv2.FONT_HERSHEY_SIMPLEX, .9, (120, 120, 120), 2)
    return img


if __name__ == '__main__':
    out = {'version': 1, 'source': 'buildings/zhili/source/floor-*.pdf vector line work', 'frame': 'plan.json drawing metres',
           'method': 'walls = bands between parallel double lines 0.05–0.42 m apart + columns; doors = swing arcs (hinge, closed-leaf end); gaps without arcs are open',
           'floors': {}}
    (B / 'review').mkdir(exist_ok=True)
    for fl in (sys.argv[1:] or FLOORS):
        s, polys, doors, (org, shape, wall) = extract(fl)
        out['floors'][fl] = {'walls': [[[round(x, 3), round(y, 3)] for x, y in list(g.exterior.coords)[:-1]] + ([] if not g.interiors else []) for g in polys],
                             'wallHoles': [[[[round(x, 3), round(y, 3)] for x, y in list(h.coords)[:-1]] for h in g.interiors] for g in polys],
                             'doors': doors}
        cv2.imwrite(str(B / f'review/walls-{fl}.png'), render(fl, s, polys, doors, org, shape))
        (B / f'review/walls-{fl}.json').write_text(json.dumps({'org': [float(org[0]), float(org[1])], 'pxPerMetre': 2 / C}))
        print(fl, 'segments', len(s), 'wall polygons', len(polys), 'area', round(sum(g.area for g in polys), 1), 'doors', len(doors))
    if not sys.argv[1:]:
        (B / 'walls.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
