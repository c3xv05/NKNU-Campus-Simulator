import assert from 'node:assert/strict';
import {stepScooter,MAX_SCOOTER_SPEED,SIDEWALK_SCOOTER_SPEED,TILE_SCOOTER_SPEED} from '../travel.js';
const top=(road,side,tile)=>{const s={speed:0,heading:0};for(let i=0;i<2000;i++)stepScooter(s,.05,1,0,road,side,tile);return s.speed*3.6;};
// 2026-11-25 (user): basement road lanes ride like the sidewalk (50), other tiles 40, roads 75, everything else stays slow.
assert.equal(Math.round(top(true,false,false)),75);assert.equal(Math.round(top(false,true,false)),50);assert.equal(Math.round(top(false,false,true)),40);assert.equal(Math.round(top(false,false,false)),14);
assert.ok(Math.abs(TILE_SCOOTER_SPEED*3.6-40)<1e-9&&SIDEWALK_SCOOTER_SPEED>TILE_SCOOTER_SPEED&&MAX_SCOOTER_SPEED>SIDEWALK_SCOOTER_SPEED);
console.log('PASS: scooter speed caps road 75 / sidewalk and basement road 50 / tile 40 km/h');
