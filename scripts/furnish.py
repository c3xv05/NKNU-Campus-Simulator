"""Room furniture laid out from the room names of the reviewed floor plans (shared by the plan-driven interiors).

Each named room gets a furniture set chosen from its name (classroom, lecture hall, service office, office,
conference, lounge, pantry, copy room, clinic, equipment, storage, club / recreation, principal's suite).
Pieces are axis-aligned boxes in the drawing frame, placed inside the room's largest clear rectangle; anything
that would fall within 1.3 m of a door, exit or stair hall is dropped so circulation stays open, and rows keep
>= 0.9 m aisles. Layouts are model approximations from the room names, not furniture surveys.
Output item: {'r': [x0, y0, x1, y1], 'y': [bottom, top], 'm': material}; blocks: footprints that stop walking.
"""
import numpy as np, cv2

KINDS = [  # (keyword, kind) — first match wins
    ('校長室', 'principal'), ('會議室', 'conference'), ('接待室', 'lounge'), ('休息室', 'lounge'), ('茶水間', 'pantry'),
    ('影印室', 'copy'), ('健康中心', 'clinic'), ('郵局', 'post'), ('教務處', 'service'), ('學務處', 'service'),
    ('總務處', 'service'), ('人事會計室', 'service'), ('辦公室', 'office'), ('祕書室', 'office'), ('電化教室', 'classroom'),
    ('普通教室', 'classroom'), ('108 階梯教室', 'lecture'), ('演講廳空調', 'equipment'), ('康樂室', 'recreation'),
    ('社團室', 'club'), ('軍訓室', 'club'), ('電信室', 'equipment'), ('機房', 'equipment'), ('中央控制室', 'control'),
    ('配電室', 'equipment'), ('機械室', 'equipment'), ('空調機房', 'equipment'), ('器材室', 'storage'), ('儲藏室', 'storage'),
    ('準備室', 'storage'), ('放映室', 'projection'), ('舞台', 'stage')]

def kind_of(name):
    for k, v in KINDS:
        if k in name: return v
    return None

def largest_rect(free):
    """Largest axis-aligned all-True rectangle (cells): returns (x0, y0, x1, y1) inclusive or None."""
    H, W = free.shape; h = np.zeros(W, int); best = (0, None)
    for y in range(H):
        h = np.where(free[y], h + 1, 0); stack = []
        for x in range(W + 1):
            cur = h[x] if x < W else 0; start = x
            while stack and stack[-1][1] >= cur:
                s, hh = stack.pop(); area = hh * (x - s)
                if area > best[0]: best = (area, (s, y - hh + 1, x - 1, y))
                start = s
            stack.append((start, cur))
    return best[1]

class Room:
    """A room rectangle in metres with helpers to add pieces relative to a chosen 'front' side."""
    def __init__(self, x0, y0, x1, y1): self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1; self.items = []; self.blocks = []
    def box(self, r, y0, y1, m, block=True):
        r = [round(min(r[0], r[2]), 3), round(min(r[1], r[3]), 3), round(max(r[0], r[2]), 3), round(max(r[1], r[3]), 3)]
        self.items.append({'r': r, 'y': [round(y0, 3), round(y1, 3)], 'm': m})
        if block: self.blocks.append(r)

def furnish_room(kind, R, front, exterior):
    """front: side the room faces ('x0','x1','y0','y1'); exterior: sides on the facade (windows)."""
    along_x = front in ('y0', 'y1')            # rows run along x when the front is a y side
    L = (R.x1 - R.x0) if along_x else (R.y1 - R.y0)   # width across the room (parallel to the front wall)
    D = (R.y1 - R.y0) if along_x else (R.x1 - R.x0)   # depth away from the front wall
    def P(u, v):  # u across [0,L], v depth from the front [0,D] -> drawing point
        if front == 'y0': return (R.x0 + u, R.y0 + v)
        if front == 'y1': return (R.x0 + u, R.y1 - v)
        if front == 'x0': return (R.x0 + v, R.y0 + u)
        return (R.x1 - v, R.y0 + u)
    def B(u0, v0, u1, v1, y0, y1, m, block=True):
        a, b = P(u0, v0), P(u1, v1); R.box([a[0], a[1], b[0], b[1]], y0, y1, m, block)
    back_free = 'y1' if front == 'y0' else 'y0' if front == 'y1' else 'x1' if front == 'x0' else 'x0'
    inner_side = next((s for s in ('x0', 'x1', 'y0', 'y1') if s not in exterior), None)
    def table(u0, v0, u1, v1, top=.74, m='wood'):
        # top slab + two end panels (legs); the whole footprint blocks walking
        a, b = P(u0, v0), P(u1, v1); R.blocks.append([round(min(a[0], b[0]), 3), round(min(a[1], b[1]), 3), round(max(a[0], b[0]), 3), round(max(a[1], b[1]), 3)])
        B(u0, v0, u1, v1, top - .04, top, m, False); B(u0, v0, u0 + .05, v1, 0, top - .04, 'metal', False); B(u1 - .05, v0, u1, v1, 0, top - .04, 'metal', False)
    def chair(u, v, face=1):  # seat slab on two panels + backrest on the far side (face=+1 faces the front)
        a, b = P(u - .23, v - .23), P(u + .23, v + .23); R.blocks.append([round(min(a[0], b[0]), 3), round(min(a[1], b[1]), 3), round(max(a[0], b[0]), 3), round(max(a[1], b[1]), 3)])
        B(u - .23, v - .23, u + .23, v + .23, .42, .46, 'fabric', False); B(u - .23, v - .23, u - .19, v + .23, 0, .42, 'metal', False); B(u + .19, v - .23, u + .23, v + .23, 0, .42, 'metal', False)
        bv = v + .19 if face > 0 else v - .23; B(u - .23, bv, u + .23, bv + .04, .46, .9, 'fabric', False)
    def desk(u, v, w=1.2, d=.6, chair_behind=True):
        table(u, v, u + w, v + d)
        if chair_behind: chair(u + w / 2, v + d + .33, 1)
    def cabinets(side_v=None, n=None, depth=.45, h=1.8):
        # along the back wall (v = D - depth) by default
        v0 = D - depth if side_v is None else side_v
        n = n or max(1, int((L - 1.6) / .9)); w = min(.9, (L - 1.6) / n) if n else 0
        for i in range(n): u = .8 + i * w; B(u, v0, u + w - .05, v0 + depth, 0, h, 'metal')
    if kind in ('classroom', 'lecture'):
        B(L * .2, 0, L * .8, .06, .9, 2.1, 'board', False)                      # blackboard on the front wall
        B(L / 2 - .6, 1.0, L / 2 + .6, 1.6, 0, 1.0, 'wood')                       # lectern / teacher desk
        if kind == 'lecture':
            B(L * .25, 0, L * .75, .04, 2.2, 3.1, 'screen', False)
        dw, dd, pu, pv = (.6, .5, 1.05, 1.0) if kind == 'classroom' else (.55, .45, .6, 1.0)
        v = 2.6
        while v + dd + .6 < D - .9:
            if kind == 'classroom':
                n = int((L - 1.0) / pu); u0 = (L - n * pu) / 2 + (pu - dw) / 2
                for i in range(n): desk(u0 + i * pu, v, dw, dd)
            else:  # continuous bench rows with a centre aisle
                half = (L - 1.2) / 2 - .6
                for u0 in (.6, L / 2 + .6):
                    table(u0, v, u0 + half, v + .4)
                    k = int(half / pu)
                    for i in range(k): chair(u0 + .3 + i * pu, v + .75, 1)
            v += pv + (0 if kind == 'classroom' else .2)
    elif kind in ('office', 'service', 'post'):
        start = 0.0
        if kind in ('service', 'post'):                                          # counter facing the door side
            B(1.2, 1.5, L - .4, 2.1, 0, 1.05, 'wood'); start = 2.4
        u = .8; v = start + .9
        while v + 1.4 < D - 1.0:
            u = .8
            while u + 1.4 < L - .8: desk(u, v, 1.4, .7); u += 2.4
            v += 2.2
        cabinets()
        if kind == 'post':
            for i in range(int((L - 1.6) / 1.0)): B(.8 + i, D - .5, 1.7 + i, D - .05, 0, 2.0, 'wood')
    elif kind == 'principal':
        B(L / 2 - .9, D - 2.4, L / 2 + .9, D - 1.5, 0, .76, 'wood'); chair(L / 2, D - 1.0, -1)
        B(1.0, 1.6, 3.0, 2.4, 0, .45, 'wood')                                     # coffee table
        B(1.0, 1.0, 3.0, 1.4, 0, .8, 'fabric'); B(1.0, 2.6, 3.0, 3.0, 0, .8, 'fabric')
        for i in range(int((L - 1.6) / 1.0)): B(.8 + i, D - .45, 1.75 + i, D - .05, 0, 2.0, 'wood')
    elif kind == 'conference':
        tl = max(2.0, L - 3.2); td = max(1.2, min(2.0, D - 3.4)); u0 = (L - tl) / 2; v0 = (D - td) / 2
        table(u0, v0, u0 + tl, v0 + td, .76)
        n = int(tl / .8)
        for i in range(n): uc = u0 + .4 + i * .8; chair(uc, v0 - .45, -1); chair(uc, v0 + td + .45, 1)
    elif kind == 'lounge':
        for cu in ([L / 2] if L < 7 else [L * .3, L * .7]):
            B(cu - .9, D / 2 - .4, cu + .9, D / 2 + .4, 0, .45, 'wood')
            B(cu - 1.0, D / 2 - 1.5, cu + 1.0, D / 2 - .8, 0, .8, 'fabric'); B(cu - 1.0, D / 2 + .8, cu + 1.0, D / 2 + 1.5, 0, .8, 'fabric')
    elif kind == 'pantry':
        B(.4, D - .65, L - .4, D - .05, 0, .9, 'white'); B(L / 2 - .3, D - .6, L / 2 + .3, D - .1, .9, .95, 'metal', False)
        B(.4, .4, 1.1, 1.1, 0, 1.8, 'white')
    elif kind == 'copy':
        for i in range(max(1, int((L - 1.6) / 1.6))): B(.8 + i * 1.6, D - .8, 1.5 + i * 1.6, D - .1, 0, 1.05, 'white')
        B(L / 2 - .9, 1.4, L / 2 + .9, 2.1, 0, .8, 'wood')
    elif kind == 'clinic':
        for i in range(max(1, int((L - 1.0) / 1.4))): B(.6 + i * 1.4, D - 2.0, 1.5 + i * 1.4, D - .1, 0, .55, 'white')
        desk(.8, .9, 1.4, .7); cabinets(side_v=.05, n=2)
    elif kind in ('equipment', 'control'):
        if kind == 'control':
            B(.8, 1.2, L - .8, 1.9, 0, .8, 'dark'); B(.8, 1.2, L - .8, 1.3, .8, 1.4, 'screen', False)
        v = 1.6 if kind == 'equipment' else 3.0
        while v + 1.0 < D - .4:
            B(.8, v, L - .8, v + .8, 0, 2.0, 'metal'); v += 2.0
    elif kind in ('storage', 'projection'):
        if kind == 'projection': B(L / 2 - .6, .2, L / 2 + .6, .9, 0, 1.1, 'dark')
        for i in range(max(1, int((L - 1.6) / 1.0))): B(.8 + i, D - .5, 1.75 + i, D - .05, 0, 2.0, 'metal')
    elif kind == 'recreation':
        for cu in ([L / 2] if L < 9 else [L * .3, L * .7]): table(cu - .76, D / 2 - 1.37, cu + .76, D / 2 + 1.37, .76, 'green')
        B(.6, D - .9, 2.6, D - .2, 0, .8, 'fabric')
    elif kind == 'club':
        v = 1.4
        while v + 1.0 < D - 1.0:
            table(L / 2 - 1.2, v, L / 2 + 1.2, v + 1.0)
            for uc in (L / 2 - .8, L / 2, L / 2 + .8): chair(uc, v - .45, -1); chair(uc, v + 1.45, 1)
            v += 3.0
        cabinets()
    elif kind == 'stage':
        B(L / 2 - .3, D * .4, L / 2 + .3, D * .4 + .5, 0, 1.15, 'wood')
    return R

def furnish_floor(spaces, walls_final, keepout, outline_mask, H, W, cell, ox, oy, CELL):
    """spaces: dicts with name/type/mask; keepout: uint8 mask of door/exit/stair clearances (already dilated)."""
    items, blocks = [], []
    free_all = (1 - walls_final).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * int(.3 / CELL) + 1,) * 2)
    for s in spaces:
        kind = kind_of(s['name'])
        if not kind or s.get('type') == 'void': continue
        free = cv2.erode((s['mask'] & free_all).astype(np.uint8), k)
        rc = largest_rect(free > 0)
        if not rc: continue
        x0, y0, x1, y1 = rc
        if (x1 - x0) * CELL < 1.8 or (y1 - y0) * CELL < 1.8: continue
        R = Room(ox + x0 * CELL, oy + y0 * CELL, ox + (x1 + 1) * CELL, oy + (y1 + 1) * CELL)
        # Exterior sides: the rectangle side that lies near the building outline (windows there).
        def outside(px, py):
            ix, iy = int(round((px - ox) / CELL)), int(round((py - oy) / CELL))
            return not (0 <= ix < W and 0 <= iy < H) or not outline_mask[iy, ix]
        ext = [sd for sd, (px, py) in {'x0': (R.x0 - .8, (R.y0 + R.y1) / 2), 'x1': (R.x1 + .8, (R.y0 + R.y1) / 2),
                                         'y0': ((R.x0 + R.x1) / 2, R.y0 - .8), 'y1': ((R.x0 + R.x1) / 2, R.y1 + .8)}.items() if outside(px, py)]
        # Front: for rooms with a board / counter, a short interior side (classrooms) or the door side (service).
        sides = {'x0': R.y1 - R.y0, 'x1': R.y1 - R.y0, 'y0': R.x1 - R.x0, 'y1': R.x1 - R.x0}
        door_cells = np.argwhere(keepout & s['mask'] if keepout is not None else np.zeros((1, 2), int))
        def door_dist(sd):
            if not len(door_cells): return 99
            c = {'x0': lambda p: abs(ox + p[1] * CELL - R.x0), 'x1': lambda p: abs(ox + p[1] * CELL - R.x1),
                 'y0': lambda p: abs(oy + p[0] * CELL - R.y0), 'y1': lambda p: abs(oy + p[0] * CELL - R.y1)}[sd]
            return min(c(p) for p in door_cells[::7])
        if kind in ('service', 'post'): front = min(sides, key=door_dist)
        elif kind in ('classroom', 'lecture'):
            short = sorted(sides, key=lambda sd: sides[sd])[:2]; front = max(short, key=door_dist)
        else: front = next((sd for sd in sorted(sides, key=door_dist) if sd not in ext), min(sides, key=door_dist))
        furnish_room(kind, R, front, ext)
        def clear(r):
            a = [int((r[0] - ox) / CELL), int((r[1] - oy) / CELL)]; b = [int((r[2] - ox) / CELL), int((r[3] - oy) / CELL)]
            return keepout is None or not keepout[max(a[1], 0):b[1] + 1, max(a[0], 0):b[0] + 1].any()
        R.items = [it for it in R.items if clear(it['r'])]
        blocks += [b for b in R.blocks if clear(b)]
        for it in R.items:
            r = it['r']; a = [int((r[0] - ox) / CELL), int((r[1] - oy) / CELL)]; b = [int((r[2] - ox) / CELL), int((r[3] - oy) / CELL)]
            if keepout is not None and keepout[max(a[1], 0):b[1] + 1, max(a[0], 0):b[0] + 1].any(): continue
            items.append({**it, 'room': s['name']})
    return items, blocks
