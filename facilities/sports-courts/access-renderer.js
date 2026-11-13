import {edgeDistance} from './access-surface.js';
export function addCourtAccess(THREE,group,campus,terrain,access){
 if(!campus.sportsAccess)return{blockers:[]};
 const pavement=new THREE.MeshStandardMaterial({color:0xb9b9aa,roughness:1,side:THREE.DoubleSide}),earth=new THREE.MeshStandardMaterial({color:0x82916d,roughness:1,side:THREE.DoubleSide}),steel=new THREE.MeshStandardMaterial({color:0x52736b,roughness:.75}),wire=new THREE.LineBasicMaterial({color:0x55716a}),blockers=[];
 const mesh=(positions,mat,name)=>{const g=new THREE.BufferGeometry(),points=[],indices=[],lookup=new Map();for(let i=0;i<positions.length;i+=3){const p=positions.slice(i,i+3).map(Math.fround),key=p.join(',');if(!lookup.has(key)){lookup.set(key,points.length/3);points.push(...p);}indices.push(lookup.get(key));}g.setAttribute('position',new THREE.Float32BufferAttribute(points,3));g.setIndex(indices);g.computeVertexNormals();const m=new THREE.Mesh(g,mat);m.name=name;m.receiveShadow=true;group.add(m);return m;};
 const sides=[];
 for(const a of access.surfaces){
  if(a.kind==='stairs'){const [p,q]=a.line,dx=q[0]-p[0],dz=q[1]-p[1],length=Math.hypot(dx,dz),yaw=Math.atan2(-dz,dx),width=campus.sportsPerimeter.gateWidth;
   for(let i=1;i<=a.steps;i++){const t=(i-.5)/a.steps,y=a.level-i*a.rise/a.steps,bottom=Math.min(y-.3,terrain.height(p[0]+dx*t,p[1]+dz*t)-.5),m=new THREE.Mesh(new THREE.BoxGeometry(length/a.steps,y-bottom,width),pavement);m.rotation.y=yaw;m.position.set(p[0]+dx*t,(y+bottom)/2,p[1]+dz*t);m.name='basketball-east-stair-tread-'+i;m.receiveShadow=true;group.add(m);blockers.push(m);}
  }else blockers.push(mesh(a.vertices,a.kind==='shoulder'?earth:pavement,a.id));
  const sample=(surface,p)=>{const h=surface.floorAt(...p);if(h!==null)return h;for(const [dx,dz]of[[.0002,0],[-.0002,0],[0,.0002],[0,-.0002]]){const y=surface.floorAt(p[0]+dx,p[1]+dz);if(y!==null)return y;}return null;};
  for(const region of a.regions)for(const ring of region)for(let i=0;i<ring.length;i++){
   const p=ring[i],q=ring[(i+1)%ring.length],count=Math.max(1,Math.ceil(Math.hypot(q[0]-p[0],q[1]-p[1])/.2));
   for(let j=0;j<count;j++){const at=t=>[p[0]+(q[0]-p[0])*t,p[1]+(q[1]-p[1])*t],pa=at(j/count),pb=at((j+1)/count),h=sample(a,pa),hh=sample(a,pb);if(h===null||hh===null)continue;const mid=[(pa[0]+pb[0])/2,(pa[1]+pb[1])/2];if(edgeDistance(...mid,campus.sportsZones.map(z=>[z.ring]))<.002)continue;if(a.kind==='shoulder'&&access.surfaces.some(s=>s.kind!=='shoulder'&&edgeDistance(...mid,s.regions)<.002))continue;
    const neighbor=p=>{if(a.kind!=='shoulder')for(const s of access.surfaces.filter(s=>s.kind==='shoulder')){const y=sample(s,p);if(y!==null)return y;}return access.outsideFloorAt(...p);},ph=neighbor(pa),qh=neighbor(pb),v=[pa[0],Math.max(h,ph)+.04,pa[1]],w=[pb[0],Math.max(hh,qh)+.04,pb[1]],r=[pa[0],Math.min(h,ph,terrain.height(...pa))-.7,pa[1]],z=[pb[0],Math.min(hh,qh,terrain.height(...pb))-.7,pb[1]];sides.push(...v,...r,...w,...w,...r,...z);
   }
  }
 }
 mesh(sides,earth,'sports-access-ground-supports');
 // A narrow skirt seals each flat rectangular slab to its sloped shoulder or original ground.
 const slab=[];for(const zone of campus.sportsZones){const court=campus.courts.find(c=>c.osm===zone.courtIds[0]),level=terrain.platformHeight(court)+.07;for(let i=0;i<zone.ring.length;i++){const a=zone.ring[i],b=zone.ring[(i+1)%zone.ring.length],count=Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1]));for(let j=0;j<count;j++){const at=t=>[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t],p=at(j/count),q=at((j+1)/count),v=[p[0],level,p[1]],w=[q[0],level,q[1]],r=[p[0],Math.min(level,terrain.height(...p))-.7,p[1]],s=[q[0],Math.min(level,terrain.height(...q))-.7,q[1]];slab.push(...v,...r,...w,...w,...r,...s);}}}mesh(slab,earth,'rectangular-court-ground-supports');
 const wires=[],posts=[],dummy=new THREE.Object3D(),up=new THREE.Vector3(0,1,0),base=access.fenceBase;
 function beam(a,b,thickness=.06){const va=new THREE.Vector3(...a),vb=new THREE.Vector3(...b),d=vb.clone().sub(va);dummy.position.copy(va).add(vb).multiplyScalar(.5);dummy.quaternion.setFromUnitVectors(up,d.clone().normalize());dummy.scale.set(thickness,d.length(),thickness);dummy.updateMatrix();posts.push(dummy.matrix.clone());}
 for(const fence of campus.sportsAccess.fences){const [a,b]=fence.line,length=Math.hypot(b[0]-a[0],b[1]-a[1]),dx=(b[0]-a[0])/length,dz=(b[1]-a[1])/length,world=(s,h)=>[a[0]+dx*s,base+h,a[1]+dz*s],count=Math.ceil(length/2.4);for(let i=0;i<=count;i++)beam(world(length*i/count,0),world(length*i/count,fence.height),.09);for(const h of[0,fence.height/2,fence.height])beam(world(0,h),world(length,h));
  for(const sign of[-1,1])for(let intercept=(sign>0?-length:-fence.height);intercept<(sign>0?fence.height:length+fence.height);intercept+=.28){let lo=0,hi=length;if(sign>0){lo=Math.max(lo,-intercept);hi=Math.min(hi,fence.height-intercept);}else{lo=Math.max(lo,intercept-fence.height);hi=Math.min(hi,intercept);}if(hi>lo)wires.push(...world(lo,sign*lo+intercept),...world(hi,sign*hi+intercept));}
 }
 const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(wires,3));const net=new THREE.LineSegments(geometry,wire);net.name='basketball-east-south-west-chain-link';group.add(net);const frame=new THREE.InstancedMesh(new THREE.BoxGeometry(1,1,1),steel,posts.length);posts.forEach((m,i)=>frame.setMatrixAt(i,m));frame.name='basketball-fence-posts-and-rails';frame.computeBoundingSphere();group.add(frame);
 return{blockers};
}
