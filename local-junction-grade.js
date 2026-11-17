import {localJunctionGrade} from './data/local-junction-grade.js';
// A flat core retains the full half-storey drop across the junction and curbs.
// Quintic falloff has zero first/second derivatives at both ends of the blend.
export function localJunctionOffset(x,z,config=localJunctionGrade){const d=Math.hypot(x-config.center[0],z-config.center[1]);if(d<=config.coreRadius)return-config.drop;if(d>=config.fadeRadius)return 0;const t=(d-config.coreRadius)/(config.fadeRadius-config.coreRadius),ease=t*t*t*(10+t*(-15+6*t));return-config.drop*(1-ease);}
export function hasLocalJunction(roads){return localJunctionGrade.roads.every(id=>roads.some(r=>r.osm===id));}
