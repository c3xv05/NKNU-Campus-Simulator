import fitz,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];plan=json.loads((root/'buildings/foresight/plan.json').read_text());src=fitz.open(root/'buildings/foresight/source/dormitory-plans.pdf');doc=fitz.open()
for floor in [1,2]:
 p=doc.new_page(width=1191,height=842);p.insert_text((24,35),'霽遠樓衛浴／走廊修正核對：'+('一樓'if floor==1 else'二至五樓標準層'),fontname='china-ts',fontsize=20)
 p.insert_text((24,65),'左：使用者原始平面圖　右：本次實作來源，紅線為房內浴室入口；藍線為各寢室的走廊入口。',fontname='china-ts',fontsize=11)
 p.show_pdf_page(fitz.Rect(15,95,595,680),src,floor-1,keep_proportion=True)
 scale=.33;xy=lambda v:fitz.Point(610+(v[0]-50)*scale,175+(v[1]-320)*scale)
 def polygon(vertices,fill):
  shape=p.new_shape();points=[xy(v)for v in vertices];shape.draw_polyline(points+[points[0]]);shape.finish(color=(.25,.25,.25),fill=fill,width=.5);shape.commit()
 for poly in plan['corridors']:polygon(poly,(.77,.9,.97))
 for r in plan['rooms']:
  polygon(r['polygon'],(.98,.94,.83));poly=__import__('shapely').geometry.Polygon(r['polygon']);c=poly.representative_point();num=str(plan['groundRoomNumbers'][str(r['number'])])if floor==1 else str(r['number']);num='管理員室'if num=='None'else num;p.insert_text(xy([c.x-13,c.y]),num,fontname='china-ts',fontsize=6.8)
  x,y=r['door'];edges=list(poly.exterior.coords);edge=min(zip(edges,edges[1:]),key=lambda e:__import__('shapely').geometry.LineString(e).distance(__import__('shapely').geometry.Point(x,y)));a,b=edge;dx=b[0]-a[0];dy=b[1]-a[1];l=(dx*dx+dy*dy)**.5;p.draw_line(xy([x-dx/l*15,y-dy/l*15]),xy([x+dx/l*15,y+dy/l*15]),color=(.1,.35,.9),width=2.3)
 for b in plan['bathrooms']:
  polygon(b['polygon'],(.72,.9,.7));poly=__import__('shapely').geometry.Polygon(b['polygon']);c=poly.representative_point();p.insert_text(xy([c.x-10,c.y]),'獨'if len(b['rooms'])==1 else'共',fontname='china-ts',fontsize=6)
  for d in b['doors']:
   x,y=d['at'];edges=list(poly.exterior.coords);a,z=min(zip(edges,edges[1:]),key=lambda e:__import__('shapely').geometry.LineString(e).distance(__import__('shapely').geometry.Point(x,y)));dx=z[0]-a[0];dy=z[1]-a[1];l=(dx*dx+dy*dy)**.5;p.draw_line(xy([x-dx/l*12,y-dy/l*12]),xy([x+dx/l*12,y+dy/l*12]),color=(.85,.1,.1),width=2.3)
 for stair in plan['stairs']:
  x1,y1,x2,y2=stair['box'];polygon([[x1,y1],[x2,y1],[x2,y2],[x1,y2]],(.86,.86,.86))
 for public in plan['publicSpaces']:polygon(public['polygon'],(.98,.91,.65))
 notes=['本次每層：8間獨立衛浴＋8間兩房共用衛浴。','獨立（標準層）：201、206、207、212、213、214、219、224。','共用（標準層）：202/203、204/205、208/209、210/211、','215/216、217/218、220/221、222/223。','所有浴室入口只開在寢室內，沒有走廊浴室門。','主通道淨寬約2.04～3.97m；房間與浴室不得侵入藍色走廊。','整棟XYZ等比例1.1倍，層高約3.3m，總高16.5m。','示意牆厚／門寬／設備尺寸仍為模型近似；此頁不作施工圖。']
 for i,text in enumerate(notes):p.insert_text((620,520+i*23),text,fontname='china-ts',fontsize=10)
 p.insert_text((24,790),'來源：燕巢宿舍.pdf 第1、2頁；圖形與門位直接取自本次 plan.json，與實作共用。',fontname='china-ts',fontsize=11)
out=root/'buildings/foresight/source/private-bathroom-review.pdf';doc.save(out,garbage=4,deflate=True);print(out)
