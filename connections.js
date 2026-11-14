import {addTeachingCourtyard} from './facilities/teaching-courtyard/renderer.js';
import {accessStairs,stairBands,stairRing,supportOnStair,stairSurface,stairWidth} from './stair-layout.js';
import {connectionRing} from './building-layout.js';
import {subtract} from './road-ground.js';
import {ringDistance} from './terrain.js';
import {projectOnLine,platformHeightAt} from './site-physics.js';
export function stairHeightAt(x,z,currentY,campus,terrain,network){for(const stairs of accessStairs(campus,terrain,network)){const height=supportOnStair(x,z,currentY,stairs);if(height!==null)return height;}return null;}
export function addConnections(THREE,group,campus,terrain,network,tileMaterial){
 const concrete=new THREE.MeshStandardMaterial({color:0xb9b7a9,roughness:.95}),brick=new THREE.MeshStandardMaterial({color:0xa66b58,roughness:.95});const blockers=[];
 function box(w,h,d,x,y,z,mat,angle=0,name=''){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);m.position.set(x,y,z);m.rotation.y=angle;m.name=name;m.receiveShadow=true;group.add(m);return m;}
 function prism(ring,top,bottom,mat,name){const shape=new THREE.Shape();ring.forEach(([x,z],i)=>i?shape.lineTo(x,-z):shape.moveTo(x,-z));shape.closePath();const g=new THREE.ExtrudeGeometry(shape,{depth:top-bottom,bevelEnabled:false});g.rotateX(-Math.PI/2);const m=new THREE.Mesh(g,mat);m.position.y=bottom;m.name=name;m.receiveShadow=true;group.add(m);return m;}
 function ramp(line,width,start,end,name){const [a,b]=line,l=Math.hypot(b[0]-a[0],b[1]-a[1]),nx=-(b[1]-a[1])/l*width/2,nz=(b[0]-a[0])/l*width/2,points=[[a[0]+nx,start,a[1]+nz],[a[0]-nx,start,a[1]-nz],[b[0]+nx,end,b[1]+nz],[b[0]-nx,end,b[1]-nz]],g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute([...points[0],...points[2],...points[1],...points[1],...points[2],...points[3]],3));g.computeVertexNormals();const tiled=name==='courtyard-access-ramp';if(tiled){const positions=g.attributes.position,coords=[];for(let i=0;i<positions.count;i++)coords.push(positions.getX(i)/2.4,positions.getZ(i)/2.4);g.setAttribute('uv',new THREE.Float32BufferAttribute(coords,2));g.setAttribute('sidewalkEdgeDistance',new THREE.Float32BufferAttribute(Array(positions.count).fill(1),1));}const m=new THREE.Mesh(g,tiled?tileMaterial:new THREE.MeshStandardMaterial({color:0xc7c3b4,side:THREE.DoubleSide,roughness:1}));m.name=name;group.add(m);}
 const link=campus.levelLink,from=campus.places.find(a=>a.osm===link.from),to=campus.places.find(a=>a.osm===link.to),bridgeLevel=terrain.platformHeight(from),courtyardLevel=bridgeLevel+3.6,linkRing=connectionRing(link),foundation=terrain.platformHeight(to)-4;
 const teaching=(link.stairs||[]),cutPieces=(ring,cuts)=>cuts.reduce((pieces,cut)=>pieces.flatMap(p=>subtract(p.map(([x,z])=>[x,0,z]),cut).map(q=>q.map(([x,,z])=>[x,z]))),[ring]);
 for(const [i,piece] of cutPieces(linkRing,teaching.map(s=>stairRing(s))).entries())prism(piece,bridgeLevel-.25,foundation,brick,i?'zhili-gauss-solid-foundation-'+i:'zhili-gauss-solid-foundation');
 const plaza=addTeachingCourtyard(THREE,group,campus,terrain,tileMaterial);blockers.push(...plaza.blockers);
 if(campus.courtyard)ramp(campus.courtyard.ramp,campus.courtyard.width,network.walkHeight(...campus.courtyard.ramp[0],terrain.height(...campus.courtyard.ramp[0])),campus.courtyard.rampTargetFloor===1?bridgeLevel:courtyardLevel,'courtyard-access-ramp');
 const bio=campus.bioConnection,bioLevel=terrain.platformHeight(campus.places.find(a=>a.osm===bio.from))+3.6,bioRing=connectionRing(bio),stairs=bio.stairs,bioStairRing=stairRing(stairs),bottom=network.walkHeight(...stairs.line[1],terrain.height(...stairs.line[1]));
 const pieces=subtract(bioRing.map(([x,z])=>[x,0,z]),bioStairRing).map(p=>p.map(([x,,z])=>[x,z]));
 const bottomFoundation=Math.min(bottom-1,...bioRing.map(([x,z])=>terrain.height(x,z)-2));
 for(const [i,piece] of pieces.entries())prism(piece,bioLevel,bottomFoundation,concrete,'biology-solid-basement-'+i);
 if(bio.ramp)ramp(bio.ramp,bio.accessWidth,terrain.height(...bio.ramp[0]),bioLevel,'biology-access-ramp');
 const stairDefinitions=accessStairs(campus,terrain,network),planters=[],stairMaterial=new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,side:THREE.DoubleSide}),treadColor=new THREE.Color(0xc5c2b6),riserColor=new THREE.Color(0x888b80);
 // Batch the solid treads and flat intermediate landings into one mesh per staircase.
 for(const def of stairDefinitions){const positions=[],colors=[],base=Math.min(def.bottom-1,...stairRing(def).map(([x,z])=>terrain.height(x,z)-1));
  const triangle=(a,b,c,color)=>{for(const p of [a,b,c]){positions.push(...p);colors.push(...color.toArray());}},quad=(a,b,c,d,color)=>{triangle(a,b,c,color);triangle(a,c,d,color);};
  for(const band of stairBands(def)){const ring=stairRing(def,band.start,band.end),top=stairSurface(def,band.start),lip=top-.04,at=(p,y)=>[p[0],y,p[1]];
   // The pale riser lip is part of the solid mesh, never a coplanar overlay.
   quad(...ring.map(p=>at(p,top)),treadColor);quad(...[...ring].reverse().map(p=>at(p,base)),riserColor);
   for(let i=0;i<ring.length;i++){const a=ring[i],b=ring[(i+1)%ring.length];quad(at(a,base),at(b,base),at(b,lip),at(a,lip),riserColor);quad(at(a,lip),at(b,lip),at(b,top),at(a,top),treadColor);}}
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));geometry.computeVertexNormals();const mesh=new THREE.Mesh(geometry,stairMaterial);mesh.name=def.id==='biology'?'biology-east-staircase':def.id+'-staircase';mesh.receiveShadow=true;mesh.userData={steps:def.steps,flights:def.flights,landings:(def.flights||1)-1};group.add(mesh);
  const [a,b]=def.line,dx=b[0]-a[0],dz=b[1]-a[1],run=Math.hypot(dx,dz),yaw=Math.atan2(dx,dz),normal=[-dz/run,dx/run];
  // Low stepped cheek walls border each flight; the central walking line stays open.
  for(const band of stairBands(def).filter(b=>b.landing)){const t=(band.start+band.end)/2,h=stairSurface(def,t),w=stairWidth(def,t);for(const side of [-1,1])box(.45,.85,run*(band.end-band.start),a[0]+dx*t+normal[0]*side*(w/2+.25),h+.425,a[1]+dz*t+normal[1]*side*(w/2+.25),concrete,yaw,def.id+'-landing-sidewall');
   if(def.photoPlanters){const side=planters.length%2?1:-1,x=a[0]+dx*t+normal[0]*side*w*.32,z=a[1]+dz*t+normal[1]*side*w*.32;box(1.5,1,1.5,x,h+.5,z,concrete,0,'biology-stair-planter');box(1.2,.12,1.2,x,h+1.04,z,new THREE.MeshStandardMaterial({color:0x617b46,roughness:1}));planters.push({x,z,y:h,radius:1.05});}}
 }
 // Wide entrance lintel and recessed lobby between the two biology wings, facing S01.
 const [sa,sb]=stairs.line,run=Math.hypot(sb[0]-sa[0],sb[1]-sa[1]),normal=[-(sb[1]-sa[1])/run,(sb[0]-sa[0])/run],yaw=Math.atan2(sb[0]-sa[0],sb[1]-sa[1]);
 box(stairs.topWidth+1,.8,2,sa[0]-1.2,bioLevel+3.4,sa[1],concrete,yaw,'biology-central-entrance');
 for(const side of [-1,1])box(.65,3.1,.65,sa[0]+normal[0]*side*(stairs.topWidth/2+.2)-1.2,bioLevel+1.55,sa[1]+normal[1]*side*(stairs.topWidth/2+.2),concrete);
 const canvas=document.createElement('canvas');canvas.width=768;canvas.height=128;const ctx=canvas.getContext('2d');ctx.fillStyle='#b9b7a9';ctx.fillRect(0,0,768,128);ctx.fillStyle='#c9ad62';ctx.font='bold 70px serif';ctx.textAlign='center';ctx.fillText('生 科 大 樓',384,90);const sign=new THREE.Mesh(new THREE.PlaneGeometry(8,.85),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(canvas),side:THREE.DoubleSide}));sign.position.set(sa[0]-.15,bioLevel+3.4,sa[1]);sign.rotation.y=Math.PI/2;sign.name='biology-central-lintel-sign';group.add(sign);
 return{blockers,bridgeLevel,courtyardLevel,bioLevel,stairsBottom:bottom,solidBlocked(x,z,r,currentY=Infinity){
  if(plaza.blocked(x,z,r,currentY))return true;
  if(campus.courtyard.accessRampRing&&ringDistance(x,z,campus.courtyard.accessRampRing)===0&&platformHeightAt(x,z,currentY,campus,terrain,network)===null)return true;
  if(planters.some(p=>Math.hypot(x-p.x,z-p.z)<p.radius+r&&Math.abs(currentY-p.y)<2))return true;
  if(stairDefinitions.some(s=>ringDistance(x,z,stairRing(s))===0)&&stairHeightAt(x,z,currentY,campus,terrain,network)===null)return true;
  if(ringDistance(x,z,bioRing)===0&&currentY<bioLevel-.6&&stairHeightAt(x,z,currentY,campus,terrain,network)===null)return true;
  if(ringDistance(x,z,linkRing)===0&&currentY<bridgeLevel-.5&&stairHeightAt(x,z,currentY,campus,terrain,network)===null)return true;
  return false;
 }};
}
