"""Synchronize separately stored carports and their driveable floors."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
c=json.loads((root/'data/campus.json').read_text())
c['carports']=[json.loads(p.read_text()) for p in sorted((root/'facilities').glob('*/carport.json'))]
ids={p['id']+'-floor' for p in c['carports']}
c['pavedAreas']=[a for a in c.get('pavedAreas',[]) if a['id'] not in ids]+[dict(id=p['id']+'-floor',name=p['name']+'鋪面',ring=p['ring'],anchor=p['anchor'],reference=p['reference']) for p in c['carports']]
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
print('Built',len(c['carports']),'carports and shared driveable floors')
