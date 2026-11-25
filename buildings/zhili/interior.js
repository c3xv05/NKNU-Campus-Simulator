import {ringDistance} from '../../planar.js';
import {sidewalkPlan} from '../../data/sidewalk-plan.js';
import {ROAD_SURFACE_LIFT} from '../../sidewalk-layout.js';
// Zhili B1–2F interior and plan-driven facade compiled from the reviewed floor plans (scripts/build-zhili-interior.py).
// Geometry is authored in the drawing frame (axis-aligned rectangles) and placed with one rigid transform.
export const ZHILI_OSM=444867693;
export const ZHILI_CLEARANCE=.08;
// Plan-driven interiors share this runtime: Zhili and Gauss (scripts/build-gauss-interior.py), keyed by OSM id.
export const GAUSS_OSM=444867692,PLAN_OSMS=[ZHILI_OSM,GAUSS_OSM];
const prepared=new WeakMap();
function frame(t){return{toDrawing:(x,z)=>[t.a*(x-t.tx)+t.b*(z-t.tz),-t.b*(x-t.tx)+t.a*(z-t.tz)],toWorld:(x,y)=>[t.a*x-t.b*y+t.tx,t.b*x+t.a*y+t.tz],angle:Math.atan2(-t.b,t.a)};}
const inRect=(p,r,m=0)=>p[0]>=r[0]-m&&p[0]<=r[2]+m&&p[1]>=r[1]-m&&p[1]<=r[3]+m;
const rectDistance=(p,r)=>Math.hypot(Math.max(r[0]-p[0],0,p[0]-r[2]),Math.max(r[1]-p[1],0,p[1]-r[3]));
const insideRegions=(p,regions)=>regions.some(([outer,...holes])=>ringDistance(p[0],p[1],outer)===0&&!holes.some(h=>ringDistance(p[0],p[1],h)===0));
// Index wall rectangles on a 4m grid so walking checks stay cheap.
function grid(rects){const cells=new Map();for(const r of rects)for(let i=Math.floor(r[0]/4);i<=Math.floor(r[2]/4);i++)for(let j=Math.floor(r[1]/4);j<=Math.floor(r[3]/4);j++){const k=i+','+j;if(!cells.has(k))cells.set(k,[]);cells.get(k).push(r);}return(p,m)=>{const out=new Set();for(let i=Math.floor((p[0]-m)/4);i<=Math.floor((p[0]+m)/4);i++)for(let j=Math.floor((p[1]-m)/4);j<=Math.floor((p[1]+m)/4);j++)for(const r of cells.get(i+','+j)||[])out.add(r);return out;};}
export function createZhiliSurface(campus,terrain){return createPlanSurface(campus,terrain,ZHILI_OSM);}
export function planSurfaces(campus,terrain){return PLAN_OSMS.map(o=>createPlanSurface(campus,terrain,o)).filter(Boolean);}
export function createPlanSurface(campus,terrain,osm){
 if(!prepared.has(campus))prepared.set(campus,new Map());const cache=prepared.get(campus);if(cache.has(osm))return cache.get(osm);
 const data=campus.planInteriors?.[osm]??(osm===ZHILI_OSM?campus.zhiliInterior:null),building=[...campus.places,...campus.buildings].find(b=>b.osm===osm);
 if(!data||!building)return null;
 const f=frame(data.transform),base=terrain.platformHeight(building),H=data.floorHeight;
 // Walls, window glass/sills and glazed entrances all block; open entrances and doors do not.
 const floors=[...data.floors,...(data.upperFloors||[])].map(fl=>{const blocking=[...fl.walls,...(fl.furnitureBlocks||[]),...(fl.sills||[]).map(s=>s.rect),...(fl.blockOnly||[]),...(fl.doorLeaves||[]),...fl.exits.filter(e=>!e.open).flatMap(e=>e.rect)];return{...fl,y:base+fl.level,near:grid(blocking),blocking};});
 const stepRects=floors.flatMap(fl=>fl.exits.flatMap(e=>(e.steps||[]).map(t=>t.rect)));
 function supportAt(x,z,y){
  const p=f.toDrawing(x,z);if(ringDistance(p[0],p[1],data.outline)!==0&&!stepRects.some(r=>inRect(p,r)))return null;
  // Stairs first: the slab below a flight must never pull a walker down.
  let best=null,error=Infinity;
  for(const fl of floors){if(y<fl.y-.5||y>fl.y+H+.6)continue;for(const s of fl.stairs){if(!inRect(p,s.rect))continue;for(const t of s.treads)if(inRect(p,t.rect)){const h=fl.y+t.height+ZHILI_CLEARANCE,e=Math.abs(y-h);if(e<.44&&e<error){best=h;error=e;}}}}
  for(const fl of floors)for(const e of fl.exits)for(const t of e.steps||[])if(inRect(p,t.rect)){const h=fl.y+t.height+ZHILI_CLEARANCE,er=Math.abs(y-h);if(er<.44&&er<error){best=h;error=er;}}
  if(best!==null)return best;
  // Driveway ramp (B1): the floor slopes from the garage mouth down to the sidewalk-tile pad at the road.
  for(const fl of floors){const r=fl.ramp;if(!r||y<fl.y-.75-Math.max(0,r.drop)||y>fl.y+.9+Math.max(0,-r.drop)||!inRect(p,r.rect))continue;const t=Math.min(1,Math.max(0,(p[1]-r.rect[1])/(r.rect[3]-r.rect[1])));return fl.y+ZHILI_CLEARANCE-r.drop*t;}
  for(const fl of floors)if(Math.abs(y-fl.y-ZHILI_CLEARANCE)<.85&&insideRegions(p,fl.slab))return fl.y+ZHILI_CLEARANCE;
  return null;
 }
 function blocked(x,z,r,y,riding=false){
  const p=f.toDrawing(x,z);if(ringDistance(p[0],p[1],data.outline)>=r+.05)return false;
  for(const fl of floors){if(y<fl.y-.5||y>fl.y+H-.7)continue;const d=ringDistance(p[0],p[1],fl.outline);if(d>=r+.05)continue;
   // Riding stays out of the building, except on the B1 driveway ramp down to the street (user 2026-11-25: an invisible threshold stopped scooters at the mouth).
   if(riding&&fl.level>0&&!(fl.ramp&&inRect(p,[fl.ramp.rect[0],fl.ramp.rect[1],fl.ramp.rect[2],fl.ramp.rect[3]+1.2])))return true;   // user 2026-11-25: scooters ride on the ground floor and the basement; upper floors stay on foot
   for(const w of fl.near(p,r+.1))if(rectDistance(p,w)<r+.02)return true;
   if(d===0&&!(fl.openAreas||[]).some(a=>inRect(p,a))&&supportAt(x,z,y)===null)return true;
  }
  return false;
 }
 // B1 garage concrete (driveway and lanes) counts as road for scooter speed; any other supported indoor floor is tile.
 function triContains(t,x,z){const d=(t[1][1]-t[2][1])*(t[0][0]-t[2][0])+(t[2][0]-t[1][0])*(t[0][1]-t[2][1]);if(!d)return false;const a=((t[1][1]-t[2][1])*(x-t[2][0])+(t[2][0]-t[1][0])*(z-t[2][1]))/d,b=((t[2][1]-t[0][1])*(x-t[2][0])+(t[0][0]-t[2][0])*(z-t[2][1]))/d;return a>=0&&b>=0&&a+b<=1;}
 function groundKind(x,z,y){const h=supportAt(x,z,y);if(h===null)return null;const p=f.toDrawing(x,z);for(const fl of floors){if(Math.abs(h-fl.y)>1.3)continue;if(fl.ramp&&inRect(p,fl.ramp.rect))return'road';for(const t of fl.garageTriangles||[])if(triContains(t,x,z))return'road';}return'tile';}
 const result={base,floors,supportAt,blocked,groundKind,contains:(x,z)=>{const p=f.toDrawing(x,z);return ringDistance(p[0],p[1],data.outline)===0;}};result.osm=osm;cache.set(osm,result);return result;
}
export function zhiliSupportAt(x,z,y,campus,terrain){for(const s of planSurfaces(campus,terrain)){const h=s.supportAt(x,z,y);if(h!==null)return h;}return null;}
// Meshes: slabs, walls with real window openings, lintels, stair halls and treads, entrances, plan facade for 3F+.
export function addZhiliInterior(THREE,parent,campus,terrain,data,network){
 const osm=data.building??ZHILI_OSM,key=data.key||'zhili';(campus.planInteriors??={})[osm]=data;if(osm===ZHILI_OSM)campus.zhiliInterior=data;const building=campus.places.find(b=>b.osm===osm),base=terrain.platformHeight(building),H=data.floorHeight,SLAB=data.slab||.2,f=frame(data.transform);
 // Driveway ramp (B1): the drop from the floor to the sidewalk-tile pad at the road is measured from the live road height (S05 grade changes move it).
 const padPolys=(sidewalkPlan.curbCuts||[]).map(p=>p.ring),padTop=(x,z)=>(network?network.surfaceHeight(x,z):terrain.height(x,z))+ROAD_SURFACE_LIFT+.004,padAt=(x,z)=>padPolys.some(r=>ringDistance(x,z,r)===0);
 for(const fl of data.floors)if(fl.ramp){const r=fl.ramp.rect,[wx,wz]=f.toWorld((r[0]+r[2])/2,r[3]+.3);fl.ramp.drop=base+fl.level+.004-padTop(wx,wz);}
 // Entrances: open where the ground outside meets the floor; a landing and indoor steps when it is up to 1.6m higher; otherwise glazed.
 for(const fl of data.floors)for(const e of fl.exits){const cy=campus.courtyard?.floorRegions,zb=terrain.platformHeight(campus.places.find(b=>b.osm===campus.levelLink?.from)),gb=terrain.platformHeight(campus.places.find(b=>b.osm===campus.levelLink?.to)),decks=cy?[['lower',zb],['upper',zb+(campus.courtyard.floorHeight||3.6)],['gaussCourt',gb]].filter(([k])=>cy[k]&&insideRegions(e.outside,cy[k])).map(([,h])=>h):[],deck=decks.length?decks.reduce((a,h)=>Math.abs(h-(base+fl.level))<Math.abs(a-(base+fl.level))?h:a):null,padG=(()=>{const[ox,oz]=e.outside,[ix,iz]=e.inside,l=Math.hypot(ox-ix,oz-iz)||1;for(let s=.8;s<=4.5;s+=.4){const px=ox+(ox-ix)/l*s,pz=oz+(oz-iz)/l*s;if(padAt(px,pz))return padTop(px,pz);}return null;})(),g=deck??padG??(network?network.walkHeight(...e.outside,terrain.height(...e.outside)):terrain.height(...e.outside)),rise=g-(base+fl.level);e.rise=rise;e.open=Math.abs(rise)<.45||e.header===false;
  if(e.manual&&e.header!==false&&rise>=.45&&rise<=1.6){const a=f.toDrawing(...e.line[0]),b=f.toDrawing(...e.line[1]),o=f.toDrawing(...e.outside),i=f.toDrawing(...e.inside),mid=[(a[0]+b[0])/2,(a[1]+b[1])/2],len=Math.hypot(i[0]-o[0],i[1]-o[1]),u=[(i[0]-o[0])/len,(i[1]-o[1])/len],half=Math.hypot(b[0]-a[0],b[1]-a[1])/2,n=Math.ceil(rise/.18),h=rise/n,rect=(d0,d1)=>{const p0=[mid[0]+u[0]*d0,mid[1]+u[1]*d0],p1=[mid[0]+u[0]*d1,mid[1]+u[1]*d1],across=[Math.abs(u[1])*half,Math.abs(u[0])*half];return[Math.min(p0[0],p1[0])-across[0],Math.min(p0[1],p1[1])-across[1],Math.max(p0[0],p1[0])+across[0],Math.max(p0[1],p1[1])+across[1]];};
   e.steps=[{rect:rect(-.3,1.2),height:rise}];for(let k=0;k<n-1;k++)e.steps.push({rect:rect(1.2+k*.3,1.2+(k+1)*.3),height:rise-(k+1)*h});e.open=true;}
  // Ground lower than the floor (east main entrance on S05, drawing 階梯): outdoor steps down from the threshold.
  if(e.manual&&rise<=-.45&&rise>=-2.6){const a=f.toDrawing(...e.line[0]),b=f.toDrawing(...e.line[1]),o=f.toDrawing(...e.outside),i=f.toDrawing(...e.inside),mid=[(a[0]+b[0])/2,(a[1]+b[1])/2],len=Math.hypot(i[0]-o[0],i[1]-o[1]),u=[(i[0]-o[0])/len,(i[1]-o[1])/len],half=Math.hypot(b[0]-a[0],b[1]-a[1])/2+.3,n=Math.ceil(-rise/.17),h=-rise/n,rect=(d0,d1)=>{const p0=[mid[0]+u[0]*d0,mid[1]+u[1]*d0],p1=[mid[0]+u[0]*d1,mid[1]+u[1]*d1],across=[Math.abs(u[1])*half,Math.abs(u[0])*half];return[Math.min(p0[0],p1[0])-across[0],Math.min(p0[1],p1[1])-across[1],Math.max(p0[0],p1[0])+across[0],Math.max(p0[1],p1[1])+across[1]];};
   e.steps=[];for(let k=0;k<n-1;k++)e.steps.push({rect:rect(-(k+1)*.3,-k*.3),height:-(k+1)*h,bottom:rise-.4});e.open=true;}}
 const group=new THREE.Group();group.name=key+'-interior';parent.add(group);const blockers=[],props=new THREE.Group();props.name=key+'-interior-details';group.add(props);
 const mats={};for(const[k,c]of Object.entries({outer:0xa7644e,trim:0xbdbcb1,inner:0xece6d6,floor:0xd3cfc4,ceiling:0xe9e7df,frame:0x8f938c,tread:0xc9c5b8,glass:0x6f98a3,steel:0x7f898b,wood:0xa87c50,metal:0x8f979c,fabric:0x4f6f98,board:0x2e4a3c,white:0xeeeeea,dark:0x3b3d40,screen:0xe6e8ea,green:0x2f6d4a}))mats[k]=new THREE.MeshStandardMaterial({color:c,roughness:.88,side:THREE.DoubleSide,...(k==='glass'?{transparent:true,opacity:.5,roughness:.3}:{}),...(['inner','floor','ceiling','tread','wood','metal','fabric','board','white','dark','screen','green'].includes(k)?{emissive:c,emissiveIntensity:.32}:{})});
 // Interior finish (Zhili, user 2026-11-19): square floor tiles, off-white walls, black skirting, T-bar ceiling with recessed lights.
 const fin=data.finish,surf={};
 if(fin){mats.inner.color.set(fin.wall);mats.inner.emissive.set(fin.wall);mats.inner.emissiveIntensity=.5;mats.skirting=new THREE.MeshStandardMaterial({color:fin.skirting,roughness:.6});
  const canvasTex=(size,draw)=>{const c=document.createElement('canvas');c.width=c.height=size;draw(c.getContext('2d'),size);const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=4;return t;};
  // 2×2 floor tiles per texture repeat, slight shade variation, grey grout.
  const tiles=canvasTex(256,(g,n)=>{const h=n/2,shades=['#d8d4cb','#d3cfc6','#d6d2c9','#d1cdc3'];for(let i=0;i<2;i++)for(let j=0;j<2;j++){g.fillStyle=shades[i*2+j];g.fillRect(i*h,j*h,h,h);}
   for(let k=0;k<1400;k++){g.fillStyle=`rgba(120,110,95,${Math.random()*.08})`;g.fillRect(Math.random()*n,Math.random()*n,2,2);}g.fillStyle='#a9a398';for(const s of[0,h]){g.fillRect(s,0,3,n);g.fillRect(0,s,n,3);}});
  tiles.colorSpace=THREE.SRGBColorSpace;
  surf.floor=new THREE.MeshStandardMaterial({map:tiles,roughness:.45,emissive:0xffffff,emissiveMap:tiles,emissiveIntensity:.32});surf.floorRepeat=2*fin.tile;
  // 4×4 ceiling panels per repeat (2.4 m): mineral-fibre boards on a grey T-bar grid, one 60×120 recessed light.
  const P=4,draw=(lightOnly)=>(g,n)=>{const s=n/P;g.fillStyle=lightOnly?'#4a4a48':'#dcdbd3';g.fillRect(0,0,n,n);
   if(!lightOnly)for(let k=0;k<2600;k++){g.fillStyle=`rgba(110,110,100,${Math.random()*.12})`;g.fillRect(Math.random()*n,Math.random()*n,1.5,1.5);}
   g.fillStyle=lightOnly?'#ffffff':'#ffffff';g.fillRect(s+4,s+4,s-8,2*s-8);
   if(!lightOnly){g.strokeStyle='#e4e6ea';g.lineWidth=2;for(let k=1;k<6;k++){const x=s+4+k*(s-8)/6;g.beginPath();g.moveTo(x,s+6);g.lineTo(x,3*s-6);g.stroke();}}
   g.fillStyle=lightOnly?'#2c2c2a':'#a9aaa5';for(let k=0;k<=P;k++){g.fillRect(k*s-2,0,4,n);g.fillRect(0,k*s-2,n,4);}};
  const ceilMap=canvasTex(512,draw(false));ceilMap.colorSpace=THREE.SRGBColorSpace;
  // Garage: sealed concrete floor, white stall paint, bare tube lights (B1 parking, user 2026-11-19).
  const conc=canvasTex(256,(g,n)=>{g.fillStyle='#8f9390';g.fillRect(0,0,n,n);for(let k=0;k<4000;k++){const v=Math.random();g.fillStyle=`rgba(${v<.5?60:200},${v<.5?62:205},${v<.5?60:200},${Math.random()*.08})`;g.fillRect(Math.random()*n,Math.random()*n,2,2);}});
  conc.colorSpace=THREE.SRGBColorSpace;surf.garage=new THREE.MeshStandardMaterial({map:conc,roughness:.75,emissive:0xffffff,emissiveMap:conc,emissiveIntensity:.25});
  mats.paint=new THREE.MeshBasicMaterial({color:0xf2f2ec});mats.lamp=new THREE.MeshBasicMaterial({color:0xffffff});
  surf.ceiling=new THREE.MeshBasicMaterial({map:ceilMap,side:THREE.DoubleSide});/* unlit: the hemisphere light tints a lit ceiling green */surf.ceilingRepeat=4*fin.ceilingPanel;}
 // A flat surface over drawing-frame triangles with UVs aligned to the building grid (tiles and ceiling panels).
 function surface(triangles,y,mat,repeat,name){const pos=[],uv=[];for(const t of triangles)for(const[x,z]of t){pos.push(x,y,z);const d=f.toDrawing(x,z);uv.push(d[0]/repeat,d[1]/repeat);}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.computeVertexNormals();const m=new THREE.Mesh(g,mat);m.name=name;m.receiveShadow=true;group.add(m);return m;}
 const cube=new THREE.BoxGeometry(1,1,1),dummy=new THREE.Object3D(),batches=new Map();
 const isExterior=(r,ring)=>[[r[0]-.15,(r[1]+r[3])/2],[r[2]+.15,(r[1]+r[3])/2],[(r[0]+r[2])/2,r[1]-.15],[(r[0]+r[2])/2,r[3]+.15]].some(([x,y])=>ringDistance(x,y,ring)>0);
 function rectBox(r,y0,y1,key){if(y1-y0<=.001)return;const [x,z]=f.toWorld((r[0]+r[2])/2,(r[1]+r[3])/2);if(!batches.has(key))batches.set(key,[]);batches.get(key).push({w:r[2]-r[0],h:y1-y0,d:r[3]-r[1],x,y:(y0+y1)/2,z});}
 // Box along a slanted drawing segment a→b (e.g. the glazed bay beside 乙梯): length along, 'across' thick, shifted 'out' along n.
 function oBox(a,b,across,y0,y1,key,n=[0,0],out=0,extend=0){if(y1-y0<=.001)return;const wa=f.toWorld(a[0]+n[0]*out,a[1]+n[1]*out),wb=f.toWorld(b[0]+n[0]*out,b[1]+n[1]*out),len=Math.hypot(wb[0]-wa[0],wb[1]-wa[1]);if(!batches.has(key))batches.set(key,[]);batches.get(key).push({w:len+extend,h:y1-y0,d:across,x:(wa[0]+wb[0])/2,y:(y0+y1)/2,z:(wa[1]+wb[1])/2,ang:Math.atan2(-(wb[1]-wa[1]),wb[0]-wa[0])});}
 const slanted=(a,b)=>{const dx=Math.abs(b[0]-a[0]),dy=Math.abs(b[1]-a[1]);return Math.min(dx,dy)>.15*Math.max(dx,dy);};
 function slab(triangles,top,bottom,key,name){const pos=[];for(const t of triangles){for(const[x,z]of t)pos.push(x,top,z);for(const[x,z]of[...t].reverse())pos.push(x,bottom,z);}const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.computeVertexNormals();const m=new THREE.Mesh(g,mats[key]);m.name=name;m.receiveShadow=true;group.add(m);blockers.push(m);return m;}
 function plate(text,x,y,z,angle,width=1,bg='#23434b',fg='#fff1cc'){const c=document.createElement('canvas');c.width=384;c.height=144;const g=c.getContext('2d');g.fillStyle=bg;g.fillRect(0,0,384,144);g.fillStyle=fg;g.font='bold 80px serif';g.textAlign='center';g.fillText(text,192,100);const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;const m=new THREE.Mesh(new THREE.PlaneGeometry(width,width*.375),new THREE.MeshBasicMaterial({map:tex,side:THREE.DoubleSide}));m.position.set(x,y,z);m.rotation.y=angle;props.add(m);return m;}
 // A window pane on an outline edge (drawing a→b with outward normal), plus head/sill trim and a mullion.
 function pane(w,y,out=0){if(slanted(w.a,w.b)){oBox(w.a,w.b,.06,y+w.sill,y+w.head,'glass',w.normal,out);oBox(w.a,w.b,.16,y+w.sill-.08,y+w.sill,'trim',w.normal,out,.2);oBox(w.a,w.b,.16,y+w.head,y+w.head+.1,'trim',w.normal,out,.2);return;}const len=Math.hypot(w.b[0]-w.a[0],w.b[1]-w.a[1]),horiz=Math.abs(w.b[1]-w.a[1])<Math.abs(w.b[0]-w.a[0]),cx=(w.a[0]+w.b[0])/2+w.normal[0]*out,cy=(w.a[1]+w.b[1])/2+w.normal[1]*out,r=(along,across)=>horiz?[cx-along/2,cy-across/2,cx+along/2,cy+across/2]:[cx-across/2,cy-along/2,cx+across/2,cy+along/2];
  rectBox(r(len,.06),y+w.sill,y+w.head,'glass');rectBox(r(len+.2,.16),y+w.sill-.08,y+w.sill,'trim');rectBox(r(len+.2,.16),y+w.head,y+w.head+.1,'trim');rectBox(r(.07,.1),y+w.sill,y+w.head,'frame');}
 // Walls: interior partitions off-white; exterior walls brick outside with an off-white inner half; black skirting
 // along every indoor face when a finish is given.
 function wall(r,y,ring,y0=y,top=y+H-SLAB,skirt=true){const out=p=>ringDistance(p[0],p[1],ring)>0,cx=(r[0]+r[2])/2,cy=(r[1]+r[3])/2;
  // 2026-11-24 (user: red paint inside Zhili): only the two faces across a long thin wall decide where brick goes; its end caps touching the
  // outline used to paint half the partition brick-red. Faces that look indoors always get the off-white wall paint.
  const all={x0:out([r[0]-.15,cy]),x1:out([r[2]+.15,cy]),y0:out([cx,r[1]-.15]),y1:out([cx,r[3]+.15])},dx=r[2]-r[0],dz=r[3]-r[1],
   sides=dx>=dz*1.5?{y0:all.y0,y1:all.y1}:dz>=dx*1.5?{x0:all.x0,x1:all.x1}:all,n=Object.values(sides).filter(Boolean).length;
  if(!fin){rectBox(r,y0,top,n?'outer':'inner');return;}
  let inner=r;
  if(n===1){const k=Object.keys(sides).find(q=>sides[q]),mx=(r[0]+r[2])/2,my=(r[1]+r[3])/2;
   const o=k==='x0'?[r[0],r[1],mx,r[3]]:k==='x1'?[mx,r[1],r[2],r[3]]:k==='y0'?[r[0],r[1],r[2],my]:[r[0],my,r[2],r[3]];
   inner=k==='x0'?[mx,r[1],r[2],r[3]]:k==='x1'?[r[0],r[1],mx,r[3]]:k==='y0'?[r[0],my,r[2],r[3]]:[r[0],r[1],r[2],my];rectBox(o,y0,top,'outer');}
  else if(n>1){rectBox(r,y0,top,'outer');
   // a pier or corner post exposed outside on several sides: skin its indoor faces in wall paint
   const t=.02,e=.004;for(const k of Object.keys(all)){if(all[k])continue;rectBox(k==='x0'?[r[0]-e,r[1],r[0]+t,r[3]]:k==='x1'?[r[2]-t,r[1],r[2]+e,r[3]]:k==='y0'?[r[0],r[1]-e,r[2],r[1]+t]:[r[0],r[3]-t,r[2],r[3]+e],y0,top,'inner');}
   return;}
  rectBox(inner,y0,top,'inner');const e=.012;if(skirt)rectBox([inner[0]-e,inner[1]-e,inner[2]+e,inner[3]+e],y,y+fin.skirtingHeight,'skirting');}
 let shell=null;
 for(const fl of [...data.floors,...(data.upperFloors||[])]){const y=base+fl.level;
  const s=fl.slabTriangles.length?slab(fl.slabTriangles,y,y-SLAB,'floor',key+'-floor-'+fl.label+(fl.hall?'-hall':'')):null;shell??=s;
  if(fin&&fl.garageTriangles){surface(fl.garageTriangles,y+.004,surf.garage,4,key+'-garage-'+fl.label);for(const r of fl.stallLines||[])rectBox(r,y+.004,y+.014,'paint');if(fl.laneTriangles?.length)surface(fl.laneTriangles,y+.012,mats.paint,1,key+'-lanes-'+fl.label);
  if(fl.ramp){const r=fl.ramp.rect,drop=fl.ramp.drop,N=Math.max(2,Math.ceil((r[3]-r[1])/.4)),low=Math.min(...(data.foundationRing||fl.outline).map(([x,yy])=>{const [wx,wz]=f.toWorld(x,yy);return terrain.height(wx,wz);}))-.6;
   const top=yy=>y+.004-drop*(yy-r[1])/(r[3]-r[1]),V=(x,yy,h)=>{const [wx,wz]=f.toWorld(x,yy);return[wx,h,wz];};
   const posT=[],posL=[],posS=[],tileY=fl.ramp.tileFrom??r[1];let cur=posT;const T=(a,b,c)=>{for(const q of [a,b,c])cur.push(...q);};const S=(a,b,c)=>{for(const q of [a,b,c])posS.push(...q);};
   for(let i=0;i<N;i++){const y0=r[1]+(r[3]-r[1])*i/N,y1=r[1]+(r[3]-r[1])*(i+1)/N;cur=y0>=tileY-.01?posL:posT;const a=V(r[0],y0,top(y0)),b=V(r[2],y0,top(y0)),c=V(r[2],y1,top(y1)),d=V(r[0],y1,top(y1));T(a,c,b);T(a,d,c);
    for(const [x,x2] of [[r[0],r[0]],[r[2],r[2]]]){const p0=V(x,y0,top(y0)),p1=V(x,y1,top(y1)),q0=V(x,y0,low),q1=V(x,y1,low);S(p0,p1,q1);S(p0,q1,q0);}}
   {const e=V(r[0],r[3],top(r[3])),e2=V(r[2],r[3],top(r[3])),l1=V(r[0],r[3],low),l2=V(r[2],r[3],low);S(e,e2,l2);S(e,l2,l1);}
   for(const [pos,mat,nm,rep] of [[posT,surf.garage||surf.floor,'ramp',4],[posL,surf.floor||surf.garage,'ramp-tiles',surf.floorRepeat||.6]]){if(!pos.length)continue;const uv=[];for(let k=0;k<pos.length;k+=3){const d=f.toDrawing(pos[k],pos[k+2]);uv.push(d[0]/rep,d[1]/rep);}
    const gT=new THREE.BufferGeometry();gT.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));gT.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));gT.computeVertexNormals();const mT=new THREE.Mesh(gT,mat);mT.name=key+'-'+nm+'-'+fl.label;mT.receiveShadow=true;group.add(mT);blockers.push(mT);}
   const gS=new THREE.BufferGeometry();gS.setAttribute('position',new THREE.Float32BufferAttribute(posS,3));gS.computeVertexNormals();const mS=new THREE.Mesh(gS,mats.outer);mS.name=key+'-ramp-base-'+fl.label;group.add(mS);}for(const p of fl.garageLights||[])rectBox([p[0]-.6,p[1]-.06,p[0]+.6,p[1]+.06],y+H-SLAB-.1,y+H-SLAB-.04,'lamp');}
  if(fin){surface(fl.tileTriangles||fl.slabTriangles,y+.004,surf.floor,surf.floorRepeat,key+'-tiles-'+fl.label);if(fl.ceilingTriangles)surface(fl.ceilingTriangles,y+fin.ceilingHeight,surf.ceiling,surf.ceilingRepeat,key+'-ceiling-'+fl.label);}
  for(const w of fl.walls)wall(w,y,fl.outline);
  for(const d of fl.diagWalls||[])oBox(d.a,d.b,2*d.w,y,y+(d.top??H-SLAB),'inner');   // slanted walls and curbs: true rotated boxes
  for(const w of fl.sills||[])wall(w.rect,y,fl.outline,w.low?y:y-.45,y+w.top);   // low partitions and curbs stand on their own floor: never below it (user 2026-11-25)
  for(const w of fl.heads||[])wall(w.rect,y,fl.outline,y+w.bottom,y+H-SLAB,false);
  for(const w of fl.windows||[])pane(w,y,-.12);
  for(const l of fl.lintels)rectBox(l,y+2.25+(l[4]||0),y+H-SLAB,'inner');   // a fifth entry lifts the header with a raised floor (stage-height doors)
  for(const l of fl.doorLeaves||[])rectBox(l,y,y+2.25,'wood');
  for(const e of fl.exits){for(const r of e.rect){if(e.header!==false)wall(r,y,fl.outline,y+2.4,y+H-SLAB,false);if(!e.open){rectBox(r,y,y+.15,'outer');rectBox([r[0]+.08,r[1]+.08,r[2]-.08,r[3]-.08],y+.15,y+2.4,'glass');}}}
  // Room furniture (scripts/furnish.py): instanced boxes with the room's materials.
  for(const it of fl.furniture||[])rectBox(it.r,y+it.y[0],y+it.y[1],it.m);
  for(const e of fl.exits)for(const t of e.steps||[])rectBox(t.rect,y+(t.bottom??0),y+t.height,'tread');
  for(const st of fl.stairs){if(st.tiers){for(const t of st.treads)rectBox(t.rect,y,y+t.height,st.mat||'tread');continue;}
   for(const t of st.treads){const top=y+t.height;rectBox(t.rect,top-(t.flight<0?.2:.18),top,'tread');}
   rectBox(st.divider,y,y+1.1,'inner');rectBox(st.divider,y+1.1,y+H-SLAB-.05,'steel');
   const r=st.rect,[px,pz]=f.toWorld((r[0]+r[2])/2,(r[1]+r[3])/2);plate(st.id+' '+fl.label+'↑',px,y+2.6,pz,f.angle,1);}
  // Door frames (user 2026-11-24): two jambs and a head round every door opening, as thick as the wall (+2 cm each face); the passage keeps its width.
  for(const d of fl.doors){if(!d.frame)continue;const A=f.toDrawing(...d.line[0]),B=f.toDrawing(...d.line[1]),L=Math.hypot(B[0]-A[0],B[1]-A[1]);if(L<.3)continue;
   const u=[(B[0]-A[0])/L,(B[1]-A[1])/L],n=[-u[1],u[0]],t=Math.max(.12,d.frame[0])+.04,o=d.frame[1],A0=[A[0]-u[0]*.08,A[1]-u[1]*.08],B1=[B[0]+u[0]*.08,B[1]+u[1]*.08];
   const R=d.raise||0;oBox(A0,A,t,y+R,y+R+2.25,'frame',n,o);oBox(B,B1,t,y+R,y+R+2.25,'frame',n,o);oBox(A0,B1,t,y+R+2.17,y+R+2.25,'frame',n,o);}
  for(const d of fl.doors){const[a,b]=d.line,mx=(a[0]+b[0])/2,mz=(a[1]+b[1])/2,ang=Math.atan2(-(b[1]-a[1]),b[0]-a[0]);if(['classroom','office','library','hall','service','mech','unknown'].includes(d.kind)&&/^[\dB]/.test(d.name))plate(d.name,mx,y+2.55,mz,ang,.8);}
 }
 // Foundation: where the ground under the lowest walkable floor is lower than its slab, fill down to the ground
 // (the floor's ground cut would otherwise open a see-through gap along the facade).
 {const fl0=data.floors[0],ring=data.foundationRing||fl0.outline,top=base+fl0.level-SLAB,low=Math.min(...ring.map(([x,y])=>{const [wx,wz]=f.toWorld(x,y);return terrain.height(wx,wz);}))-.6;
  if(low<top-.05){const sh=new THREE.Shape();ring.forEach(([x,y],i)=>{const [wx,wz]=f.toWorld(x,y);i?sh.lineTo(wx,-wz):sh.moveTo(wx,-wz);});sh.closePath();const g=new THREE.ExtrudeGeometry(sh,{depth:top-low,bevelEnabled:false});g.rotateX(-Math.PI/2);const m=new THREE.Mesh(g,mats.outer);m.position.y=low;m.name=key+'-foundation';m.receiveShadow=true;group.add(m);blockers.push(m);}}
 for(const r of data.exposedRoofs||[]){const ry=base+r.level;slab(r.triangles,ry-.01,ry-SLAB,'ceiling',key+'-exposed-roof-'+r.level);
  // The exposed roofs lie at plaza level, so their top face is tiled like the plaza floor instead of plain off-white (user 2026-11-23).
  const tm=campus.plazaTileMaterial;if(tm&&r.triangles.length){const pos=[],uv=[];for(const t of r.triangles){const q=t.map(([x,z])=>[x,ry+.002,z]);if((q[1][0]-q[0][0])*(q[2][2]-q[0][2])-(q[1][2]-q[0][2])*(q[2][0]-q[0][0])>0)[q[1],q[2]]=[q[2],q[1]];for(const v of q){pos.push(...v);uv.push(v[0]/2.4,v[2]/2.4);}}
   const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setAttribute('sidewalkEdgeDistance',new THREE.Float32BufferAttribute(Array(pos.length/3).fill(1),1));g.computeVertexNormals();const m=new THREE.Mesh(g,tm);m.name=key+'-exposed-roof-tiles-'+r.level;m.receiveShadow=true;group.add(m);}}
 const roofY=base+data.roofLevel;slab(data.roofTriangles,roofY-.01,roofY-SLAB,'ceiling',key+'-roof');
 // 3F and above: one solid brick volume with the plan's windows on every facade, floor bands and a parapet.
 if(data.solidAbove){const ring=data.towerOutline,solid=data.solidRing||ring,sh=new THREE.Shape();solid.forEach(([x,y],i)=>{const [wx,wz]=f.toWorld(x,y);i?sh.lineTo(wx,-wz):sh.moveTo(wx,-wz);});sh.closePath();const g=new THREE.ExtrudeGeometry(sh,{depth:data.solidAbove.to-data.solidAbove.from,bevelEnabled:false});g.rotateX(-Math.PI/2);const m=new THREE.Mesh(g,mats.outer);m.position.y=base+data.solidAbove.from;m.name=key+'-solid-upper-floors';m.castShadow=true;m.receiveShadow=true;group.add(m);blockers.push(m);
  if(data.hallRoofTriangles?.length){const rt=base+data.solidAbove.to;slab(data.hallRoofTriangles,rt,rt-SLAB,'outer',key+'-hall-roof');}   // the hollowed 乙梯 hall keeps its roof
  for(const [label,wins] of Object.entries(data.facade||{})){const level=(+label.replace('F','')-1)*H,y=base+level;for(const w of wins)pane(w,y,.04);}
  for(let i=0;i<ring.length;i++){const a=ring[i],b=ring[(i+1)%ring.length];if(slanted(a,b)){for(let lv=data.solidAbove.from;lv<data.solidAbove.to-.1;lv+=H)oBox(a,b,.24,base+lv-.12,base+lv+.06,'trim',[0,0],0,.2);oBox(a,b,.24,base+data.solidAbove.to,base+data.solidAbove.to+.9,'outer',[0,0],0,.2);oBox(a,b,.24,base+data.solidAbove.to+.9,base+data.solidAbove.to+1,'trim',[0,0],0,.2);continue;}const horiz=Math.abs(b[1]-a[1])<Math.abs(b[0]-a[0]),len=Math.hypot(b[0]-a[0],b[1]-a[1]),cx=(a[0]+b[0])/2,cy=(a[1]+b[1])/2,r=horiz?[cx-len/2-.1,cy-.12,cx+len/2+.1,cy+.12]:[cx-.12,cy-len/2-.1,cx+.12,cy+len/2+.1];
   for(let lv=data.solidAbove.from;lv<data.solidAbove.to-.1;lv+=H)rectBox(r,base+lv-.12,base+lv+.06,'trim');rectBox(r,base+data.solidAbove.to,base+data.solidAbove.to+.9,'outer');rectBox(r,base+data.solidAbove.to+.9,base+data.solidAbove.to+1,'trim');}}
 // Building name over the main (east) entrance, as on the S05 facade.
 const main=data.floors.find(fl=>fl.label==='1F')?.exits.find(e=>Math.abs(f.toDrawing(...e.outside)[1]-f.toDrawing(...e.inside)[1])>.5&&f.toDrawing(...e.outside)[1]>f.toDrawing(...e.inside)[1]);
 const signText=data.signText??(osm===ZHILI_OSM?'致理大樓':null);
 if(main&&signText){const [a,b]=main.line,mx=(a[0]+b[0])/2,mz=(a[1]+b[1])/2,dx=main.outside[0]-mx,dz=main.outside[1]-mz,l=Math.hypot(dx,dz),ang=Math.atan2(-(b[1]-a[1]),b[0]-a[0]);plate(signText,mx+dx/l*.32,base+3.05,mz+dz/l*.32,ang,3.2,'#8e8d80','#f3e3b5');}
 for(const[key,items]of batches){const m=new THREE.InstancedMesh(cube,mats[key],items.length);m.name=data.key?data.key+'-'+key:'zhili-'+key;for(let i=0;i<items.length;i++){const b=items[i];dummy.position.set(b.x,b.y,b.z);dummy.rotation.set(0,b.ang??f.angle,0);dummy.scale.set(b.w,b.h,b.d);dummy.updateMatrix();m.setMatrixAt(i,dummy.matrix);}m.computeBoundingSphere();m.receiveShadow=true;m.castShadow=key==='outer';group.add(m);if(key!=='glass')blockers.push(m);}
 return{group,detail:props,shell,blockers,groundCuts:data.floors[0].slabTriangles};
}
