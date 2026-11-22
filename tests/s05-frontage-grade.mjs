import fs from 'node:fs';import assert from 'node:assert/strict';import {createTerrain} from '../terrain.js';import {createRoadNetwork} from '../roads.js';import {routeSections} from '../pavement.js';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url))),c=read('data/campus.json'),t=createTerrain(read('data/elevation.json'),[...c.places,...c.buildings,...c.water,...c.courts],{levelLink:c.levelLink,courtyard:c.courtyard,bioConnection:c.bioConnection});
const make=o=>createRoadNetwork(c.roads,t.rawHeight,read('data/road-tags.json'),{apron:c.entranceApron,pavedAreas:c.pavedAreas,junctionFillets:c.junctionFillets,sharedGradeGrid:true,...o}),n=make({}),base=make({localFrontageGrade:false}),g=n.localGrade;
assert(g,'S05 frontage grade missing');const r=g.route,s=g.stations;
// Between the Zhili north end and the Gauss south end the centreline falls at one even grade, never level or rising.
let min=Infinity,max=-Infinity,prev=null;for(let i=0;i<r.points.length;i++){if(s[i]<g.from+1||s[i]>g.to-1)continue;const h=n.surfaceHeight(r.points[i].x,r.points[i].z);if(prev){const slope=(prev.h-h)/(s[i]-prev.s);min=Math.min(min,slope);max=Math.max(max,slope);}prev={s:s[i],h};}
assert(min>.025&&max<.037,`S05 frontage grade not even: ${min} .. ${max}`);
// Ends keep the original heights; far outside the ramps nothing changes.
for(const i of [r.points.length-1,r.points.length-2])assert.equal(n.surfaceHeight(r.points[i].x,r.points[i].z),base.surfaceHeight(r.points[i].x,r.points[i].z));assert(Math.abs(n.surfaceHeight(r.points[0].x,r.points[0].z)-base.surfaceHeight(r.points[0].x,r.points[0].z))<.03,'S06 junction end moved');
assert(Math.abs(g.lineStart-base.surfaceHeight(...[r.points.find((_,i)=>s[i]>=g.from).x,r.points.find((_,i)=>s[i]>=g.from).z]))<.02);
// Sidewalks stay level across the road (same limit as campus-refinements) and the gridded surface is continuous.
let cross=0;for(const p of routeSections(r).slice(4,-4)){const half=r.width/2,a=half+.3,b=half+3.3;for(const side of [-1,1])cross=Math.max(cross,Math.abs(n.surfaceHeight(p.x+p.nx*side*b,p.z+p.nz*side*b)-n.surfaceHeight(p.x+p.nx*side*a,p.z+p.nz*side*a))/(b-a));}assert(cross<.02,'crossfall '+cross);
// The offset itself is continuous (lateral taper stays gentler than 0.4 m per m) (pre-existing site steps elsewhere in the window are not ours).
let jump=0;for(let z=-300;z<-160;z+=.5)for(let x=-125;x<-70;x+=.7){const o=g.offset(x,z);jump=Math.max(jump,Math.abs(o-g.offset(x+.05,z)),Math.abs(o-g.offset(x,z+.05)));}assert(jump<.02,'offset changes faster than 0.4 m per m: '+jump);
console.log('PASS: S05 Zhili/Gauss frontage falls at one even grade',{min,max,cross,jump});
