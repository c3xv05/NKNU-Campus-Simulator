import {createXiangyangPlanter} from './surface.js';
export function addXiangyangPlanter(THREE,parent,campus,terrain,network){
 const planter=createXiangyangPlanter(campus,network,terrain),group=new THREE.Group(),blockers=[];group.name='xiangyang-planter';parent.add(group);
 const p=planter.stations;if(p.length<2)return{...planter,group,blockers};
 const concrete=[],grass=[],apron=[],quad=(out,a,b,c,d)=>out.push(...a,...b,...c,...a,...c,...d),v=(xz,y)=>[xz[0],y,xz[1]];
 for(let i=1;i<p.length;i++){const a=p[i-1],b=p[i];
  // Curb: road-side face, top, and inner face down to the grass.
  quad(concrete,v(a.inner,a.road-.05),v(b.inner,b.road-.05),v(b.inner,b.curbTop),v(a.inner,a.curbTop));
  quad(concrete,v(a.inner,a.curbTop),v(b.inner,b.curbTop),v(b.curbOuter,b.curbTop),v(a.curbOuter,a.curbTop));
  quad(concrete,v(a.curbOuter,a.curbTop),v(b.curbOuter,b.curbTop),v(b.curbOuter,b.grass),v(a.curbOuter,a.grass));
  // Grass bed.
  quad(grass,v(a.curbOuter,a.grass),v(b.curbOuter,b.grass),v(b.wallIn,b.grass),v(a.wallIn,a.grass));
  // Court-side ground between the wall and the court/building edge (terrain is clipped here).
  quad(apron,v(a.wallOut,a.courtSide+.02),v(b.wallOut,b.courtSide+.02),v(b.cutOuter,b.courtSide+.02),v(a.cutOuter,a.courtSide+.02));
  // Court wall: lip above the grass on the planter side, full height on the court side, and the cap.
  quad(concrete,v(a.wallIn,a.grass),v(b.wallIn,b.grass),v(b.wallIn,b.wallTop),v(a.wallIn,a.wallTop));
  quad(concrete,v(a.wallOut,a.wallBottom),v(a.wallOut,a.wallTop),v(b.wallOut,b.wallTop),v(b.wallOut,b.wallBottom));
  quad(concrete,v(a.wallIn,a.wallTop),v(b.wallIn,b.wallTop),v(b.wallOut,b.wallTop),v(a.wallOut,a.wallTop));}
 // Planter end walls close the raised bed down to the ground at both ends.
 for(const [e,flip] of [[p[0],false],[p.at(-1),true]]){const lo=Math.min(e.wallBottom,e.road-.3),pts=[v(e.inner,lo),v(e.wallOut,lo),v(e.wallOut,e.wallTop),v(e.inner,e.curbTop)];if(flip)pts.reverse();quad(concrete,...pts);}
 const mesh=(positions,color,name)=>{const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.computeVertexNormals();const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color,roughness:1,side:THREE.DoubleSide}));m.name=name;m.receiveShadow=true;m.castShadow=true;group.add(m);return m;};
 blockers.push(mesh(concrete,0xa3a39b,'xiangyang-planter-concrete'));mesh(grass,0x6f9a4f,'xiangyang-planter-grass');mesh(apron,0x85bb78,'xiangyang-court-side-ground');
 // Chain-link fence on the wall above road level, matching the tennis court fences.
 const steel=new THREE.MeshStandardMaterial({color:0x52736b,roughness:.75}),wire=new THREE.LineBasicMaterial({color:0x55716a}),posts=[],wires=[],dummy=new THREE.Object3D(),up=new THREE.Vector3(0,1,0);
 const mid=q=>[(q.wallIn[0]+q.wallOut[0])/2,(q.wallIn[1]+q.wallOut[1])/2];
 function beam(a,b,thickness=.06){const va=new THREE.Vector3(...a),vb=new THREE.Vector3(...b),d=vb.clone().sub(va);dummy.position.copy(va).add(vb).multiplyScalar(.5);dummy.quaternion.setFromUnitVectors(up,d.clone().normalize());dummy.scale.set(thickness,d.length(),thickness);dummy.updateMatrix();posts.push(dummy.matrix.clone());}
 const h=planter.config.fenceHeight,step=Math.max(1,Math.round(planter.config.postSpacing/.5));
 for(let i=0;i<p.length;i+=step)beam(v(mid(p[i]),p[i].wallTop),v(mid(p[i]),p[i].wallTop+h),.08);beam(v(mid(p.at(-1)),p.at(-1).wallTop),v(mid(p.at(-1)),p.at(-1).wallTop+h),.08);
 for(let i=1;i<p.length;i++){const a=p[i-1],b=p[i],ma=mid(a),mb=mid(b),len=Math.hypot(mb[0]-ma[0],mb[1]-ma[1]);
  for(const f of [0,.5,1])beam(v(ma,a.wallTop+h*f),v(mb,b.wallTop+h*f),.045);
  // Diamond mesh: diagonal wires in both directions every 0.28m along this panel.
  for(const sign of [-1,1])for(let k=0;k*.28<h;k++){const y0=k*.28,lerp=t=>[ma[0]+(mb[0]-ma[0])*t,ma[1]+(mb[1]-ma[1])*t],base=t=>a.wallTop*(1-t)+b.wallTop*t;const t1=Math.min(1,(h-y0)/Math.max(len,1e-6));if(sign>0)wires.push(...v(lerp(0),base(0)+y0),...v(lerp(t1),base(t1)+y0+t1*len));else wires.push(...v(lerp(1),base(1)+y0),...v(lerp(1-t1),base(1-t1)+y0+t1*len));}}
 const frame=new THREE.InstancedMesh(new THREE.BoxGeometry(1,1,1),steel,posts.length);posts.forEach((m,i)=>frame.setMatrixAt(i,m));frame.name='xiangyang-fence-frame';frame.castShadow=true;group.add(frame);
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(wires,3));const net=new THREE.LineSegments(g,wire);net.name='xiangyang-chain-link';group.add(net);
 return{...planter,group,blockers};
}
