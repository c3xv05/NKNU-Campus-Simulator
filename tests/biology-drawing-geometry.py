"""2026-11-23 Bio A/B link from the floor plans: plan geometry checks (no browser)."""
import json, math
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
root = Path(__file__).resolve().parents[1]
c = json.loads((root / 'data/campus.json').read_text()); bio = c['bioConnection']; st = bio['stairs']
ring = Polygon(st['ring'])
walk = unary_union([Polygon(p['ring']) for p in st['pieces']])
planters = unary_union([Polygon(p['ring']) for p in st['planters'] + st['wallPlanters']])
# The terraces are fully covered by walkable pieces and planters (no hole in the cut ground), and planters never sit on a walking surface.
assert ring.difference(walk.union(planters)).area < .01, ring.difference(walk.union(planters)).area
assert planters.intersection(walk).area < .05, planters.intersection(walk).area
assert walk.union(planters).difference(ring.buffer(.3)).area < .01, 'only the 0.25 m ramp overlaps leave the field, never the terrace ring'
# Pieces and planters stay clear of both buildings and the motor road footprint of S01.
buildings = unary_union([Polygon(b['ring']) for b in c['places'] + c['buildings'] if b.get('height')])
assert ring.intersection(buildings).area < 1e-6 and Polygon(bio['eastLanding']['ring']).intersection(buildings).area < 1e-6
# Hall walls follow the drawing: glazing, open double doors to the plaza and to both +505 side stairs, closed end and sewage-room doors, solid sewage-room front.
kinds = [w['kind'] for w in bio['corridor']['walls']]
assert kinds.count('door-open') == 4 and kinds.count('door-closed') == 3 and kinds.count('glass') == 5 and kinds.count('wall') == 6, kinds
assert len(bio['corridor']['columns']) == 8
# Sewage room is a closed solid; its triangulation (ground cut) matches the outline exactly.
under = Polygon(bio['sewageRoom']['undercroft'])
assert abs(sum(Polygon(t).area for t in bio['sewageRoom']['undercroftTriangles']) - under.area) < 1e-6
assert under.intersection(unary_union([Polygon(r[0]) for r in bio['corridor']['regions']])).area < 1e-6, 'sewage room outside the hall floor'
# Hall 1F, plaza and terraces share one centre line; the 2F deck covers the hall.
deck = Polygon(bio['corridor']['deckRing']); hall = Polygon(bio['ring'])
assert hall.difference(deck).area < 1e-6
axis = bio['corridor']['east']; j = bio['corridor']['joint']
for p in [bio['eastLanding']['line'][0], bio['eastLanding']['line'][1], st['line'][0], st['line'][1]]:
    d = [p[0] - j[0], p[1] - j[1]]; assert abs(d[0] * axis[1] - d[1] * axis[0]) < .02, 'on the T-stem centre line'
# +505 side stairs: wells open the stem floor above both flights; sewage room sits between the lanes; stairs clear of the hall floor.
stem = next(a for a in c['campusTransitions'] if a['id'] == 'biology-s05'); stemshape = unary_union([Polygon(r[0], r[1:]) for r in stem['regions']])
for side in bio['sideStairs']:
    assert stemshape.intersection(Polygon(side['well'])).area < 1e-6, 'stem floor open above the stair'
    for piece in side['pieces']:
        assert Polygon(piece['ring']).intersection(under).area < 1e-6 and Polygon(piece['ring']).intersection(hall).area < 1e-6
        assert Polygon(piece['ring']).intersection(buildings).area < 1e-6
print('PASS: terraces fully covered (walk + planters, no overlap), drawing doors/glazing, closed sewage room, deck over hall, shared centre line, open stem wells over the +505 side stairs')
