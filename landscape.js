import {sidegateWalls} from './facilities/s24-sidegate/renderer.js';
import {sidewalkSides,SIDEWALK_WIDTH} from './sidewalk-layout.js';
import {offsetRing} from './building-layout.js';
import {ringDistance} from './terrain.js';
import {coverAt} from './landcover.js';
function bezier(a,b,c,d,t){const u=1-t;return[u*u*u*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t*t*t*d[0],u*u*u*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t*t*t*d[1]];}
export function entranceBed(){
 const x=-267.5,tip=[x,519],left=[x-9,492],right=[x+9,492],ring=[];
 const curves=[[tip,[x-4,510],[x-9,500],left],[left,[x-9,478],[x+9,478],right],[right,[x+9,500],[x+4,510],tip]];
 for(const curve of curves)for(let i=0;i<16;i++)ring.push(bezier(...curve,i/16));
 return ring;
}
export function createLandscapeLayout(campus,network,height){
 let seed=170491;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
 const bed=entranceBed(),areas=[...campus.places,...campus.buildings,...campus.water,...campus.courts,...(campus.pavedAreas||[]),...(campus.junctionFillets||[]),...(campus.sidewalkFrontages||[]),...(campus.pedestrianAreas||[]),...(campus.pedestrianLinks||[]),...(campus.sideGate?sidegateWalls(campus.sideGate).map(ring=>({ring})):[]),...(campus.courtyard?[campus.courtyard]:[]),...(campus.welcomeBoard?[campus.welcomeBoard]:[])].map(a=>{const xs=a.ring.map(p=>p[0]),zs=a.ring.map(p=>p[1]);return{...a,west:Math.min(...xs),east:Math.max(...xs),north:Math.min(...zs),south:Math.max(...zs)};});
 function eligible(x,z,margin=0){
  if(ringDistance(x,z,campus.boundary)!==0)return false;
  const road=network.nearest(x,z);if(road){const s=road.segment,side=Math.sign((x-s.a.x)*(-s.dz)+(z-s.a.z)*s.dx),walk=(campus.sidewalkRoadIds||[]).includes(s.route.osm)&&sidewalkSides(campus,s.route.osm).includes(side)?SIDEWALK_WIDTH:0;if(road.d<road.width/2+walk+margin)return false;}
  if(ringDistance(x,z,bed)<1+margin)return false;
  return !areas.some(a=>x>=a.west-margin&&x<=a.east+margin&&z>=a.north-margin&&z<=a.south+margin&&ringDistance(x,z,a.ring)<margin+.01);
 }
 const trees=[],flowers=[],weeds=[];
 for(let z=-545;z<535;z+=9)for(let x=-410;x<425;x+=9){
  const px=x+(random()-.5)*7,pz=z+(random()-.5)*7;
  if(coverAt(px,pz)==='forest'&&eligible(px,pz,3))trees.push({x:px,z:pz,y:height(px,pz),size:.85+random()*.65,tint:random()});
 }
 for(let z=185;z<530;z+=2.8)for(let x=-240;x< -50;x+=2.4){
  const px=x+(random()-.5)*.6,pz=z+(random()-.5)*.5;
  if(coverAt(px,pz)==='flowers'&&eligible(px,pz,.8))flowers.push({x:px,z:pz,y:height(px,pz),size:.6+random()*.4,tint:Math.floor((x+245)/13)%3});
 }
 for(let z=-480;z<500;z+=5)for(let x=-400;x<425;x+=5){
  const px=x+(random()-.5)*4,pz=z+(random()-.5)*4;
  if(coverAt(px,pz)==='weeds'&&eligible(px,pz,.5))weeds.push({x:px,z:pz,y:height(px,pz),size:.6+random()*.9,tint:random()});
 }
 for(let z=483;z<519;z+=1.1)for(let x=-277;x< -258;x+=1.1)if(ringDistance(x,z,bed)===0)flowers.push({x,z,y:height(x,z)+.2,size:.65,tint:(Math.round(x+z)%3+3)%3});
 const wall=[]; // Retaining walls removed at the user’s request.
 const treeCells=new Map();for(const tree of trees){const key=`${Math.floor(tree.x/15)},${Math.floor(tree.z/15)}`;if(!treeCells.has(key))treeCells.set(key,[]);treeCells.get(key).push(tree);}
 function blocked(x,z,radius=.5){
  if(ringDistance(x,z,bed)<radius)return true;
  const cx=Math.floor(x/15),cz=Math.floor(z/15);
  for(let iz=cz-1;iz<=cz+1;iz++)for(let ix=cx-1;ix<=cx+1;ix++)if((treeCells.get(`${ix},${iz}`)||[]).some(t=>Math.hypot(x-t.x,z-t.z)<radius+.25*t.size))return true;
  return wall.some(({a,b})=>{const dx=b.x-a.x,dz=b.z-a.z,t=Math.max(0,Math.min(1,((x-a.x)*dx+(z-a.z)*dz)/(dx*dx+dz*dz||1)));return Math.hypot(x-a.x-dx*t,z-a.z-dz*t)<radius+.3;});
 }
 return{trees,flowers,weeds,wall,bed,blocked};
}
export function addLandscape(THREE,scene,layout,height){
 const group=new THREE.Group();group.name='campus-landscape';scene.add(group);const dummy=new THREE.Object3D();
 const material=(color)=>new THREE.MeshStandardMaterial({color,roughness:1});
 function instances(name,geometry,mat,items,transform,color){
  if(!items.length)return;
  const mesh=new THREE.InstancedMesh(geometry,mat,items.length);mesh.name=name;
  items.forEach((item,i)=>{dummy.position.set(0,0,0);dummy.rotation.set(0,0,0);dummy.scale.set(1,1,1);transform(dummy,item,i);dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix);if(color)mesh.setColorAt(i,new THREE.Color(color(item)));});
  mesh.instanceMatrix.needsUpdate=true;if(mesh.instanceColor)mesh.instanceColor.needsUpdate=true;mesh.receiveShadow=true;mesh.castShadow=name==='tree-trunks';group.add(mesh);return mesh;
 }
 instances('tree-trunks',new THREE.CylinderGeometry(.19,.32,1,5),material(0x6c5540),layout.trees,(d,t)=>{d.position.set(t.x,t.y+2.2*t.size,t.z);d.scale.set(t.size,4.4*t.size,t.size);});
 const crowns=layout.trees.flatMap(t=>[t,{...t,x:t.x+1.1*t.size,z:t.z-.8*t.size,y:t.y+1.5*t.size,size:t.size*.8}]);
 const canopy=instances('forest-canopies',new THREE.SphereGeometry(1,7,5),material(0xffffff),crowns,(d,t)=>{d.position.set(t.x,t.y+5*t.size,t.z);d.scale.set(3*t.size,3.3*t.size,2.8*t.size);},t=>new THREE.Color().setHSL(.29+t.tint*.08,.3,.19+t.tint*.08));
 if(canopy){
  const fades=new THREE.InstancedBufferAttribute(new Float32Array(crowns.length).fill(1),1);
  canopy.geometry.setAttribute('instanceFade',fades);canopy.material.alphaHash=true;
  canopy.material.onBeforeCompile=shader=>{
   shader.vertexShader='attribute float instanceFade; varying float vCanopyFade;\n'+shader.vertexShader;
   shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvCanopyFade=instanceFade;');
   shader.fragmentShader='varying float vCanopyFade;\n'+shader.fragmentShader;
   shader.fragmentShader=shader.fragmentShader.replace('#include <alphahash_fragment>','if(vCanopyFade<0.01)discard;\ndiffuseColor.a *= vCanopyFade;\n#include <alphahash_fragment>');
  };
  canopy.material.customProgramCacheKey=()=> 'canopy-view-fade-v1';
  group.userData.updateView=(camera,focus)=>{
   const dx=camera.x-focus.x,dy=camera.y-focus.y,dz=camera.z-focus.z,length=dx*dx+dy*dy+dz*dz;
   let changed=false;
   crowns.forEach((t,i)=>{
    const y=t.y+5*t.size,vx=t.x-focus.x,vy=y-focus.y,vz=t.z-focus.z;
    const u=Math.max(0,Math.min(1,(vx*dx+vy*dy+vz*dz)/(length||1)));
    const distance=Math.hypot(vx-dx*u,vy-dy*u,vz-dz*u);
    const next=distance<3.7*t.size+1?0:1;
    if(fades.getX(i)!==next){fades.setX(i,next);changed=true;}
   });if(changed)fades.needsUpdate=true;
  };
 }
 instances('flower-stems',new THREE.CylinderGeometry(.025,.03,1,3),material(0x5d7941),layout.flowers,(d,f)=>{d.position.set(f.x,f.y+.35*f.size,f.z);d.scale.set(1,.7*f.size,1);});
 instances('flower-heads',new THREE.IcosahedronGeometry(1,0),material(0xffffff),layout.flowers,(d,f)=>{d.position.set(f.x,f.y+.7*f.size,f.z);d.scale.set(.3*f.size,.15*f.size,.3*f.size);},f=>[0xf2c94c,0xe798bb,0xa69bd8][f.tint]);
 const grass=new THREE.BufferGeometry();grass.setAttribute('position',new THREE.Float32BufferAttribute([-.2,0,0,.2,0,0,0,.55,0,0,0,-.2,0,0,.2,0,.4,0],3));grass.computeVertexNormals();
 instances('wild-grass',grass,new THREE.MeshStandardMaterial({color:0xffffff,side:THREE.DoubleSide,roughness:1}),layout.weeds,(d,w)=>{d.position.set(w.x,w.y,w.z);d.rotation.y=w.tint*Math.PI;d.scale.setScalar(w.size);},w=>new THREE.Color().setHSL(.19+w.tint*.08,.28,.35+w.tint*.12));
 const wallVertices=[];
 for(const {a,b,ha,hb} of layout.wall){
  const p=[a.x,ha-.5,a.z],q=[b.x,hb-.5,b.z],r=[a.x,ha+2.8,a.z],s=[b.x,hb+2.8,b.z];wallVertices.push(...p,...r,...q,...q,...r,...s);
 }
 if(wallVertices.length){const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(wallVertices,3));geometry.computeVertexNormals();const wall=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({color:0x999b92,side:THREE.DoubleSide,roughness:1}));wall.name='A1-retaining-wall';wall.receiveShadow=true;group.add(wall);}
 const shape=new THREE.Shape();layout.bed.forEach(([x,z],i)=>i?shape.lineTo(x,-z):shape.moveTo(x,-z));shape.closePath();
 const outlineGeometry=new THREE.ShapeGeometry(shape);outlineGeometry.rotateX(-Math.PI/2);
 const position=outlineGeometry.attributes.position,index=outlineGeometry.index,soilPositions=[];
 function soilTriangle(a,b,c,depth){
  if(depth){const mid=(p,q)=>[(p[0]+q[0])/2,(p[1]+q[1])/2],ab=mid(a,b),bc=mid(b,c),ca=mid(c,a);soilTriangle(a,ab,ca,depth-1);soilTriangle(ab,b,bc,depth-1);soilTriangle(ca,bc,c,depth-1);soilTriangle(ab,bc,ca,depth-1);return;}
  for(const [x,z] of [a,b,c])soilPositions.push(x,height(x,z)+.18,z);
 }
 for(let i=0;i<index.count;i+=3){const points=[];for(let k=0;k<3;k++){const v=index.getX(i+k);points.push([position.getX(v),position.getZ(v)]);}soilTriangle(...points,3);}
 outlineGeometry.dispose();const soilGeometry=new THREE.BufferGeometry();soilGeometry.setAttribute('position',new THREE.Float32BufferAttribute(soilPositions,3));soilGeometry.computeVertexNormals();
 const bed=new THREE.Mesh(soilGeometry,material(0x795742));bed.name='south-pointing-teardrop-bed';group.add(bed);
 // The kerb uses the same polygon as the road hole; no spline overshoot or gap.
 const inner=offsetRing(layout.bed,-.16),outer=offsetRing(layout.bed,.16),vertices=[];
 function kerbQuad(a,b,c,d){vertices.push(...a,...c,...b,...b,...c,...d);}
 for(let i=0;i<inner.length;i++){const j=(i+1)%inner.length,at=(p,h)=>[p[0],height(...p)+h,p[1]];kerbQuad(at(inner[i],.22),at(outer[i],.22),at(inner[j],.22),at(outer[j],.22));kerbQuad(at(outer[i],-.03),at(outer[i],.22),at(outer[j],-.03),at(outer[j],.22));kerbQuad(at(inner[i],-.03),at(inner[i],.22),at(inner[j],-.03),at(inner[j],.22));}
 const kg=new THREE.BufferGeometry();kg.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));kg.computeVertexNormals();const kerb=new THREE.Mesh(kg,new THREE.MeshStandardMaterial({color:0xcec6b4,roughness:1,side:THREE.DoubleSide}));kerb.name='flowerbed-kerb';group.add(kerb);
 return group;
}
