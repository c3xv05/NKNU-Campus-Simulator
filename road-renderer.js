import {motorPavementPlan} from './data/motor-pavement-plan.js';
import {eachPlanTriangle} from './surface-plans.js';
import {ringDistance} from './terrain.js';
import {entranceMesh} from './data/entrance-mesh.js';
import {pavementIndex} from './pavement.js';
// Original procedural pavement and markings; no external texture assets.
export function addRoads(THREE,scene,network,groundHeight=(x,z)=>network.surfaceHeight(x,z),campus=null) {
  const group=new THREE.Group();group.name='campus-roads';scene.add(group);
  const textureCanvas=document.createElement('canvas');textureCanvas.width=128;textureCanvas.height=128;
  const context=textureCanvas.getContext('2d'),image=context.createImageData(128,128);
  let seed=38197;
  for(let i=0;i<image.data.length;i+=4){seed=(seed*1664525+1013904223)>>>0;const v=182+(seed%37);image.data[i]=v;image.data[i+1]=v;image.data[i+2]=v;image.data[i+3]=255;}
  context.putImageData(image,0,0);
  const texture=new THREE.CanvasTexture(textureCanvas);texture.wrapS=texture.wrapT=THREE.RepeatWrapping;
  texture.colorSpace=THREE.SRGBColorSpace;texture.anisotropy=2;
  const asphalt=new THREE.MeshStandardMaterial({color:0x3d4248,map:texture,roughness:1,side:THREE.DoubleSide});
  const concrete=new THREE.MeshStandardMaterial({color:0xaaa99e,roughness:1,side:THREE.DoubleSide});
  const white=new THREE.MeshBasicMaterial({color:0xffffff,side:THREE.DoubleSide,polygonOffset:true,polygonOffsetFactor:-2,polygonOffsetUnits:-2});
  const yellow=new THREE.MeshBasicMaterial({color:0xffcc00,side:THREE.DoubleSide,polygonOffset:true,polygonOffsetFactor:-2,polygonOffsetUnits:-2});
  const earth=new THREE.MeshStandardMaterial({color:0x7f9167,roughness:1,side:THREE.DoubleSide});
  const batches={asphalt:[],concrete:[],white:[],yellow:[],earth:[]};
  const footprints=[],pathFootprints=[],pavement=pavementIndex(network);let currentRoute=null,pavementLift=0;
  const levels={asphalt:.035,concrete:.035,white:.045,yellow:.045};
  function vertex(x,z,type){return [x,network.surfaceHeight(x,z)+levels[type]+pavementLift,z];}
  function quad(points,type){if(type==='white'||type==='yellow'){for(const piece of pavement.clip([points[0],points[1],points[3],points[2]],currentRoute?.osm))for(let i=1;i<piece.length-1;i++)batches[type].push(...vertex(...piece[0],type),...vertex(...piece[i],type),...vertex(...piece[i+1],type));return;}if(type==='asphalt'||type==='concrete'){const p=[points[0],points[1],points[3],points[2]];footprints.push(p);if(type==='concrete')pathFootprints.push(p);}const v=points.map(p=>vertex(p[0],p[1],type));batches[type].push(...v[0],...v[2],...v[1],...v[1],...v[2],...v[3]);}
  function skirt(a,b){
    // A broad sloped shoulder stitches the analytic pavement to the existing
    // triangulated ground, without changing clipped terrain edge interpolation.
    const dx=b[0]-a[0],dz=b[1]-a[1],l=Math.hypot(dx,dz)||1,mx=(a[0]+b[0])/2,mz=(a[1]+b[1])/2;
    if(campus?.flowerbed&&ringDistance(mx,mz,campus.flowerbed.ring)<1.35)return;
    const nx=-dz/l,nz=dx/l,plus=network.nearest(mx+nx,mz+nz),minus=network.nearest(mx-nx,mz-nz),sign=(plus?.d||0)>(minus?.d||0)?1:-1;
    const outer=p=>[p[0]+nx*sign*.85,p[1]+nz*sign*.85],oa=outer(a),ob=outer(b);
    const polygon=[a,b,ob,oa];
    for(const piece of pavement.clip(polygon,undefined,true))for(let i=1;i<piece.length-1;i++)for(const [x,z] of [piece[0],piece[i],piece[i+1]]){
      const t=Math.max(0,Math.min(1,((x-a[0])*nx*sign+(z-a[1])*nz*sign)/.85));
      const y=(network.surfaceHeight(x,z)+.005)*(1-t)+(groundHeight(x,z)+.015)*t;
      batches.earth.push(x,y,z);
    }
  }
  function cap(x,z,radius,type){
    const centre=vertex(x,z,type);
    const ring=Array.from({length:20},(_,i)=>[x+Math.cos(i*Math.PI/10)*radius,z+Math.sin(i*Math.PI/10)*radius]);footprints.push(ring);if(type==='concrete')pathFootprints.push(ring);
    for(let i=0;i<20;i++){
      const a=i*Math.PI/10,b=(i+1)*Math.PI/10;
      skirt([x+Math.cos(a)*radius,z+Math.sin(a)*radius],[x+Math.cos(b)*radius,z+Math.sin(b)*radius]);
      batches[type].push(...centre,...vertex(x+Math.cos(a)*radius,z+Math.sin(a)*radius,type),...vertex(x+Math.cos(b)*radius,z+Math.sin(b)*radius,type));
    }
  }
  function pointAt(route,distance){
    let traversed=0;
    for(let i=1;i<route.points.length;i++){
      const a=route.points[i-1],b=route.points[i],length=Math.hypot(b.x-a.x,b.z-a.z);
      if(traversed+length>=distance||i===route.points.length-1){const t=Math.max(0,Math.min(1,(distance-traversed)/(length||1)));return{x:a.x+(b.x-a.x)*t,z:a.z+(b.z-a.z)*t,dx:(b.x-a.x)/(length||1),dz:(b.z-a.z)/(length||1)};}
      traversed+=length;
    }
  }
  const crossings=new Map([[218881805,18],[293423732,27],[293423728,12]]);
  function nearJunction(x,z){return network.junctions.some(j=>j.motor&&Math.hypot(j.x-x,j.z-z)<j.width*.85+1);}
  for(const route of network.routes){if(route.entrance&&campus?.entranceApron?.ring)continue;currentRoute=route;
    const type=route.style.path?'concrete':'asphalt',half=route.width/2,points=route.points,sections=[];
    let distance=0;
    for(let i=0;i<points.length;i++){
      const a=points[Math.max(0,i-1)],b=points[Math.min(points.length-1,i+1)];
      const length=Math.hypot(b.x-a.x,b.z-a.z)||1,nx=-(b.z-a.z)/length,nz=(b.x-a.x)/length;
      const p=points[i];if(i)distance+=Math.hypot(p.x-points[i-1].x,p.z-points[i-1].z);
      sections.push({x:p.x,z:p.z,nx,nz,distance});
    }
    for(let i=1;i<sections.length;i++){
      const a=sections[i-1],b=sections[i];
      const offset=(p,t)=>[p.x+p.nx*t,p.z+p.nz*t];
      if(type==='concrete'&&network.onMotorRoad((a.x+b.x)/2,(a.z+b.z)/2))continue;
      quad([offset(a,-half),offset(a,half),offset(b,-half),offset(b,half)],type);
      skirt(offset(a,-half),offset(b,-half));skirt(offset(a,half),offset(b,half));
      const crossing=crossings.get(route.osm),centreDistance=(a.distance+b.distance)/2;
      const interrupted=route.entrance||nearJunction((a.x+b.x)/2,(a.z+b.z)/2)||(crossing!==undefined&&Math.abs(centreDistance-crossing)<2.1);
      if(!interrupted&&route.style.center)for(const side of [-1,1]){
        // Two 10 cm yellow lines with a 10 cm gap.
        const t=side*.1;
        quad([offset(a,t-.05),offset(a,t+.05),offset(b,t-.05),offset(b,t+.05)],'yellow');
      }
      if(!interrupted&&route.parkingBands){
        const inner=route.parkingBands.travelWidth/2;
        for(const side of [-1,1]){
          const t=side*inner;quad([offset(a,t-.06),offset(a,t+.06),offset(b,t-.06),offset(b,t+.06)],'white');
          // Transverse bay ends every six metres; omit junction approaches and sharp bends.
          const slot=Math.floor(b.distance/6)*6;
          if(slot>a.distance&&centreDistance>15&&centreDistance<route.length-15){const u=(slot-a.distance)/(b.distance-a.distance),p={x:a.x+(b.x-a.x)*u,z:a.z+(b.z-a.z)*u,nx:a.nx+(b.nx-a.nx)*u,nz:a.nz+(b.nz-a.nz)*u},dx=p.nz*.06,dz=-p.nx*.06,lo=offset(p,side*inner),hi=offset(p,side*(half-.3));quad([[lo[0]-dx,lo[1]-dz],[hi[0]-dx,hi[1]-dz],[lo[0]+dx,lo[1]+dz],[hi[0]+dx,hi[1]+dz]],'white');}
        }
      }
      if(!interrupted&&route.style.edges)for(const side of [-1,1]){
        const t=side*(half-.3);
        quad([offset(a,t-.075),offset(a,t+.075),offset(b,t-.075),offset(b,t+.075)],'white');
      }
    }
    for(const p of (route.entrance?[]:[points[0],points.at(-1)]))if(type!=='concrete'||!network.onMotorRoad(p.x,p.z))cap(p.x,p.z,half,type);
    if(crossings.has(route.osm)&&!route.style.path&&!route.entrance){
      const p=pointAt(route,Math.min(route.length-4,crossings.get(route.osm)));
      // Taiwan sleeper-style crossing: 40 cm bars, 40 cm gaps, parallel to traffic.
      for(let lateral=-half+.6;lateral+.4<half-.5;lateral+=.8){
        const corners=[];
        for(const forward of [-1.5,1.5])for(const side of [lateral,lateral+.4])corners.push([p.x+p.dx*forward-p.dz*side,p.z+p.dz*forward+p.dx*side]);
        quad(corners,'white');
      }
    }
    if(route.style.oneWay&&!route.style.path&&!route.entrance&&route.length>16){
      const p=pointAt(route,route.length*.5),direction=route.style.reverse?-1:1;
      const dx=p.dx*direction,dz=p.dz*direction;
      const local=(side,forward)=>[p.x-dz*side+dx*forward,p.z+dx*side+dz*forward];
      quad([local(-.13,-1.5),local(.13,-1.5),local(-.13,.3),local(.13,.3)],'white');
      const arrow=[local(-.65,.3),local(.65,.3),local(0,1.5)];for(const piece of pavement.clip(arrow,currentRoute.osm))for(let i=1;i<piece.length-1;i++)for(const p of [piece[0],piece[i],piece[i+1]])batches.white.push(...vertex(...p,'white'));
    }
  }
  // One pavement with the exact shared flowerbed hole, not overlapping offset strips.
  if(campus?.entranceApron?.ring){for(let i=0;i<entranceMesh.length;i+=6)for(let k=0;k<6;k+=2)batches.asphalt.push(...vertex(entranceMesh[i+k],entranceMesh[i+k+1],'asphalt'));footprints.push(...campus.entranceApron.footprints);}
  for(const area of [...(network.pavedAreas||[]),...(network.junctionFillets||[])]){
    function triangle(a,b,c,depth){if(depth){const mid=(p,q)=>[(p[0]+q[0])/2,(p[1]+q[1])/2],ab=mid(a,b),bc=mid(b,c),ca=mid(c,a);triangle(a,ab,ca,depth-1);triangle(ab,b,bc,depth-1);triangle(ca,bc,c,depth-1);triangle(ab,bc,ca,depth-1);return;}for(const p of [a,b,c])batches.asphalt.push(...vertex(...p,'asphalt'));}
    for(const piece of area.triangles||pavement.clip(area.ring,area.id,true))for(let i=1;i<piece.length-1;i++)triangle(piece[0],piece[i],piece[i+1],area.triangles?0:3);footprints.push(...(area.triangles||[area.ring]));
    for(let i=0;i<area.ring.length;i++)skirt(area.ring[i],area.ring[(i+1)%area.ring.length]);
  }
  // Motor asphalt and raised kerbs share one boundary and the same grade triangles.
  batches.asphalt.length=0;eachPlanTriangle(motorPavementPlan,triangle=>{for(const p of triangle)batches.asphalt.push(...vertex(...p,'asphalt'));});
  if(campus?.entranceApron?.ring)for(let i=0;i<entranceMesh.length;i+=6)for(let k=0;k<6;k+=2)batches.asphalt.push(...vertex(entranceMesh[i+k],entranceMesh[i+k+1],'asphalt'));
  const entranceIds=new Set(network.routes.filter(r=>r.entrance).map(r=>r.osm));footprints.length=0;for(const a of pavement.all)if(!a.actual&&!entranceIds.has(a.osm))footprints.push(a.points);footprints.push(...pathFootprints);
  for(const [type,positions] of Object.entries(batches)){
    if(!positions.length)continue;
    if(type==='asphalt'||type==='concrete')for(let i=0;i<positions.length;i+=9){const cross=(positions[i+3]-positions[i])*(positions[i+8]-positions[i+2])-(positions[i+5]-positions[i+2])*(positions[i+6]-positions[i]);if(cross>0)for(let k=0;k<3;k++){const v=positions[i+3+k];positions[i+3+k]=positions[i+6+k];positions[i+6+k]=v;}}
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
    if(type==='asphalt')geometry.setAttribute('uv',new THREE.Float32BufferAttribute(positions.flatMap((v,i)=>i%3===0?[v/5,positions[i+2]/5]:[]),2));
    if(type==='earth')geometry.computeVertexNormals();
    else if(type==='asphalt'||type==='concrete'){
      const normals=[];
      for(let i=0;i<positions.length;i+=3){
        const x=positions[i],z=positions[i+2],e=.25;
        const gx=(network.surfaceHeight(x+e,z)-network.surfaceHeight(x-e,z))/(2*e);
        const gz=(network.surfaceHeight(x,z+e)-network.surfaceHeight(x,z-e))/(2*e);
        const length=Math.hypot(gx,1,gz);normals.push(-gx/length,1/length,-gz/length);
      }
      geometry.setAttribute('normal',new THREE.Float32BufferAttribute(normals,3));
    }
    const material={asphalt,concrete,white,yellow,earth}[type],mesh=new THREE.Mesh(geometry,material);
    mesh.name=`road-${type}`;mesh.receiveShadow=true;mesh.renderOrder=type==='white'||type==='yellow'?2:0;group.add(mesh);
  }
  return {group,footprints};
}
