// Shared planar polygon distance without a terrain dependency.
export function ringDistance(x, z, ring) {
  let inside = false, distance = Infinity;
  ring.forEach(([ax, az], i) => {
    const [bx, bz] = ring[(i+1) % ring.length];
    if ((az > z) !== (bz > z) && x < ax + (bx-ax)*(z-az)/(bz-az)) inside = !inside;
    const dx = bx-ax, dz = bz-az, length = dx*dx+dz*dz;
    const t = length ? Math.max(0, Math.min(1, ((x-ax)*dx+(z-az)*dz)/length)) : 0;
    distance = Math.min(distance, Math.hypot(x-ax-dx*t, z-az-dz*t));
  });
  return inside ? 0 : distance;
}

// Prepare immutable region rings once. Classification needs containment, not a
// nearest-edge distance: only edges crossing this north/south band can matter.
export function prepareRingContains(ring) {
  let west=Infinity,east=-Infinity,north=Infinity,south=-Infinity;
  for(const [x,z] of ring){west=Math.min(west,x);east=Math.max(east,x);north=Math.min(north,z);south=Math.max(south,z);}
  const count=Math.max(1,Math.min(256,Math.ceil((south-north)/8))),step=(south-north)/count||1;
  const bands=Array.from({length:count},()=>[]),band=z=>Math.max(0,Math.min(count-1,Math.floor((z-north)/step)));
  for(let i=0;i<ring.length;i++){
    const [ax,az]=ring[i],[bx,bz]=ring[(i+1)%ring.length];
    const edge={ax,az,bx,bz,dx:bx-ax,dz:bz-az,length:(bx-ax)**2+(bz-az)**2};
    for(let k=band(Math.min(az,bz));k<=band(Math.max(az,bz));k++)bands[k].push(edge);
  }
  return (x,z)=>{
    if(x<west||x>east||z<north||z>south)return false;
    let inside=false;
    for(const {ax,az,bx,bz,dx,dz,length} of bands[band(z)]){
      if((az>z)!==(bz>z)&&x<ax+dx*(z-az)/dz)inside=!inside;
      // Match ringDistance===0 at vertices and edges, including horizontal ones.
      if(x>=Math.min(ax,bx)&&x<=Math.max(ax,bx)&&z>=Math.min(az,bz)&&z<=Math.max(az,bz)){
        const t=length?Math.max(0,Math.min(1,((x-ax)*dx+(z-az)*dz)/length)):0;
        if(x-ax-dx*t===0&&z-az-dz*t===0)return true;
      }
    }
    return inside;
  };
}
