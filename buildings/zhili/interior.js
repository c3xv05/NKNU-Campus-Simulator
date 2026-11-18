import {ringDistance} from '../../planar.js';
// Zhili B1–2F interior and plan-driven facade compiled from the reviewed floor plans (scripts/build-zhili-interior.py).
// Geometry is authored in the drawing frame (axis-aligned rectangles) and placed with one rigid transform.
export const ZHILI_OSM=444867693;
export const ZHILI_CLEARANCE=.08;
const prepared=new WeakMap();
function frame(t){return{toDrawing:(x,z)=>[t.a*(x-t.tx)+t.b*(z-t.tz),-t.b*(x-t.tx)+t.a*(z-t.tz)],toWorld:(x,y)=>[t.a*x-t.b*y+t.tx,t.b*x+t.a*y+t.tz],angle:Math.atan2(-t.b,t.a)};}
const inRect=(p,r,m=0)=>p[0]>=r[0]-m&&p[0]<=r[2]+m&&p[1]>=r[1]-m&&p[1]<=r[3]+m;
const rectDistance=(p,r)=>Math.hypot(Math.max(r[0]-p[0],0,p[0]-r[2]),Math.max(r[1]-p[1],0,p[1]-r[3]));
const insideRegions=(p,regions)=>regions.some(([outer,...holes])=>ringDistance(p[0],p[1],outer)===0&&!holes.some(h=>ringDistance(p[0],p[1],h)===0));
// Index wall rectangles on a 4m grid so walking checks stay cheap.
function grid(rects){const cells=new Map();for(const r of rects)for(let i=Math.floor(r[0]/4);i<=Math.floor(r[2]/4);i++)for(let j=Math.floor(r[1]/4);j<=Math.floor(r[3]/4);j++){const k=i+','+j;if(!cells.has(k))cells.set(k,[]);cells.get(k).push(r);}return(p,m)=>{const out=new Set();for(let i=Math.floor((p[0]-m)/4);i<=Math.floor((p[0]+m)/4);i++)for(let j=Math.floor((p[1]-m)/4);j<=Math.floor((p[1]+m)/4);j++)for(const r of cells.get(i+','+j)||[])out.add(r);return out;};}
export function createZhiliSurface(campus,terrain){
 if(prepared.has(campus))return prepared.get(campus);
 const data=campus.zhiliInterior,building=[...campus.places,...campus.buildings].find(b=>b.osm===ZHILI_OSM);
 if(!data||!building)return null;
 const f=frame(data.transform),base=terrain.platformHeight(building),H=data.floorHeight;
 // Walls, window glass/sills and glazed entrances all block; open entrances and doors do not.
 const floors=data.floors.map(fl=>{const blocking=[...fl.walls,...(fl.sills||[]).map(s=>s.rect),...fl.exits.filter(e=>!e.open).flatMap(e=>e.rect)];return{...fl,y:base+fl.level,near:grid(blocking),blocking};});
 const stepRects=floors.flatMap(fl=>fl.exits.flatMap(e=>(e.steps||[]).map(t=>t.rect)));
 function supportAt(x,z,y){
  const p=f.toDrawing(x,z);if(ringDistance(p[0],p[1],data.outline)!==0&&!stepRects.some(r=>inRect(p,r)))return null;
  // Stairs first: the slab below a flight must never pull a walker down.
  let best=null,error=Infinity;
  for(const fl of floors){if(y<fl.y-.5||y>fl.y+H+.6)continue;for(const s of fl.stairs){if(!inRect(p,s.rect))continue;for(const t of s.treads)if(inRect(p,t.rect)){const h=fl.y+t.height+ZHILI_CLEARANCE,e=Math.abs(y-h);if(e<.44&&e<error){best=h;error=e;}}}}
  for(const fl of floors)for(const e of fl.exits)for(const t of e.steps||[])if(inRect(p,t.rect)){const h=fl.y+t.height+ZHILI_CLEARANCE,er=Math.abs(y-h);if(er<.44&&er<error){best=h;error=er;}}
  if(best!==null)return best;
  for(const fl of floors)if(Math.abs(y-fl.y-ZHILI_CLEARANCE)<.85&&insideRegions(p,fl.slab))return fl.y+ZHILI_CLEARANCE;
  return null;
 }
 function blocked(x,z,r,y,riding=false){
  const p=f.toDrawing(x,z);if(ringDistance(p[0],p[1],data.outline)>=r+.05)return false;
  for(const fl of floors){if(y<fl.y-.5||y>fl.y+H-.7)continue;const d=ringDistance(p[0],p[1],fl.outline);if(d>=r+.05)continue;
   if(riding)return true;
   for(const w of fl.near(p,r+.1))if(rectDistance(p,w)<r+.02)return true;
   if(d===0&&supportAt(x,z,y)===null)return true;
  }
  return false;
 }
 const result={base,floors,supportAt,blocked,contains:(x,z)=>{const p=f.toDrawing(x,z);return ringDistance(p[0],p[1],data.outline)===0;}};prepared.set(campus,result);return result;
}
export function zhiliSupportAt(x,z,y,campus,terrain){return createZhiliSurface(campus,terrain)?.supportAt(x,z,y)??null;}
// Meshes: slabs, walls with real window openings, lintels, stair halls and treads, entrances, plan facade for 3F+.
export function addZhiliInterior(THREE,parent,campus,terrain,data,network){
 campus.zhiliInterior=data;const building=campus.places.find(b=>b.osm===ZHILI_OSM),base=terrain.platformHeight(building),H=data.floorHeight,SLAB=data.slab||.2,f=frame(data.transform);
 // Entrances: open where the ground outside meets the floor; a landing and indoor steps when it is up to 1.6m higher; otherwise glazed.
 for(const fl of data.floors)for(const e of fl.exits){const deck=fl.level>0&&insideRegions(e.outside,campus.courtyard?.floorRegions?.upper||[])?base+H:null,g=deck??(network?network.walkHeight(...e.outside,terrain.height(...e.outside)):terrain.height(...e.outside)),rise=g-(base+fl.level);e.rise=rise;e.open=Math.abs(rise)<.45;
  if(e.manual&&rise>=.45&&rise<=1.6){const a=f.toDrawing(...e.line[0]),b=f.toDrawing(...e.line[1]),o=f.toDrawing(...e.outside),i=f.toDrawing(...e.inside),mid=[(a[0]+b[0])/2,(a[1]+b[1])/2],len=Math.hypot(i[0]-o[0],i[1]-o[1]),u=[(i[0]-o[0])/len,(i[1]-o[1])/len],half=Math.hypot(b[0]-a[0],b[1]-a[1])/2,n=Math.ceil(rise/.18),h=rise/n,rect=(d0,d1)=>{const p0=[mid[0]+u[0]*d0,mid[1]+u[1]*d0],p1=[mid[0]+u[0]*d1,mid[1]+u[1]*d1],across=[Math.abs(u[1])*half,Math.abs(u[0])*half];return[Math.min(p0[0],p1[0])-across[0],Math.min(p0[1],p1[1])-across[1],Math.max(p0[0],p1[0])+across[0],Math.max(p0[1],p1[1])+across[1]];};
   e.steps=[{rect:rect(-.3,1.2),height:rise}];for(let k=0;k<n-1;k++)e.steps.push({rect:rect(1.2+k*.3,1.2+(k+1)*.3),height:rise-(k+1)*h});e.open=true;}
  // Ground lower than the floor (east main entrance on S05, drawing 階梯): outdoor steps down from the threshold.
  if(e.manual&&rise<=-.45&&rise>=-2.6){const a=f.toDrawing(...e.line[0]),b=f.toDrawing(...e.line[1]),o=f.toDrawing(...e.outside),i=f.toDrawing(...e.inside),mid=[(a[0]+b[0])/2,(a[1]+b[1])/2],len=Math.hypot(i[0]-o[0],i[1]-o[1]),u=[(i[0]-o[0])/len,(i[1]-o[1])/len],half=Math.hypot(b[0]-a[0],b[1]-a[1])/2+.3,n=Math.ceil(-rise/.17),h=-rise/n,rect=(d0,d1)=>{const p0=[mid[0]+u[0]*d0,mid[1]+u[1]*d0],p1=[mid[0]+u[0]*d1,mid[1]+u[1]*d1],across=[Math.abs(u[1])*half,Math.abs(u[0])*half];return[Math.min(p0[0],p1[0])-across[0],Math.min(p0[1],p1[1])-across[1],Math.max(p0[0],p1[0])+across[0],Math.max(p0[1],p1[1])+across[1]];};
   e.steps=[];for(let k=0;k<n-1;k++)e.steps.push({rect:rect(-(k+1)*.3,-k*.3),height:-(k+1)*h,bottom:rise-.4});e.open=true;}}
 const group=new THREE.Group();group.name='zhili-interior';parent.add(group);const blockers=[],props=new THREE.Group();props.name='zhili-interior-details';group.add(props);
 const mats={};for(const[k,c]of Object.entries({outer:0xa7644e,trim:0xbdbcb1,inner:0xece6d6,floor:0xd3cfc4,ceiling:0xe9e7df,frame:0x8f938c,tread:0xc9c5b8,glass:0x6f98a3,steel:0x7f898b}))mats[k]=new THREE.MeshStandardMaterial({color:c,roughness:.88,side:THREE.DoubleSide,...(k==='glass'?{transparent:true,opacity:.5,roughness:.3}:{}),...(['inner','floor','ceiling','tread'].includes(k)?{emissive:c,emissiveIntensity:.32}:{})});
 const cube=new THREE.BoxGeometry(1,1,1),dummy=new THREE.Object3D(),batches=new Map();
 const isExterior=(r,ring)=>[[r[0]-.15,(r[1]+r[3])/2],[r[2]+.15,(r[1]+r[3])/2],[(r[0]+r[2])/2,r[1]-.15],[(r[0]+r[2])/2,r[3]+.15]].some(([x,y])=>ringDistance(x,y,ring)>0);
 function rectBox(r,y0,y1,key){if(y1-y0<=.001)return;const [x,z]=f.toWorld((r[0]+r[2])/2,(r[1]+r[3])/2);if(!batches.has(key))batches.set(key,[]);batches.get(key).push({w:r[2]-r[0],h:y1-y0,d:r[3]-r[1],x,y:(y0+y1)/2,z});}
 function slab(triangles,top,bottom,key,name){const pos=[];for(const t of triangles){for(const[x,z]of t)pos.push(x,top,z);for(const[x,z]of[...t].reverse())pos.push(x,bottom,z);}const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.computeVertexNormals();const m=new THREE.Mesh(g,mats[key]);m.name=name;m.receiveShadow=true;group.add(m);blockers.push(m);return m;}
 function plate(text,x,y,z,angle,width=1,bg='#23434b',fg='#fff1cc'){const c=document.createElement('canvas');c.width=384;c.height=144;const g=c.getContext('2d');g.fillStyle=bg;g.fillRect(0,0,384,144);g.fillStyle=fg;g.font='bold 80px serif';g.textAlign='center';g.fillText(text,192,100);const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;const m=new THREE.Mesh(new THREE.PlaneGeometry(width,width*.375),new THREE.MeshBasicMaterial({map:tex,side:THREE.DoubleSide}));m.position.set(x,y,z);m.rotation.y=angle;props.add(m);return m;}
 // A window pane on an outline edge (drawing a→b with outward normal), plus head/sill trim and a mullion.
 function pane(w,y,out=0){const len=Math.hypot(w.b[0]-w.a[0],w.b[1]-w.a[1]),horiz=Math.abs(w.b[1]-w.a[1])<1e-6,cx=(w.a[0]+w.b[0])/2+w.normal[0]*out,cy=(w.a[1]+w.b[1])/2+w.normal[1]*out,r=(along,across)=>horiz?[cx-along/2,cy-across/2,cx+along/2,cy+across/2]:[cx-across/2,cy-along/2,cx+across/2,cy+along/2];
  rectBox(r(len,.06),y+w.sill,y+w.head,'glass');rectBox(r(len+.2,.16),y+w.sill-.08,y+w.sill,'trim');rectBox(r(len+.2,.16),y+w.head,y+w.head+.1,'trim');rectBox(r(.07,.1),y+w.sill,y+w.head,'frame');}
 let shell=null;
 for(const fl of data.floors){const y=base+fl.level;
  const s=slab(fl.slabTriangles,y,y-SLAB,'floor','zhili-floor-'+fl.label);shell??=s;
  for(const w of fl.walls)rectBox(w,y,y+H-SLAB,isExterior(w,fl.outline)?'outer':'inner');
  for(const w of fl.sills||[]){rectBox(w.rect,y,y+w.top,'outer');}
  for(const w of fl.heads||[]){rectBox(w.rect,y+w.bottom,y+H-SLAB,'outer');}
  for(const w of fl.windows||[])pane(w,y,-.12);
  for(const l of fl.lintels)rectBox(l,y+2.25,y+H-SLAB,'inner');
  for(const e of fl.exits){for(const r of e.rect){rectBox(r,y+2.4,y+H-SLAB,'outer');if(!e.open){rectBox(r,y,y+.15,'outer');rectBox([r[0]+.08,r[1]+.08,r[2]-.08,r[3]-.08],y+.15,y+2.4,'glass');}}}
  for(const e of fl.exits)for(const t of e.steps||[])rectBox(t.rect,y+(t.bottom??0),y+t.height,'tread');
  for(const st of fl.stairs){if(st.tiers){for(const t of st.treads)rectBox(t.rect,y,y+t.height,'tread');continue;}
   for(const t of st.treads){const top=y+t.height;rectBox(t.rect,top-(t.flight<0?.2:.18),top,'tread');}
   rectBox(st.divider,y,y+1.1,'inner');rectBox(st.divider,y+1.1,y+H-SLAB-.05,'steel');
   const r=st.rect,[px,pz]=f.toWorld((r[0]+r[2])/2,(r[1]+r[3])/2);plate(st.id+' '+fl.label+'↑',px,y+2.6,pz,f.angle,1);}
  for(const d of fl.doors){const[a,b]=d.line,mx=(a[0]+b[0])/2,mz=(a[1]+b[1])/2,ang=Math.atan2(-(b[1]-a[1]),b[0]-a[0]);if(['classroom','office','library','hall','service','mech','unknown'].includes(d.kind)&&/^[\dB]/.test(d.name))plate(d.name,mx,y+2.55,mz,ang,.8);}
 }
 const roofY=base+data.roofLevel;slab(data.roofTriangles,roofY-.01,roofY-SLAB,'ceiling','zhili-roof');
 // 3F and above: one solid brick volume with the plan's windows on every facade, floor bands and a parapet.
 if(data.solidAbove){const ring=data.towerOutline,sh=new THREE.Shape();ring.forEach(([x,y],i)=>{const [wx,wz]=f.toWorld(x,y);i?sh.lineTo(wx,-wz):sh.moveTo(wx,-wz);});sh.closePath();const g=new THREE.ExtrudeGeometry(sh,{depth:data.solidAbove.to-data.solidAbove.from,bevelEnabled:false});g.rotateX(-Math.PI/2);const m=new THREE.Mesh(g,mats.outer);m.position.y=base+data.solidAbove.from;m.name='zhili-solid-upper-floors';m.castShadow=true;m.receiveShadow=true;group.add(m);blockers.push(m);
  for(const [label,wins] of Object.entries(data.facade||{})){const level=(+label.replace('F','')-1)*H,y=base+level;for(const w of wins)pane(w,y,.04);}
  for(let i=0;i<ring.length;i++){const a=ring[i],b=ring[(i+1)%ring.length],horiz=Math.abs(b[1]-a[1])<1e-6,len=Math.abs(b[0]-a[0])+Math.abs(b[1]-a[1]),cx=(a[0]+b[0])/2,cy=(a[1]+b[1])/2,r=horiz?[cx-len/2-.1,cy-.12,cx+len/2+.1,cy+.12]:[cx-.12,cy-len/2-.1,cx+.12,cy+len/2+.1];
   for(let lv=data.solidAbove.from;lv<data.solidAbove.to-.1;lv+=H)rectBox(r,base+lv-.12,base+lv+.06,'trim');rectBox(r,base+data.solidAbove.to,base+data.solidAbove.to+.9,'outer');rectBox(r,base+data.solidAbove.to+.9,base+data.solidAbove.to+1,'trim');}}
 // Building name over the main (east) entrance, as on the S05 facade.
 const main=data.floors.find(fl=>fl.label==='1F')?.exits.find(e=>Math.abs(f.toDrawing(...e.outside)[1]-f.toDrawing(...e.inside)[1])>.5&&f.toDrawing(...e.outside)[1]>f.toDrawing(...e.inside)[1]);
 if(main){const [a,b]=main.line,mx=(a[0]+b[0])/2,mz=(a[1]+b[1])/2,dx=main.outside[0]-mx,dz=main.outside[1]-mz,l=Math.hypot(dx,dz),ang=Math.atan2(-(b[1]-a[1]),b[0]-a[0]);plate('致理大樓',mx+dx/l*.32,base+3.05,mz+dz/l*.32,ang,3.2,'#8e8d80','#f3e3b5');}
 for(const[key,items]of batches){const m=new THREE.InstancedMesh(cube,mats[key],items.length);m.name='zhili-'+key;for(let i=0;i<items.length;i++){const b=items[i];dummy.position.set(b.x,b.y,b.z);dummy.rotation.set(0,f.angle,0);dummy.scale.set(b.w,b.h,b.d);dummy.updateMatrix();m.setMatrixAt(i,dummy.matrix);}m.computeBoundingSphere();m.receiveShadow=true;m.castShadow=key==='outer';group.add(m);if(key!=='glass')blockers.push(m);}
 return{group,detail:props,shell,blockers,groundCuts:data.floors[0].slabTriangles};
}
