// Low-poly tree species (style A): faceted clumps, several silhouettes, all instanced.
// Geometry is unit-sized; landscape.js scales each instance by tree.size.
// Species are generic hillside/campus shapes chosen for variety, not botanical survey data.

function mergeParts(THREE,parts){
 const positions=[],normals=[];
 for(const {geometry,matrix} of parts){
  const g=(geometry.index?geometry.toNonIndexed():geometry.clone()).applyMatrix4(matrix);g.computeVertexNormals();
  positions.push(...g.attributes.position.array);normals.push(...g.attributes.normal.array);g.dispose();geometry.dispose();
 }
 const merged=new THREE.BufferGeometry();
 merged.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
 merged.setAttribute('normal',new THREE.Float32BufferAttribute(normals,3));
 merged.computeBoundingSphere();return merged;
}

function part(THREE,geometry,{x=0,y=0,z=0,sx=1,sy=1,sz=1,rx=0,ry=0,rz=0}={}){
 const m=new THREE.Matrix4().compose(new THREE.Vector3(x,y,z),new THREE.Quaternion().setFromEuler(new THREE.Euler(rx,ry,rz)),new THREE.Vector3(sx,sy,sz));
 return{geometry,matrix:m};
}

// Deterministically jitter icosahedron vertices so clumps don't look like perfect gems.
function clump(THREE,seed){
 const g=new THREE.IcosahedronGeometry(1,0),p=g.attributes.position;
 for(let i=0;i<p.count;i++){const k=Math.sin((i+1)*12.9898+seed*78.233)*43758.5453,j=.82+(k-Math.floor(k))*.3;p.setXYZ(i,p.getX(i)*j,p.getY(i)*j,p.getZ(i)*j);}
 return g;
}

export function createTreeSpecies(THREE){
 const trunk=(h,r0,r1,lean=0)=>part(THREE,new THREE.CylinderGeometry(r0,r1,h,6),{y:h/2,rz:lean});
 const branch=(len,r,x,y,rz)=>part(THREE,new THREE.CylinderGeometry(r*.6,r,len,5),{x,y,rz});
 const species=[
  {// Broad round crown (camphor-like), the forest default.
   name:'round',weight:.42,fadeHeight:5,fadeRadius:4.4,
   trunk:mergeParts(THREE,[trunk(4.2,.2,.34),branch(1.6,.13,.45,3.6,-.7),branch(1.4,.12,-.4,3.8,.6)]),
   crown:mergeParts(THREE,[
    part(THREE,clump(THREE,1),{y:5.2,sx:2.3,sy:2,sz:2.2}),
    part(THREE,clump(THREE,2),{x:1.5,y:4.6,z:.4,sx:1.6,sy:1.4,sz:1.5}),
    part(THREE,clump(THREE,3),{x:-1.4,y:4.7,z:-.3,sx:1.6,sy:1.5,sz:1.6}),
    part(THREE,clump(THREE,4),{x:.2,y:6.4,z:-.6,sx:1.5,sy:1.3,sz:1.4}),
    part(THREE,clump(THREE,5),{x:-.3,y:4.4,z:1.4,sx:1.4,sy:1.2,sz:1.3})])
  },
  {// Wide flat umbrella crown (acacia-like), common on dry slopes.
   name:'umbrella',weight:.3,fadeHeight:5.4,fadeRadius:4.8,
   trunk:mergeParts(THREE,[trunk(3.6,.16,.28,.08),branch(2.4,.12,.9,4.3,-.9),branch(2.2,.11,-.8,4.2,.85)]),
   crown:mergeParts(THREE,[
    part(THREE,clump(THREE,6),{x:1.6,y:5.4,sx:2,sy:.9,sz:1.9}),
    part(THREE,clump(THREE,7),{x:-1.5,y:5.3,z:.3,sx:1.9,sy:.85,sz:1.8}),
    part(THREE,clump(THREE,8),{y:5.9,z:-.4,sx:2.1,sy:.9,sz:2}),
    part(THREE,clump(THREE,9),{x:.3,y:5.2,z:1.5,sx:1.6,sy:.75,sz:1.4})])
  },
  {// Tiered horizontal layers (tropical almond-like), used on campus edges.
   name:'tiered',weight:.18,fadeHeight:5,fadeRadius:4.1,
   trunk:mergeParts(THREE,[trunk(6.6,.13,.24)]),
   crown:mergeParts(THREE,[
    part(THREE,clump(THREE,11),{y:3.5,sx:2.8,sy:.45,sz:2.6,ry:.3}),
    part(THREE,clump(THREE,12),{y:4.7,sx:2.2,sy:.42,sz:2.1,ry:1.1}),
    part(THREE,clump(THREE,13),{y:5.8,sx:1.6,sy:.4,sz:1.5,ry:.6}),
    part(THREE,clump(THREE,14),{y:6.7,sx:.9,sy:.4,sz:.9,ry:1.7})])
  },
  {// Columnar conifer for silhouette variety on ridges.
   name:'conifer',weight:.1,fadeHeight:4.6,fadeRadius:3.1,
   trunk:mergeParts(THREE,[trunk(2.2,.14,.24)]),
   crown:mergeParts(THREE,[
    part(THREE,new THREE.ConeGeometry(1.8,3,7),{y:3.2}),
    part(THREE,new THREE.ConeGeometry(1.4,2.6,7),{y:4.8,ry:.4}),
    part(THREE,new THREE.ConeGeometry(.9,2.2,6),{y:6.3,ry:.9})])
  }
 ];
 return species;
}

// Stable species choice from position so the forest never reshuffles between loads.
export function treeSpeciesIndex(tree,species){
 const k=Math.sin(tree.x*12.9898+tree.z*78.233)*43758.5453,u=k-Math.floor(k);
 let acc=0;for(let i=0;i<species.length;i++){acc+=species[i].weight;if(u<acc)return i;}return species.length-1;
}

// [hue, saturation, lightness] per species; each tree adds a small tint offset.
export const treeCrownPalette=[[.3,.38,.19],[.27,.36,.21],[.32,.42,.18],[.37,.32,.16]];
