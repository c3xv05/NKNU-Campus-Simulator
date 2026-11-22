// Zhili driveway (ramp to the B1 garage) and S05 curb-cut pads (user 2026-11-22, drawing floor-1F-current.pdf).
// Pads are tile at road level cut out of the raised sidewalk (the sidewalk surface draws the curbs along the cut);
// the driveway ramp is asphalt between two side walls, rising from road level to the B1 floor.
import {ROAD_SURFACE_LIFT} from '../../sidewalk-layout.js';
import {sidewalkPlan} from '../../data/sidewalk-plan.js';
import {ringDistance} from '../../planar.js';
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export function addZhiliCurbCuts(THREE,group,campus,terrain,network,tileMaterial){
 const cfg=campus.zhiliCurbCuts,blockers=[];if(!cfg)return null;
 const zhili=campus.places.find(a=>a.osm===444867693),lower=terrain.platformHeight(zhili);
 const roadBase=(x,z)=>network.surfaceHeight(x,z)+ROAD_SURFACE_LIFT;
 const add=(positions,mat,name,tiled=false)=>{const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));if(tiled){const uv=[];for(let i=0;i<positions.length;i+=3)uv.push(positions[i]/2.4,positions[i+2]/2.4);g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setAttribute('sidewalkEdgeDistance',new THREE.Float32BufferAttribute(Array(positions.length/3).fill(1),1));}g.computeVertexNormals();const m=new THREE.Mesh(g,mat);m.name=name;m.receiveShadow=true;group.add(m);return m;};
 const up=(a,b,c)=>((b[0]-a[0])*(c[2]-a[2])-(b[2]-a[2])*(c[0]-a[0]))>0?[a,c,b]:[a,b,c];
 // Tile pads at road height (flush with the S05 pavement, rounded flares at both sides).
 const pads=(sidewalkPlan.curbCuts||[]);
 for(const pad of pads){const pos=[];for(const t of pad.triangles){const p=up(...t.map(([x,z])=>[x,roadBase(x,z)+.004,z]));for(const q of p)pos.push(...q);}blockers.push(add(pos,tileMaterial,'zhili-curbcut-pad-'+pad.id,true));}
 const d=cfg.driveway,[a,b]=d.axis,len=Math.hypot(b[0]-a[0],b[1]-a[1]),ux=(b[0]-a[0])/len,uz=(b[1]-a[1])/len,nx=-uz,nz=ux,b1=lower+d.b1Level;
 // Ramp surface: B1 floor at the garage mouth, S05 road height where the pad begins.
 const rampT=(x,z)=>clamp(((x-a[0])*ux+(z-a[1])*uz)/len,0,1),rampH=(x,z)=>{const t=rampT(x,z);return b1+(roadBase(x,z)-b1)*t;};
 const half=d.width/2,N=Math.ceil(len/.4),M=Math.ceil(d.width/.5),corner=(i,j)=>[a[0]+ux*len*i/N+nx*half*(2*j/M-1),a[1]+uz*len*i/N+nz*half*(2*j/M-1)];
 const rampPos=[];for(let i=0;i<N;i++)for(let j=0;j<M;j++){const q=[corner(i,j),corner(i+1,j),corner(i+1,j+1),corner(i,j+1)].map(([x,z])=>[x,rampH(x,z)+.004,z]);rampPos.push(...up(q[0],q[1],q[2]).flat(),...up(q[0],q[2],q[3]).flat());}
 const asphalt=new THREE.MeshStandardMaterial({color:0x3b3c3e,roughness:1,side:THREE.DoubleSide});blockers.push(add(rampPos,asphalt,'zhili-driveway-ramp'));
 // Side walls: solid down to the ground, top follows the ramp.
 const wallMat=new THREE.MeshStandardMaterial({color:0xa66b58,roughness:.95,side:THREE.DoubleSide}),capMat=new THREE.MeshStandardMaterial({color:0xb8bab2,roughness:1,side:THREE.DoubleSide});
 for(const [k,ring] of d.walls.entries()){const wallA=ring.map(([x,z])=>[x,z]),proj=ring.map(([x,z])=>((x-a[0])*ux+(z-a[1])*uz)),lo=Math.min(...proj),hi=Math.max(...proj),across=ring.map(([x,z])=>((x-a[0])*nx+(z-a[1])*nz)),minAcross=Math.min(...across),maxAcross=Math.max(...across);
  const at=(s,o)=>[a[0]+ux*s+nx*o,a[1]+uz*s+nz*o],pos=[],cap=[],S=Math.max(1,Math.ceil((hi-lo)/.5));
  const topAt=(s,o)=>{const [x,z]=at(s,o);return rampH(x,z)+d.wallAbove;},baseAt=(s,o)=>{const [x,z]=at(s,o);return terrain.height(x,z)-1.5;};
  for(let i=0;i<S;i++){const s0=lo+(hi-lo)*i/S,s1=lo+(hi-lo)*(i+1)/S;
   const T=(s,o)=>{const [x,z]=at(s,o);return[x,topAt(s,o),z];},B=(s,o)=>{const [x,z]=at(s,o);return[x,baseAt(s,o),z];};
   cap.push(...up(T(s0,minAcross),T(s1,minAcross),T(s1,maxAcross)).flat(),...up(T(s0,minAcross),T(s1,maxAcross),T(s0,maxAcross)).flat());
   for(const o of [minAcross,maxAcross])pos.push(...B(s0,o),...B(s1,o),...T(s1,o),...B(s0,o),...T(s1,o),...T(s0,o));
   if(i===0)for(const [o0,o1] of [[minAcross,maxAcross]])pos.push(...B(s0,o0),...B(s0,o1),...T(s0,o1),...B(s0,o0),...T(s0,o1),...T(s0,o0));
   if(i===S-1)for(const [o0,o1] of [[minAcross,maxAcross]])pos.push(...B(s1,o0),...B(s1,o1),...T(s1,o1),...B(s1,o0),...T(s1,o1),...T(s1,o0));}
  blockers.push(add(pos,wallMat,'zhili-driveway-wall-'+k),add(cap,capMat,'zhili-driveway-wall-cap-'+k));}
 // Wheelchair ramp beside the entrance stair (drawing 殘障坡道): 1F platform height at the west end, sidewalk height at the east end; solid body.
 const ada=cfg.ada,[aa,ab]=ada.axis,alen=Math.hypot(ab[0]-aa[0],ab[1]-aa[1]),aux=(ab[0]-aa[0])/alen,auz=(ab[1]-aa[1])/alen,anx=-auz,anz=aux,ahalf=ada.width/2;
 const adaT=(x,z)=>clamp(((x-aa[0])*aux+(z-aa[1])*auz)/alen,0,1),adaH=(x,z)=>{const t=adaT(x,z),end=roadBase(x,z)+.15;return lower+(end-lower)*t;};
 {const AN=Math.ceil(alen/.5),AM=2,at=(i,j)=>[aa[0]+aux*alen*i/AN+anx*ahalf*(2*j/AM-1),aa[1]+auz*alen*i/AN+anz*ahalf*(2*j/AM-1)],top=[],side=[];
  for(let i=0;i<AN;i++)for(let j=0;j<AM;j++){const q=[at(i,j),at(i+1,j),at(i+1,j+1),at(i,j+1)].map(([x,z])=>[x,adaH(x,z)+.004,z]);top.push(...up(q[0],q[1],q[2]).flat(),...up(q[0],q[2],q[3]).flat());}
  for(let i=0;i<AN;i++)for(const j of [0,AM]){const p=at(i,j),q=at(i+1,j),bp=terrain.height(...p)-1,bq=terrain.height(...q)-1;side.push(p[0],bp,p[1],q[0],bq,q[1],q[0],adaH(...q),q[1],p[0],bp,p[1],q[0],adaH(...q),q[1],p[0],adaH(...p),p[1]);}
  {const p=at(0,0),q=at(0,AM),bp=terrain.height(...p)-1,bq=terrain.height(...q)-1;side.push(p[0],bp,p[1],q[0],bq,q[1],q[0],adaH(...q),q[1],p[0],bp,p[1],q[0],adaH(...q),q[1],p[0],adaH(...p),p[1]);}
  {const p=at(AN,0),q=at(AN,AM),bp=terrain.height(...p)-1,bq=terrain.height(...q)-1;side.push(p[0],bp,p[1],q[0],bq,q[1],q[0],adaH(...q),q[1],p[0],bp,p[1],q[0],adaH(...q),q[1],p[0],adaH(...p),p[1]);}
  blockers.push(add(top,tileMaterial,'zhili-ada-ramp',true),add(side,capMat,'zhili-ada-ramp-body'));}
 const inAda=(x,z)=>ringDistance(x,z,ada.ring)===0;
 // Upper-plaza planters / benches (Zhili 2F drawing) and the B1 skylight of glass pyramids.
 const plz=cfg.plaza,upperLevel=lower+3.6,solids=[];
 if(plz){const prism=(ring,h,name)=>{const shape=new THREE.Shape();ring.forEach(([x,z],k)=>k?shape.lineTo(x,-z):shape.moveTo(x,-z));shape.closePath();const g=new THREE.ExtrudeGeometry(shape,{depth:h,bevelEnabled:false});g.rotateX(-Math.PI/2);const pos=g.attributes.position,uv=[];for(let i=0;i<pos.count;i++)uv.push(pos.getX(i)/2.4+pos.getY(i)/2.4,pos.getZ(i)/2.4+pos.getY(i)/2.4);g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setAttribute('sidewalkEdgeDistance',new THREE.Float32BufferAttribute(Array(pos.count).fill(1),1));const m=new THREE.Mesh(g,tileMaterial);m.position.y=upperLevel;m.name=name;m.receiveShadow=true;group.add(m);blockers.push(m);solids.push({ring,top:upperLevel+h});return m;};
  for(const [i,it] of plz.items.entries())prism(it.ring,it.kind==='planter'?plz.planterHeight:plz.benchHeight,'zhili-plaza-'+it.kind+'-'+i);
  prism(plz.skylight.outer,.18,'zhili-plaza-skylight-curb');
  const glass=new THREE.MeshStandardMaterial({color:0x9fd2e6,roughness:.15,metalness:.1,transparent:true,opacity:.45,side:THREE.DoubleSide}),pos=[];
  for(const cell of plz.skylight.cells){const cx=cell.reduce((s,p)=>s+p[0],0)/4,cz=cell.reduce((s,p)=>s+p[1],0)/4,apex=[cx,upperLevel+.18+.55,cz];for(let k=0;k<4;k++){const a=cell[k],b=cell[(k+1)%4];pos.push(a[0],upperLevel+.18,a[1],b[0],upperLevel+.18,b[1],...apex);}}
  const gg=new THREE.BufferGeometry();gg.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));gg.computeVertexNormals();const gm=new THREE.Mesh(gg,glass);gm.name='zhili-plaza-skylight-glass';group.add(gm);}
 const inRamp=(x,z)=>ringDistance(x,z,d.ramp)===0,inPad=(x,z)=>pads.some(p=>ringDistance(x,z,p.ring)===0),inWall=(x,z,r)=>d.walls.some(w=>ringDistance(x,z,w)<r);
 return{blockers,
  supportAt(x,z,currentY){if(inAda(x,z)){const h=adaH(x,z)+.08;return Math.abs(currentY-h)<.85?h:null;}if(inRamp(x,z)){const h=rampH(x,z)+.08;return Math.abs(currentY-h)<.85?h:null;}if(inPad(x,z)){const h=roadBase(x,z)+.08;return Math.abs(currentY-h)<.85?h:null;}return null;},
  blocked(x,z,r,currentY){if(ringDistance(x,z,ada.ring)<r&&currentY<adaH(x,z)-.35)return true;if(solids.some(p=>currentY>upperLevel-.6&&currentY<p.top-.1&&ringDistance(x,z,p.ring)<r))return true;return inWall(x,z,r)&&currentY<rampH(x,z)+d.wallAbove-.1;}};
}
