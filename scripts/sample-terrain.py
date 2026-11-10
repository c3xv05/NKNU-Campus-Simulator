"""Resample public Mapzen Terrarium tiles to local campus metres (Pillow required)."""
import json, math, urllib.request, io
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
ORIGIN = (120.407, 22.7865)
ZOOM = 14
CACHE = Path('/tmp/nknu-elevation-tiles')
CACHE.mkdir(exist_ok=True)
tiles = {}
def pixel(x, y):
    tx, ty = x // 256, y // 256
    key = (tx, ty)
    if key not in tiles:
        f = CACHE / f'{ZOOM}-{tx}-{ty}.png'
        if not f.exists():
            url = f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{ZOOM}/{tx}/{ty}.png'
            with urllib.request.urlopen(url, timeout=30) as response: f.write_bytes(response.read())
        tiles[key] = Image.open(f).convert('RGB')
    r, g, b = tiles[key].getpixel((x % 256, y % 256))
    return r * 256 + g + b / 256 - 32768

def elevation(x, z):
    lon = ORIGIN[0] + x / (111195 * math.cos(math.radians(ORIGIN[1])))
    lat = ORIGIN[1] - z / 111195
    # XYZ pixels represent cell centres, hence the half-pixel offset.
    px = (lon + 180) / 360 * 2**ZOOM * 256 - .5
    py = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * 2**ZOOM * 256 - .5
    ix, iy = math.floor(px), math.floor(py)
    fx, fy = px - ix, py - iy
    return round((pixel(ix, iy)*(1-fx)+pixel(ix+1, iy)*fx)*(1-fy)+(pixel(ix, iy+1)*(1-fx)+pixel(ix+1, iy+1)*fx)*fy, 2)

grid = {'origin': list(ORIGIN), 'west': -460, 'north': -580, 'step': 20, 'columns': 48, 'rows': 59,
        'source': 'Mapzen Terrain Tiles / USGS SRTM', 'sampledOn': '2026-11-10', 'zoom': ZOOM}
grid['heights'] = [elevation(grid['west'] + c*20, grid['north'] + r*20) for r in range(grid['rows']) for c in range(grid['columns'])]
(ROOT / 'data/elevation.json').write_text(json.dumps(grid, separators=(',', ':'))+'\n')
print('Sampled', len(grid['heights']), 'points; range', min(grid['heights']), max(grid['heights']))
