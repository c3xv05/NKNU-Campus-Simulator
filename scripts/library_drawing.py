"""Shared reading of the 圖資大樓 floor-plan PDFs (user upload 2026-11-25, buildings/library/source/floor-1F.pdf / floor-2F.pdf).

Frame: drawing metres on the 1F sheet, x = page_x * S, y = page_y * S (y points down the sheet, roughly south).
The 2F sheet is the same drawing shifted on the page by (68.09, 37.06) pt (72 columns coincide within 0.25 pt).
S = 8.0 m / 112.8 pt (the 8 m column grid; 1:200 on A1).  World placement (NLSC 2023 orthophoto, centre of the
pool dome + south-wing direction; fan plaza edges checked): world = R(THETA) * (x, y) + T, x east / z south.
User 2026-11-25: drawing 1F = game B1, drawing 2F = game 1F (the entrance level, below S04); nothing above.
"""
import math
from pathlib import Path
import numpy as np
import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'buildings/library/source'
S = 8.0 / 112.8
PAGE_SHIFT = {'1F': (0.0, 0.0), '2F': (68.09, 37.06)}
THETA = math.radians(2.0)
T = (-16.661, -143.445)


def to_world(p):
    c, s = math.cos(THETA), math.sin(THETA)
    return [round(c * p[0] - s * p[1] + T[0], 4), round(s * p[0] + c * p[1] + T[1], 4)]


def transform():
    """Same form as the Zhili/Gauss drawing transform: world = (a x - b y + tx, b x + a y + tz)."""
    return {'a': math.cos(THETA), 'b': math.sin(THETA), 'tx': T[0], 'tz': T[1]}


def page_to_drawing(fl, x, y):
    dx, dy = PAGE_SHIFT[fl]
    return ((x - dx) * S, (y - dy) * S)


def raw_segments(fl):
    pg = fitz.open(SRC / f'floor-{fl}.pdf')[0]
    out = []
    for d in pg.get_drawings():
        if d['type'] == 'f': continue
        for it in d['items']:
            pts = []
            if it[0] == 'l': pts = [it[1], it[2]]
            elif it[0] == 'qu': q = it[1]; pts = [q.ul, q.ur, q.lr, q.ll, q.ul]
            elif it[0] == 're': r = it[1]; pts = [r.tl, r.tr, r.br, r.bl, r.tl]
            for a, b in zip(pts, pts[1:]):
                out.append((*page_to_drawing(fl, a.x, a.y), *page_to_drawing(fl, b.x, b.y)))
    s = np.array(out)
    L = np.hypot(s[:, 2] - s[:, 0], s[:, 3] - s[:, 1])
    return s[L > 1e-4]


def merge_collinear(s, gap=.02, ang=.3, off=.006):
    """Join touching / overlapping collinear pieces (the sheets trace long lines as short runs)."""
    d = s[:, 2:] - s[:, :2]; th = np.mod(np.arctan2(d[:, 1], d[:, 0]), np.pi)
    nb = int(round(180 / ang)); bucket = np.round(th / math.radians(ang)).astype(int) % nb
    merged = []
    for b in np.unique(bucket):
        I = np.nonzero(bucket == b)[0]
        t = b * math.radians(ang); u = np.array([math.cos(t), math.sin(t)]); n = np.array([-u[1], u[0]])
        o = ((s[I, :2] + s[I, 2:]) / 2) @ n; t0 = np.minimum(s[I, :2] @ u, s[I, 2:] @ u); t1 = np.maximum(s[I, :2] @ u, s[I, 2:] @ u)
        order = np.lexsort((t0, np.round(o / off)))
        runs, cur = [], None
        for k in order:
            if cur and abs(o[k] - cur[0]) <= off and t0[k] <= cur[2] + gap:
                cur[2] = max(cur[2], t1[k]); continue
            if cur: runs.append(cur)
            cur = [o[k], t0[k], t1[k]]
        if cur: runs.append(cur)
        merged += [[*(u * a + n * om), *(u * e + n * om)] for om, a, e in runs]
    return np.array(merged)


def segments(fl):
    return merge_collinear(raw_segments(fl))
