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
