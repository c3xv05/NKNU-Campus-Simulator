const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const ease=(a,b,v)=>{const t=clamp((v-a)/(b-a),0,1);return t*t*(3-2*t);};
const pointKey=(x,z)=>`${x.toFixed(3)},${z.toFixed(3)}`;
export function roadStyle(road,tags={}) {
  const path=['footway','pedestrian','path','steps'].includes(tags.highway)||road.width<=2.5;
  const oneWay=tags.oneway==='yes'||tags.oneway==='1'||tags.oneway==='-1';
  return {path,oneWay,reverse:tags.oneway==='-1',center:!path&&!oneWay&&tags.lanes!=='1'&&road.width>=6.5,edges:!path&&road.width>=4};
}
// Round unconnected bends; retain every original junction position.
function roundedLine(line,width,connections) {
  const result=[line[0]];
  for(let i=1;i<line.length-1;i++) {
    const a=line[i-1],b=line[i],c=line[i+1];
    if((connections.get(pointKey(...b))||0)>1){result.push(b);continue;}
    const la=Math.hypot(a[0]-b[0],a[1]-b[1]),lc=Math.hypot(c[0]-b[0],c[1]-b[1]);
    const cut=Math.min(width*.7,5,la*.2,lc*.2);
    if(cut<.3){result.push(b);continue;}
    const p=[b[0]+(a[0]-b[0])*cut/la,b[1]+(a[1]-b[1])*cut/la];
    const q=[b[0]+(c[0]-b[0])*cut/lc,b[1]+(c[1]-b[1])*cut/lc];
    result.push(p);
    const steps=Math.max(2,Math.ceil(cut/1.2));
    for(let k=1;k<=steps;k++) {
      const t=k/steps,u=1-t;
      result.push([u*u*p[0]+2*u*t*b[0]+t*t*q[0],u*u*p[1]+2*u*t*b[1]+t*t*q[1]]);
    }
  }
  result.push(line.at(-1));return result;
}
export function createRoadNetwork(roads,height,tags={}) {
  const connections=new Map(),nodes=[],nodeMap=new Map(),routes=[],segments=[];
  for(const road of roads) for(const [x,z] of road.line){const k=pointKey(x,z);connections.set(k,(connections.get(k)||0)+1);}
  function nodeAt(x,z,width){
    const key=pointKey(x,z);let node=nodeMap.get(key);
    if(!node){node={x,z,raw:height(x,z),h:height(x,z),width,neighbours:new Set(),vehicleNeighbours:new Set()};nodeMap.set(key,node);nodes.push(node);}
    node.width=Math.max(width,node.width);return node;
  }
  for(const road of roads) {
    const line=roundedLine(road.line,road.width,connections),points=[];
    for(let i=1;i<line.length;i++) {
      const a=line[i-1],b=line[i],length=Math.hypot(b[0]-a[0],b[1]-a[1]);
      if(length<.001)continue;
      const count=Math.max(1,Math.ceil(length/2));
      for(let j=0;j<count;j++) {
        const t=j/count;points.push(nodeAt(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,road.width));
      }
    }
    points.push(nodeAt(...line.at(-1),road.width));
    for(let i=1;i<points.length;i++){points[i-1].neighbours.add(points[i]);points[i].neighbours.add(points[i-1]);}
    const style=roadStyle(road,tags[road.osm]||{});
    if(!style.path)for(let i=1;i<points.length;i++){points[i-1].vehicleNeighbours.add(points[i]);points[i].vehicleNeighbours.add(points[i-1]);}
    routes.push({...road,style,points});
  }
  // A shared graph avoids independently graded endpoints at intersections.
  for(let iteration=0;iteration<100;iteration++) {
    const next=nodes.map(node=>{
      if(!node.neighbours.size)return node.h;
      let sum=0,weight=0;
      for(const other of node.neighbours){const w=1/Math.max(.3,Math.hypot(node.x-other.x,node.z-other.z));sum+=other.h*w;weight+=w;}
      return node.raw*.025+sum/weight*.975;
    });
    nodes.forEach((node,i)=>node.h=next[i]);
  }
  const junctions=nodes.filter(node=>node.neighbours.size>2).map(node=>({x:node.x,z:node.z,h:node.h,width:node.width,motor:node.vehicleNeighbours.size>2}));
  // Gentle approaches into one level intersection apron; no cross-road banking.
  for(const node of nodes){
    let strength=0,total=0,target=0;
    for(const joint of junctions){
      const distance=Math.hypot(node.x-joint.x,node.z-joint.z);
      const weight=1-ease(joint.width*.85,joint.width*2.4,distance);
      const influence=weight**4;
      strength=Math.max(strength,weight);total+=influence;target+=joint.h*influence;
    }
    if(total)node.h+=(target/total-node.h)*strength;
  }
  // Fit a gradient at shared nodes for continuous, shape-preserving cubic grades.
  for(const node of nodes){
    let xx=0,xz=0,zz=0,xh=0,zh=0;
    for(const other of node.neighbours){
      const dx=other.x-node.x,dz=other.z-node.z,dh=other.h-node.h,w=1/Math.max(.01,dx*dx+dz*dz);
      xx+=dx*dx*w;xz+=dx*dz*w;zz+=dz*dz*w;xh+=dx*dh*w;zh+=dz*dh*w;
    }
    const determinant=xx*zz-xz*xz;
    if(Math.abs(determinant)>1e-7){node.gx=(xh*zz-zh*xz)/determinant;node.gz=(zh*xx-xh*xz)/determinant;}
    else{const trace=xx+zz;node.gx=xh/(trace||1);node.gz=zh/(trace||1);}
  }
  const cellSize=24,buckets=new Map();
  function key(x,z){return `${Math.floor(x/cellSize)},${Math.floor(z/cellSize)}`;}
  for(const route of routes) {
    let distance=0;
    for(let i=1;i<route.points.length;i++) {
      const a=route.points[i-1],b=route.points[i],dx=b.x-a.x,dz=b.z-a.z,length=Math.hypot(dx,dz);
      if(length<.001)continue;
      const segment={a,b,dx,dz,length,width:route.width,route,distance};
      segments.push(segment);distance+=length;
      const margin=route.width/2+12;
      for(let z=Math.floor((Math.min(a.z,b.z)-margin)/cellSize);z<=Math.floor((Math.max(a.z,b.z)+margin)/cellSize);z++)
        for(let x=Math.floor((Math.min(a.x,b.x)-margin)/cellSize);x<=Math.floor((Math.max(a.x,b.x)+margin)/cellSize);x++){
          const k=`${x},${z}`;if(!buckets.has(k))buckets.set(k,[]);buckets.get(k).push(segment);
        }
    }
    route.length=distance;
  }
  function nearest(x,z) {
    let closest=null,best=Infinity,motor=null,bestMotor=Infinity;
    for(const segment of buckets.get(key(x,z))||[]) {
      const {a,dx,dz,length,width}=segment;
      const t=clamp(((x-a.x)*dx+(z-a.z)*dz)/(length*length),0,1);
      const d=Math.hypot(x-a.x-dx*t,z-a.z-dz*t);
      // Compare distance to pavement, so a footpath cannot steal a main-road lane.
      const score=Math.max(0,d-width/2)+d*.001;
      const delta=segment.b.h-a.h;
      const limit=slope=>delta===0?0:clamp(slope/delta,0,3)*delta;
      const ma=limit(a.gx*dx+a.gz*dz),mb=limit(segment.b.gx*dx+segment.b.gz*dz);
      const h=(2*t**3-3*t*t+1)*a.h+(t**3-2*t*t+t)*ma+(-2*t**3+3*t*t)*segment.b.h+(t**3-t*t)*mb;
      const candidate={segment,t,d,h,width};
      if(score<best){best=score;closest=candidate;}
      if(!segment.route.style.path&&score<bestMotor){bestMotor=score;motor=candidate;}
    }
    return motor&&motor.d<=motor.width/2+1e-6?motor:closest;
  }
  function onMotorRoad(x,z){
    return (buckets.get(key(x,z))||[]).some(segment=>{
      if(segment.route.style.path)return false;
      const t=clamp(((x-segment.a.x)*segment.dx+(z-segment.a.z)*segment.dz)/(segment.length*segment.length),0,1);
      return Math.hypot(x-segment.a.x-segment.dx*t,z-segment.a.z-segment.dz*t)<segment.width/2;
    });
  }
  function surfaceHeight(x,z) {const road=nearest(x,z);return road?road.h:height(x,z);}
  function gradeTerrain(mesh,protectedAreas=[]) {
    for(let r=0;r<mesh.rows;r++)for(let c=0;c<mesh.columns;c++){
      const x=mesh.west+c*mesh.step,z=mesh.north+r*mesh.step,road=nearest(x,z);
      if(!road)continue;
      const inner=road.width/2+mesh.step*.8,outer=inner+5;
      if(road.d>=outer)continue;
      // Preserve building, water and sports platforms; roads are rendered separately.
      if(protectedAreas.some(a=>x>=a.west&&x<=a.east&&z>=a.north&&z<=a.south&&a.contains(x,z)))continue;
      const weight=1-ease(inner,outer,road.d),index=r*mesh.columns+c;
      mesh.heights[index]+=(road.h-.22-mesh.heights[index])*weight;
    }
  }
  function walkHeight(x,z,ground) {
    const road=nearest(x,z);if(!road)return ground;
    const weight=1-ease(road.width/2,road.width/2+.4,road.d);
    return ground+(road.h+.06-ground)*weight;
  }
  return {routes,segments,junctions,nearest,surfaceHeight,gradeTerrain,walkHeight,onMotorRoad,groundHeight:height};
}
