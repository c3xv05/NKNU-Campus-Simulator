"""Round free paving edges while preserving exact road/building/stair contacts."""
import json
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
from road_shapes import motor_shape

def finish_sidewalks(shape,campus):
 cfg=json.loads((Path(__file__).resolve().parents[1]/'facilities/sidewalks/finishing.json').read_text())
 motor=motor_shape(fillets=True)
 buildings=unary_union([Polygon(a['ring']).buffer(.015,join_style=2) for a in campus['places']+campus['buildings'] if a.get('height')])
 stairs=unary_union([Polygon(s['ring']) for s in [campus['bioConnection']['stairs']]+campus['levelLink'].get('stairs',[])])
 protected=unary_union([motor.boundary.buffer(cfg['protectedRoadEdge']),buildings.boundary.buffer(cfg['protectedBuildingEdge']),stairs.boundary.buffer(cfg['protectedStairEdge'])])
 notch,corner=cfg['notchRadius'],cfg['cornerRadius']
 smooth=shape.buffer(notch,quad_segs=4).buffer(-notch,quad_segs=4).buffer(-corner,quad_segs=4).buffer(corner,quad_segs=4)
 result=shape.intersection(protected).union(smooth.difference(protected))
 return result.difference(unary_union([motor,buildings,stairs])).simplify(cfg['outlineTolerance'],preserve_topology=True)
