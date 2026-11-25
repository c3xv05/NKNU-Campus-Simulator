// Site heights for the 圖資大樓 build (scripts/build-library-interior.py): S04 sidewalk beside the fan plaza,
// raw ground at the pad anchor and the ground at the G/H stair tops. Prints JSON.
import fs from 'node:fs';import {createTerrain} from '../terrain.js';import {createRoadNetwork} from '../roads.js';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url)));const c=read('data/campus.json');
const t=createTerrain(read('data/elevation.json'),[...c.places,...c.buildings,...c.water,...c.courts],{levelLink:c.levelLink,courtyard:c.courtyard,bioConnection:c.bioConnection});
const n=createRoadNetwork(c.roads,t.rawHeight,read('data/road-tags.json'),{apron:c.entranceApron,pavedAreas:c.pavedAreas,junctionFillets:c.junctionFillets,sharedGradeGrid:true});
const q=JSON.parse(process.argv[2]),out={};
for(const [k,[x,z]] of Object.entries(q.walk||{}))out[k]=+n.walkHeight(x,z,t.height(x,z)).toFixed(3);
for(const [k,[x,z]] of Object.entries(q.raw||{}))out[k]=+t.rawHeight(x,z).toFixed(3);
for(const [k,[x,z]] of Object.entries(q.terrain||{}))out[k]=+t.height(x,z).toFixed(3);
console.log(JSON.stringify(out));
