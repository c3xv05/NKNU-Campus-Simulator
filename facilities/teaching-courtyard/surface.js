import {ringDistance} from '../../planar.js';
export function inFloor(x,z,regions){return (regions||[]).some(([outer,...holes])=>ringDistance(x,z,outer)===0&&!holes.some(h=>ringDistance(x,z,h)===0));}
export function courtyardSupportAt(x,z,currentY,campus,terrain){const c=campus.courtyard;if(!c?.floorRegions)return null;const lower=terrain.platformHeight(campus.places.find(a=>a.osm===campus.levelLink.from));for(const [floor,level]of[['upper',lower+c.floorHeight],['lower',lower]])if(Math.abs(currentY-level-.08)<.85&&inFloor(x,z,c.floorRegions[floor]))return level+.08;return null;}
