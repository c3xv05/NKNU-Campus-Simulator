"""Read the dashed driveway lane curves of the Zhili B1 drawing (floor-B1.pdf) into buildings/zhili/lanes.json.

The lane centre lines are drawn as chains of very short non-axis segments. Circled stall numbers, stair arcs, seat rows and
the ramp grating are also short segments, so only connected chains at least 5 m wide and 10 m long count. Output: B1 paint
polygons (0.1 m wide strokes, drawing metres) that scripts/build-zhili-interior.py triangulates into the garage floor paint.
"""
import importlib.util, json, math
from pathlib import Path
from shapely.geometry import LineString, mapping
from shapely.ops import unary_union
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ex', root / 'scripts/extract-zhili-walls.py'); ex = importlib.util.module_from_spec(spec); spec.loader.exec_module(ex)
segs = [tuple(float(v) for v in q) for q in ex.segments('B1')]
ang = [q for q in segs if math.hypot(q[2] - q[0], q[3] - q[1]) < .4 and abs(q[0] - q[2]) > .005 and abs(q[1] - q[3]) > .005]
lines = [LineString([q[:2], q[2:]]) for q in ang]
blob = unary_union([l.buffer(.25) for l in lines])
out = []
for comp in (blob.geoms if hasattr(blob, 'geoms') else [blob]):
    w, h = comp.bounds[2] - comp.bounds[0], comp.bounds[3] - comp.bounds[1]
    if min(w, h) < 5 or max(w, h) < 10: continue
    stroke = unary_union([l.buffer(.05, cap_style=2) for l in lines if comp.contains(l.centroid)]).simplify(.03)
    for g in (stroke.geoms if hasattr(stroke, 'geoms') else [stroke]):
        if g.area > .02: out.append([[round(x, 3), round(y, 3)] for x, y in g.exterior.coords][:-1])
(root / 'buildings/zhili/lanes.json').write_text(json.dumps({'note': 'B1 driveway lane paint polygons (drawing metres), scripts/extract-zhili-lanes.py', 'B1': out}, separators=(',', ':')))
print(len(out), 'paint polygons', sum(len(p) for p in out), 'vertices')
