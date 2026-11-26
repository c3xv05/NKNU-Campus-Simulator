import {observedRegionAt,flowerPalette,observedLandscape} from './observed-landscape.js';
import {r04RegionAt,r04Vegetation} from './r04-vegetation.js';
import {perimeterWallRings} from './facilities/s24-sidegate/west-wall.js';
import {sidegateWalls} from './facilities/s24-sidegate/renderer.js';
import {sidewalkSides,SIDEWALK_WIDTH} from './sidewalk-layout.js';
import {offsetRing} from './building-layout.js';
import {ringDistance} from './terrain.js';
import {coverAt} from './landcover.js';
import {landscapeSeedAreas} from './data/landscape-seed-areas.js';
import {createTreeSpecies,treeSpeciesIndex,treeCrownPalette} from './tree-models.js';
function bezier(a,b,c,d,t){const u=1-t;return[u*u*u*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t*t*t*d[0],u*u*u*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t*t*t*d[1]];}
export function entranceBed(){
 const x=-267.5,tip=[x,519],left=[x-9,492],right=[x+9,492],ring=[];
 const curves=[[tip,[x-4,510],[x-9,500],left],[left,[x-9,478],[x+9,478],right],[right,[x+9,500],[x+4,510],tip]];
 for(const curve of curves)for(let i=0;i<16;i++)ring.push(bezier(...curve,i/16));
 return ring;
}
// The seeded plant sequence is generated with a FROZEN copy of the exclusion areas (data/landscape-seed-areas.js, taken
// before the 2026-11 relocations of Jiyuan / 歸燕食巢 / 飛燕 / 詠絮樓) so that moving buildings or paths cannot shift the
// random draws of every later tree. Plants that conflict with the CURRENT areas are removed afterwards. Do not overwrite the snapshot.
export function landscapeAreas(campus){return [...(campus.campusTransitions||[]).flatMap(a=>a.regions.map(([ring])=>({ring}))),...(campus.bioConnection.corridor?.regions||[]).map(([ring])=>({ring})),...(campus.gaussStop?[campus.gaussStop]:[]),...(campus.grassParking?[campus.grassParking]:[]),...(campus.courtParking?.entrance?[campus.courtParking.entrance]:[]),...(campus.yongxuLandscape?[campus.yongxuLandscape.lawn]:[]),...(campus.huanyuAccess?[campus.huanyuAccess,campus.huanyuAccess.ramp]:[]),campus.bioConnection.stairs,...(campus.bioConnection.sewageRoom?[{ring:campus.bioConnection.sewageRoom.undercroft}]:[]),...(campus.bioConnection.sideStairs||[]).flatMap(s=>[{ring:s.well},...s.pieces.map(p=>({ring:p.ring}))]),...(campus.bioConnection.corridor?.deckRing?[{ring:campus.bioConnection.corridor.deckRing}]:[]),...(campus.bioConnection.eastLanding?.sidePlanters||[]).map(ring=>({ring})),...(campus.levelLink.stairs||[]),...(campus.courtyard.stairs||[]),...campus.places,...campus.buildings,...campus.water,...campus.courts,...(campus.sportsAccess?.surfaces||[]).flatMap(a=>a.regions.map(([ring])=>({ring}))),...(campus.sportsGardens||[]),...(campus.pavedAreas||[]),...(campus.junctionFillets||[]),...(campus.sidewalkFrontages||[]),...(campus.pedestrianAreas||[]),...(campus.pedestrianLinks||[]),...perimeterWallRings(campus.perimeterWalls).map(ring=>({ring})),...(campus.sideGate?sidegateWalls(campus.sideGate).map(ring=>({ring})):[]),...(campus.courtyard?[campus.courtyard]:[]),...(campus.levelLink?.ring?[campus.levelLink]:[]),...(campus.welcomeBoard?[campus.welcomeBoard]:[])].map(a=>{const xs=a.ring.map(p=>p[0]),zs=a.ring.map(p=>p[1]);return{...a,west:Math.min(...xs),east:Math.max(...xs),north:Math.min(...zs),south:Math.max(...zs)};});}
export function createLandscapeLayout(campus,network,height){
 let seed=170491;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
 const bed=entranceBed(),areas=landscapeSeedAreas,currentAreas=landscapeAreas(campus),removedPaths=(campus.removeFootpaths||[]).map(r=>r.line);
 function eligible(x,z,margin=0,list=areas){
  if(ringDistance(x,z,campus.boundary)!==0)return false;
  // Footpaths removed later (campus.removeFootpaths) still take part in the SEEDED sequence as the nearest 'road' (width 2, no sidewalk),
  // so removing a path never shifts every later random plant; the final filter below uses the current network only.
  let road=network.nearest(x,z);
  if(list===areas&&removedPaths.length&&!(road&&!road.segment.route.style.path&&road.d<=road.width/2+1e-6)){   // same ranking as roads.js nearest(): distance to the pavement edge, 24 m buckets (+13 m margin)
   const cell=24,cx=Math.floor(x/cell),cz=Math.floor(z/cell),own=road?Math.max(0,road.d-road.width/2)+road.d*.001:Infinity;let best=null;
   for(const l of removedPaths)for(let i=0;i<l.length-1;i++){const a=l[i],b=l[i+1];
    if(Math.floor((Math.min(a[0],b[0])-13)/cell)>cx||Math.floor((Math.max(a[0],b[0])+13)/cell)<cx||Math.floor((Math.min(a[1],b[1])-13)/cell)>cz||Math.floor((Math.max(a[1],b[1])+13)/cell)<cz)continue;
    const dx=b[0]-a[0],dz=b[1]-a[1],q=dx*dx+dz*dz;if(q<1e-6)continue;const u=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/q)),d=Math.hypot(x-a[0]-dx*u,z-a[1]-dz*u),score=Math.max(0,d-1)+d*.001;if(!best||score<best.score)best={d,score};}
   if(best&&best.score<own){if(best.d<1+margin)return false;road=null;}   // a removed footpath was the nearest 'road': width 2, no sidewalk
  }
  if(road){const s=road.segment,side=Math.sign((x-s.a.x)*(-s.dz)+(z-s.a.z)*s.dx),walk=(campus.sidewalkRoadIds||[]).includes(s.route.osm)&&sidewalkSides(campus,s.route.osm).includes(side)?SIDEWALK_WIDTH:0;if(road.d<road.width/2+walk+margin)return false;}
  if(ringDistance(x,z,bed)<1+margin)return false;
  return !list.some(a=>x>=a.west-margin&&x<=a.east+margin&&z>=a.north-margin&&z<=a.south+margin&&ringDistance(x,z,a.ring)<margin+.01);
 }
 const trees=[],flowers=[],weeds=[];
 for(let z=-545;z<535;z+=9)for(let x=-410;x<425;x+=9){
  const px=x+(random()-.5)*7,pz=z+(random()-.5)*7;
  if(coverAt(px,pz,true)==='forest'&&r04RegionAt(px,pz,true)?.category!=='forest'&&observedRegionAt(px,pz)!=='R09'&&eligible(px,pz,3))trees.push({x:px,z:pz,y:height(px,pz),size:.85+random()*.65,tint:random()});
 }
 for(let z=-305;z<530;z+=r04Vegetation.forestSpacing)for(let x=-420;x< -25;x+=r04Vegetation.forestSpacing){const px=x+(random()-.5)*4,pz=z+(random()-.5)*4;if(r04RegionAt(px,pz,true)?.category==='forest'&&eligible(px,pz,3))trees.push({x:px,z:pz,y:height(px,pz),size:1+random()*.6,tint:random()});}
 for(let z=-520;z< -9;z+=observedLandscape.r09.spacing)for(let x=-350;x<20;x+=observedLandscape.r09.spacing){const px=x+(random()-.5)*4,pz=z+(random()-.5)*4;if(observedRegionAt(px,pz)==='R09'&&eligible(px,pz,3))trees.push({x:px,z:pz,y:height(px,pz),size:1+random()*.6,tint:random()});}
 let flowerSeed=observedLandscape.r02.seed;const flowerRandom=()=>{flowerSeed=(Math.imul(flowerSeed,1664525)+1013904223)>>>0;return flowerSeed/4294967296;};const flowerCells=new Map(),flowerCell=observedLandscape.r02.minimumSpacing;for(let attempt=0,planted=0;attempt<90000&&planted<observedLandscape.r02.count;attempt++){const px=-306+flowerRandom()*293,pz=87+flowerRandom()*391;if(observedRegionAt(px,pz)!=='R02'||!eligible(px,pz,.65))continue;const ix=Math.floor(px/flowerCell),iz=Math.floor(pz/flowerCell);let near=false;for(let a=-1;a<=1;a++)for(let b=-1;b<=1;b++)for(const f of flowerCells.get((ix+a)+','+(iz+b))||[])if(Math.hypot(px-f.x,pz-f.z)<flowerCell)near=true;if(near)continue;const f={x:px,z:pz,y:height(px,pz),size:.55+flowerRandom()*.85,tint:Math.floor(flowerRandom()*flowerPalette.length),angle:flowerRandom()*Math.PI*2};flowers.push(f);const key=ix+','+iz;if(!flowerCells.has(key))flowerCells.set(key,[]);flowerCells.get(key).push(f);planted++;}
 for(let z=-480;z<500;z+=5)for(let x=-400;x<425;x+=5){
  const px=x+(random()-.5)*4,pz=z+(random()-.5)*4;
  if(coverAt(px,pz,true)==='weeds'&&eligible(px,pz,.5))weeds.push({x:px,z:pz,y:height(px,pz),size:.6+random()*.9,tint:random()});
 }
 for(let z=483;z<519;z+=1.1)for(let x=-277;x< -258;x+=1.1)if(ringDistance(x,z,bed)===0)flowers.push({x,z,y:height(x,z)+.2,size:.65,tint:(Math.round(x+z)%3+3)%3});
 const wall=[]; // Retaining walls removed at the user’s request.
 // Preserve the seeded campus layout: remove only plants crossing the new Jiyuan shell.
 // Filtering after generation avoids shifting every later random tree/flower in the campus.
 const interiorRings=(campus.jiyuanInterior?.floors[0].regions||[]).map(r=>r[0]);
 if(interiorRings.length)for(const [items,margin]of [[trees,t=>3.6*t.size],[flowers,()=>.35],[weeds,()=>.35]])for(let i=items.length-1;i>=0;i--)if(interiorRings.some(r=>ringDistance(items[i].x,items[i].z,r)<margin(items[i])))items.splice(i,1);
 // Remove seeded plants that conflict with the current (relocated) buildings, walkways and cover.
 for(let i=trees.length-1;i>=0;i--)if(coverAt(trees[i].x,trees[i].z)!=='forest'||!eligible(trees[i].x,trees[i].z,3,currentAreas))trees.splice(i,1);
 for(let i=weeds.length-1;i>=0;i--)if(coverAt(weeds[i].x,weeds[i].z)!=='weeds'||!eligible(weeds[i].x,weeds[i].z,.5,currentAreas))weeds.splice(i,1);
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
 // Soft rounded forest: several species, each with instanced trunks and faceted crowns.
 const species=createTreeSpecies(THREE),bySpecies=species.map(()=>[]);for(const t of layout.trees)bySpecies[treeSpeciesIndex(t,species)].push(t);
 const trunkMaterial=new THREE.MeshStandardMaterial({color:0x7a5c42,roughness:1});
 const crownMaterial=new THREE.MeshStandardMaterial({color:0xffffff,roughness:.9});crownMaterial.alphaHash=true;
 crownMaterial.onBeforeCompile=shader=>{
  shader.vertexShader='attribute float instanceFade; varying float vCanopyFade;\n'+shader.vertexShader;
  shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvCanopyFade=instanceFade;');
  shader.fragmentShader='varying float vCanopyFade;\n'+shader.fragmentShader;
  shader.fragmentShader=shader.fragmentShader.replace('#include <alphahash_fragment>','if(vCanopyFade<0.01)discard;\ndiffuseColor.a *= vCanopyFade;\n#include <alphahash_fragment>');
 };
 crownMaterial.customProgramCacheKey=()=> 'canopy-view-fade-v2';
 const canopies=[];
 species.forEach((sp,k)=>{
  const items=bySpecies[k];if(!items.length)return;const place=(d,t)=>{d.position.set(t.x,t.y-.05,t.z);d.rotation.y=t.tint*Math.PI*2;d.scale.setScalar(t.size);};
  const trunks=instances('tree-trunks-'+sp.name,sp.trunk,trunkMaterial,items,place);trunks.castShadow=true;
  const [h,s,l]=treeCrownPalette[k%treeCrownPalette.length];
  const mesh=instances('forest-canopies-'+sp.name,sp.crown,crownMaterial,items,(d,t)=>{place(d,t);d.scale.set(t.size*1.22,t.size*1.12,t.size*1.22);},t=>new THREE.Color().setHSL(h+(t.tint-.5)*.05,s,l+t.tint*.07));
  const fades=new THREE.InstancedBufferAttribute(new Float32Array(items.length).fill(1),1);mesh.geometry.setAttribute('instanceFade',fades);mesh.castShadow=true;
  canopies.push({items,fades,sp});
 });
 group.userData.updateView=(camera,focus)=>{
  const dx=camera.x-focus.x,dy=camera.y-focus.y,dz=camera.z-focus.z,length=dx*dx+dy*dy+dz*dz;
  for(const {items,fades,sp} of canopies){let changed=false;
   items.forEach((t,i)=>{
    const y=t.y+sp.fadeHeight*t.size,vx=t.x-focus.x,vy=y-focus.y,vz=t.z-focus.z;
    const u=Math.max(0,Math.min(1,(vx*dx+vy*dy+vz*dz)/(length||1)));
    const distance=Math.hypot(vx-dx*u,vy-dy*u,vz-dz*u);
    const next=distance<sp.fadeRadius*t.size+1?0:1;
    if(fades.getX(i)!==next){fades.setX(i,next);changed=true;}
   });if(changed)fades.needsUpdate=true;}
 };
 instances('flower-stems',new THREE.CylinderGeometry(.025,.03,1,3),material(0x5d7941),layout.flowers,(d,f)=>{d.position.set(f.x,f.y+.35*f.size,f.z);d.scale.set(1,.7*f.size,1);});
 instances('flower-heads',new THREE.IcosahedronGeometry(1,0),material(0xffffff),layout.flowers,(d,f)=>{d.position.set(f.x,f.y+.7*f.size,f.z);d.rotation.y=f.angle||0;d.scale.set(.48*f.size,.16*f.size,.38*f.size);},f=>flowerPalette[f.tint%flowerPalette.length]);
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
