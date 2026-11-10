// Pure terrain sampling shared by rendering, collision height and tests.
export function sampleElevation(grid, x, z) {
  const gx = Math.max(0, Math.min(grid.columns - 1, (x - grid.west) / grid.step));
  const gz = Math.max(0, Math.min(grid.rows - 1, (z - grid.north) / grid.step));
  const c = Math.min(Math.floor(gx), grid.columns - 2), r = Math.min(Math.floor(gz), grid.rows - 2);
  const u = gx - c, v = gz - r, a = r * grid.columns + c;
  return (grid.heights[a] * (1-u) + grid.heights[a+1] * u) * (1-v)
    + (grid.heights[a+grid.columns] * (1-u) + grid.heights[a+grid.columns+1] * u) * v;
}
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
export function createTerrain(grid, areas) {
  const datum = sampleElevation(grid, -268.2, 525.55);
  const pads = areas.map(area => {
    const xs = area.ring.map(p=>p[0]), zs = area.ring.map(p=>p[1]);
    const x = (Math.min(...xs)+Math.max(...xs))/2, z = (Math.min(...zs)+Math.max(...zs))/2;
    return { ring: area.ring, west: Math.min(...xs)-15, east: Math.max(...xs)+15,
      north: Math.min(...zs)-15, south: Math.max(...zs)+15, height: sampleElevation(grid,x,z)-datum };
  });
  function shaped(x,z) {
    const raw = sampleElevation(grid,x,z)-datum;
    let bestWeight = 0, value = raw;
    for (const pad of pads) {
      if (x<pad.west || x>pad.east || z<pad.north || z>pad.south) continue;
      const d = ringDistance(x,z,pad.ring);
      const t = Math.max(0, Math.min(1, (d-3)/12));
      const weight = 1-t*t*(3-2*t);
      if (weight>bestWeight) { bestWeight=weight; value=raw+(pad.height-raw)*weight; }
    }
    return value;
  }
  const mesh = {west:grid.west, north:grid.north, step:5,
    columns:(grid.columns-1)*grid.step/5+1, rows:(grid.rows-1)*grid.step/5+1};
  mesh.heights = new Float32Array(mesh.columns*mesh.rows);
  for(let r=0;r<mesh.rows;r++) for(let c=0;c<mesh.columns;c++)
    mesh.heights[r*mesh.columns+c] = shaped(mesh.west+c*mesh.step,mesh.north+r*mesh.step);
  // Same top-right to bottom-left diagonal as the rendered triangles.
  function height(x,z) {
    const gx=Math.max(0,Math.min(mesh.columns-1,(x-mesh.west)/mesh.step));
    const gz=Math.max(0,Math.min(mesh.rows-1,(z-mesh.north)/mesh.step));
    const c=Math.min(Math.floor(gx),mesh.columns-2), r=Math.min(Math.floor(gz),mesh.rows-2);
    const u=gx-c,v=gz-r,a=r*mesh.columns+c,h=mesh.heights;
    return u+v<=1 ? h[a]*(1-u-v)+h[a+1]*u+h[a+mesh.columns]*v
      : h[a+1]*(1-v)+h[a+mesh.columns]*(1-u)+h[a+mesh.columns+1]*(u+v-1);
  }
  return {mesh,height,datum};
}
