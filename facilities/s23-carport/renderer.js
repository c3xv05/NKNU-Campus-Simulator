export function carportPosts(c){const x=c.anchor[0],z=c.ring[0][1];return Array.from({length:c.bays+1},(_,i)=>[-1,1].map(side=>({x:x+side*(c.width/2-.25),z:z+i*c.length/c.bays,radius:.16}))).flat();}
export function addCarports(THREE,parent,campus,network){
 const group=new THREE.Group();group.name='campus-carports';parent.add(group);const blockers=[],columns=[];
 for(const c of campus.carports||[]){const base=network.surfaceHeight(...c.anchor),steel=new THREE.MeshStandardMaterial({color:0x7b8587,roughness:.85}),roofMat=new THREE.MeshStandardMaterial({color:c.roofColor,roughness:.85}),posts=carportPosts(c),dummy=new THREE.Object3D(),items=[];
  for(const p of posts){columns.push(p);items.push({x:p.x,y:base+c.clearance/2,z:p.z,w:.16,h:c.clearance,d:.16});}
  for(let i=0;i<=c.bays;i++)items.push({x:c.anchor[0],y:base+c.clearance-.08,z:c.ring[0][1]+i*c.length/c.bays,w:c.width,h:.16,d:.16});
  const frame=new THREE.InstancedMesh(new THREE.BoxGeometry(1,1,1),steel,items.length);frame.name=c.id+'-frame';items.forEach((p,i)=>{dummy.position.set(p.x,p.y,p.z);dummy.scale.set(p.w,p.h,p.d);dummy.updateMatrix();frame.setMatrixAt(i,dummy.matrix);});frame.instanceMatrix.needsUpdate=true;frame.castShadow=true;frame.receiveShadow=true;group.add(frame);blockers.push(frame);
  const roof=new THREE.Mesh(new THREE.BoxGeometry(c.width+.6,.15,c.length+.6),roofMat);roof.name=c.id+'-roof';roof.position.set(c.anchor[0],base+c.clearance+.075,c.ring[0][1]+c.length/2);roof.castShadow=true;roof.receiveShadow=true;group.add(roof);blockers.push(roof);
 }
 return{group,blockers,columns};
}
