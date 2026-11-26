"""圖資大樓 west hillside terrace (user 2026-11-26).

The hill between the building and the road (S04 / 師大路三段 side) must sit at the B1 floor height, i.e. level with
the car park north of the building (the plaza outside the door has another storey below it).  The strip within
1.5 x the sidewalk width (5.4 m) beyond the road's sidewalk stays untouched; beyond it the ground drops quickly
(BLEND m) to the B1 level, which then continues to the building.  The south-west end blends into the falling
terrain (level-area blend).  Writes the level area 'library-west-terrace' into facilities/campus-plazas/layout.json
and patches data/campus.json + data/site-layout.js; the footpaths east of the S04 sidewalk are removed (listed in layout['removeFootpaths']) the footpaths to remove east of the S04 sidewalk.
Level = B1 base - 0.185 (level areas add 0.185 when rendering the ground).
"""
import json, subprocess, math
from pathlib import Path
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union
root = Path(__file__).resolve().parents[1]
layout_path = root / 'facilities/campus-plazas/layout.json'
layout = json.loads(layout_path.read_text()); c = json.loads((root / 'data/campus.json').read_text())
tags = json.loads((root / 'data/road-tags.json').read_text())
base = json.loads((root / 'buildings/library/building.json').read_text())['geometry']['drawingPlacement']['base']
SIDEWALK, RESERVE, BLEND = 3.6, 1.5 * 3.6, 8.0
WINDOW = Polygon([(-45, -112), (26, -112), (26, -8), (8, 2), (-4, 16), (-45, 16)])   # world: west side of the building, SW end
buffers = []
for r in c['roads']:
    t = tags.get(str(r['osm']), {})
    if t.get('highway') not in ('residential', 'service', 'tertiary', 'unclassified'): continue
    line = LineString(r['line'])
    if line.distance(WINDOW) > 40: continue
    buffers.append(line.buffer(r['width'] / 2 + SIDEWALK + RESERVE + BLEND))
ring = WINDOW.difference(unary_union(buffers))
parts = sorted([g for g in ([ring] if ring.geom_type == 'Polygon' else ring.geoms) if g.area > 50], key=lambda g: -g.area)
area = unary_union(parts).buffer(.5).buffer(-.5).simplify(.2)
assert area.geom_type == 'Polygon', area.geom_type
anchor = [-40.0, -60.0]
q = json.dumps({'raw': {'a': anchor}})
raw = json.loads(subprocess.run(['node', str(root / 'scripts/library-heights.mjs'), q], capture_output=True, text=True, check=True).stdout)['a']
entry = {'id': 'library-west-terrace', 'name': '圖資大樓西側山體（與B1／北側停車場同高）', 'ring': [[round(x, 3), round(z, 3)] for x, z in list(area.exterior.coords)[:-1]],
         'anchor': anchor, 'heightOffset': round(base - .185 - raw, 3), 'blend': BLEND,
         'reference': '使用者2026-11-26：圖資大樓西邊到馬路前的山體與北側停車場（B1）同高；與馬路保留1.5倍人行道寬（5.4m），其餘斜坡快速降到B1高度；西南端以平台混合銜接。anchor處原始高程可能被其他平台影響，故只在anchor遠離所有平台時才可信。'}
layout['levelAreas'] = [a for a in layout['levelAreas'] if a['id'] != entry['id']] + [entry]
# Footpaths east of the S04 sidewalk (OSM 445696818 and the short plaza links/steps 4599205xx, superseded by the drawn fan plaza).
# 'line' = the route points of the original network (landscape.js replays them so the seeded plant sequence never shifts).
assert layout.get('removeFootpaths'), 'removeFootpaths with route lines must already be in layout.json (created 2026-11-26)'
layout_path.write_text(json.dumps(layout, ensure_ascii=False, indent=2) + '\n')
# Patch the generated data directly: scripts/build-campus-plazas.py would also regenerate yongxuAccess clip data.
c['levelAreas'] = layout['levelAreas']; c['removeFootpaths'] = layout['removeFootpaths']
gone = {r['osm'] for r in layout['removeFootpaths']}; c['roads'] = [r for r in c['roads'] if r['osm'] not in gone]
(root / 'data/campus.json').write_text(json.dumps(c, ensure_ascii=False, separators=(',', ':')) + '\n')
import re
sp = root / 'data/site-layout.js'; m = re.match(r'(// .*?\nexport const campusSiteLayout=)(.*);\n$', sp.read_text(), re.S)
sl = json.loads(m.group(2)); sl['levelAreas'] = layout['levelAreas']; sl['removeFootpaths'] = layout['removeFootpaths']
sp.write_text(m.group(1) + json.dumps(sl, ensure_ascii=False, separators=(',', ':')) + ';\n')
print('terrace area %.0f m2, vertices %d, raw(anchor) %.2f, level %.2f' % (area.area, len(entry['ring']), raw, base - .185))
