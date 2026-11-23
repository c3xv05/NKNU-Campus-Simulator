// 2026-11-23 Bio A/B link from the user's floor plans: levels, terraced ramps/stairs and walking continuity.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createTerrain} from '../terrain.js';
import {createRoadNetwork} from '../roads.js';
import {createCampusCorridors} from '../facilities/campus-corridors/surface.js';
import {accessStairs,biologyTerraceScale,stairSurface} from '../stair-layout.js';
import {stairHeightAt} from '../connections.js';
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url))),c=read('data/campus.json'),t=createTerrain(read('data/elevation.json'),[...c.places,...c.buildings,...c.courts,...c.water],c),n=createRoadNetwork(c.roads,t.rawHeight,read('data/road-tags.json'),{pavedAreas:c.pavedAreas,apron:c.entranceApron,junctionFillets:c.junctionFillets,sharedGradeGrid:true}),s=createCampusCorridors(c,t,n);
const bio=c.bioConnection,A=c.places.find(p=>p.osm===444867696),B=c.places.find(p=>p.osm===444867695);
// Levels: the S05 T deck keeps its height and is 2F; 1F is 4.5 m below (+520 -> +970), upper floors 4.0 m (+970 -> +1370).
assert.equal(t.platformHeight(A),t.platformHeight(B));
for(const b of [A,B]){assert.deepEqual(b.floorLevels,[0,4.5,8.5,12.5,16.5,20.5]);assert.equal(b.height,20.5);assert.equal(b.platformOffset,-.9);}
assert(Math.abs(s.bioFloors[1].level-s.bioFloors[0].level-4.5)<1e-9);
const stem=s.approaches.find(a=>a.id==='biology-s05');assert.equal(stem.level,s.bioFloors[1].level);assert(Math.abs(s.bioFloors[1].level-34.53495109691744)<1e-6,'2F deck = the former T deck height');
// Names follow the drawings (A = 生物科技館, B = 生物教學大樓).
assert(A.name.includes('生物科技館')&&B.name.includes('生物教學大樓'));
// Terraces: drawing +0 at S01, +510 at the hall floor, plan as drawn, rises scaled linearly (user option 1).
const scale=biologyTerraceScale(c,t,n);assert(Math.abs(scale.height(510)-s.bioLower)<1e-9);assert(scale.k>.02&&scale.k<.025,'scaled rise factor ≈2.25');
const defs=accessStairs(c,t,n).filter(d=>d.id.startsWith('biology-terrace'));assert.equal(defs.length,25);
assert.equal(defs.filter(d=>d.type==='ramp').length,7);assert.equal(defs.filter(d=>d.type==='stair').length,8);
const walk=(id,line,y)=>{let max=0;for(let i=0;i<=400;i++){const u=i/400,x=line[0][0]+(line[1][0]-line[0][0])*u,z=line[0][1]+(line[1][1]-line[0][1])*u,h=stairHeightAt(x,z,y,c,t,n);assert(h!==null,id+' lost support at '+u.toFixed(3));max=Math.max(max,Math.abs(h-y));y=h;}return{y,max};};
// Each lane bottom-to-top along its centre line; each ramp low end to high end.
for(const lane of ['left','right']){const parts=defs.filter(d=>d.id.includes('-'+lane+'-'));const bottom=parts[0].line[1],top=parts.at(-1).line[0];const r=walk(lane,[bottom,top],parts[0].bottom+.08);assert(Math.abs(r.y-(parts.at(-1).top+.08))<1e-6,lane+' reaches +500');assert(r.max<.5,lane+' riser '+r.max);}
for(const d of defs.filter(d=>d.type==='ramp')){const r=walk(d.id,[d.line[1],d.line[0]],d.bottom+.08);assert(Math.abs(r.y-d.top-.08)<1e-6);assert(r.max<.05,d.id+' smooth ramp');const grade=(d.top-d.bottom)/Math.hypot(d.line[0][0]-d.line[1][0],d.line[0][1]-d.line[1][1]);assert(grade<.3,d.id+' grade '+grade);}
// Every ramp end meets a landing at the same height (no step between ramp and landing).
for(const d of defs.filter(d=>d.type==='ramp'))for(const [end,h] of [[d.line[0],d.top],[d.line[1],d.bottom]]){const landing=defs.find(o=>o!==d&&o.type!=='ramp'&&o.type==='landing'&&Math.abs(o.top-h)<1e-9&&Math.hypot(...[0,1].map(i=>end[i]-(o.line[0][i]+o.line[1][i])/2))<Math.hypot(o.line[0][0]-o.line[1][0],o.line[0][1]-o.line[1][1])/2+o.width);assert(landing,d.id+' end meets a landing at '+h.toFixed(2));}
{const r=defs.find(d=>d.type==='ramp');assert(Math.abs(stairSurface(r,.5)-(r.top+r.bottom)/2)<1e-9);}
// +505 side stairs (user 2026-11-23): 1F door landing -> one 32-riser flight -> T stem floor at the top of the open stair well.
{const side=accessStairs(c,t,n).filter(d=>d.id.startsWith('biology-side'));assert.equal(side.length,4);
 for(const lane of ['left','right']){const landing=side.find(d=>d.id===`biology-side-${lane}-landing`),flight=side.find(d=>d.id===`biology-side-${lane}-stair`);
  assert.equal(landing.top,s.bioLower);assert.equal(flight.bottom,s.bioLower);assert.equal(flight.steps,32);
  assert(Math.abs(flight.top-stem.profile(...flight.line[0]))<1e-9,'top tread = stem floor');const rise=(flight.top-flight.bottom)/32;assert(rise>.15&&rise<.19,'riser '+rise);
  const r=walk(lane+' side stair',[landing.line[1],flight.line[0]],s.bioLower+.08);assert(Math.abs(r.y-flight.top-.08)<1e-6);assert(r.max<.2);
  // Step off the top tread onto the stem: its floor starts at the same height (no step at the well's end).
  const [a,b]=flight.line,len=Math.hypot(a[0]-b[0],a[1]-b[1]),beyond=[a[0]+(a[0]-b[0])/len*.05,a[1]+(a[1]-b[1])/len*.05];assert(Math.abs(stem.heightAt(...beyond)-flight.top)<.02,'stem continues from the top tread');
  {const end=[a[0]+(a[0]-b[0])/len*1.5,a[1]+(a[1]-b[1])/len*1.5];let y=flight.bottom+.08;for(let i=0;i<=400;i++){const u=i/400,x=b[0]+(end[0]-b[0])*u,z=b[1]+(end[1]-b[1])*u,h=stairHeightAt(x,z,y,c,t,n)??s.heightAt(x,z,y);assert(h!==null,lane+' stair -> stem lost support at '+u.toFixed(3));assert(Math.abs(h-y)<.2);y=h;}assert(Math.abs(y-stem.heightAt(...end)-.08)<1e-6,'walked onto the stem');}
  // The well is open: no stem floor above the middle of the flight; the ground stays below every tread.
  const mid=[(a[0]+b[0])/2,(a[1]+b[1])/2];assert.equal(stem.heightAt(...mid),null);assert(c.bioConnection.sideStairs.every(s=>s.pieces.every(p=>p.ring.length===4)),'convex ground cuts (index.html) under both side-stair pieces');}}
console.log('PASS: Bio drawing levels (1F 4.5 m, 2F = T deck), drawing names, 25 terrace pieces, continuous lanes and ramps ≤30%, +505 side stairs up to the T stem',{k:+scale.k.toFixed(4),foot:+scale.foot.toFixed(2),hall:+s.bioLower.toFixed(2)});
