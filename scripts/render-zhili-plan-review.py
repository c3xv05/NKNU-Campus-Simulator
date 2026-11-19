"""Draw the built Zhili interior (walls, doors, exits, stairs) over the original floor-plan line work.

Output: buildings/zhili/review/built-<floor>.png — grey = original drawing, dark red = wall as built,
green = door opening (with drawn swing), blue = exterior entrance, orange = stair treads. Drawing metres.
"""
import json, math, sys, importlib.util
from pathlib import Path
import numpy as np, cv2
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ex', root / 'scripts/extract-zhili-walls.py'); ex = importlib.util.module_from_spec(spec); spec.loader.exec_module(ex)
I = json.loads((root / 'buildings/zhili/interior.json').read_text()); WJ = json.loads((root / 'buildings/zhili/walls.json').read_text())['floors']
T = I['transform']
def drawing(p):
    x, z = p[0] - T['tx'], p[1] - T['tz']; return (T['a'] * x + T['b'] * z, -T['b'] * x + T['a'] * z)
K = 40  # px per metre
for fl in I['floors']:
    lab = fl['label']; s = ex.segments(lab)
    ol = np.array(fl['outline']); org = ol.min(0) - 3; size = ol.max(0) + 3 - org
    img = np.full((int(size[1] * K), int(size[0] * K), 3), 255, np.uint8)
    P = lambda p: (int(round((p[0] - org[0]) * K)), int(round((p[1] - org[1]) * K)))
    for q in s: cv2.line(img, P(q[:2]), P(q[2:]), (175, 175, 175), 1, cv2.LINE_AA)
    over = img.copy()
    for st in fl['stairs']:
        for t in st['treads']: cv2.rectangle(over, P(t['rect'][:2]), P(t['rect'][2:]), (60, 160, 250), 1)
    for r in fl['walls']: cv2.rectangle(over, P(r[:2]), P(r[2:]), (40, 30, 170), -1)
    for r in fl['sills']: cv2.rectangle(over, P(r['rect'][:2]), P(r['rect'][2:]), (200, 170, 120), -1)
    for e in fl['exits']:
        for r in e['rect']: cv2.rectangle(over, P(r[:2]), P(r[2:]), (220, 120, 20), -1)
    img = cv2.addWeighted(over, .8, img, .2, 0)
    built = [[drawing(q) for q in d['line']] for d in fl['doors']] + [[drawing(q) for q in e['line']] for e in fl['exits']]
    for d in WJ[lab]['doors']:
        if not any(math.dist(d['hinge'], b[0]) < .05 or math.dist(d['hinge'], b[1]) < .05 for b in built): continue   # only doors that were built
        h = np.array(d['hinge']); c = np.array(d['closed']); o = np.array(d['open']); R = d['r']
        a0 = math.degrees(math.atan2(*(c - h)[::-1])); a1 = math.degrees(math.atan2(*(o - h)[::-1])); da = (a1 - a0 + 540) % 360 - 180
        cv2.ellipse(img, P(h), (int(R * K),) * 2, 0, a0, a0 + da, (20, 150, 20), 2, cv2.LINE_AA)
        cv2.line(img, P(h), P(o), (20, 150, 20), 2, cv2.LINE_AA); cv2.line(img, P(h), P(c), (0, 210, 0), 5)
    for sp in fl['spaces']:
        if sp['anchor'] and sp['type'] not in ('elevator',):
            a = drawing(sp['anchor'])
    cv2.imwrite(str(root / f'buildings/zhili/review/built-{lab}.png'), img)
    print(lab, img.shape)
