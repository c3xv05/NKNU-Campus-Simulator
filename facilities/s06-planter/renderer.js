import {createS06Planter} from './surface.js';
import {ROAD_SURFACE_LIFT} from '../../sidewalk-layout.js';
// Grass bed (30 cm) between the S06 road edge and the set-back walkway; top and walking height share planter.topAt.
export function addS06Planter(THREE,parent,campus,network){
 const planter=createS06Planter(campus,network),group=new THREE.Group();group.name='s06-planter';parent.add(group);
 if(!planter.pieces.length)return{...planter,group};
 const grass=[],concrete=[],v=(p,y)=>[p[0],y,p[1]];
 for(const points of planter.pieces)for(let i=1;i<points.length-1;i++)for(const p of [points[0],points[i],points[i+1]])grass.push(...v(p,planter.topAt(p[0],p[1])));
 // Road-side lip: vertical face from the asphalt surface up to the grass top, along the road edge.
 for(const [a,b] of planter.lips){const ya=network.surfaceHeight(...a)+ROAD_SURFACE_LIFT-.02,yb=network.surfaceHeight(...b)+ROAD_SURFACE_LIFT-.02;concrete.push(...v(a,ya),...v(b,yb),...v(b,planter.topAt(...b)),...v(a,ya),...v(b,planter.topAt(...b)),...v(a,planter.topAt(...a)));}
 const mesh=(positions,color,name)=>{const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.computeVertexNormals();const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color,roughness:1,side:THREE.DoubleSide}));m.name=name;m.receiveShadow=true;group.add(m);return m;};
 mesh(grass,0x6f9a4f,'s06-planter-grass');if(concrete.length)mesh(concrete,0xa3a39b,'s06-planter-lip');
 return{...planter,group};
}
