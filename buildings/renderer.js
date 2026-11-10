import {selectFront} from '../building-layout.js';
// Original geometry and procedural materials, derived from the supplied facade references.
// A building keeps one shell and a few instanced detail batches; distant details are hidden.
export async function loadBuildingProfiles(){const r=await fetch('./buildings/catalog.json');if(!r.ok)throw new Error('建築外觀資料載入失敗');return r.json();}
export function addBuildings(THREE,scene,campus,terrain,profiles,network){
 const group=new THREE.Group();group.name='campus-buildings';scene.add(group);const blockers=[],entries=[],materials=new Map(),cube=new THREE.BoxGeometry(1,1,1),dummy=new THREE.Object3D();
 function material(color,brick=false){const key=color+brick;if(materials.has(key))return materials.get(key);const m=new THREE.MeshStandardMaterial({color,roughness:.9});if(brick==='tiles'){const c=document.createElement('canvas');c.width=c.height=128;const ctx=c.getContext('2d');ctx.fillStyle='#d8d8d1';ctx.fillRect(0,0,128,128);ctx.strokeStyle='#a4a59c';ctx.lineWidth=1;ctx.strokeRect(.5,.5,127,127);m.map=new THREE.CanvasTexture(c);m.map.wrapS=m.map.wrapT=THREE.RepeatWrapping;m.map.repeat.set(1.5,1.5);m.map.colorSpace=THREE.SRGBColorSpace;}else if(brick){const c=document.createElement('canvas');c.width=128;c.height=64;const x=c.getContext('2d');x.fillStyle='#d4c6ba';x.fillRect(0,0,128,64);for(let row=0;row<8;row++)for(let col=-1;col<8;col++){x.fillStyle=['#9f6555','#ad7460','#a86c59'][(row+col+9)%3];x.fillRect(col*24+(row%2)*12,row*8,23,7);}m.map=new THREE.CanvasTexture(c);m.map.wrapS=m.map.wrapT=THREE.RepeatWrapping;m.map.repeat.set(.8,.8);m.map.colorSpace=THREE.SRGBColorSpace;}materials.set(key,m);return m;}
 function outline(ring){const s=new THREE.Shape();ring.forEach(([x,z],i)=>i?s.lineTo(x,-z):s.moveTo(x,-z));s.closePath();return s;}
 for(const a of [...campus.places,...campus.buildings].filter(a=>a.height)){
  const p=profiles[a.osm],base=terrain.platformHeight(a),xs=a.ring.map(v=>v[0]),zs=a.ring.map(v=>v[1]),cx=(Math.min(...xs)+Math.max(...xs))/2,cz=(Math.min(...zs)+Math.max(...zs))/2;
  if(p.style==='gatehouse'){const detail=new THREE.Group(),shell=scene.getObjectByName('entrance-guardhouse');group.add(detail);if(shell)blockers.push(shell);entries.push({id:p.id,cx,cz,detail,shell,limit:p.detailDistance||145});continue;}
  const wall=material(p.wall,['canteen','technology','library'].includes(p.style)?'tiles':['brick-frame','foresight','academic','dorm-two-tone','guesthouse'].includes(p.style)),accent=material(p.accent||p.wall),frame=material(p.frame),glass=material(p.glass),dark=material('#25363c'),awning=material('#477f7b');
  const lowerBase=Math.min(base-3,...a.ring.map(([x,z])=>(network?network.integratedHeight(x,z,terrain.height(x,z)):terrain.height(x,z))-1));
  const shape=outline(a.ring);shape.holes=(a.holes||[]).map(outline);const g=new THREE.ExtrudeGeometry(shape,{depth:a.height+base-Math.min(base-3,...a.ring.map(([x,z])=>(network?network.integratedHeight(x,z,terrain.height(x,z)):terrain.height(x,z))-1)),bevelEnabled:false});g.rotateX(-Math.PI/2);const shell=new THREE.Mesh(g,wall);shell.position.y=Math.min(base-3,...a.ring.map(([x,z])=>(network?network.integratedHeight(x,z,terrain.height(x,z)):terrain.height(x,z))-1));shell.name='building-shell-'+p.id;shell.castShadow=true;shell.receiveShadow=true;group.add(shell);blockers.push(shell);
  if(p.upperWall){const split=(p.splitAt||1)*(a.floorHeight||3.6),ug=new THREE.ExtrudeGeometry(shape,{depth:Math.max(.1,a.height-split),bevelEnabled:false});ug.rotateX(-Math.PI/2);const upper=new THREE.Mesh(ug,material(p.upperWall));upper.position.set(cx*(1-1.0005),base+split+.015,cz*(1-1.0005));upper.scale.set(1.0005,1,1.0005);upper.name='upper-plaster-'+p.id;group.add(upper);}
  const detail=new THREE.Group();detail.name='building-details-'+p.id;group.add(detail);const batches=new Map();
  function box(w,h,d,x,y,z,mat,angle=0){if(!batches.has(mat))batches.set(mat,[]);batches.get(mat).push({w,h,d,x,y,z,angle});}
  let area=0;for(let i=0;i<a.ring.length;i++){const u=a.ring[i],v=a.ring[(i+1)%a.ring.length];area+=u[0]*v[1]-v[0]*u[1];}
  const floors=a.floors||Math.max(1,Math.round(a.height/3.6)),fh=a.height/floors,edges=[];
  for(let i=0;i<a.ring.length;i++){
   const v=a.ring[i],q=a.ring[(i+1)%a.ring.length],dx=q[0]-v[0],dz=q[1]-v[1],len=Math.hypot(dx,dz),nx=dz/len*Math.sign(area),nz=-dx/len*Math.sign(area),angle=Math.atan2(-dz,dx);if(len<1)continue;
   const edge={v,q,dx,dz,len,nx,nz,angle};edges.push(edge);
   const at=(u,y,out=0)=>[v[0]+dx*u+nx*out,base+y,v[1]+dz*u+nz*out];
   const put=(w,h,d,u,y,out,mat)=>box(w,h,d,...at(u,y,out),mat,angle);
   for(let f=1;f<=floors;f++)put(len,.28,.24,.5,f*fh-.14,.07,frame);
   const bays=Math.max(1,Math.floor(len/4.6)),bay=len/bays;
   for(let j=0;j<=bays;j++)if(p.style!=='foresight')put(.28,a.height,.32,j/bays,a.height/2,.12,frame);
   for(let j=0;j<bays;j++)for(let f=0;f<floors;f++){
    const u=(j+.5)/bays,y=f*fh+fh*.53,wide=Math.min(bay-.75,['technology','library','dormitory'].includes(p.style)?3.4:p.style==='foresight'?3.2:2.4),h=fh*.49;
    put(wide+.18,h+.18,.14,u,y,.12,frame);put(wide,h,.16,u,y,.22,glass);put(.06,h,.06,u,y,.33,frame);put(wide,.06,.06,u,y,.33,frame);
    if(p.style==='foresight'){put(wide+.5,.12,1.05,u,y+h/2+.22,.52,awning);if(j%2===0)put(.6,.4,.4,u+.15/bays,f*fh+.7,.4,frame);}
   }
   if(['dorm-two-tone','dormitory','guesthouse'].includes(p.style)&&len>12){for(let f=1;f<floors;f++){put(len,.18,1.05,.5,f*fh,.55,frame);for(const y of [.45,.9])put(len,.06,.06,.5,f*fh+y,1.08,frame);for(let j=0;j<=bays;j++)put(.06,1,.06,j/bays,f*fh+.5,1.08,frame);}}
   if(p.style==='library'&&len>15){for(let j=0;j<bays;j++){const u=(j+.5)/bays,y=a.height*.6;if(j%2)put(.28,2.8,.22,u,y,.55,frame);else{put(1.3,.18,.22,u,y-1.25,.55,frame);put(1.3,.18,.22,u,y+1.25,.55,frame);for(const shift of [-.6,.6])put(.18,2.6,.22,u+shift/len,y,.55,frame);}}}
   if(p.style==='technology'&&len>16){put(len,.55,.7,.5,a.height-.1,.3,accent);for(let f=1;f<floors;f++)put(len,.15,.55,.5,f*fh+.12,.25,frame);}
   if(p.style==='biology'&&len>12){for(const u of [.08,.92]){put(1,a.height+1,.5,u,a.height/2,.3,accent);put(.38,a.height+1,.56,u+.025,a.height/2,.35,frame);}}
   if(p.style==='canteen'&&len>20)for(let j=0;j<bays;j++)put(.4,fh*2.3,1.5,(j+.5)/bays,a.height-fh,.7,frame);
  }
  // Pick the front facade from each building's own reference metadata.
  const front=selectFront(a,p,network);
  if(front&&p.showEntrance!==false){const e=front,x=(e.v[0]+e.q[0])/2,z=(e.v[1]+e.q[1])/2,w=Math.min(e.len*.72,12),entryBase=base+((p.entranceFloor||1)-1)*fh,place=(along,y,out)=>[x+e.dx/e.len*along+e.nx*out,entryBase+y,z+e.dz/e.len*along+e.nz*out];
   box(w,2.7,.2,...place(0,1.35,.25),dark,e.angle);for(const t of [-w/2,w/2])box(.6,3.6,2.4,...place(t,1.8,1.1),frame,e.angle);box(w+1,.45,3.2,...place(0,3.35,1.4),frame,e.angle);
   if(p.style==='canteen'){for(const side of [-1,1])box(.35,5,1,...place(side*1.7,a.height+1.8,.4),frame,e.angle);for(let i=0;i<4;i++)box(3.4,.25,1,...place(0,a.height-.5+i*1.35,.4),frame,e.angle);}
   if(p.style==='brick-frame'){for(const t of [-w/2,w/2])box(.4,fh*2.6,.8,...place(t,fh*2,.6),frame,e.angle);box(w+.7,.7,1.2,...place(0,fh*3.2,.7),frame,e.angle);}
   const canvas=document.createElement('canvas');canvas.width=1024;canvas.height=256;const ctx=canvas.getContext('2d');ctx.fillStyle='#8e8d80';ctx.fillRect(0,0,1024,256);ctx.fillStyle='#e9cb83';ctx.textAlign='center';ctx.font='bold 90px serif';ctx.fillText(p.sign,512,112);ctx.font='32px sans-serif';ctx.fillText(p.english,512,190);const tex=new THREE.CanvasTexture(canvas);tex.colorSpace=THREE.SRGBColorSpace;const sign=new THREE.Mesh(new THREE.PlaneGeometry(w,.25*w),new THREE.MeshBasicMaterial({map:tex,side:THREE.FrontSide}));sign.name='facade-sign-'+p.id;sign.position.set(...place(0,4.2,3.03));sign.rotation.y=e.angle+(Math.sign(area)>0?Math.PI:0);detail.add(sign);
  }
  if(p.style==='technology'&&front){const e=front,x=e.v[0]+e.nx*1.4,z=e.v[1]+e.nz*1.4,tower=new THREE.Mesh(new THREE.CylinderGeometry(2.1,2.1,a.height,12),wall);tower.position.set(x,base+a.height/2,z);detail.add(tower);for(let f=0;f<floors;f++){const band=new THREE.Mesh(new THREE.CylinderGeometry(2.12,2.12,1.35,12,1,true),glass);band.position.set(x,base+f*fh+fh*.55,z);detail.add(band);}}
  for(const [mat,items] of batches){const mesh=new THREE.InstancedMesh(cube,mat,items.length);mesh.name='facade-batch-'+p.id;for(let i=0;i<items.length;i++){const b=items[i];dummy.position.set(b.x,b.y,b.z);dummy.rotation.set(0,b.angle,0);dummy.scale.set(b.w,b.h,b.d);dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix);}mesh.computeBoundingSphere();mesh.castShadow=false;mesh.receiveShadow=true;detail.add(mesh);}
  entries.push({id:p.id,cx,cz,detail,shell,front,limit:p.detailDistance||145});
 }
 let previous=-Infinity;
 return{group,blockers,entries,update(x,z,now){if(now>=previous&&now-previous<180)return;previous=now;for(const e of entries)e.detail.visible=Math.hypot(x-e.cx,z-e.cz)<e.limit;}};
}
