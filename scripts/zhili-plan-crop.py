"""Crop a Zhili floor plan with a metre grid, the original line work (grey) and the walls as built (red).

  python scripts/zhili-plan-crop.py B1 0 28 9 46 out.png        # floor x0 y0 x1 y1 (drawing metres) [out.png] [px per metre]
Blue = low partitions, green = fixtures, brown = closed door leaves. Read coordinates off the grid
(red lines every 5 m, grey every 1 m) and write them into buildings/zhili/overrides.json.
"""
import importlib.util, json, sys
from pathlib import Path
import numpy as np, cv2
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ex', root / 'scripts/extract-zhili-walls.py'); ex = importlib.util.module_from_spec(spec); spec.loader.exec_module(ex)
I = json.loads((root / 'buildings/zhili/interior.json').read_text())
lab = sys.argv[1]; x0, y0, x1, y1 = map(float, sys.argv[2:6]); out = sys.argv[6] if len(sys.argv) > 6 else f'zhili-{lab}-crop.png'; K = float(sys.argv[7]) if len(sys.argv) > 7 else 60
fl = next(f for f in I['floors'] if f['label'] == lab)
img = np.full((int((y1 - y0) * K), int((x1 - x0) * K), 3), 255, np.uint8)
P = lambda p: (int(round((p[0] - x0) * K)), int(round((p[1] - y0) * K)))
for q in ex.segments(lab): cv2.line(img, P(q[:2]), P(q[2:]), (120, 120, 120), 1, cv2.LINE_AA)
ov = img.copy()
for r in fl['walls']: cv2.rectangle(ov, P(r[:2]), P(r[2:]), (40, 30, 170), -1)
for r in fl['sills']: cv2.rectangle(ov, P(r['rect'][:2]), P(r['rect'][2:]), (200, 120, 30), -1)
for r in fl['furniture']:
    if 'r' in r: cv2.rectangle(ov, P(r['r'][:2]), P(r['r'][2:]), (60, 170, 60), -1)
for r in fl.get('doorLeaves', []): cv2.rectangle(ov, P(r[:2]), P(r[2:]), (30, 100, 160), -1)
img = cv2.addWeighted(ov, .5, img, .5, 0)
for g in range(int(np.floor(x0)), int(np.ceil(x1)) + 1):
    cv2.line(img, P((g, y0)), P((g, y1)), (210, 210, 210) if g % 5 else (150, 150, 255), 1); cv2.putText(img, str(g), (P((g, y0))[0] + 2, 12), 0, .4, (200, 0, 0), 1)
for g in range(int(np.floor(y0)), int(np.ceil(y1)) + 1):
    cv2.line(img, P((x0, g)), P((x1, g)), (210, 210, 210) if g % 5 else (150, 150, 255), 1); cv2.putText(img, str(g), (2, P((x0, g))[1] - 2), 0, .4, (200, 0, 0), 1)
cv2.imwrite(out, img); print(out, img.shape)
