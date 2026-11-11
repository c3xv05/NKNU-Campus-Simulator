"""Synchronize the shared flat quarters and pedestrian layout from one source file."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];layout=json.loads((root/'facilities/campus-plazas/layout.json').read_text());c=json.loads((root/'data/campus.json').read_text())
for key in ['levelAreas','pedestrianAreas','pedestrianLinks']:c[key]=layout[key]
(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
(root/'data/site-layout.js').write_text('// Shared flat campus quarters and pedestrian additions; source: facilities/campus-plazas/layout.json.\nexport const campusSiteLayout='+json.dumps(layout,ensure_ascii=False,separators=(',',':'))+';\n')
print('Built',len(layout['levelAreas']),'shared level areas and',len(layout['pedestrianLinks']),'pedestrian connections')
