import {addPlayingCourts,addSportsGardens} from './facilities/sports-courts/renderer.js';
import {addHuanyuPlatform} from './facilities/huanyu-platform/renderer.js';
import {createSidewalkSurface} from './sidewalk-surface.js';
import {sidewalkPlan} from './data/sidewalk-plan.js';
import {addSidegate} from './facilities/s24-sidegate/renderer.js';
import {addCarports} from './facilities/s23-carport/renderer.js';
import {addConnections} from './connections.js';
import {ringDistance} from './terrain.js';
export function addSiteDetails(THREE,scene,campus,terrain,network){
 const group=new THREE.Group();group.name='campus-site-details';scene.add(group);
 const blockers=[],columns=[],waterMeshes=[];const material=(color)=>new THREE.MeshStandardMaterial({color,roughness:.9,side:THREE.DoubleSide});
 const cream=material(0xd4cfbf),steel=material(0x8fabb1),lineWhite=new THREE.LineBasicMaterial({color:0xffffff}),glass=new THREE.MeshStandardMaterial({color:0x7fa6b4,transparent:true,opacity:.35,side:THREE.DoubleSide});
 function box(w,h,d,x,y,z,mat,angle=0){const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);mesh.position.set(x,y,z);mesh.rotation.y=angle;mesh.castShadow=true;mesh.receiveShadow=true;group.add(mesh);return mesh;}
 function meshPositions(positions,mat,name){const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.computeVertexNormals();const mesh=new THREE.Mesh(geometry,mat);mesh.name=name;mesh.receiveShadow=true;group.add(mesh);return mesh;}
 function quad(p,positions){positions.push(...p[0],...p[2],...p[1],...p[1],...p[2],...p[3]);}
 const sidewalks=(sidewalkPlan.footprints||sidewalkPlan.triangles).map(points=>({points})),sidewalkSurface=createSidewalkSurface(network,sidewalkPlan,terrain.height);
 const tileCanvas=document.createElement('canvas');tileCanvas.width=tileCanvas.height=512;const tileCtx=tileCanvas.getContext('2d');
 // Slightly varied white ceramic, fine grout and restrained grey inserts.
 tileCtx.fillStyle='#e1e2dc';tileCtx.fillRect(0,0,512,512);
 for(let row=0;row<8;row++)for(let col=0;col<8;col++){const shade=223+(row*7+col*11)%5;tileCtx.fillStyle=`rgb(${shade},${shade+1},${shade-4})`;tileCtx.fillRect(col*64+1,row*64+1,62,62);}
 tileCtx.fillStyle='#c5c9c3';for(const [x,z] of [[128,64],[384,320]])tileCtx.fillRect(x,z,64,128);
 tileCtx.strokeStyle='#bfc4bf';tileCtx.lineWidth=1;for(let i=0;i<=512;i+=64){tileCtx.beginPath();tileCtx.moveTo(i,0);tileCtx.lineTo(i,512);tileCtx.moveTo(0,i);tileCtx.lineTo(512,i);tileCtx.stroke();}
 const tileTexture=new THREE.CanvasTexture(tileCanvas);tileTexture.wrapS=tileTexture.wrapT=THREE.RepeatWrapping;tileTexture.colorSpace=THREE.SRGBColorSpace;tileTexture.anisotropy=4;const tileMaterial=new THREE.MeshStandardMaterial({color:0xffffff,map:tileTexture,roughness:.95,side:THREE.DoubleSide});
 tileMaterial.onBeforeCompile=shader=>{shader.vertexShader='attribute float sidewalkEdgeDistance; varying float vSidewalkEdgeDistance;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvSidewalkEdgeDistance=sidewalkEdgeDistance;');shader.fragmentShader='varying float vSidewalkEdgeDistance;\n'+shader.fragmentShader;shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>','#include <map_fragment>\nfloat edgeBlend=1.0-smoothstep(0.15,0.19,vSidewalkEdgeDistance);diffuseColor.rgb=mix(diffuseColor.rgb,vec3(0.52,0.55,0.54),edgeBlend);');};tileMaterial.customProgramCacheKey=()=> 'natural-white-tiles-grey-edge-v3';
 const sidewalkGeometry=new THREE.BufferGeometry();sidewalkGeometry.setAttribute('position',new THREE.Float32BufferAttribute(sidewalkSurface.vertices,3));sidewalkGeometry.setAttribute('uv',new THREE.Float32BufferAttribute(sidewalkSurface.uv,2));sidewalkGeometry.setAttribute('sidewalkEdgeDistance',new THREE.Float32BufferAttribute(sidewalkSurface.edges,1));sidewalkGeometry.setIndex(sidewalkSurface.indices);sidewalkGeometry.computeVertexNormals();const sidewalk=new THREE.Mesh(sidewalkGeometry,tileMaterial);sidewalk.name='attached-sidewalks';sidewalk.receiveShadow=true;group.add(sidewalk);
 meshPositions(sidewalkSurface.curbPositions,material(0x89918d),'sidewalk-15cm-curbs');
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
 const facilityLabels=[],courtRoofs=[];
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
  const canopy=meshPositions(roof,steel.clone(),'canopy-'+court.facility+'-'+court.osm);canopy.castShadow=true;blockers.push(canopy);courtRoofs.push({mesh:canopy,roofY});
  if(court.playingCourts){addPlayingCourts(THREE,group,court,base);facilityLabels.push({name:court.name,x:cx,z:cz,y:roofY+2});continue;}
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
 const sportsGardens=addSportsGardens(THREE,group,campus,terrain);
 const sidegate=addSidegate(THREE,group,campus,network);blockers.push(...sidegate.blockers);
 const carports=addCarports(THREE,group,campus,network);blockers.push(...carports.blockers);columns.push(...carports.columns);
 const huanyu=addHuanyuPlatform(THREE,group,campus,terrain,network,tileMaterial);blockers.push(...huanyu.blockers);
 const connections=addConnections(THREE,group,campus,terrain,network,tileMaterial);
 const {bridgeLevel,courtyardLevel,bioLevel}=connections;blockers.push(...connections.blockers);
 // Guardhouse touches the flowerbed tip; the two barrier arms sit in separate lanes.
 const guard=campus.gatehouse;if(guard){const [x,z]=guard.center,y=network.surfaceHeight(x,z);box(guard.width,guard.height,guard.depth,x,y+guard.height/2,z,cream).name='entrance-guardhouse';box(guard.width+.8,.25,guard.depth+.8,x,y+guard.height,z,steel);for(const side of [-1,1])box(.04,1.35,guard.depth-2,x+side*(guard.width/2+.025),y+2,z,glass);for(const [gx,gz] of guard.gates){const gy=network.surfaceHeight(gx,gz);box(.35,1.1,.35,gx-2.8,gy+.55,gz,steel);for(let i=0;i<6;i++)box(.9,.12,.13,gx-2.25+i*.9,gy+1.1,gz,i%2?cream:material(0xb74732));}}
 return{group,sidewalks,blockers,columns,bridgeLevel,courtyardLevel,bioLevel,facilityLabels,waterMeshes,sidewalkSurface,sidewalkAt(x,z){return sidewalkSurface.heightAt(x,z);},update(now,camera){for(const {mesh,roofY}of courtRoofs){const above=camera&&camera.y>roofY+1;mesh.material.transparent=!!above;mesh.material.opacity=above ? .16 : 1;mesh.material.depthWrite=!above;mesh.castShadow=!above;}bump.offset.set(now*.000006,Math.sin(now*.0001)*.05);},blocked(x,z,r,y){return sportsGardens.blocked(x,z,r)||huanyu.blocked(x,z,r,y)||sidegate.blocked(x,z,r)||connections.solidBlocked(x,z,r,y)||(campus.gatehouse&&Math.abs(x-campus.gatehouse.center[0])<campus.gatehouse.width/2+r&&Math.abs(z-campus.gatehouse.center[1])<campus.gatehouse.depth/2+r)||columns.some(p=>Math.hypot(p.x-x,p.z-z)<r+p.radius);}};
}
