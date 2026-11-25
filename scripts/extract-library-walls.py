"""Read walls, doors and columns from the 圖資大樓 floor-plan PDFs (same method as scripts/extract-zhili-walls.py).

Wall = band between two parallel drawn lines 0.05–0.42 m apart that overlap (the sheets trace lines as short runs,
merged first by scripts/library_drawing.py); door = swing arc found in the short-segment line work; column = solid
blob on the rendered sheet. Output (drawing metres, library_drawing frame): buildings/library/walls.json and
review images buildings/library/review/walls-<floor>.png.
"""
import importlib.util, json, math, sys
from pathlib import Path
import numpy as np, cv2
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
sys.path.insert(0, str(Path(__file__).resolve().parent))
import library_drawing as LD

root = LD.ROOT
spec = importlib.util.spec_from_file_location('zw', root / 'scripts/extract-zhili-walls.py')
ZW = importlib.util.module_from_spec(spec); spec.loader.exec_module(ZW)
C = ZW.C


def columns(fl):
    """Solid column blobs on the sheet rendered at 300 dpi (squares on the facade, rounds inside)."""
    pg = LD.fitz.open(LD.SRC / f'floor-{fl}.pdf')[0]
    pix = pg.get_pixmap(dpi=300, colorspace=LD.fitz.csGRAY)
    im = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)
    b = (im < 100).astype(np.uint8)
    o = cv2.morphologyEx(b, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    n, lab, st, cen = cv2.connectedComponentsWithStats(o)
    out = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if not (20 < w < 90 and 20 < h < 90): continue
        comp = (lab[y:y + h, x:x + w] == i).astype(np.uint8)
        cs, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        poly = [LD.page_to_drawing(fl, (q[0] + x) * 72 / 300, (q[1] + y) * 72 / 300) for q in cs[0].reshape(-1, 2)]
        P = Polygon(poly).buffer(0).simplify(.03)
        round_ = a / (w * h) < .86
        cx, cy = LD.page_to_drawing(fl, cen[i][0] * 72 / 300, cen[i][1] * 72 / 300)
        out.append({'c': [round(cx, 3), round(cy, 3)], 'r': round(math.sqrt(P.area / math.pi), 3) if round_ else None,
                    'ring': [[round(px, 3), round(py, 3)] for px, py in list(P.minimum_rotated_rectangle.exterior.coords)[:-1]] if not round_ else None})
    return out


def extract(fl):
    raw = LD.raw_segments(fl); s = LD.segments(fl)
    arcs = ZW.find_arcs(raw)
    leaves = set()
    for a in arcs:
        c = np.array(a['c']); R = a['r']
        for t in (a['a0'], a['a1']):
            e = c + R * np.array([math.cos(t), math.sin(t)])
            for P, Q in ((s[:, :2], s[:, 2:]), (s[:, 2:], s[:, :2])):
                hit = (np.hypot(*(P - c).T) < .08) & (np.hypot(*(Q - e).T) < .12)
                leaves.update(np.nonzero(hit)[0].tolist())
                if hit.any(): a['leaf'] = True
    prs = ZW.pairs(s, exclude=leaves); pat = ZW.pattern_lines(s, prs)
    quads = []
    for i, j, d, t0, t1, u, n in prs:
        if i in pat or j in pat: continue
        mi = (s[i, :2] + s[i, 2:]) / 2; base = n * (mi @ n)
        p0 = base + u * t0; p1 = base + u * t1
        Lmin = min(np.hypot(*(s[i, 2:] - s[i, :2])), np.hypot(*(s[j, 2:] - s[j, :2])))
        quads.append((Polygon([p0, p1, p1 + n * d, p0 + n * d]).buffer(.012, join_style=2), Lmin >= .95, abs(d)))
    return raw, s, arcs, quads


if __name__ == '__main__':
    out = {}
    for fl in ['1F', '2F']:
        raw, s, arcs, quads = extract(fl)
        cols = columns(fl)
        out[fl] = {'arcs': len(arcs), 'quads': len(quads), 'columns': len(cols)}
        mn = s[:, :2].min(0); mx = s[:, :2].max(0); k = 20
        img = np.full((int((mx[1] - mn[1]) * k) + 10, int((mx[0] - mn[0]) * k) + 10, 3), 255, np.uint8)
        P = lambda p: (int((p[0] - mn[0]) * k), int((p[1] - mn[1]) * k))
        for q in s: cv2.line(img, P(q[:2]), P(q[2:]), (190, 190, 190), 1)
        for g, long_, d in quads: cv2.fillPoly(img, [np.array([P(q) for q in g.exterior.coords], np.int32)], (40, 40, 220) if long_ else (40, 160, 220))
        for a in arcs: cv2.circle(img, P(a['c']), int(a['r'] * k), (0, 160, 0), 1)
        for c in cols: cv2.circle(img, P(c['c']), 6, (200, 0, 200), -1)
        cv2.imwrite(str(root / f'buildings/library/review/walls-{fl}.png'), img)
    print(out)
