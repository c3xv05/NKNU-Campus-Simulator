import {r04Vegetation} from './data/r04-vegetation.js';
import {prepareRingContains} from './planar.js';
export {r04Vegetation};
const regions=r04Vegetation.regions.map(r=>({...r,prepared:r.regions.map(([ring,...holes])=>({ring,holes,contains:prepareRingContains(ring),holeContains:holes.map(prepareRingContains),w:Math.min(...ring.map(p=>p[0])),e:Math.max(...ring.map(p=>p[0])),n:Math.min(...ring.map(p=>p[1])),s:Math.max(...ring.map(p=>p[1]))}))}));
export function r04RegionAt(x,z){return regions.find(r=>r.prepared.some(p=>x>=p.w&&x<=p.e&&z>=p.n&&z<=p.s&&p.contains(x,z)&&!p.holeContains.some(contains=>contains(x,z))))||null;}
