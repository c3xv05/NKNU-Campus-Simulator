"""Place Bio A / Bio B from the user's floor-plan drawings around the preserved T-stem joint.

2026-11-23 user decision: the connection follows the drawings (A = 生物科技館 = north
building 444867696, B = 生物教學大樓 = south building 444867695). Both shells become
the traced 1F outlines; the S05 T deck keeps its height and is the 2F datum, so
the 1F floor drops by 4.5 - 3.6 = 0.9 m via platformOffset. Upper floors are 4.0 m.
The previous map-sketch rings stay as beforeDrawingFootprint (history only).
"""
import json
from pathlib import Path
import biology_drawing as D

root = Path(__file__).resolve().parents[1]
source = json.loads((root / 'facilities/biology-layout/layout.json').read_text())
t = source['axis']
north = [-t[0], -t[1]]
east = [t[1], -t[0]]
frame = D.Frame(source['joint'], north, east)
GROUND, UPPER, FLOORS = 4.5, 4.0, 5
levels = [0] + [round(GROUND + UPPER * i, 3) for i in range(FLOORS)]
names = {
    'bio-a': ('生科 A 館（生物科技館）', '生物科技系教學與研究空間。', '生科 A 館', D.A_RING, frame.a, (235.0, 629.5), (117.75, 629.5)),
    'bio-b': ('生科 B 館（生物教學大樓）', '生命科學系教學與研究空間。', '生科 B 館', D.B_RING, frame.b, (350.0, 636.5), (467.5, 636.5)),
}
for name, (title, desc, sign, ring, place, f0, f1) in names.items():
    path = root / f'buildings/{name}/building.json'
    d = json.loads(path.read_text())
    g, p = d['geometry'], d['appearance']
    g.setdefault('beforeDrawingFootprint', {'ring': g['ring'], 'frontHint': p['frontHint'], 'height': g['height'],
                                            'floorHeight': g['floorHeight'], 'name': g['name'], 'desc': g['desc']})
    g['ring'] = D.ccw([place(*q) for q in ring])
    g.update(name=title, desc=desc, floors=FLOORS, floorHeight=UPPER, floorLevels=levels, height=levels[-1],
             platformOffset=round(-(GROUND - 3.6), 3), alignmentReference='facilities/biology-layout/layout.json',
             drawingReference=f'buildings/{name}/source/floor-1.pdf')
    g.pop('terrainRing', None)
    front = [place(*f0), place(*f1)]
    p.update(name=title, sign=sign, frontHint=[round((front[0][i] + front[1][i]) / 2, 7) for i in range(2)], frontRoadIds=[218881800],
             reference='2026-11-23依使用者提供之生物科技館（A）／生物教學大樓（B）1F～3F平面圖描出外框（略去冷氣窗台及小凸出），'
                       '以通廊、廣場、坡道階梯與污水機房共同中心線對齊既有S05 T支線接點；1F 4.5m（圖面+520→+970）、2F以上4.0m（+970→+1370），'
                       '二樓沿用原T平台高度。立面外觀仍為模型近似。')
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
print('Placed Bio A/B drawing outlines around the preserved T-stem joint; 1F 4.5 m, upper 4.0 m')
