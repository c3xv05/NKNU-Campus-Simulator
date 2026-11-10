// Subtract convex pavement footprints from ground triangles. No raster masking,
// so grass cannot poke through a road even beside a protected building platform.
const area=polygon=>polygon.reduce((sum,p,i)=>{const q=polygon[(i+1)%polygon.length];return sum+p[0]*q[1]-q[0]*p[1];},0);
const areaXZ=polygon=>Math.abs(polygon.reduce((sum,p,i)=>{const q=polygon[(i+1)%polygon.length];return sum+p[0]*q[2]-q[0]*p[2];},0));
function clean(polygon){const result=[];for(const p of polygon){const q=result.at(-1);if(!q||Math.hypot(p[0]-q[0],p[2]-q[2])>1e-8)result.push(p);}if(result.length>1&&Math.hypot(result[0][0]-result.at(-1)[0],result[0][2]-result.at(-1)[2])<1e-8)result.pop();return result.length>=3&&areaXZ(result)>1e-8?result:[];}
export function subtract(subject,clip) {
  let inside=subject;const outside=[],orientation=Math.sign(area(clip))||1;
  for(let i=0;i<clip.length&&inside.length>=3;i++){
    const a=clip[i],b=clip[(i+1)%clip.length],left=[],right=[];
    const distance=p=>orientation*((b[0]-a[0])*(p[2]-a[1])-(b[1]-a[1])*(p[0]-a[0]));
    for(let j=0;j<inside.length;j++){
      const p=inside[j],q=inside[(j+1)%inside.length],dp=distance(p),dq=distance(q);
      if(dp>=-1e-8)left.push(p);
      if(dp<=1e-8)right.push(p);
      if((dp>1e-8&&dq< -1e-8)||(dp< -1e-8&&dq>1e-8)){
        const t=dp/(dp-dq),point=p.map((value,k)=>value+(q[k]-value)*t);
        left.push(point);right.push(point);
      }
    }
    const exterior=clean(right);if(exterior.length>=3)outside.push(exterior);
    inside=clean(left);
  }
  return outside;
}
export function cutRoadsFromGround(mesh,footprints,normals) {
  const size=20,buckets=new Map();
  for(const polygon of footprints){
    if(Math.abs(area(polygon))<1e-8)continue;
    const xs=polygon.map(p=>p[0]),zs=polygon.map(p=>p[1]);
    const item={polygon,west:Math.min(...xs),east:Math.max(...xs),north:Math.min(...zs),south:Math.max(...zs)};
    for(let z=Math.floor(item.north/size);z<=Math.floor(item.south/size);z++)for(let x=Math.floor(item.west/size);x<=Math.floor(item.east/size);x++){
      const key=`${x},${z}`;if(!buckets.has(key))buckets.set(key,[]);buckets.get(key).push(item);
    }
  }
  const positions=[],outputNormals=[];
  function vertex(c,r){const i=r*mesh.columns+c;return[mesh.west+c*mesh.step,mesh.heights[i],mesh.north+r*mesh.step,...(normals?Array.from(normals.slice(i*3,i*3+3)):[])];}
  function triangle(points){
    const xs=points.map(p=>p[0]),zs=points.map(p=>p[2]);const west=Math.min(...xs),east=Math.max(...xs),north=Math.min(...zs),south=Math.max(...zs);
    const candidates=new Set();
    for(let z=Math.floor(north/size);z<=Math.floor(south/size);z++)for(let x=Math.floor(west/size);x<=Math.floor(east/size);x++)for(const item of buckets.get(`${x},${z}`)||[])
      if(item.west<=east&&item.east>=west&&item.north<=south&&item.south>=north)candidates.add(item);
    let pieces=[points];
    for(const {polygon} of candidates){pieces=pieces.flatMap(piece=>subtract(piece,polygon));if(!pieces.length)return;}
    for(const piece of pieces)for(let i=1;i<piece.length-1;i++){
      const [a,b,c]=[piece[0],piece[i],piece[i+1]];
      if(Math.abs((b[0]-a[0])*(c[2]-a[2])-(b[2]-a[2])*(c[0]-a[0]))<1e-8)continue;
      for(const p of [a,b,c]){positions.push(...p.slice(0,3));if(normals)outputNormals.push(...p.slice(3,6));}
    }
  }
  for(let r=0;r<mesh.rows-1;r++)for(let c=0;c<mesh.columns-1;c++){
    const a=vertex(c,r),b=vertex(c+1,r),c0=vertex(c,r+1),d=vertex(c+1,r+1);
    triangle([a,c0,b]);triangle([b,c0,d]);
  }
  return {positions,normals:outputNormals};
}
