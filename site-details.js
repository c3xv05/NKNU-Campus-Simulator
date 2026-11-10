import {sidewalkSections} from './site-physics.js';
export function addSiteDetails(THREE,scene,campus,terrain,network){
 const group=new THREE.Group();group.name='campus-site-details';scene.add(group);
 const blockers=[],columns=[],waterMeshes=[];const material=(color)=>new THREE.MeshStandardMaterial({color,roughness:.9,side:THREE.DoubleSide});
 const cream=material(0xd4cfbf),steel=material(0x8fabb1),lineWhite=new THREE.LineBasicMaterial({color:0xffffff}),glass=new THREE.MeshStandardMaterial({color:0x7fa6b4,transparent:true,opacity:.35,side:THREE.DoubleSide});
 function box(w,h,d,x,y,z,mat,angle=0){const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);mesh.position.set(x,y,z);mesh.rotation.y=angle;mesh.castShadow=true;mesh.receiveShadow=true;group.add(mesh);return mesh;}
 function meshPositions(positions,mat,name){const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.computeVertexNormals();const mesh=new THREE.Mesh(geometry,mat);mesh.name=name;mesh.receiveShadow=true;group.add(mesh);return mesh;}
 function quad(p,positions){positions.push(...p[0],...p[2],...p[1],...p[1],...p[2],...p[3]);}
 const sidewalks=sidewalkSections(campus,network),sidewalkPositions=[];
 for(const section of sidewalks){const p=section.points.map(([x,z])=>[x,network.surfaceHeight(x,z)+.13,z]);quad([p[0],p[1],p[3],p[2]],sidewalkPositions);}
 const sidewalk=meshPositions(sidewalkPositions,cream,'attached-sidewalks');
 // Lake surfaces have depth in the terrain and physical exclusion in movement.
 const bumpCanvas=document.createElement('canvas');bumpCanvas.width=bumpCanvas.height=128;const ctx=bumpCanvas.getContext('2d'),image=ctx.createImageData(128,128);
 for(let y=0;y<128;y++)for(let x=0;x<128;x++){const v=128+Math.sin(x*.23+y*.11)*38+Math.sin(y*.37-x*.08)*25,i=(y*128+x)*4;image.data.set([v,v,v,255],i);}ctx.putImageData(image,0,0);
 const bump=new THREE.CanvasTexture(bumpCanvas);bump.wrapS=bump.wrapT=THREE.RepeatWrapping;
 for(const lake of campus.water){
  const shape=new THREE.Shape();lake.ring.forEach(([x,z],i)=>i?shape.lineTo(x,-z):shape.moveTo(x,-z));shape.closePath();
  for(const ring of lake.holes||[]){const path=new THREE.Path();ring.forEach(([x,z],i)=>i?path.lineTo(x,-z):path.moveTo(x,-z));path.closePath();shape.holes.push(path);}
  const geometry=new THREE.ShapeGeometry(shape);geometry.rotateX(-Math.PI/2);const p=geometry.attributes.position,uv=[];for(let i=0;i<p.count;i++)uv.push(p.getX(i)/12,p.getZ(i)/12);geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
  const mat=new THREE.MeshPhysicalMaterial({color:0x2c83ab,roughness:.24,metalness:.16,transparent:true,opacity:.83,bumpMap:bump,bumpScale:.11,clearcoat:.8,side:THREE.DoubleSide});
  const water=new THREE.Mesh(geometry,mat);water.position.y=terrain.platformHeight(lake)+.05;water.name='lake-'+lake.name;water.receiveShadow=true;group.add(water);waterMeshes.push(water);
 }
 // Court roofs, structural columns and playable court markings.
 const facilityLabels=[];
 for(const court of campus.courts){
  const ring=court.ring,cx=ring.reduce((s,p)=>s+p[0],0)/ring.length,cz=ring.reduce((s,p)=>s+p[1],0)/ring.length,base=terrain.platformHeight(court);
  const dx=ring[1][0]-ring[0][0],dz=ring[1][1]-ring[0][1],length=Math.hypot(dx,dz),ux=dx/length,uz=dz/length,vx=-uz,vz=ux;
  const projections=ring.map(([x,z])=>[(x-cx)*ux+(z-cz)*uz,(x-cx)*vx+(z-cz)*vz]);
  const minU=Math.min(...projections.map(p=>p[0]))-1,maxU=Math.max(...projections.map(p=>p[0]))+1,minV=Math.min(...projections.map(p=>p[1]))-1,maxV=Math.max(...projections.map(p=>p[1]))+1;
  const world=(u,v,y)=>[cx+u*ux+v*vx,y,cz+u*uz+v*vz],roofY=base+court.canopyHeight;
  for(const u of [minU,maxU])for(const v of [minV,maxV]){const [x,,z]=world(u,v,0);box(.25,court.canopyHeight,.25,x,base+court.canopyHeight/2,z,steel);columns.push({x,z,radius:.2});}
  const midV=(minV+maxV)/2,roof=[];
  quad([world(minU,minV,roofY),world(maxU,minV,roofY),world(minU,midV,roofY+1.1),world(maxU,midV,roofY+1.1)],roof);
  quad([world(minU,midV,roofY+1.1),world(maxU,midV,roofY+1.1),world(minU,maxV,roofY),world(maxU,maxV,roofY)],roof);
  const canopy=meshPositions(roof,steel,'canopy-'+court.facility+'-'+court.osm);canopy.castShadow=true;blockers.push(canopy);
  const line=[];const courtU=Math.min((maxU-minU)/2-2,court.sport==='basketball'?14:court.sport==='tennis'?11.8:9),courtV=Math.min((maxV-minV)/2-2,court.sport==='basketball'?7.5:court.sport==='tennis'?5.5:4.5);
  const corners=[[-courtU,-courtV],[courtU,-courtV],[courtU,courtV],[-courtU,courtV]];
  for(let i=0;i<4;i++){line.push(...world(...corners[i],base+.12),...world(...corners[(i+1)%4],base+.12));}line.push(...world(0,-courtV,base+.12),...world(0,courtV,base+.12));
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(line,3));group.add(new THREE.LineSegments(geometry,lineWhite));
  if(court.sport!=='basketball'){
   const netHeight=court.sport==='volleyball'?2.43:.95;
   for(const v of [-courtV,courtV]){const [x,,z]=world(0,v,0);box(.08,netHeight+.2,.08,x,base+(netHeight+.2)/2,z,steel);}
   for(let row=0;row<5;row++){const p=[...world(0,-courtV,base+netHeight-row*.15),...world(0,courtV,base+netHeight-row*.15)],g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));group.add(new THREE.Line(g,lineWhite));}
  }else for(const side of [-1,1]){
   const u=side*(courtU-.6),[x,,z]=world(u,0,0);box(.15,3.3,.15,x,base+1.65,z,steel);
   const board=box(.12,1.05,1.8,x,base+3.5,z,cream,Math.atan2(-uz,ux));
   const hoop=new THREE.Mesh(new THREE.TorusGeometry(.225,.025,5,20),new THREE.MeshBasicMaterial({color:0xea7036}));hoop.rotation.x=Math.PI/2;hoop.position.set(x-ux*side*.45,base+3.05,z-uz*side*.45);group.add(hoop);
  }
  facilityLabels.push({name:court.name,x:cx,z:cz,y:roofY+2});
 }
 // Horizontal connection: Zhili 1F and Gauss 2F share the same world elevation.
 const link=campus.levelLink,from=campus.places.find(p=>p.osm===link.from),bridgeLevel=terrain.platformHeight(from),a=link.line[0],b=link.line[1],dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz),yaw=Math.atan2(dx,dz),cx=(a[0]+b[0])/2,cz=(a[1]+b[1])/2;
 const floor=box(link.width,.18,length,cx,bridgeLevel,cz,cream,yaw);floor.name='zhili-1f-gauss-2f-connection';
 const roof=box(link.width+.4,.16,length+.5,cx,bridgeLevel+3,cz,steel,yaw);blockers.push(roof);
 for(const side of [-1,1]){const nx=dz/length*side*link.width/2,nz=-dx/length*side*link.width/2;box(.06,1.1,length,cx+nx,bridgeLevel+.65,cz+nz,glass,yaw);}
 // Floor bands and regularly sized windows make storeys legible at human scale.
 const windowTransforms=[];
 for(const building of [...campus.places,...campus.buildings].filter(a=>a.height)){
  const base=terrain.platformHeight(building),floors=building.floors||Math.max(1,Math.round(building.height/3.6)),fh=building.floorHeight||building.height/floors,ring=building.ring;
  if(base===undefined)continue;
  const lines=[];let area=0;for(let i=0;i<ring.length;i++){const a=ring[i],b=ring[(i+1)%ring.length];area+=a[0]*b[1]-b[0]*a[1];}
  for(let i=0;i<ring.length;i++){
   const a=ring[i],b=ring[(i+1)%ring.length],dx=b[0]-a[0],dz=b[1]-a[1],len=Math.hypot(dx,dz),sign=area>0?1:-1,nx=dz/(len||1)*sign,nz=-dx/(len||1)*sign;
   for(let f=1;f<floors;f++)lines.push(a[0]+nx*.04,base+f*fh,a[1]+nz*.04,b[0]+nx*.04,base+f*fh,b[1]+nz*.04);
   for(let s=2;s<len-1;s+=3.5)for(let f=0;f<floors;f++)windowTransforms.push({x:a[0]+dx*s/len+nx*.06,y:base+f*fh+fh*.53,z:a[1]+dz*s/len+nz*.06,angle:Math.atan2(-dz,dx)});
  }
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(lines,3));group.add(new THREE.LineSegments(g,new THREE.LineBasicMaterial({color:0xcbd3d3})));
 }
 if(windowTransforms.length){const windows=new THREE.InstancedMesh(new THREE.PlaneGeometry(1.3,1.6),new THREE.MeshStandardMaterial({color:0x547d92,roughness:.35,metalness:.15,side:THREE.DoubleSide}),windowTransforms.length),dummy=new THREE.Object3D();windowTransforms.forEach((p,i)=>{dummy.position.set(p.x,p.y,p.z);dummy.rotation.set(0,p.angle,0);dummy.updateMatrix();windows.setMatrixAt(i,dummy.matrix);});windows.name='building-storey-windows';group.add(windows);}
 return{group,sidewalks,blockers,columns,bridgeLevel,facilityLabels,waterMeshes,sidewalkAt(x,z){const r=network.nearest(x,z,true);return r&&(campus.sidewalkRoadIds||[]).includes(r.segment.route.osm)&&r.d>=r.width/2-.1&&r.d<=r.width/2+1.8?network.surfaceHeight(x,z)+.13:null;},update(now){bump.offset.set(now*.000006,Math.sin(now*.0001)*.05);},blocked(x,z,r){return columns.some(p=>Math.hypot(p.x-x,p.z-z)<r+p.radius);}};
}
