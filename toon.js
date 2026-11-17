// Shared bright cartoon look for the player and scooter: three-step toon shading plus an
// inverted-hull outline pushed out along vertex normals by a fixed world-space width.
export function createToonKit(THREE,{outlineColor=0x2a2422,outlineWidth=.012}={}){
 const gradient=new THREE.DataTexture(new Uint8Array([110,190,255]),3,1,THREE.RedFormat);
 gradient.minFilter=gradient.magFilter=THREE.NearestFilter;gradient.generateMipmaps=false;gradient.needsUpdate=true;
 const materials=new Map();
 const mat=color=>{if(!materials.has(color))materials.set(color,new THREE.MeshToonMaterial({color,gradientMap:gradient}));return materials.get(color);};
 const outlineMaterial=new THREE.MeshBasicMaterial({color:outlineColor,side:THREE.BackSide});
 outlineMaterial.onBeforeCompile=shader=>{shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>\ntransformed+=normal*${outlineWidth.toFixed(4)};`);};
 outlineMaterial.customProgramCacheKey=()=> 'toon-outline-'+outlineWidth;
 // Outline geometry must not be shared with flat-shaded parts; capsules/spheres have smooth normals.
 function part(parent,geometry,color,{x=0,y=0,z=0,rx=0,ry=0,rz=0,sx=1,sy=1,sz=1,outline=true,name}={}){
  const mesh=new THREE.Mesh(geometry,mat(color));mesh.position.set(x,y,z);mesh.rotation.set(rx,ry,rz);mesh.scale.set(sx,sy,sz);mesh.castShadow=true;if(name)mesh.name=name;
  if(outline){const hull=new THREE.Mesh(geometry,outlineMaterial);hull.name=(name||'part')+'-outline';hull.castShadow=false;mesh.add(hull);}
  parent.add(mesh);return mesh;
 }
 function pivot(parent,x=0,y=0,z=0,name){const g=new THREE.Group();g.position.set(x,y,z);if(name)g.name=name;parent.add(g);return g;}
 return{mat,part,pivot,gradient,outlineMaterial};
}
