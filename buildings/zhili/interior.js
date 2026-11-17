import {ringDistance} from '../../planar.js';
// Zhili empty-room interior compiled from the reviewed floor-plan draft (scripts/build-zhili-interior.py).
// Geometry is authored in the drawing frame (axis-aligned rectangles) and placed with one rigid transform.
export const ZHILI_OSM=444867693;
export const ZHILI_CLEARANCE=.08;
const SLAB=.2,prepared=new WeakMap();
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
 const floors=data.floors.map(fl=>{const blocking=[...fl.walls,...fl.exits.filter(e=>!e.open).flatMap(e=>e.rect)];return{...fl,y:base+fl.level,near:grid(blocking),blocking};});
 const outline=data.outline;
 function supportAt(x,z,y){
  const p=f.toDrawing(x,z);if(ringDistance(p[0],p[1],outline)!==0)return null;
  // Stairs first: the slab below a flight must never pull a walker down.
  let best=null,error=Infinity;
  for(const fl of floors){if(y<fl.y-.5||y>fl.y+H+.6)continue;for(const s of fl.stairs){if(!inRect(p,s.rect))continue;for(const t of s.treads)if(inRect(p,t.rect)){const h=fl.y+t.height+ZHILI_CLEARANCE,e=Math.abs(y-h);if(e<.44&&e<error){best=h;error=e;}}}}
  if(best!==null)return best;
  for(const fl of floors)if(Math.abs(y-fl.y-ZHILI_CLEARANCE)<.85&&insideRegions(p,fl.slab))return fl.y+ZHILI_CLEARANCE;
  return null;
 }
 function blocked(x,z,r,y,riding=false){
  const p=f.toDrawing(x,z),inside=ringDistance(p[0],p[1],outline)<r+.05;if(!inside)return false;
  if(riding)return true;
  for(const fl of floors){if(y<fl.y-.5||y>fl.y+H-.7)continue;
   for(const w of fl.near(p,r+.1))if(rectDistance(p,w)<r+.02)return true;
   if(ringDistance(p[0],p[1],outline)===0&&supportAt(x,z,y)===null)return true;
  }
  return false;
 }
 const result={base,floors,supportAt,blocked,contains:(x,z)=>{const p=f.toDrawing(x,z);return ringDistance(p[0],p[1],outline)===0;}};prepared.set(campus,result);return result;
}
export function zhiliSupportAt(x,z,y,campus,terrain){return createZhiliSurface(campus,terrain)?.supportAt(x,z,y)??null;}
// Meshes: slabs, partition / exterior wall boxes, lintels, door frames, stair treads, room number plates.
export function addZhiliInterior(THREE,parent,campus,terrain,data,network){
 campus.zhiliInterior=data;const building=campus.places.find(b=>b.osm===ZHILI_OSM),base=terrain.platformHeight(building),H=data.floorHeight,f=frame(data.transform);
 // Exterior openings stay open only where the ground outside meets the floor; otherwise they are glazed.
 for(const fl of data.floors)for(const e of fl.exits){const g=network?network.walkHeight(...e.outside,terrain.height(...e.outside)):terrain.height(...e.outside);e.open=Math.abs(g-(base+fl.level))<.45;}
 const group=new THREE.Group();group.name='zhili-interior';parent.add(group);const blockers=[],props=new THREE.Group();props.name='zhili-interior-details';group.add(props);
 const mats={};for(const[k,c]of Object.entries({outer:0xa7644e,inner:0xece6d6,floor:0xd3cfc4,ceiling:0xe9e7df,frame:0x9c9d94,tread:0xc9c5b8,glass:0x6f98a3,steel:0x7f898b,plate:0x23434b}))mats[k]=new THREE.MeshStandardMaterial({color:c,roughness:.88,side:THREE.DoubleSide,...(k==='glass'?{transparent:true,opacity:.55}:{}),...(['inner','floor','ceiling','tread'].includes(k)?{emissive:c,emissiveIntensity:.32}:{})});
 const cube=new THREE.BoxGeometry(1,1,1),dummy=new THREE.Object3D(),batches=new Map();
 const outline=data.outline,minX=Math.min(...outline.map(p=>p[0])),maxX=Math.max(...outline.map(p=>p[0])),minY=Math.min(...outline.map(p=>p[1])),maxY=Math.max(...outline.map(p=>p[1]));
 const exterior=r=>ringDistance((r[0]+r[2])/2,(r[1]+r[3])/2,outline)<.5&&[[r[0],r[1]],[r[2],r[1]],[r[0],r[3]],[r[2],r[3]]].some(([x,y])=>ringDistance(x+(x===r[0]?-.2:.2),y+(y===r[1]?-.2:.2),outline)>0);
 function rectBox(r,y0,y1,key){const [x,z]=f.toWorld((r[0]+r[2])/2,(r[1]+r[3])/2);if(!batches.has(key))batches.set(key,[]);batches.get(key).push({w:r[2]-r[0],h:y1-y0,d:r[3]-r[1],x,y:(y0+y1)/2,z});}
 function slab(triangles,top,bottom,key,name){const pos=[];for(const t of triangles){for(const[x,z]of t)pos.push(x,top,z);for(const[x,z]of[...t].reverse())pos.push(x,bottom,z);}const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.computeVertexNormals();const m=new THREE.Mesh(g,mats[key]);m.name=name;m.receiveShadow=true;group.add(m);blockers.push(m);return m;}
 function plate(text,x,y,z,angle,width=1){const c=document.createElement('canvas');c.width=192;c.height=72;const g=c.getContext('2d');g.fillStyle='#23434b';g.fillRect(0,0,192,72);g.fillStyle='#fff1cc';g.font='bold 40px sans-serif';g.textAlign='center';g.fillText(text,96,50);const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;const m=new THREE.Mesh(new THREE.PlaneGeometry(width,width*.375),new THREE.MeshBasicMaterial({map:tex,side:THREE.DoubleSide}));m.position.set(x,y,z);m.rotation.y=angle;props.add(m);}
 let shell=null;
 for(const fl of data.floors){const y=base+fl.level;
  const s=slab(fl.slabTriangles,y,y-SLAB,'floor','zhili-floor-'+fl.label);shell??=s;
  for(const w of fl.walls)rectBox(w,y,y+H-SLAB,exterior(w)?'outer':'inner');
  for(const l of fl.lintels)rectBox(l,y+2.25,y+H-SLAB,'inner');
  for(const e of fl.exits){for(const r of e.rect){rectBox(r,y+2.4,y+H-SLAB,'outer');if(!e.open){rectBox(r,y,y+.9,'outer');rectBox([r[0]+.05,r[1]+.05,r[2]-.05,r[3]-.05],y+.9,y+2.4,'glass');}}}
  for(const st of fl.stairs){for(const t of st.treads){const top=y+t.height;rectBox(t.rect,top-(t.flight<0?.2:.18),top,'tread');}
   const r=st.rect,along=['x0','x1'].includes(st.entrance),mid=along?[(r[1]+r[3])/2]:[(r[0]+r[2])/2];
   // A low centre wall separates the two flights; rails are omitted in the empty-room pass.
   const div=along?[r[0]+st.landing,mid[0]-.05,r[2]-st.landing,mid[0]+.05]:[mid[0]-.05,r[1]+st.landing,mid[0]+.05,r[3]-st.landing];rectBox(div,y,y+H-SLAB,'inner');
   const [px,pz]=f.toWorld((r[0]+r[2])/2,(r[1]+r[3])/2);plate(fl.label+' ↑',px,y+2.5,pz,f.angle,.9);}
  for(const d of fl.doors){const[a,b]=d.line,mx=(a[0]+b[0])/2,mz=(a[1]+b[1])/2,ang=Math.atan2(-(b[1]-a[1]),b[0]-a[0]);if(['classroom','office','library','hall','service','mech','unknown'].includes(d.kind)&&/^[\dB]/.test(d.name))plate(d.name,mx,y+2.55,mz,ang,.8);}
 }
 const roofY=base+data.roofLevel;slab(data.roofTriangles,roofY,roofY-SLAB,'ceiling','zhili-roof');
 for(const[key,items]of batches){const m=new THREE.InstancedMesh(cube,mats[key],items.length);m.name='zhili-'+key;for(let i=0;i<items.length;i++){const b=items[i];dummy.position.set(b.x,b.y,b.z);dummy.rotation.set(0,f.angle,0);dummy.scale.set(b.w,b.h,b.d);dummy.updateMatrix();m.setMatrixAt(i,dummy.matrix);}m.computeBoundingSphere();m.receiveShadow=true;m.castShadow=key==='outer';group.add(m);if(key!=='glass')blockers.push(m);}
 return{group,detail:props,shell,blockers,groundCuts:data.floors[0].slabTriangles};
}
