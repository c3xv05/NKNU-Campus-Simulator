import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];c=json.loads((root/'data/campus.json').read_text());c['sideGate']=json.loads((root/'facilities/s24-sidegate/gate.json').read_text());c['sideGate']['tanks']=json.loads((root/'buildings/osm-397467191/building.json').read_text())['appearance']['tanks'];(root/'data/campus.json').write_text(json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n')
