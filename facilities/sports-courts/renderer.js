import {ringDistance} from '../../planar.js';
export function addPlayingCourts(THREE,group,court,base){
 const white=new THREE.LineBasicMaterial({color:0xffffff}),steel=new THREE.MeshStandardMaterial({color:0x879d9b,roughness:.8}),boardMat=new THREE.MeshStandardMaterial({color:0xe2e2d4,roughness:.8});
 for(const field of court.playingCourts){const [ux,uz]=field.axis,vx=-uz,vz=ux,[cx,cz]=field.center,world=(x,z,y=base+.10)=>[cx+x*ux+z*vx,y,cz+x*uz+z*vz],line=[];
  const segment=(a,b)=>line.push(...world(...a),...world(...b));
  const arc=(x,z,r,start,end)=>{for(let i=0;i<48;i++){const a=start+(end-start)*i/48,b=start+(end-start)*(i+1)/48,p=[x+Math.cos(a)*r,z+Math.sin(a)*r],q=[x+Math.cos(b)*r,z+Math.sin(b)*r];if([p,q].every(p=>Math.abs(p[0])<=field.length/2+.001&&Math.abs(p[1])<=field.width/2+.001))segment(p,q);}};
  const rectangle=(x0,x1,z0,z1)=>{const p=[[x0,z0],[x1,z0],[x1,z1],[x0,z1]];p.forEach((a,i)=>segment(a,p[(i+1)%4]));};
  rectangle(-field.length/2,field.length/2,-field.width/2,field.width/2);segment([0,-field.width/2],[0,field.width/2]);
  const box=(w,h,d,x,y,z,mat,name)=>{const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);m.rotation.y=Math.atan2(-uz,ux);m.position.set(...world(x,z,y));m.name=name;group.add(m);return m;};
  if(field.sport==='basketball'){
   const scale=field.length/28;arc(0,0,1.8*scale,0,Math.PI*2);
   for(const side of [-1,1]){const baseline=side*field.length/2,hoopX=side*(field.length/2-1.575*scale),free=side*(field.length/2-5.8*scale);rectangle(Math.min(baseline,free),Math.max(baseline,free),-2.45*scale,2.45*scale);arc(free,0,1.8*scale,0,Math.PI*2);arc(hoopX,0,6.75*scale,side>0?Math.PI/2:-Math.PI/2,side>0?Math.PI*1.5:Math.PI/2);
    box(.15,3.3,.15,side*(field.length/2-.3),base+1.65,0,steel,field.id+'-basket-post');box(.12,1.05,1.8,hoopX+side*.45,base+3.5,0,boardMat,field.id+'-backboard');const hoop=new THREE.Mesh(new THREE.TorusGeometry(.225,.025,5,20),new THREE.MeshBasicMaterial({color:0xe87d41}));hoop.rotation.x=Math.PI/2;hoop.position.set(...world(hoopX,0,base+3.05));hoop.name=field.id+'-hoop';group.add(hoop);
   }
  }else{
   for(const side of [-1,1])segment([-field.length/2,side*4.115],[field.length/2,side*4.115]);segment([-6.4,-4.115],[-6.4,4.115]);segment([6.4,-4.115],[6.4,4.115]);segment([-6.4,0],[6.4,0]);
   for(const side of [-1,1])box(.08,1.15,.08,0,base+.575,side*(field.width/2+.45),steel,field.id+'-net-post');
   const net=[];for(let i=0;i<=6;i++)net.push(...world(0,-field.width/2-.45,base+.15+i*.15),...world(0,field.width/2+.45,base+.15+i*.15));const ng=new THREE.BufferGeometry();ng.setAttribute('position',new THREE.Float32BufferAttribute(net,3));const mesh=new THREE.LineSegments(ng,white);mesh.name=field.id+'-net';group.add(mesh);
  }
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(line,3));const markings=new THREE.LineSegments(geometry,white);markings.name=field.id+'-full-court-markings';markings.userData={sport:field.sport,length:field.length,width:field.width,axis:field.axis};group.add(markings);
 }
}
export function addSportsGardens(THREE,group,campus,terrain){
 const solid=new THREE.MeshStandardMaterial({color:0xb9b2a2,roughness:1}),soil=new THREE.MeshStandardMaterial({color:0x665846,roughness:1}),green=new THREE.MeshStandardMaterial({color:0x698653,roughness:1}),petal=new THREE.MeshStandardMaterial({color:0xe9a6bd,roughness:1}),beds=[],flowers=[],dummy=new THREE.Object3D();
 for(const garden of campus.sportsGardens||[]){const [ux,uz]=garden.axis,vx=-uz,vz=ux,top=terrain.platformHeight(campus.courts.find(c=>c.osm===garden.upperCourt))+.07,bottom=terrain.platformHeight(campus.courts.find(c=>c.osm===garden.lowerCourt))+.07,mid=(garden.across[0]+garden.across[1])/2,width=(garden.along[1]-garden.along[0])/garden.tiers;
  for(let i=0;i<garden.tiers;i++){const a=garden.along[0]+i*width,b=a+width,y=top+(bottom-top)*(i+.5)/garden.tiers+garden.rimHeight+(garden.tiers-1-i)*garden.tierRise,base=Math.min(top,bottom)-.7;
   for(const [left,right]of[[garden.across[0],mid-garden.aisleWidth/2],[mid+garden.aisleWidth/2,garden.across[1]]]){const along=(a+b)/2,across=(left+right)/2,x=along*ux+across*vx,z=along*uz+across*vz,bed=new THREE.Mesh(new THREE.BoxGeometry(width,y-base,right-left),solid);bed.position.set(x,(y+base)/2,z);bed.rotation.y=Math.atan2(-uz,ux);bed.name='sports-flowerbed-tier-'+(i+1);group.add(bed);const fill=new THREE.Mesh(new THREE.BoxGeometry(Math.max(.1,width-.22),.08,right-left-.22),soil);fill.position.set(x,y+.015,z);fill.rotation.y=bed.rotation.y;group.add(fill);const ring=[[a,left],[b,left],[b,right],[a,right]].map(([u,v])=>[u*ux+v*vx,u*uz+v*vz]);beds.push({ring,top:y});
    for(let v=left+.35;v<right-.2;v+=.65)flowers.push({x:along*ux+v*vx,z:along*uz+v*vz,y:y+.23,tint:i%2});
   }
  }
 }
 for(const [name,geometry,mat,dy]of[['leaves',new THREE.IcosahedronGeometry(.16,0),green,0],['flowers',new THREE.IcosahedronGeometry(.12,0),petal,.16]]){const mesh=new THREE.InstancedMesh(geometry,mat,flowers.length);flowers.forEach((p,i)=>{dummy.position.set(p.x,p.y+dy,p.z);dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix);});mesh.name='sports-terraced-'+name;mesh.computeBoundingSphere();group.add(mesh);}
 return{beds,blocked(x,z,r){return beds.some(b=>ringDistance(x,z,b.ring)<r+.001);}};
}
