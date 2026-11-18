import {createJiyuanSurface,JIYUAN_OSM} from './surface.js';
import {ringDistance} from '../../planar.js';
// Author detail dimensions in the original metres, then scale the whole model in XYZ.
// Inverse-transform compiled world vertices so the parent transform does not scale them twice.
export function unscaledRenderSurface(world,scale,pivot,ground){
 const point=([x,z])=>[pivot[0]+(x-pivot[0])/scale,pivot[1]+(z-pivot[1])/scale];
 const ring=r=>r.map(point),regions=r=>r.map(region=>region.map(ring));
 return{base:ground+(world.base-ground)/scale,floors:world.floors.map(f=>({...f,height:f.height/scale,level:ground+(f.level-ground)/scale,
  regions:regions(f.regions),floorTriangles:f.floorTriangles.map(ring),roofTriangles:f.roofTriangles.map(ring),walls:f.walls.map(ring),windows:f.windows.map(ring),entrances:f.entrances.map(ring),
  doors:f.doors.map(d=>({...d,line:ring(d.line)})),partitions:(f.partitions||[]).map(ring),shaftWalls:(f.shaftWalls||[]).map(ring),planters:(f.planters||[]).map(ring),cabinets:(f.cabinets||[]).map(c=>({...c,center:point(c.center)})),vents:(f.vents||[]).map(ring),spaces:f.spaces.map(s=>({...s,center:point(s.center),ring:ring(s.ring),triangles:s.triangles.map(ring),...(s.door?{door:ring(s.door)}:{}),...(s.fixtures?{fixtures:s.fixtures.map(v=>({...v,center:point(v.center)}))}:{})})),
  stairs:f.stairs.map(s=>({...s,route:ring(s.route),bounds:ring(s.bounds),treads:s.treads.map(t=>({...t,height:t.height/scale,ring:ring(t.ring)}))}))}))};
}
// The compiled plan drives both meshes and walking. No terrain/road source is changed here.
export function addJiyuanInterior(THREE,parent,campus,terrain,data){
 campus.jiyuanInterior=data;const worldSurface=createJiyuanSurface(campus,terrain),scale=data.modelScale||1,pivot=data.scalePivot||[0,0],ground=terrain.platformHeight(campus.places.find(b=>b.osm===JIYUAN_OSM)),surface=unscaledRenderSurface(worldSurface,scale,pivot,ground),base=surface.base;
 const group=new THREE.Group();group.name='jiyuan-interior';group.scale.setScalar(scale);group.position.set((1-scale)*pivot[0],(1-scale)*ground,(1-scale)*pivot[1]);parent.add(group);const blockers=[],props=new THREE.Group();props.name='jiyuan-interior-details';group.add(props);
 const cube=new THREE.BoxGeometry(1,1,1),dummy=new THREE.Object3D(),batches=new Map(),materials={};
 for(const[k,color]of Object.entries({wall:0xb87d62,inner:0xebe5d5,frame:0xb7b8ae,floor:0xd6d1c5,bath:0xc4d9d4,wood:0x8b6446,white:0xf5f2e8,steel:0x858f91,dark:0x29484e,water:0x78b0b1,glass:0x719eaa,landing:0xd5d2c6,partition:0xa9c3c4,cabinet:0xd9d4c4,planter:0xb9b2a4,soil:0x5b4634,shrub:0x4f7d3c}))materials[k]=new THREE.MeshStandardMaterial({color,roughness:.85,side:THREE.DoubleSide});
 // Slab undersides face the hemisphere ground colour; an unlit ceiling keeps eye-level views neutral.
 materials.ceiling=new THREE.MeshBasicMaterial({color:0xd9d4c8,side:THREE.DoubleSide});
 function ceiling(triangles,y,name){const positions=[];for(const tri of triangles)for(const[x,z]of [...tri].reverse())positions.push(x,y-.004,z);const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.computeVertexNormals();const m=new THREE.Mesh(g,materials.ceiling);m.name=name;props.add(m);}
 function box(w,h,d,x,y,z,key='inner',angle=0,level=0){const k=key+':'+level;if(!batches.has(k))batches.set(k,[]);batches.get(k).push({w,h,d,x,y,z,angle});}
 function segment(a,b,y,h,key='inner',width=.15,level=0){const dx=b[0]-a[0],dz=b[1]-a[1];box(Math.hypot(dx,dz),h,width,(a[0]+b[0])/2,y+h/2,(a[1]+b[1])/2,key,Math.atan2(-dz,dx),level);}
 function meshTriangles(triangles,y,bottom,key,name,owner=group){const positions=[];for(const tri of triangles){for(const[x,z]of tri)positions.push(x,y,z);if(bottom!==null)for(const[x,z]of [...tri].reverse())positions.push(x,bottom,z);}const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.computeVertexNormals();const m=new THREE.Mesh(g,materials[key]);m.name=name;m.receiveShadow=true;owner.add(m);blockers.push(m);return m;}
 function rail(a,b,y1,y2,level){const dx=b[0]-a[0],dz=b[1]-a[1],dy=y2-y1,length=Math.hypot(dx,dz,dy),key='steel:'+level;if(!batches.has(key))batches.set(key,[]);const q=new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(1,0,0),new THREE.Vector3(dx,dy,dz).normalize());batches.get(key).push({w:length,h:.06,d:.06,x:(a[0]+b[0])/2,y:(y1+y2)/2,z:(a[1]+b[1])/2,quaternion:q});}
 function label(text,x,y,z,angle=0,width=1.05){const canvas=document.createElement('canvas');canvas.width=256;canvas.height=96;const c=canvas.getContext('2d');c.fillStyle='#23434b';c.fillRect(0,0,256,96);c.fillStyle='#fff1cc';c.font='bold 46px sans-serif';c.textAlign='center';c.fillText(text,128,64);const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;const m=new THREE.Mesh(new THREE.PlaneGeometry(width,width*.375),new THREE.MeshBasicMaterial({map:texture,side:THREE.DoubleSide}));m.position.set(x,y,z);m.rotation.y=angle;props.add(m);return m;}
 // The foundation follows the actual shell; no concrete plinth is added outside it.
 let foundation=null;
 for(const region of surface.floors[0].regions){const s=new THREE.Shape();region[0].forEach(([x,z],i)=>i?s.lineTo(x,-z):s.moveTo(x,-z));s.closePath();const g=new THREE.ExtrudeGeometry(s,{depth:1,bevelEnabled:false});g.rotateX(-Math.PI/2);const m=new THREE.Mesh(g,materials.wall);m.name='jiyuan-plan-foundation';m.position.y=base-1.16;group.add(m);blockers.push(m);foundation??=m;}
 // Ground-floor planters (user: about 1m high) fill the drawing's outer outline beyond the upper-floor rooms.
 for(const ring of surface.floors[0].planters){const s=new THREE.Shape();ring.forEach(([x,z],i)=>i?s.lineTo(x,-z):s.moveTo(x,-z));s.closePath();
  for(const[key,bottom,top]of[['planter',base-1.16,base+1],['soil',base+1,base+1.005]]){const g=new THREE.ExtrudeGeometry(s,{depth:top-bottom,bevelEnabled:false});g.rotateX(-Math.PI/2);const m=new THREE.Mesh(g,materials[key]);m.name='jiyuan-planter';m.position.y=bottom;m.receiveShadow=true;group.add(m);blockers.push(m);}
  const xs=ring.map(p=>p[0]),zs=ring.map(p=>p[1]);for(let x=Math.min(...xs)+.45;x<Math.max(...xs);x+=.8)for(let z=Math.min(...zs)+.45;z<Math.max(...zs);z+=.8)if(ringDistance(x,z,ring)===0&&ring.every((a,i)=>{const b=ring[(i+1)%ring.length],dx=b[0]-a[0],dz=b[1]-a[1],t=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz||1)));return Math.hypot(x-a[0]-dx*t,z-a[1]-dz*t)>.32;}))box(.62,.42,.62,x,base+1.2,z,'shrub',((x*7+z*3)%1.6),0);}
 for(const f of surface.floors){
  meshTriangles(f.floorTriangles,f.level,f.level-.16,'floor','jiyuan-floor-'+f.floor);
  if(f.floor>1)ceiling(f.floorTriangles,f.level-.16,'jiyuan-ceiling-'+f.floor);
  for(const [i,[a,b]]of f.walls.entries())segment(a,b,f.level,f.lowWallIndices.includes(i)?1.05:2.84,f.exteriorWallIndices.includes(i)?'wall':'inner',.15,f.floor);
  // Ceiling/wall cap band ties each partition to the next slab without closing door openings.
  for(const d of f.doors){const[a,b]=d.line,dx=b[0]-a[0],dz=b[1]-a[1],l=Math.hypot(dx,dz),ang=Math.atan2(-dz,dx),nx=-dz/l,nz=dx/l;
   segment(a,b,f.level+2.24,.60,'frame',.18,f.floor);
   for(const p of[a,b])box(.055,2.24,.21,p[0],f.level+1.12,p[1],'wood',ang,f.floor);
   const m=[(a[0]+b[0])/2,(a[1]+b[1])/2];
   if(d.kind==='room')label(d.name,m[0]+nx*.13,f.level+2.48,m[1]+nz*.13,ang,Math.min(1,l*.92));
  }
  for(const [a,b]of f.entrances){segment(a,b,f.level+2.24,.6,'frame',.22,f.floor);for(const p of[a,b])box(.10,2.24,.24,p[0],f.level+1.12,p[1],'wood',0,f.floor);}
  for(const [a,b]of f.windows){segment(a,b,f.level,1,'wall',.18,f.floor);segment(a,b,f.level+2.15,.69,'wall',.18,f.floor);segment(a,b,f.level+1,1.15,'glass',.05,f.floor);for(const p of[a,b])box(.06,1.15,.22,p[0],f.level+1.575,p[1],'frame',0,f.floor);segment(a,b,f.level+1,.055,'frame',.24,f.floor);segment(a,b,f.level+2.12,.055,'frame',.24,f.floor);}
  // Shared-bath stalls: 1.9m panels lifted 0.12m with open doorways (no leaves yet), closed exhaust vent, 2x2 open cabinets (no doors) above urinals; pipe shafts are closed full-height boxes.
  for(const[a,b]of f.partitions)segment(a,b,f.level+.12,1.9,'partition',.04,f.floor);
  for(const[a,b]of f.shaftWalls)segment(a,b,f.level,2.84,'inner',.15,f.floor);
  for(const[a,b]of f.vents){segment(a,b,f.level+1.86,.42,'glass',.19,f.floor);for(const y of[1.84,2.3])segment(a,b,f.level+y,.04,'frame',.21,f.floor);for(const p of[a,b])box(.05,.5,.21,p[0],f.level+2.07,p[1],'frame',Math.atan2(a[1]-b[1],b[0]-a[0]),f.floor);}
  for(const c of f.cabinets){const[x,z]=c.center,a=c.angle,put=(w,h,d,dx,y,dz,key)=>{const u=dx*Math.cos(a)+dz*Math.sin(a),v=-dx*Math.sin(a)+dz*Math.cos(a);box(w,h,d,x+u,f.level+y,z+v,key,a,f.floor);};
   // Open 2x2 cubbies: back, outer frame, middle shelf and divider; front left open.
   put(.62,.62,.02,0,1.72,.13,'cabinet');for(const y of[1.42,1.72,2.02])put(.62,.02,.28,0,y,0,'cabinet');for(const x of[-.3,0,.3])put(.02,.62,.28,x,1.72,0,'cabinet');}
  for(const s of f.spaces){
   if(s.kind==='bathroom'){
    meshTriangles(s.triangles,f.level+.008,null,'bath','jiyuan-bath-floor-'+f.floor+'-'+s.id,props);
    for(const fx of s.fixtures){const[x,z]=fx.center,a=fx.angle,put=(w,h,d,dx,y,dz,key)=>{const u=dx*Math.cos(a)+dz*Math.sin(a),v=-dx*Math.sin(a)+dz*Math.cos(a);box(w,h,d,x+u,f.level+y,z+v,key,a,f.floor);};
     if(fx.kind==='squat'){put(.48,.05,.65,0,.025,0,'white');put(.23,.055,.4,0,.055,0,'dark');for(const side of[-1,1])put(.105,.02,.47,side*.18,.06,0,'steel');}
     if(fx.kind==='seat'){put(.36,.4,.46,0,.2,-.04,'white');put(.4,.05,.52,0,.425,-.06,'white');put(.26,.02,.32,0,.452,-.08,'water');put(.42,.4,.18,0,.68,.22,'white');put(.08,.02,.04,.12,.89,.22,'steel');}
     if(fx.kind==='showerhead'){put(.03,1.1,.03,0,1.45,.04,'steel');put(.17,.03,.17,0,2.0,-.05,'steel');put(.16,.1,.06,0,1.1,.03,'steel');put(.14,.01,.14,0,.012,-.32,'dark');}
     if(fx.kind==='urinal'){put(.38,.62,.32,0,.66,0,'white');put(.23,.38,.06,0,.65,-.17,'dark');put(.045,.36,.05,0,1.14,.06,'steel');}
     if(fx.kind==='sink'){put(.54,.13,.44,0,.83,0,'white');put(.34,.025,.25,0,.91,0,'water');put(.045,.2,.045,0,1.02,.13,'steel');put(.08,.75,.08,0,.4,0,'steel');}
     if(fx.kind==='shower'){put(.68,.025,.68,0,.018,0,'white');put(.035,1.8,.035,.22,1.06,.22,'steel');put(.25,.04,.15,.12,1.96,.22,'steel');put(.12,.06,.06,.22,1.1,.22,'steel');}
    }
   }else if(s.kind==='laundry'){
    const[x,z]=s.center;for(const side of[-1,1]){box(.62,.85,.62,x+side*.38,f.level+.425,z,'white',0,f.floor);box(.43,.025,.43,x+side*.38,f.level+.865,z,'steel',0,f.floor);}
   }
  }
  for(const stairs of f.stairs){
   for(const t of stairs.treads){const a=t.ring[0],b=t.ring[1],c=t.ring[3],w=Math.hypot(b[0]-a[0],b[1]-a[1]),d=Math.hypot(c[0]-a[0],c[1]-a[1]),x=(a[0]+t.ring[2][0])/2,z=(a[1]+t.ring[2][1])/2;box(w,t.flight<0?.16:.1875,d,x,f.level+t.height-(t.flight<0?.08:.09375),z,'landing',Math.atan2(a[1]-b[1],b[0]-a[0]),f.floor);}
   // Derive rail direction and height from the actual flight, including ground returns.
   for(const flight of [0,1]){const steps=stairs.treads.filter(t=>t.flight===flight);if(!steps.length)continue;const first=steps[0],last=steps.at(-1),rise=first.height-(flight===0?0:stairs.treads.filter(t=>t.flight===0).at(-1).height);
    for(const side of [0,1]){const forward=(last.ring[0][0]+last.ring[3][0]-first.ring[0][0]-first.ring[3][0])*(first.ring[0][0]-first.ring[3][0])+(last.ring[0][1]+last.ring[3][1]-first.ring[0][1]-first.ring[3][1])*(first.ring[0][1]-first.ring[3][1])>0,a=first.ring[forward?3-side:side],b=last.ring[forward?side:3-side],h1=first.height-rise,h2=last.height;for(let i=0;i<=8;i++){const u=i/8;box(.045,.92,.045,a[0]+(b[0]-a[0])*u,f.level+h1+(h2-h1)*u+.46,a[1]+(b[1]-a[1])*u,'steel',0,f.floor);}rail(a,b,f.level+h1+1,f.level+h2+1,f.floor);}
   }
   const p=stairs.route[0];label(f.floor+'F ↑ '+(f.floor+1)+'F',p[0],f.level+2.3,p[1],0,1.5);
  }
 }
 // Roof closes the uppermost rooms; lower ceilings are the underside of real slabs.
 meshTriangles(surface.floors[4].roofTriangles,base+15,base+14.82,'frame','jiyuan-roof');
 ceiling(surface.floors[4].roofTriangles,base+14.82,'jiyuan-ceiling-roof');
 for(const[key,items]of batches){const [mat,level]=key.split(':'),m=new THREE.InstancedMesh(cube,materials[mat],items.length);m.name='jiyuan-'+mat+'-'+level;for(let i=0;i<items.length;i++){const b=items[i];dummy.position.set(b.x,b.y,b.z);if(b.quaternion)dummy.quaternion.copy(b.quaternion);else dummy.rotation.set(0,b.angle||0,0);dummy.scale.set(b.w,b.h,b.d);dummy.updateMatrix();m.setMatrixAt(i,dummy.matrix);}m.computeBoundingSphere();m.receiveShadow=true;group.add(m);if(['inner','frame','landing'].includes(mat))blockers.push(m);}
 const[a,b]=surface.floors[0].entrances[0];label('霽遠樓',(a[0]+b[0])/2,base+2.6,(a[1]+b[1])/2,Math.atan2(a[1]-b[1],b[0]-a[0]),2.5);
 return{group,detail:props,shell:foundation,blockers,surface:worldSurface};
}
