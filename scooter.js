export function createScooter(THREE){
 const scooter=new THREE.Group();scooter.name='scooter';scooter.visible=false;
 const mat=c=>new THREE.MeshStandardMaterial({color:c,roughness:.75});
 const blue=mat(0x167d8f),black=mat(0x242c31),chrome=mat(0xbac8ca),light=mat(0xfff0b5);
 const box=(w,h,d,x,y,z,m)=>{const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),m);mesh.position.set(x,y,z);mesh.castShadow=true;scooter.add(mesh);return mesh;};
 for(const z of [-.95,.95]){const wheel=new THREE.Mesh(new THREE.CylinderGeometry(.5,.5,.3,12),black);wheel.rotation.z=Math.PI/2;wheel.position.set(0,.5,z);scooter.add(wheel);const hub=new THREE.Mesh(new THREE.CylinderGeometry(.24,.24,.32,10),chrome);hub.rotation.z=Math.PI/2;hub.position.copy(wheel.position);scooter.add(hub);}
 box(.82,.65,.95,0,.95,.5,blue);box(.78,.16,.95,0,1.36,.5,black);
 box(.7,.16,1.3,0,.5,-.1,black);box(.75,1.1,.28,0,1.1,-.8,blue);
 box(.85,.4,.4,0,1.77,-.86,blue);box(.4,.2,.04,0,1.79,-1.08,light);
 box(1.25,.09,.13,0,1.8,-.6,chrome);box(.34,.16,.04,0,1,.99,mat(0xd94f49));
 for(const x of [-.53,.53]){box(.035,.44,.035,x,2,-.63,chrome);box(.23,.16,.07,x,2.23,-.63,chrome);}
 return scooter;
}

export function createRiderGear(THREE){
 const gear=new THREE.Group();gear.name='rider-gear';gear.visible=false;
 const cloth=new THREE.MeshStandardMaterial({color:0x264453,roughness:.9});
 for(const x of [-.32,.32]){const leg=new THREE.Mesh(new THREE.BoxGeometry(.24,.65,.3),cloth);leg.position.set(x,1.05,-.1);leg.rotation.x=-.25;gear.add(leg);const arm=new THREE.Mesh(new THREE.BoxGeometry(.18,.75,.18),cloth);arm.position.set(x*1.35,2.05,-.3);arm.rotation.x=-.6;gear.add(arm);}
 const helmet=new THREE.Mesh(new THREE.SphereGeometry(.58,12,7,0,Math.PI*2,0,Math.PI/2),new THREE.MeshStandardMaterial({color:0xf6ca61,roughness:.55}));helmet.position.set(0,3.05,0);gear.add(helmet);return gear;
}
