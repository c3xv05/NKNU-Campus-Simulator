import {ringDistance} from './planar.js';
export {ringDistance} from './planar.js';
import {createSiteLevels} from './site-levels.js';
import {yongjiHeightAdjustment} from './terrain-calibration.js';
// Pure terrain sampling shared by rendering, collision height and tests.
export function sampleElevation(grid, x, z) {
  const gx = Math.max(0, Math.min(grid.columns - 1, (x - grid.west) / grid.step));
  const gz = Math.max(0, Math.min(grid.rows - 1, (z - grid.north) / grid.step));
  const c = Math.min(Math.floor(gx), grid.columns - 2), r = Math.min(Math.floor(gz), grid.rows - 2);
  const u = gx - c, v = gz - r, a = r * grid.columns + c;
  return (grid.heights[a] * (1-u) + grid.heights[a+1] * u) * (1-v)
    + (grid.heights[a+grid.columns] * (1-u) + grid.heights[a+grid.columns+1] * u) * v;
}
export function createTerrain(grid, areas,options={}) {
  const datum = sampleElevation(grid, -268.2, 525.55);
  const smoothRaw=(x,z)=>{
    let sum=0,total=0;for(const [dx,dz,w] of [[0,0,4],[-15,0,2],[15,0,2],[0,-15,2],[0,15,2],[-15,-15,1],[-15,15,1],[15,-15,1],[15,15,1]]){sum+=sampleElevation(grid,x+dx,z+dz)*w;total+=w;}return sum/total-datum;
  };
  const baseRaw=(x,z)=>smoothRaw(x,z)+(options.observationAdjustments===false?0:yongjiHeightAdjustment(x,z));
  let correction=()=>0;
  if(options.levelLink){
    const link=options.levelLink,centre=id=>{if(link.terrainAnchors?.[id]){const [x,z]=link.terrainAnchors[id];return{x,z};}const a=areas.find(a=>a.osm===id);if(!a)return null;const xs=a.ring.map(p=>p[0]),zs=a.ring.map(p=>p[1]);return{x:(Math.min(...xs)+Math.max(...xs))/2,z:(Math.min(...zs)+Math.max(...zs))/2};};
    const from=centre(link.from),to=centre(link.to);
    if(from&&to){const radius=70,k=Math.exp(-((from.x-to.x)**2+(from.z-to.z)**2)/radius**2),difference=(link.toFloor-link.fromFloor)*link.floorHeight;
      const amplitude=(difference-(baseRaw(from.x,from.z)-baseRaw(to.x,to.z)))/(1-k*k);
      correction=(x,z)=>amplitude*(Math.exp(-((x-from.x)**2+(z-from.z)**2)/radius**2)-k*Math.exp(-((x-to.x)**2+(z-to.z)**2)/radius**2));
    }
  }
  const unlevelledHeight=(x,z)=>baseRaw(x,z)+correction(x,z),siteLevels=createSiteLevels(unlevelledHeight);
  const rawHeight=(x,z)=>siteLevels.heightAt(x,z,unlevelledHeight(x,z));
  const pads = areas.map(area => {
    const xs = area.ring.map(p=>p[0]), zs = area.ring.map(p=>p[1]);
    const [x,z] = area.platformAnchor||[(Math.min(...xs)+Math.max(...xs))/2,(Math.min(...zs)+Math.max(...zs))/2];
    return { osm:area.osm,kind:area.kind,holes:area.holes||[],depth:area.depth||2.5,ring: area.ring, west: Math.min(...xs)-15, east: Math.max(...xs)+15,
      north: Math.min(...zs)-15, south: Math.max(...zs)+15, height: siteLevels.levelAt(x,z)!==null?siteLevels.levelAt(x,z)+.185:rawHeight(x,z) };
  });
  if(options.levelLink){const link=options.levelLink,from=pads.find(p=>p.osm===link.from),to=pads.find(p=>p.osm===link.to);if(from&&to)from.height=to.height+(link.toFloor-link.fromFloor)*link.floorHeight;}
  if(options.courtyard){const gauss=pads.find(p=>p.osm===444867692),huanyu=pads.find(p=>p.osm===444867694);if(gauss&&huanyu)huanyu.height=gauss.height+3.6;}
  if(options.bioConnection){const link=options.bioConnection,a=pads.find(p=>p.osm===link.from),b=pads.find(p=>p.osm===link.to);if(a&&b)b.height=a.height;}
  // Apply group offsets after floor constraints; road elevations keep their original anchors.
  for(const area of areas){if(area.platformOffset){const pad=pads.find(p=>p.osm===area.osm);if(pad)pad.height+=area.platformOffset;}}
  const platformHeight=area=>pads.find(p=>p.osm===area.osm)?.height;
  function shaped(x,z) {
    const raw = rawHeight(x,z);
    let strength=0,total=0,target=0;
    for(const pad of pads){
      if(x<pad.west||x>pad.east||z<pad.north||z>pad.south)continue;
      const d=ringDistance(x,z,pad.ring);
      if(d===0){
        if(pad.kind==='lake'){
          if(pad.holes.some(ring=>ringDistance(x,z,ring)===0))return raw;
          let shore=Infinity;for(let i=0;i<pad.ring.length;i++){const a=pad.ring[i],b=pad.ring[(i+1)%pad.ring.length],dx=b[0]-a[0],dz=b[1]-a[1],u=Math.max(0,Math.min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz||1)));shore=Math.min(shore,Math.hypot(x-a[0]-dx*u,z-a[1]-dz*u));}
          const u=Math.min(1,shore/4);return pad.height-pad.depth*u*u*(3-2*u);
        }
        return pad.height;
      }
      const t=Math.max(0,Math.min(1,d/15)),weight=1-t*t*(3-2*t);
      const influence=weight**4/(d*d+.0025);
      strength=Math.max(strength,weight);total+=influence;target+=pad.height*influence;
    }
    return siteLevels.heightAt(x,z,total ? raw+(target/total-raw)*strength : raw,true);
  }

  const mesh = {west:grid.west, north:grid.north, step:4,
    columns:(grid.columns-1)*grid.step/4+1, rows:(grid.rows-1)*grid.step/4+1};
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
  return {mesh,height,datum,platformHeight,rawHeight};
}
