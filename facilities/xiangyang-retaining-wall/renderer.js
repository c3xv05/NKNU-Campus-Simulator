import {createXiangyangWall} from './surface.js';
export function addXiangyangWall(THREE,parent,campus,terrain,network){
 const wall=createXiangyangWall(network,terrain),group=new THREE.Group(),blockers=[];group.name='xiangyang-retaining-wall';parent.add(group);
 const p=wall.points;if(p.length<2)return{...wall,group,blockers};
 const positions=[],quad=(a,b,c,d)=>positions.push(...a,...b,...c,...a,...c,...d);
 for(let i=1;i<p.length;i++){const a=p[i-1],b=p[i];
  quad([a.inner[0],a.bottom,a.inner[1]],[b.inner[0],b.bottom,b.inner[1]],[b.inner[0],b.top,b.inner[1]],[a.inner[0],a.top,a.inner[1]]);
  quad([a.outer[0],a.bottom,a.outer[1]],[a.outer[0],a.top,a.outer[1]],[b.outer[0],b.top,b.outer[1]],[b.outer[0],b.bottom,b.outer[1]]);
  quad([a.inner[0],a.top,a.inner[1]],[b.inner[0],b.top,b.inner[1]],[b.outer[0],b.top,b.outer[1]],[a.outer[0],a.top,a.outer[1]]);}
 for(const e of [p[0],p.at(-1)])quad([e.inner[0],e.bottom,e.inner[1]],[e.outer[0],e.bottom,e.outer[1]],[e.outer[0],e.top,e.outer[1]],[e.inner[0],e.top,e.inner[1]]);
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.computeVertexNormals();
 const concrete=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:0x9c9d96,roughness:1,side:THREE.DoubleSide}));concrete.name='xiangyang-retaining-wall-body';concrete.castShadow=true;concrete.receiveShadow=true;group.add(concrete);blockers.push(concrete);
 const steel=new THREE.MeshStandardMaterial({color:0x5f6a6d,roughness:.6,metalness:.4}),h=wall.config.railHeight,step=Math.max(1,Math.round(wall.config.postSpacing/.5));
 const postGeometry=new THREE.BoxGeometry(.06,h,.06),posts=[];for(let i=0;i<p.length;i+=step)posts.push(p[i]);if(posts.at(-1)!==p.at(-1))posts.push(p.at(-1));
 const postMesh=new THREE.InstancedMesh(postGeometry,steel,posts.length),dummy=new THREE.Object3D();posts.forEach((q,i)=>{dummy.position.set(q.x,q.top+h/2,q.z);dummy.rotation.set(0,0,0);dummy.updateMatrix();postMesh.setMatrixAt(i,dummy.matrix);});postMesh.name='xiangyang-railing-posts';postMesh.castShadow=true;group.add(postMesh);
 const railGeometry=new THREE.BoxGeometry(1,.05,.05),rails=new THREE.InstancedMesh(railGeometry,steel,(p.length-1)*2);let k=0;
 for(let i=1;i<p.length;i++){const a=p[i-1],b=p[i],len=Math.hypot(b.x-a.x,b.z-a.z),yaw=Math.atan2(-(b.z-a.z),b.x-a.x),pitch=Math.atan2(b.top-a.top,len);
  for(const f of [1,.5]){dummy.position.set((a.x+b.x)/2,(a.top+b.top)/2+h*f,(a.z+b.z)/2);dummy.rotation.set(0,yaw,pitch);dummy.scale.set(Math.hypot(len,b.top-a.top),1,1);dummy.updateMatrix();rails.setMatrixAt(k++,dummy.matrix);}}
 dummy.scale.set(1,1,1);rails.name='xiangyang-railing-rails';group.add(rails);
 return{...wall,group,blockers};
}
