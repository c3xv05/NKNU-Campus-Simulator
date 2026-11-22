import {r04Vegetation} from './data/r04-vegetation.js';
import {r04VegetationSeed} from './data/r04-vegetation-seed.js';
import {prepareRingContains} from './planar.js';
export {r04Vegetation};
const prepare=list=>list.regions.map(r=>({...r,prepared:r.regions.map(([ring,...holes])=>({ring,holes,contains:prepareRingContains(ring),holeContains:holes.map(prepareRingContains),w:Math.min(...ring.map(p=>p[0])),e:Math.max(...ring.map(p=>p[0])),n:Math.min(...ring.map(p=>p[1])),s:Math.max(...ring.map(p=>p[1]))}))}));
const regions=prepare(r04Vegetation),seedRegions=prepare(r04VegetationSeed);
const at=(list,x,z)=>list.find(r=>r.prepared.some(p=>x>=p.w&&x<=p.e&&z>=p.n&&z<=p.s&&p.contains(x,z)&&!p.holeContains.some(contains=>contains(x,z))))||null;
export function r04RegionAt(x,z,seed=false){return at(seed?seedRegions:regions,x,z);}
