// Bio A/B link from the user's floor plans (2026-11-23, scripts/biology_layout.py):
// 1F hall with full-height glazing (落地窗) and doors, 2F open deck rails, the closed
// sewage room (污水機房) under the T deck, the flower-pattern plaza and the terraced
// stepped flower beds beside the zigzag ramps. Walkable treads/ramps/landings are
// stair definitions in stair-layout.js; this module renders the rest and blocks it.
import {biologyTerraceScale} from '../../stair-layout.js';
import {ringDistance} from '../../planar.js';
import {createCampusCorridors} from '../campus-corridors/surface.js';

const segmentDistance=(x,z,[a,b])=>{const dx=b[0]-a[0],dz=b[1]-a[1],t=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz||1)));return Math.hypot(x-a[0]-dx*t,z-a[1]-dz*t);};

export function addBiologyLink(THREE,group,campus,terrain,network,tileMaterial){
 const bio=campus.bioConnection,corridor=bio.corridor,floor=terrain.platformHeight(campus.places.find(a=>a.osm===bio.from)),fh=corridor.floorHeight||3.6,deck=floor+fh,ceiling=deck-.25;
 const scale=biologyTerraceScale(campus,terrain,network),blockers=[],walls=[],rails=[],solids=[];
 const concrete=new THREE.MeshStandardMaterial({color:0xbdbab0,roughness:.95}),frame=new THREE.MeshStandardMaterial({color:0x4b5257,roughness:.6,metalness:.3}),
  glass=new THREE.MeshStandardMaterial({color:0x9cc3cc,roughness:.1,metalness:.1,transparent:true,opacity:.32,side:THREE.DoubleSide,depthWrite:false}),
  doorLeaf=new THREE.MeshStandardMaterial({color:0x5a5f5c,roughness:.7}),soil=new THREE.MeshStandardMaterial({color:0x5f7e45,roughness:1}),
  planterWall=new THREE.MeshStandardMaterial({color:0xc9c4b6,roughness:.95}),bark=new THREE.MeshStandardMaterial({color:0x6b4f37,roughness:1}),leaves=new THREE.MeshStandardMaterial({color:0x4f7d3a,roughness:1});
 function bar(a,b,y0,y1,thick,mat,name,offset=0){const dx=b[0]-a[0],dz=b[1]-a[1],len=Math.hypot(dx,dz);if(len<1e-3)return null;const nx=-dz/len,nz=dx/len,m=new THREE.Mesh(new THREE.BoxGeometry(len,y1-y0,thick),mat);m.position.set((a[0]+b[0])/2+nx*offset,(y0+y1)/2,(a[1]+b[1])/2+nz*offset);m.rotation.y=-Math.atan2(dz,dx);m.name=name;m.receiveShadow=true;group.add(m);return m;}
 function prism(ring,top,bottom,mat,name){const shape=new THREE.Shape();ring.forEach(([x,z],i)=>i?shape.lineTo(x,-z):shape.moveTo(x,-z));shape.closePath();const g=new THREE.ExtrudeGeometry(shape,{depth:Math.max(.02,top-bottom),bevelEnabled:false});g.rotateX(-Math.PI/2);const m=new THREE.Mesh(g,mat);m.position.y=bottom;m.name=name;m.receiveShadow=true;group.add(m);return m;}
 const lerp=(a,b,u)=>[a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u],center=[(corridor.line[0][0]+corridor.line[1][0])/2,(corridor.line[0][1]+corridor.line[1][1])/2];
 // Every wall segment is pulled 4 cm towards the hall centre so it never shares a plane with the building shells.
 const inward=([a,b])=>{const m=lerp(a,b,.5),dx=b[0]-a[0],dz=b[1]-a[1],l=Math.hypot(dx,dz),nx=-dz/l,nz=dx/l,s=Math.sign((center[0]-m[0])*nx+(center[1]-m[1])*nz)||1;return [[a[0]+nx*s*.04,a[1]+nz*s*.04],[b[0]+nx*s*.04,b[1]+nz*s*.04]];};
 // 1F hall: 落地窗 from floor to deck soffit with mullions, double doors (plaza side open, others closed), solid walls.
 for(const w of corridor.walls){const line=inward(w.line),[a,b]=line,len=Math.hypot(b[0]-a[0],b[1]-a[1]),dir=[(b[0]-a[0])/len,(b[1]-a[1])/len],post=(p,y0,y1,t,mat,name,w=.08)=>bar([p[0]-dir[0]*w/2,p[1]-dir[1]*w/2],[p[0]+dir[0]*w/2,p[1]+dir[1]*w/2],y0,y1,t,mat,name);
  if(w.kind==='wall'){blockers.push(bar(a,b,floor-.3,ceiling,.2,concrete,'biology-hall-wall'));walls.push(line);continue;}
  if(w.kind==='glass'){bar(a,b,floor,ceiling,.03,glass,'biology-hall-glazing');for(let i=0,n=Math.max(1,Math.round(len/1.2));i<=n;i++)post(lerp(a,b,i/n),floor,ceiling,.1,frame,'biology-hall-mullion');for(const y of [floor+.05,floor+2.4,ceiling-.05])bar(a,b,y-.05,y+.05,.09,frame,'biology-hall-rail');walls.push(line);continue;}
  // Doors: frame, transom glazing above 2.4 m; closed leaves block, open leaves swing out flat against the facade.
  for(const u of [0,.5,1])post(lerp(a,b,u),floor,u===.5?floor+2.4:ceiling,.12,frame,'biology-hall-door-jamb',u===.5?.05:.1);
  bar(a,b,floor+2.35,floor+2.45,.12,frame,'biology-hall-door-head');bar(a,b,floor+2.45,ceiling,.03,glass,'biology-hall-transom');
  if(w.kind==='door-closed'){bar(a,b,floor+.02,floor+2.35,.06,doorLeaf,'biology-closed-door');for(const u of [.46,.54])post(lerp(a,b,u),floor+1,floor+1.2,.14,frame,'biology-door-handle',.04);walls.push(line);}
  else{const dx=b[0]-a[0],dz=b[1]-a[1],nx=-dz/len,nz=dx/len,out=Math.sign((center[0]-a[0])*nx+(center[1]-a[1])*nz)>0?-1:1,half=len/2;for(const [hinge,dir] of [[a,1],[b,-1]]){const tip=[hinge[0]+nx*out*half,hinge[1]+nz*out*half];bar(hinge,tip,floor+.02,floor+2.35,.05,glass,'biology-open-door-leaf');bar(hinge,tip,floor+.02,floor+.12,.06,frame,'biology-open-door-rail');}}
 }
 // 2F deck rails (open-air deck = the S05 T platform datum).
 for(const line of corridor.deckRails||[]){const [a,b]=line,len=Math.hypot(b[0]-a[0],b[1]-a[1]);bar(a,b,deck+1.02,deck+1.1,.08,frame,'biology-deck-rail');const d=[(b[0]-a[0])/len,(b[1]-a[1])/len];for(let i=0,n=Math.max(1,Math.round(len/1.5));i<=n;i++){const p=lerp(a,b,i/n);bar([p[0]-d[0]*.03,p[1]-d[1]*.03],[p[0]+d[0]*.03,p[1]+d[1]*.03],deck,deck+1.05,.05,frame,'biology-deck-baluster');}rails.push(line);}
 // Closed sewage room and the solid fill under the T deck (its doors are drawn on the hall walls above).
 const room=bio.sewageRoom;if(room){solids.push(room.undercroft);blockers.push(prism(room.undercroft,ceiling,Math.min(floor-1,...room.undercroft.map(([x,z])=>terrain.height(x,z)-1)),concrete,'biology-sewage-room'));}
 // +505 side stairs (drawing): solid outer walls rising to a parapet above the stem floor, sloped rails on the stem's inner well edges.
 const stem=createCampusCorridors(campus,terrain,network).approaches.find(a=>a.id==='biology-s05'),sideWalls=[],sideRails=[];
 if(stem)for(const s of bio.sideStairs||[]){const [a,b]=s.outerWallLine,n=Math.max(1,Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1])));let top=-Infinity;
  for(let i=0;i<n;i++){const p=lerp(a,b,i/n),q=lerp(a,b,(i+1)/n),y=Math.max(stem.profile(...p),stem.profile(...q))+1.05;top=Math.max(top,y);blockers.push(bar(p,q,Math.min(floor-1,terrain.height(...p)-1,terrain.height(...q)-1),y,s.outerWallWidth,concrete,'biology-side-stair-wall'));}
  sideWalls.push({ring:s.outerWall,top});
  const [c,d]=s.innerRail,len=Math.hypot(d[0]-c[0],d[1]-c[1]),m=Math.max(1,Math.round(len/1.5));
  for(let i=0;i<m;i++){const p=lerp(c,d,i/m),q=lerp(c,d,(i+1)/m);bar(p,q,stem.profile(...p)+1.02,stem.profile(...p)+1.1,.08,frame,'biology-side-stair-rail');bar(lerp(p,q,-.02),lerp(p,q,.02),stem.profile(...p),stem.profile(...p)+1.05,.05,frame,'biology-side-stair-baluster');}
  sideRails.push(s.innerRail);}
 // Flower plaza: the drawn circle and eight-point lens rosette as an inlaid paving decal; low planters on both sides.
 const plaza=bio.eastLanding;if(plaza?.pattern){const pat=plaza.pattern,size=pat.size,canvas=document.createElement('canvas');canvas.width=canvas.height=1024;const g=canvas.getContext('2d'),s=1024/size,c=512;
  g.clearRect(0,0,1024,1024);g.lineWidth=7;g.strokeStyle='rgba(120,96,80,.85)';g.fillStyle='rgba(176,112,92,.30)';
  const lens=(angle,tip,half)=>{const r=(tip*tip+half*half)/(2*half),off=r-half,a=Math.atan2(off,tip);g.save();g.translate(c,c);g.rotate(angle);g.beginPath();g.arc(0,off*s,r*s,-Math.PI+a,-a);g.arc(0,-off*s,r*s,a,Math.PI-a);g.closePath();g.fill();g.stroke();g.restore();};
  for(let k=0;k<4;k++)lens(k*Math.PI/4,size*.5,size*.29);g.fillStyle='rgba(214,206,190,.95)';g.beginPath();g.arc(c,c,size*.29*s,0,Math.PI*2);g.fill();g.stroke();g.lineWidth=5;g.strokeRect(10,10,1004,1004);
  const tex=new THREE.CanvasTexture(canvas);tex.anisotropy=4;const m=new THREE.Mesh(new THREE.PlaneGeometry(size,size),new THREE.MeshStandardMaterial({map:tex,transparent:true,roughness:.9,polygonOffset:true,polygonOffsetFactor:-2,polygonOffsetUnits:-2}));
  m.rotation.x=-Math.PI/2;m.rotation.z=Math.atan2(-pat.axis[1],pat.axis[0]);m.position.set(pat.center[0],floor+.015,pat.center[1]);m.name='biology-flower-plaza-pattern';group.add(m);
  for(const ring of plaza.sidePlanters||[]){blockers.push(prism(ring,floor+.5,floor-1.2,planterWall,'biology-plaza-planter'));prism(ring.map(p=>lerp(p,ring.reduce((s,q)=>[s[0]+q[0]/4,s[1]+q[1]/4],[0,0]),.12)),floor+.52,floor+.3,soil,'biology-plaza-planter-soil');solids.push(ring);}}
 // Terraced planters between the ramps and wall planters along both side walls: flower beds as drawn (no trees), each flush with the tread of the side stair on the same line.
 const stairs=bio.stairs,planterTops=[];if(scale&&stairs?.planters){const base=Math.min(scale.foot-1.5,...stairs.ring.map(([x,z])=>terrain.height(x,z)-1.5));
  for(const p of [...stairs.planters,...stairs.wallPlanters]){const top=scale.height(p.h)+p.raise;blockers.push(prism(p.ring,top,base,planterWall,'biology-terrace-planter'));const c=p.ring.reduce((s,q)=>[s[0]+q[0]/p.ring.length,s[1]+q[1]/p.ring.length],[0,0]);prism(p.ring.map(q=>lerp(q,c,.08)),top+.02,top-.2,soil,'biology-terrace-planter-soil');planterTops.push({ring:p.ring,top});}
}
 return{blockers,blocked(x,z,r,currentY){
  if(currentY>floor-.6&&currentY<ceiling&&walls.some(l=>segmentDistance(x,z,l)<r+.1))return true;
  if(Math.abs(currentY-deck-.6)<.9&&rails.some(l=>segmentDistance(x,z,l)<r+.06))return true;
  if(currentY<ceiling&&solids.some(ring=>ringDistance(x,z,ring)<r))return true;
  if(sideWalls.some(w=>currentY<w.top&&ringDistance(x,z,w.ring)<r))return true;
  if(stem&&sideRails.some(l=>segmentDistance(x,z,l)<r+.08&&currentY<stem.profile(x,z)+1))return true;
  return planterTops.some(p=>currentY<p.top+1.1&&ringDistance(x,z,p.ring)<r*.5);   // beds are flush with the treads: never walk onto them
 }};
}
