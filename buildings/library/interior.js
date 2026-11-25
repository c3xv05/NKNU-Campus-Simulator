import {ringDistance} from '../../planar.js';
// 圖資大樓 (library): walkable B1 / 1F compiled from the user's floor plans by scripts/build-library-interior.py.
// The data are world-coordinate prisms (walls, glass, columns, treads, planters…) and flat walk surfaces with
// heights relative to the B1 floor; the B1 floor sits on the building's terrain pad (terrain.platformHeight).
export const LIBRARY_OSM=381963953;
const CLEARANCE=.02,STEP_UP=.45,BODY_LOW=.3,BODY_HIGH=1.7;
const prepared=new WeakMap();
function bbox(points){let a=Infinity,b=Infinity,c=-Infinity,d=-Infinity;for(const[x,z]of points){a=Math.min(a,x);b=Math.min(b,z);c=Math.max(c,x);d=Math.max(d,z);}return[a,b,c,d];}
// Spatial hash on a 4 m grid.
function index(items,boxOf){const cells=new Map();for(const it of items){const[a,b,c,d]=boxOf(it);for(let i=Math.floor(a/4);i<=Math.floor(c/4);i++)for(let j=Math.floor(b/4);j<=Math.floor(d/4);j++){const k=i+','+j;if(!cells.has(k))cells.set(k,[]);cells.get(k).push(it);}}return(x,z,m=0)=>{const out=new Set();for(let i=Math.floor((x-m)/4);i<=Math.floor((x+m)/4);i++)for(let j=Math.floor((z-m)/4);j<=Math.floor((z+m)/4);j++)for(const it of cells.get(i+','+j)||[])out.add(it);return out;};}
function inTri(x,z,t,o){const ax=t[o],az=t[o+1],bx=t[o+2],bz=t[o+3],cx=t[o+4],cz=t[o+5];const d1=(x-bx)*(az-bz)-(ax-bx)*(z-bz),d2=(x-cx)*(bz-cz)-(bx-cx)*(z-cz),d3=(x-ax)*(cz-az)-(cx-ax)*(z-az);const neg=d1<0||d2<0||d3<0,pos=d1>0||d2>0||d3>0;return!(neg&&pos);}
function polyDistance(x,z,p){const outer=ringDistance(x,z,p[0]);if(outer===0){for(const h of p.slice(1)){const d=ringDistance(x,z,h);if(d===0){let e=Infinity;for(let i=0;i<h.length;i++){const a=h[i],b=h[(i+1)%h.length],dx=b[0]-a[0],dz=b[1]-a[1],u=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz||1)));e=Math.min(e,Math.hypot(x-a[0]-dx*u,z-a[1]-dz*u));}return e;}}return 0;}return outer;}
export function createLibrarySurface(campus,terrain){
 if(!prepared.has(campus))prepared.set(campus,null);const cached=prepared.get(campus);if(cached)return cached;
 const data=campus.libraryInterior,building=[...campus.places,...campus.buildings].find(b=>b.osm===LIBRARY_OSM);if(!data||!building)return null;
 const base=terrain.platformHeight(building);
 const tris=[];for(const w of data.walks)for(let o=0;o<w.t.length;o+=6)tris.push({t:w.t,o,y:base+w.y+CLEARANCE,yv:w.yv?[w.yv[o/2],w.yv[o/2+1],w.yv[o/2+2]].map(v=>base+v+CLEARANCE):null,box:[Math.min(w.t[o],w.t[o+2],w.t[o+4]),Math.min(w.t[o+1],w.t[o+3],w.t[o+5]),Math.max(w.t[o],w.t[o+2],w.t[o+4]),Math.max(w.t[o+1],w.t[o+3],w.t[o+5])]});
 const triAt=index(tris,t=>t.box);
 const solids=data.prisms.filter(p=>p.b).map(p=>({p:p.p,y0:base+p.y0,y1:base+p.y1,box:bbox(p.p[0])}));
 const solidAt=index(solids,s=>s.box);
 const slopeY=(x,z,t)=>{const q=t.t,o=t.o,ax=q[o],az=q[o+1],bx=q[o+2],bz=q[o+3],cx=q[o+4],cz=q[o+5],d=(bz-cz)*(ax-cx)+(cx-bx)*(az-cz)||1e-9,u=((bz-cz)*(x-cx)+(cx-bx)*(z-cz))/d,v=((cz-az)*(x-cx)+(ax-cx)*(z-cz))/d;return t.yv[0]*u+t.yv[1]*v+t.yv[2]*(1-u-v);};
 function supportAt(x,z,y){let best=null;for(const t of triAt(x,z)){if(x<t.box[0]||x>t.box[2]||z<t.box[1]||z>t.box[3])continue;const h=t.yv?slopeY(x,z,t):t.y;if(h>y+STEP_UP||(best!==null&&h<=best))continue;if(inTri(x,z,t.t,t.o))best=h;}return best;}
 function blocked(x,z,r,y,riding=false){
  if(riding&&ringDistance(x,z,data.outline)<r)return true;
  for(const s of solidAt(x,z,r+.1)){if(s.y1<=y+BODY_LOW||s.y0>=y+BODY_HIGH)continue;if(x<s.box[0]-r||x>s.box[2]+r||z<s.box[1]-r||z>s.box[3]+r)continue;if(polyDistance(x,z,s.p)<r)return true;}
  return false;
 }
 const result={osm:LIBRARY_OSM,base,supportAt,blocked,contains:(x,z)=>ringDistance(x,z,data.outline)===0};prepared.set(campus,result);return result;
}
const COLORS={outer:0xc9ccc4,trim:0xe1e0d4,inner:0xece6d6,column:0xd9d6cb,ceiling:0xe9e7df,floor:0xd3cfc4,tread:0xc9c5b8,rail:0x8f979c,steel:0x7f898b,wood:0xa87c50,
 paving:0xcfc8b8,planter:0x9a8f80,soil:0x5f8a3e,pebble:0xb9b1a2,water:0x3f7d94,portal:0xe8e6de,paint:0xf2f2ec,roof:0xb7b8b1,frame:0x6f7a7d,glass:0x6f98a3,asphalt:0x4b4e50};
export function addLibraryInterior(THREE,parent,campus,terrain,data){
 campus.libraryInterior=data;(campus.planInteriors??={})[LIBRARY_OSM]=data;
 const building=[...campus.places,...campus.buildings].find(b=>b.osm===LIBRARY_OSM),base=terrain.platformHeight(building);
 const group=new THREE.Group();group.name='library-interior';parent.add(group);const detail=new THREE.Group();detail.name='library-details';group.add(detail);
 // Canvas textures (world-aligned UVs, 2.4 m repeat): floor tiles, T-bar ceiling, pavers, asphalt, facade tiles.
 const tex=(draw,size=256)=>{const c=document.createElement('canvas');c.width=c.height=size;draw(c.getContext('2d'),size);const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=4;t.colorSpace=THREE.SRGBColorSpace;return t;};
 const grid=(bg,line,n,lw,noise=0)=>tex((g,s)=>{g.fillStyle=bg;g.fillRect(0,0,s,s);for(let k=0;k<noise;k++){g.fillStyle=`rgba(90,85,75,${Math.random()*.08})`;g.fillRect(Math.random()*s,Math.random()*s,2,2);}g.fillStyle=line;for(let i=0;i<n;i++){g.fillRect(i*s/n,0,lw,s);g.fillRect(0,i*s/n,s,lw);}});
 const maps={floor:()=>grid('#d6d2c8','#aaa498',4,3,1200),ceiling:()=>tex((g,s)=>{g.fillStyle='#e2e1da';g.fillRect(0,0,s,s);g.fillStyle='#ffffff';g.fillRect(s/4+4,s/4+4,s/2-8,s/4-8);g.fillStyle='#a9aaa5';for(let i=0;i<4;i++){g.fillRect(i*s/4-1,0,3,s);g.fillRect(0,i*s/4-1,s,3);}}),
  paving:()=>grid('#cbc3b2','#a99f8c',6,2,1500),asphalt:()=>grid('#4b4e50','#4b4e50',1,0,3000),outer:()=>grid('#cfd2cb','#b3b7af',3,2,600),tread:()=>grid('#cdc9bc','#b1ad9f',2,2,800),roof:()=>grid('#b9bab3','#a3a49c',2,2,1500)};
 const mats={};const mat=k=>{if(!mats[k]){const c=COLORS[k]??0xcccccc,lit=['inner','floor','column','tread'].includes(k),map=maps[k]?.();
   mats[k]=k==='ceiling'?new THREE.MeshBasicMaterial({map,color:0xf4f2ea,side:THREE.DoubleSide}):new THREE.MeshStandardMaterial({color:map?0xffffff:c,map,roughness:k==='glass'||k==='water'?.25:.88,side:THREE.DoubleSide,...(k==='glass'?{transparent:true,opacity:.45,depthWrite:false}:{}),...(k==='water'?{transparent:true,opacity:.8}:{}),...(lit?{emissive:map?0xffffff:c,emissiveMap:map||null,emissiveIntensity:.3}:{})});}return mats[k];};
 // Prisms merged per material: top, bottom and side faces of each polygon (with holes), world-aligned UVs.
 const buffers=new Map();const buf=k=>{if(!buffers.has(k))buffers.set(k,{p:[],u:[]});return buffers.get(k);};
 const V=(x,z)=>new THREE.Vector2(x,z),R=2.4;
 for(const pr of data.prisms){const out=buf(pr.m),y0=base+pr.y0,y1=base+pr.y1,rings=pr.p.map(r=>{const v=r.map(([x,z])=>V(x,z));return THREE.ShapeUtils.isClockWise(v)?v:v.reverse();});
  const outer=rings[0],holes=rings.slice(1).map(h=>h.slice().reverse()),all=[...outer,...holes.flat()];
  let faces=[];try{faces=THREE.ShapeUtils.triangulateShape(outer,holes);}catch(e){faces=[];}
  const top=(i,y)=>{out.p.push(all[i].x,y,all[i].y);out.u.push(all[i].x/R,all[i].y/R);};
  for(const f of faces){for(const i of f)top(i,y1);for(const i of f.slice().reverse())top(i,y0);}
  for(const r of [outer,...holes]){let s=0;for(let i=0;i<r.length;i++){const a=r[i],b=r[(i+1)%r.length],l=Math.hypot(b.x-a.x,b.y-a.y),s1=s+l;
   out.p.push(a.x,y0,a.y,b.x,y0,b.y,b.x,y1,b.y,a.x,y0,a.y,b.x,y1,b.y,a.x,y1,a.y);out.u.push(s/R,y0/R,s1/R,y0/R,s1/R,y1/R,s/R,y0/R,s1/R,y1/R,s/R,y1/R);s=s1;}}}
 for(const w of data.walks){if(!w.m)continue;const out=buf(w.m),y=base+w.y+.004;for(let o=0;o<w.t.length;o+=6)for(let j=0;j<6;j+=2){out.p.push(w.t[o+j],w.yv?base+w.yv[(o+j)/2]+.004:y,w.t[o+j+1]);out.u.push(w.t[o+j]/R,w.t[o+j+1]/R);}}
 const blockers=[];
 for(const[k,arr]of buffers){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(arr.p,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(arr.u,2));g.computeVertexNormals();const m=new THREE.Mesh(g,mat(k));m.name='library-'+k;m.receiveShadow=true;m.castShadow=['outer','portal','column'].includes(k);if(k==='glass'||k==='water')m.renderOrder=2;group.add(m);if(['outer','inner','portal','column','roof','ceiling'].includes(k))blockers.push(m);}
 // Atrium dome (glass) over the pool.
 for(const d of data.domes||[]){const s=new THREE.Mesh(new THREE.SphereGeometry(d.r,40,10,0,Math.PI*2,0,Math.PI/2),mat('glass'));s.scale.y=.35;s.position.set(d.c[0],base+d.y,d.c[1]);s.name='library-dome';group.add(s);
  for(let i=0;i<12;i++){const rib=new THREE.Mesh(new THREE.TorusGeometry(d.r,.05,4,24,Math.PI),mat('frame'));rib.rotation.y=i/12*Math.PI;const holder=new THREE.Group();holder.position.set(d.c[0],base+d.y,d.c[1]);holder.scale.y=.35;holder.add(rib);group.add(holder);}}
 // Room numbers (user: numbers only), small plaques readable indoors.
 const cache=new Map();for(const l of data.labels||[]){if(!cache.has(l.n)){const c=document.createElement('canvas');c.width=128;c.height=64;const x=c.getContext('2d');x.fillStyle='rgba(40,52,60,.85)';x.fillRect(0,0,128,64);x.fillStyle='#f4f1e6';x.font='bold 40px sans-serif';x.textAlign='center';x.textBaseline='middle';x.fillText(l.n,64,34);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;cache.set(l.n,new THREE.SpriteMaterial({map:t,depthTest:true}));}
  const s=new THREE.Sprite(cache.get(l.n));s.scale.set(.7,.35,1);s.position.set(l.at[0],base+l.y,l.at[1]);s.name='library-room-'+l.n;detail.add(s);}
 return{group,detail,shell:group,blockers};
}
