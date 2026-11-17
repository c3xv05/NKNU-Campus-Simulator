import {localJunctionGrade} from './data/local-junction-grade.js';
// A flat core retains the full cumulative drop across the junction and curbs.
// Quintic falloff has zero first/second derivatives at both ends of the blend.
export function localJunctionOffset(x,z,config=localJunctionGrade){const dx=x-config.center[0],dz=z-config.center[1],d=Math.hypot(dx,dz);if(d<=config.coreRadius)return-config.drop;const axis=config.axis||[0,1],along=dx*axis[0]+dz*axis[1],across=-dx*axis[1]+dz*axis[0],metric=Math.hypot(along/(config.alongScale||1),across/(config.acrossScale||1)),fade=config.fadeRadius*d/metric;if(d>=fade)return 0;const t=(d-config.coreRadius)/(fade-config.coreRadius),ease=t*t*t*(10+t*(-15+6*t));return-config.drop*(1-ease);}
export function hasLocalJunction(roads){return localJunctionGrade.roads.every(id=>roads.some(r=>r.osm===id));}
