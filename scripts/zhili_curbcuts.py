"""Zhili driveway / entrance curb-cut shapes (world coordinates) derived from facilities/zhili-curbcuts/layout.json."""
import json,math
from shapely.geometry import Polygon
def load(root):
    lay=json.loads((root/'facilities/zhili-curbcuts/layout.json').read_text())
    t=json.loads((root/'buildings/zhili/building.json').read_text())['geometry']['drawingFootprint']['transform']
    return lay,t
def world(t,pts):return [(t['a']*x-t['b']*y+t['tx'],t['b']*x+t['a']*y+t['tz']) for x,y in pts]
def flare_polygon(t,x0,x1,y0,y1,R,cap,step=.2):
    def f(d):
        d=min(d,R);return min(cap,R-math.sqrt(R*R-d*d))
    ys=[y0+k*step for k in range(int((y1-y0)/step)+1)]+[y1]
    left=[(x0-f(y-y0),y) for y in ys];right=[(x1+f(y-y0),y) for y in ys]
    return Polygon(world(t,left+right[::-1])).buffer(0)
def shapes(root):
    lay,t=load(root);end=lay['padEndY'];out={'pads':{},'ramps':{},'walls':{},'open':None}
    for k in('driveway','entrance'):
        d=lay[k];out['pads'][k]=flare_polygon(t,d['x'][0],d['x'][1],d['padStartY'],end,d['flareR'],d['flareMax'])
    d=lay['driveway'];(x0,x1),(r0,r1)=d['x'],d['rampY']
    out['ramps']['driveway']=Polygon(world(t,[[x0,r0],[x1,r0],[x1,r1],[x0,r1]]))
    a=lay['adaRamp'];(ax0,ax1),(ay0,ay1)=a['x'],a['y']
    out['ramps']['ada']=Polygon(world(t,[[ax0,ay0],[ax1,ay0],[ax1,ay1],[ax0,ay1]]))
    out['open']=Polygon(world(t,[[x0,d['openY'][0]],[x1,d['openY'][0]],[x1,d['openY'][1]],[x0,d['openY'][1]]]))
    out['walls']['driveway']=[Polygon(world(t,[[a,r0],[b,r0],[b,r1],[a,r1]])) for a,b in d['wallX']]
    return out,lay,t


def plaza_items(t):
    """Upper-plaza planters (花圃), benches (椅子) and the B1 skylight from the Zhili 2F drawing (drawing metres -> world rings)."""
    from shapely.geometry import LineString,box
    from shapely.ops import unary_union
    WALL,BED,BENCH=.12,.5,.45
    def frame(x0,x1,y_bar,y_end,top_bench):
        sign=1 if y_end>y_bar else -1
        def path(inset):
            return LineString([(x0+inset,y_end),(x0+inset,y_bar+sign*inset),(x1-inset,y_bar+sign*inset),(x1-inset,y_end)])
        w=WALL+BED+WALL  # outer line (L1) to inner line (L4): planter wall, bed, planter wall
        planter=path(w/2).buffer(w/2,cap_style='flat',join_style='mitre')
        bench=path(w+BENCH/2).buffer(BENCH/2,cap_style='flat',join_style='mitre')
        extra=box(x0,y_bar-BENCH,x1,y_bar) if top_bench else None
        return planter,[b for b in (bench,extra) if b is not None]
    planters=[];benches=[]
    for x0,x1,y_bar,y_end,tb in [(5.89,16.67,40.17,42.66,True),(5.89,16.67,46.85,44.66,False),(5.89,16.67,49.31,51.4,True),(5.89,16.67,55.63,53.41,False)]:
        p,b=frame(x0,x1,y_bar,y_end,tb);planters.append(p);benches+=b
    def ring(poly):
        return [[round(x,7),round(z,7)] for x,z in world(t,list(poly.exterior.coords)[:-1])]
    items=[{'kind':'planter','ring':ring(p)} for p in planters]+[{'kind':'bench','ring':ring(b)} for b in benches]
    sk=[34.06,41.3,43.4,45.16]
    sky={'outer':ring(box(sk[0],sk[1],sk[2],sk[3])),'cells':[ring(box(sk[0]+.25+i*(sk[2]-sk[0]-.5)/8,sk[1]+.2+j*(sk[3]-sk[1]-.4)/3,sk[0]+.25+(i+1)*(sk[2]-sk[0]-.5)/8,sk[1]+.2+(j+1)*(sk[3]-sk[1]-.4)/3)) for j in range(3) for i in range(8)]}
    pillars=[ring(box(16.5,65.8,17.3,66.6))]
    return items,sky,pillars
