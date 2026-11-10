// Original procedural pavement and markings; no external texture assets.
export function addRoads(THREE,scene,network) {
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
  const earth=new THREE.MeshStandardMaterial({color:0x68715f,roughness:1,side:THREE.DoubleSide});
  const batches={asphalt:[],concrete:[],white:[],yellow:[],earth:[]};
  const footprints=[];
  const levels={asphalt:.06,concrete:.06,white:.08,yellow:.08};
  function vertex(x,z,type){return [x,network.surfaceHeight(x,z)+levels[type],z];}
  function quad(points,type){if(type==='asphalt'||type==='concrete')footprints.push([points[0],points[1],points[3],points[2]]);const v=points.map(p=>vertex(p[0],p[1],type));batches[type].push(...v[0],...v[2],...v[1],...v[1],...v[2],...v[3]);}
  function skirt() {} // Smooth earth shoulders replace the former vertical road skirts.
  function cap(x,z,radius,type){
    const centre=vertex(x,z,type);
    footprints.push(Array.from({length:20},(_,i)=>[x+Math.cos(i*Math.PI/10)*radius,z+Math.sin(i*Math.PI/10)*radius]));
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
  for(const route of network.routes){
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
      const interrupted=nearJunction((a.x+b.x)/2,(a.z+b.z)/2)||(crossing!==undefined&&Math.abs(centreDistance-crossing)<2.1);
      if(!interrupted&&route.style.center)for(const side of [-1,1]){
        // Two 10 cm yellow lines with a 10 cm gap.
        const t=side*.1;
        quad([offset(a,t-.05),offset(a,t+.05),offset(b,t-.05),offset(b,t+.05)],'yellow');
      }
      if(!interrupted&&route.style.edges)for(const side of [-1,1]){
        const t=side*(half-.3);
        quad([offset(a,t-.075),offset(a,t+.075),offset(b,t-.075),offset(b,t+.075)],'white');
      }
    }
    for(const p of [points[0],points.at(-1)])if(type!=='concrete'||!network.onMotorRoad(p.x,p.z))cap(p.x,p.z,half,type);
    if(crossings.has(route.osm)&&!route.style.path){
      const p=pointAt(route,Math.min(route.length-4,crossings.get(route.osm)));
      // Taiwan sleeper-style crossing: 40 cm bars, 40 cm gaps, parallel to traffic.
      for(let lateral=-half+.6;lateral+.4<half-.5;lateral+=.8){
        const corners=[];
        for(const forward of [-1.5,1.5])for(const side of [lateral,lateral+.4])corners.push([p.x+p.dx*forward-p.dz*side,p.z+p.dz*forward+p.dx*side]);
        quad(corners,'white');
      }
    }
    if(route.style.oneWay&&!route.style.path&&route.length>16){
      const p=pointAt(route,route.length*.5),direction=route.style.reverse?-1:1;
      const dx=p.dx*direction,dz=p.dz*direction;
      const local=(side,forward)=>[p.x-dz*side+dx*forward,p.z+dx*side+dz*forward];
      quad([local(-.13,-1.5),local(.13,-1.5),local(-.13,.3),local(.13,.3)],'white');
      for(const p of [local(-.65,.3),local(.65,.3),local(0,1.5)])batches.white.push(...vertex(...p,'white'));
    }
  }
  for(const [type,positions] of Object.entries(batches)){
    if(!positions.length)continue;
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
