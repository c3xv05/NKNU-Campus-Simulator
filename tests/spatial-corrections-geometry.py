"""Independent plan checks: road clearance, exact doorstep contact and true L footprint."""
import json,sys
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'));from road_shapes import motor_shape
c=json.loads((root/'data/campus.json').read_text());roads=motor_shape(fillets=True);lookup={a['osm']:a for a in c['places']+c['buildings']};clearance=[]
for id in [-2401,397467190,397467191]:
 p=Polygon(lookup[id]['ring']);assert p.intersection(roads).area<1e-7
 for r in c['roads']:assert p.intersection(LineString(r['line']).buffer(r['width']/2)).area<1e-7,(id,r['osm'])
 clearance.append(round(p.distance(roads),2))
assert clearance[0]>8 and clearance[1]>10 and clearance[2]>10
centres=[Polygon(lookup[id]['ring']).centroid.x for id in [-2401,397467190,397467191]];assert centres==sorted(centres)
profile=json.loads((root/'buildings/osm-397467191/building.json').read_text());assert len(profile['appearance']['tanks'])==2
apron=Polygon(next(a for a in c['pavedAreas']if a['id']=='yongxu-entry-apron')['ring']);building=Polygon(lookup[381735423]['ring']);assert apron.intersection(building).area<1e-7;assert apron.boundary.intersection(building.boundary).length>20;assert apron.distance(Point(c['yongxuAccess']['door']))<1e-7
upper=unary_union([Polygon(r[0],r[1:])for r in c['courtyard']['floorRegions']['upper']]);lower=unary_union([Polygon(r[0],r[1:])for r in c['courtyard']['floorRegions']['lower']]);assert upper.geom_type=='Polygon' and upper.area<lower.area*.6
h=lookup[444867694];opening=Polygon(h['passage']['ring']);walls=unary_union([Polygon(r[0],r[1:])for r in h['passage']['shellRegions']]);assert opening.intersection(walls).area<1e-7;assert abs(opening.union(walls).area-Polygon(h['ring']).area)<1e-6
print('PASS: north-side west-to-east order, two water tanks, all-road non-overlap, 20m+ exact road/building contact, one connected L floor, shell cutout preserves footprint',{'clearanceMetres':clearance,'doorContactMetres':apron.boundary.intersection(building.boundary).length})
