"""Round only the sidewalk noses at S07; seal removed tips with asphalt."""
import json
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely import constrained_delaunay_triangles
from road_shapes import motor_shape
root=Path(__file__).resolve().parents[1];path=root/'facilities/jiyuan-access/layout.json';cfg=json.loads(path.read_text());cfg.setdefault('beforeNorthTransition',cfg['sidewalk']['ring']);cfg.setdefault('northTransition',{'radius':2,'southLimit':-7,'reference':'S20與S22的人行道碰到S07處以2m模型圓弧過渡，填回瀝青避免草縫；道路中心線及原坡度保留。'});settings=cfg['northTransition'];p=root/'data/campus.json';c=json.loads(p.read_text());c['junctionFillets']=[a for a in c['junctionFillets']if not a['id'].startswith('jiyuan-north-round-')];p.write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');original=Polygon(cfg['beforeNorthTransition']).difference(motor_shape(fillets=True));smooth=original.buffer(-settings['radius'],quad_segs=12).buffer(settings['radius'],quad_segs=12);cut=original.difference(smooth).intersection(box(-280,-30,-245,settings['southLimit']));parts=list(cut.geoms)if hasattr(cut,'geoms')else[cut];coords=lambda r:[[round(x,7),round(z,7)]for x,z in list(r.coords)[:-1]]
for i,a in enumerate(parts):
 if a.area<.001:continue
 c['junctionFillets'].append({'id':f'jiyuan-north-round-{i}','ring':coords(a.exterior),'triangles':[coords(t.exterior)for t in constrained_delaunay_triangles(a).geoms if t.area>1e-9]})
shape=Polygon(cfg['beforeNorthTransition']).difference(cut);cfg['sidewalk']['ring']=coords(shape.exterior);path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');layout_path=root/'facilities/campus-plazas/layout.json';layout=json.loads(layout_path.read_text());layout['pedestrianAreas']=[cfg['sidewalk']if a['id']==cfg['sidewalk']['id']else a for a in layout['pedestrianAreas']];layout_path.write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n');p.write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n');print('Rounded S20/S22 sidewalk tips at S07; asphalt infill',round(cut.area,3),'m²')
