"""Convert game world coordinates (the developer's 「複製座標」 JSON: x, z) to Zhili drawing metres, or back.

  python scripts/zhili-coords.py '{"x":-129.1,"z":-266.8}'          # JSON from 複製座標 -> drawing x,y
  python scripts/zhili-coords.py 39.54 53.06                         # drawing x y -> world x,z   (add --world)
Drawing metres are the frame used by buildings/zhili/overrides.json (a / b / rect).
"""
import json, sys
from pathlib import Path
T = json.loads((Path(__file__).resolve().parents[1] / 'buildings/zhili/interior.json').read_text())['transform']
def to_drawing(x, z): X, Z = x - T['tx'], z - T['tz']; return (T['a'] * X + T['b'] * Z, -T['b'] * X + T['a'] * Z)
def to_world(x, y): return (T['a'] * x - T['b'] * y + T['tx'], T['b'] * x + T['a'] * y + T['tz'])
if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 1:
        p = json.loads(a[0]); print('drawing x %.2f  y %.2f' % to_drawing(p['x'], p['z']))
    elif len(a) == 2: print('world x %.2f  z %.2f' % to_world(float(a[0]), float(a[1])))
    else: print(__doc__)
