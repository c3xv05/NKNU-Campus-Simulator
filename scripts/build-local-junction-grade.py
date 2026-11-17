"""Compile the confirmed local junction height correction, without rewriting DEM."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];data=json.loads((root/'facilities/southwest-junction/layout.json').read_text())
(root/'data/local-junction-grade.js').write_text('// Source: facilities/southwest-junction/layout.json; local model correction, not survey data.\nexport const localJunctionGrade='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
print('Built local junction grade',data['center'],data['drop'])
