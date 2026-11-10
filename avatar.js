export function createAvatar(THREE){
 const group=new THREE.Group();group.name='human-avatar';const meshes={};
 const mats={shirt:new THREE.MeshStandardMaterial({color:0x187b92,roughness:.9}),skin:new THREE.MeshStandardMaterial({color:0xe7ba93,roughness:1}),pants:new THREE.MeshStandardMaterial({color:0x334b58}),shoes:new THREE.MeshStandardMaterial({color:0x2b3338}),bag:new THREE.MeshStandardMaterial({color:0xdb9849})};
 function box(name,w,h,d,x,y,z,material){const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),material);mesh.position.set(x,y,z);mesh.castShadow=true;group.add(mesh);meshes[name]=mesh;return mesh;}
 const body=box('body',.43,.6,.25,0,1.15,0,mats.shirt),backpack=box('backpack',.31,.43,.15,0,1.15,.18,mats.bag);
 const head=new THREE.Mesh(new THREE.SphereGeometry(.12,12,9),mats.skin);head.position.y=1.64;group.add(head);
 const neck=new THREE.Mesh(new THREE.CylinderGeometry(.045,.05,.09,8),mats.skin);neck.position.y=1.485;group.add(neck);
 for(const side of [-1,1]){box('leg'+side,.14,.78,.16,side*.105,.42,0,mats.pants);box('shoe'+side,.16,.1,.28,side*.105,.05,-.05,mats.shoes);box('arm'+side,.12,.57,.13,side*.28,1.15,0,mats.shirt);}
 const helmet=new THREE.Mesh(new THREE.SphereGeometry(.14,12,8,0,Math.PI*2,0,Math.PI/2),new THREE.MeshStandardMaterial({color:0xf4c85c}));helmet.visible=false;helmet.position.y=1.68;group.add(helmet);
 function setRiding(riding){
  body.position.y=riding?1.2:1.15;body.rotation.x=riding?.15:0;head.position.y=riding?1.68:1.64;neck.position.y=riding?1.525:1.485;backpack.position.y=riding?1.2:1.15;helmet.visible=riding;
  for(const side of [-1,1]){const leg=meshes['leg'+side],shoe=meshes['shoe'+side],arm=meshes['arm'+side];leg.scale.y=riding?.65:1;leg.position.set(side*.16,riding?.61:.42,riding?-.17:0);leg.rotation.x=riding?-.7:0;shoe.position.set(side*.16,riding?.34:.05,riding?-.38:-.05);arm.rotation.x=riding?-.85:0;arm.position.z=riding?-.15:0;}
 }
 return{group,body,head,backpack,setRiding,height:1.76};
}
