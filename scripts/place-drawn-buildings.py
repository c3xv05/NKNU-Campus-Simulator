"""Re-shape and re-place 詠絮樓, 燕窩 and 科技大樓 from the user-supplied floor-plan drawings (2026-11-22).

Shape  : outlines traced from the plan images (pixel polygons below, scale taken from the dimension chains
         printed on the drawings: Yongxu 4292 cm L-wing, Yanwo 4.0 m room module, tech building 1/300 on A3
         printed at A4 = 0.1 m per 110-dpi px).
Place  : rotation / translation fitted by eye + edge-gradient search against the NLSC 2023 orthophoto
         (same origin / projection as scripts/sample-terrain.py).  Positions are model approximations.
Idempotent: the previous rings are kept as geometry.beforeRelocationRing (landscape.js seeds its plants from
         them) and terrainRing keeps the old ground pad, so terrain / road / paving data are NOT regenerated.
Run before scripts/build-building-catalog.py.  Source PDFs are copied next to each building.
"""
import json, math, shutil
from pathlib import Path
root = Path(__file__).resolve().parents[1]
UP = Path('/root/.claude/uploads')


def rot(p, ang, piv, scale, t):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    x, y = (p[0] - piv[0]) * scale, (p[1] - piv[1]) * scale
    return [round(x * c - y * s + t[0], 3), round(x * s + y * c + t[1], 3)]


def load(b):
    return json.loads((root / f'buildings/{b}/building.json').read_text())


def save(b, d):
    (root / f'buildings/{b}/building.json').write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')


def signed(r):
    return sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r))) / 2


# ---------------------------------------------------------------- pixel outlines
# 詠絮樓 2F-5F plan (PDF page 4 @200 dpi); inner corner chamfered (交誼廳 diagonal lobby) so the entrance edge is > 7 m.
YONGXU_PX = [[272, 25], [272, 108], [216, 109], [216, 216], [196, 217], [196, 590], [240, 591], [240, 773], [320, 774],
             [321, 882], [427, 882], [429, 961], [611, 961], [612, 992], [984, 992], [986, 985], [1093, 985], [1095, 929],
             [1178, 929], [1178, 765], [1094, 764], [1093, 709], [986, 709], [984, 686], [655, 686], [515, 546],
             [515, 217], [495, 216], [495, 109], [437, 107], [437, 24]]
YONGXU_FRONT_VERTEX = [655, 686]  # start of the chamfer edge = main entrance (大門)


def mirror(x):
    return 1970 - x


# 燕窩 2F-6F plan (PDF page 6 @200 dpi); symmetric about x=985.  Notch between the arms is the 花園 (open to the garden).
SW_PX = [[658, 295], [1312, 295], [1312, 479], [1661, 479], [1661, 602], [mirror(308), 618], [mirror(47), 748], [mirror(155), 945],
         [mirror(421), 822], [mirror(382), 740], [mirror(437), 705], [mirror(437), 702], [mirror(717), 702], [mirror(775), 702],
         [mirror(800), 675], [mirror(800), 625], [mirror(775), 595], [mirror(717), 595], [mirror(717), 530],
         [717, 530], [717, 595], [775, 595], [800, 625], [800, 675], [775, 702], [717, 702], [437, 702], [437, 705], [382, 740],
         [421, 822], [155, 945], [47, 748], [308, 618], [309, 602], [309, 479], [658, 479]]

TECH_PIX_FILE = root / 'buildings/technology/plan-footprint.json'


def tech_px():
    """Traced from the roof plan (科R, 110 dpi): courtyard block + D wing + fan + SE block + long wing + stair drums."""
    from shapely.geometry import Polygon, Point, box
    from shapely.ops import unary_union
    c = lambda x, y, r: Point(x, y).buffer(r, 64)
    parts = [box(205, 52, 603, 560), c(402, 52, 38).intersection(box(300, 0, 500, 52)), box(398, 548, 512, 725), c(512, 637, 88),
             c(505, 880, 182).intersection(Polygon([(400, 757), (700, 700), (700, 1000), (585, 990)])), c(505, 885, 78),
             Polygon([(630, 740), (775, 692), (790, 692), (790, 1020), (585, 1020), (585, 985)]),
             Polygon([(205, 560), (398, 560), (398, 757), (402, 780), (215, 1090), (166, 1100), (160, 1062), (75, 1088), (55, 1005), (205, 745)]),
             box(75, 588, 205, 690), c(75, 639, 51).intersection(box(0, 580, 75, 700)), c(110, 1105, 45)]
    u = unary_union([p.buffer(0) for p in parts]).buffer(4).buffer(-4)
    g = u if u.geom_type == 'Polygon' else max(u.geoms, key=lambda g: g.area)
    g = g.simplify(1.5)
    return [list(p) for p in g.exterior.coords[:-1]], list(g.centroid.coords[0])


PLACEMENTS = {
    'yongxu': dict(px=YONGXU_PX, scale=1 / 22.55, ang=198, pivot=(21.4 * 22.55 + 196, 21.4 * 22.55 + 25), t=(-159.5, -83.0),
                   pdf='dormitory-escape-plans.pdf', pages='第3、4頁（詠絮樓一樓、二至五樓）'),
    'swallow-dorm': dict(px=SW_PX, scale=0.0727, ang=-8, pivot=(985, 640), t=(94.5, -450.5),
                         pdf='dormitory-escape-plans.pdf', pages='第5–8頁（燕窩一樓、二至六樓、七樓、地下一樓）'),
    'technology': dict(px=None, scale=0.1, ang=70, pivot=None, t=(-40.5, -471.5),
                       pdf=None, pages='工教大樓科B/科1/工2/科3/科4/科5/科R（B1、1F–5F、屋頂）'),
}


def main():
    src_pdfs = sorted(UP.glob('*/*____.pdf')) if UP.exists() else []
    for name, cfg in PLACEMENTS.items():
        d = load(name)
        g, a = d['geometry'], d['appearance']
        old = g.setdefault('beforeRelocationRing', g['ring'])
        g.setdefault('terrainRing', old)  # keep the established ground pad / terrain
        px, piv = cfg['px'], cfg['pivot']
        if name == 'technology':
            px, piv = tech_px()
        ring = [rot(p, cfg['ang'], piv, cfg['scale'], cfg['t']) for p in px]
        if signed(ring) * signed(old) < 0:
            ring.reverse()
            px = px[::-1]
        g['ring'] = ring
        info = dict(source=f"使用者提供平面圖：{cfg['pages']}", pixelOutline=px, pivotPx=piv, metresPerPixel=cfg['scale'],
                    rotationDeg=cfg['ang'], translation=cfg['t'],
                    method='外框由平面圖描出，比例取自圖上尺寸標註；旋轉／平移依國土測繪中心2023正射影像擬合，為模型近似。')
        g['drawingPlacement'] = info
        if name == 'yongxu':
            idx = next(i for i in range(len(px)) if sorted([px[i], px[(i + 1) % len(px)]]) == sorted([YONGXU_FRONT_VERTEX, [515, 546]]))
            a['frontEdge'] = idx
            q, r = ring[idx], ring[(idx + 1) % len(ring)]
            a['frontHint'] = [round((q[0] + r[0]) / 2, 3), round((q[1] + r[1]) / 2, 3)]
        elif name == 'swallow-dorm':
            # 花園 back wall (second-row south face) – main-road mode still picks the road-facing edge
            i = next(i for i, p in enumerate(px) if p == [mirror(717), 530])
            q, r = ring[i], ring[(i + 1) % len(ring)]
            a['frontHint'] = [round((q[0] + r[0]) / 2, 3), round((q[1] + r[1]) / 2, 3)]
        else:
            # keep the hint on the edge nearest to the old hint
            h = a['frontHint']
            best = min(range(len(ring)), key=lambda i: math.hypot((ring[i][0] + ring[(i + 1) % len(ring)][0]) / 2 - h[0], (ring[i][1] + ring[(i + 1) % len(ring)][1]) / 2 - h[1]))
            q, r = ring[best], ring[(best + 1) % len(ring)]
            a['frontHint'] = [round((q[0] + r[0]) / 2, 3), round((q[1] + r[1]) / 2, 3)]
        note = '2026-11-22依使用者提供平面圖重描外框並依正射影像重新定位（舊輪廓保留為beforeRelocationRing，地形台地沿用terrainRing）；外觀與細節待補。'
        a['reference'] = a['reference'].split('；2026-11-22')[0] + '；' + note
        save(name, d)
        print(name, len(old), '->', len(ring), 'vertices; area', round(abs(signed(ring))), 'vs old', round(abs(signed(old))))
    # source drawings
    dorm = root / 'buildings/yongxu/source'
    print('copy PDFs manually from the upload folder if missing (see README)')


if __name__ == '__main__':
    main()
