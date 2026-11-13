import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];data={name:json.loads((root/path).read_text())for name,path in [('r09','facilities/r09-vegetation/layout.json'),('r02','facilities/r02-flowers/layout.json')]};(root/'data/observed-landscape.js').write_text('// Generated from user-observed R09 forest and R02 flower sources.\nexport const observedLandscape='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
