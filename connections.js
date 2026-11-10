import {connectionRing} from './building-layout.js';
import {subtract} from './road-ground.js';
import {ringDistance} from './terrain.js';
import {projectOnLine} from './site-physics.js';
export function stairHeightAt(x,z,currentY,campus,terrain,network){const stairs=campus.bioConnection?.stairs;if(!stairs)return null;const p=projectOnLine(x,z,...stairs.line);if(p.t< -1e-7||p.t>1+1e-7||p.distance>stairs.width/2)return null;const from=campus.places.find(a=>a.osm===campus.bioConnection.from),top=terrain.platformHeight(from)+3.6,bottom=network.walkHeight(...stairs.line[1],terrain.height(...stairs.line[1])),step=Math.min(stairs.steps,Math.floor(Math.max(0,Math.min(1,p.t))*stairs.steps+1e-7)),height=top+(bottom-top)*step/stairs.steps+.08;return Math.abs(currentY-height)<.85?height:null;}
export function addConnections(THREE,group,campus,terrain,network){
 const concrete=new THREE.MeshStandardMaterial({color:0xb9b7a9,roughness:.95}),brick=new THREE.MeshStandardMaterial({color:0xa66b58,roughness:.95}),glass=new THREE.MeshStandardMaterial({color:0x475d65,roughness:.5}),steel=new THREE.MeshStandardMaterial({color:0x72888d,roughness:.7});const blockers=[];
 function box(w,h,d,x,y,z,mat,angle=0,name=''){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);m.position.set(x,y,z);m.rotation.y=angle;m.name=name;m.receiveShadow=true;group.add(m);return m;}
 function prism(ring,top,bottom,mat,name){const shape=new THREE.Shape();ring.forEach(([x,z],i)=>i?shape.lineTo(x,-z):shape.moveTo(x,-z));shape.closePath();const g=new THREE.ExtrudeGeometry(shape,{depth:top-bottom,bevelEnabled:false});g.rotateX(-Math.PI/2);const m=new THREE.Mesh(g,mat);m.position.y=bottom;m.name=name;m.receiveShadow=true;group.add(m);return m;}
 function ramp(line,width,start,end,name){const [a,b]=line,l=Math.hypot(b[0]-a[0],b[1]-a[1]),nx=-(b[1]-a[1])/l*width/2,nz=(b[0]-a[0])/l*width/2,points=[[a[0]+nx,start,a[1]+nz],[a[0]-nx,start,a[1]-nz],[b[0]+nx,end,b[1]+nz],[b[0]-nx,end,b[1]-nz]],g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute([...points[0],...points[2],...points[1],...points[1],...points[2],...points[3]],3));g.computeVertexNormals();const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:0xc7c3b4,side:THREE.DoubleSide,roughness:1}));m.name=name;group.add(m);}
 const link=campus.levelLink,from=campus.places.find(a=>a.osm===link.from),to=campus.places.find(a=>a.osm===link.to),bridgeLevel=terrain.platformHeight(from),courtyardLevel=bridgeLevel+3.6,linkRing=connectionRing(link),foundation=terrain.platformHeight(to)-4;
 prism(linkRing,bridgeLevel,foundation,brick,'zhili-gauss-solid-foundation');
 const [a,b]=link.line,dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz),angle=Math.atan2(dx,dz),cx=(a[0]+b[0])/2,cz=(a[1]+b[1])/2;
 // A built-in lower corridor and upper courtyard: no open space below the connection.
 for(const side of [-1,1]){const nx=dz/length*side*link.width/2,nz=-dx/length*side*link.width/2;box(.25,3.6,length,cx+nx,bridgeLevel+1.8,cz+nz,brick,angle);box(.28,1.3,length*.8,cx+nx,bridgeLevel+1.9,cz+nz,glass,angle);}
 const roof=prism(linkRing,courtyardLevel,courtyardLevel-.2,concrete,'zhili-gauss-upper-level');blockers.push(roof);
 if(campus.courtyard){prism(campus.courtyard.ring,courtyardLevel,courtyardLevel-.35,concrete,'teaching-courtyard-platform');ramp(campus.courtyard.ramp,campus.courtyard.width,terrain.height(...campus.courtyard.ramp[0]),courtyardLevel,'courtyard-access-ramp');}
 const bio=campus.bioConnection,bioLevel=terrain.platformHeight(campus.places.find(a=>a.osm===bio.from))+3.6,bioRing=connectionRing(bio),stairs=bio.stairs,stairRing=connectionRing(stairs),bottom=network.walkHeight(...stairs.line[1],terrain.height(...stairs.line[1]));
 const pieces=subtract(bioRing.map(([x,z])=>[x,0,z]),stairRing).map(p=>p.map(([x,,z])=>[x,z]));
 const bottomFoundation=Math.min(bottom-1,...bioRing.map(([x,z])=>terrain.height(x,z)-2));
 for(const [i,piece] of pieces.entries())prism(piece,bioLevel,bottomFoundation,concrete,'biology-solid-basement-'+i);
 if(bio.ramp)ramp(bio.ramp,bio.accessWidth,terrain.height(...bio.ramp[0]),bioLevel,'biology-access-ramp');
 const [sa,sb]=stairs.line,sdx=sb[0]-sa[0],sdz=sb[1]-sa[1],run=Math.hypot(sdx,sdz),yaw=Math.atan2(sdx,sdz),dummy=new THREE.Object3D(),geometry=new THREE.BoxGeometry(1,1,1),steps=new THREE.InstancedMesh(geometry,concrete,stairs.steps);
 for(let i=0;i<stairs.steps;i++){const t=(i+.5)/stairs.steps,h=bioLevel+(bottom-bioLevel)*i/stairs.steps,base=bottomFoundation-1;dummy.position.set(sa[0]+sdx*t,(h+base)/2,sa[1]+sdz*t);dummy.rotation.set(0,yaw,0);dummy.scale.set(stairs.width,h-base,run/stairs.steps+.005);dummy.updateMatrix();steps.setMatrixAt(i,dummy.matrix);}steps.name='biology-east-staircase';steps.receiveShadow=true;steps.computeBoundingSphere();group.add(steps);
 const normal=[-sdz/run,sdx/run];for(const side of [-1,1]){const start=new THREE.Vector3(sa[0]+normal[0]*side*stairs.width/2,bioLevel+1,sa[1]+normal[1]*side*stairs.width/2),end=new THREE.Vector3(sb[0]+normal[0]*side*stairs.width/2,bottom+1,sb[1]+normal[1]*side*stairs.width/2),vector=end.clone().sub(start),rail=new THREE.Mesh(new THREE.CylinderGeometry(.045,.045,vector.length(),6),steel);rail.position.copy(start).add(end).multiplyScalar(.5);rail.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),vector.normalize());group.add(rail);}
 for(const side of [-1,1])box(.22,2.5,.22,sb[0]+normal[0]*side*stairs.width/2,bottom+1.25,sb[1]+normal[1]*side*stairs.width/2,concrete);box(stairs.width+.3,.3,.5,sb[0],bottom+2.5,sb[1],concrete,Math.atan2(-sdz,sdx),'biology-east-exit');
 return{blockers,bridgeLevel,courtyardLevel,bioLevel,stairsBottom:bottom,solidBlocked(x,z,r,currentY=Infinity){
  if(ringDistance(x,z,stairRing)===0&&stairHeightAt(x,z,currentY,campus,terrain,network)===null)return true;
  if(ringDistance(x,z,bioRing)===0&&currentY<bioLevel-.6&&stairHeightAt(x,z,currentY,campus,terrain,network)===null)return true;
  if(ringDistance(x,z,linkRing)===0&&currentY<bridgeLevel-.5)return true;
  return false;
 }};
}
