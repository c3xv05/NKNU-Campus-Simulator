import {createToonKit} from './toon.js';
// Original retro-round small scooter in the shared cartoon style (no brand names or logos).
// Modelled in real metres (≈1.75m long, 0.76m seat) inside a holder that cancels the
// 0.62 scale index.html/heping.js apply to the returned group. Front is -z.
export const SCOOTER_OUTER_SCALE=.62;
export function createScooter(THREE){
 const scooter=new THREE.Group();scooter.name='scooter';scooter.visible=false;
 const body=new THREE.Group();body.scale.setScalar(1/SCOOTER_OUTER_SCALE);scooter.add(body);
 const {part,pivot}=createToonKit(THREE,{outlineWidth:.01});
 const C={paint:0x8fd3c4,cream:0xf6ecd4,chrome:0xd6dcdf,tire:0x2b2b2d,rim:0xb9c2c6,seat:0x5b3b2c,lamp:0xfff3c4,tail:0xe2493b,dark:0x3a3f44};
 const cap=(r,len,seg=12)=>new THREE.CapsuleGeometry(r,len,6,seg),ball=(r,w=18,h=12)=>new THREE.SphereGeometry(r,w,h);

 // Wheels: rounded tyres, painted rims and a hub.
 for(const z of [-.74,.56]){const w=pivot(body,0,.24,z);part(w,new THREE.TorusGeometry(.18,.065,10,22),C.tire,{ry:Math.PI/2});part(w,new THREE.CylinderGeometry(.13,.13,.1,18),C.rim,{rz:Math.PI/2});part(w,new THREE.CylinderGeometry(.045,.045,.14,10),C.chrome,{rz:Math.PI/2,outline:false});}
 // Front fender hugging the front tyre, and the fork.
 part(body,new THREE.TorusGeometry(.25,.05,8,20,Math.PI*.9),C.paint,{y:.25,z:-.74,ry:Math.PI/2,rz:Math.PI*.05,sx:1.4});
 for(const s of [-1,1])part(body,new THREE.CylinderGeometry(.022,.022,.5,8),C.chrome,{x:s*.08,y:.48,z:-.7,rx:-.25,outline:false});
 // Rounded leg shield and front apron.
 part(body,ball(.3),C.paint,{y:.62,z:-.6,sx:1.05,sy:1.45,sz:.55,name:'scooter-shield'});
 part(body,ball(.2),C.cream,{y:.52,z:-.76,sx:1.2,sy:1.3,sz:.35});
 // Floorboard and the curved spine to the rear body.
 part(body,cap(.09,.42),C.cream,{y:.27,z:-.18,rx:Math.PI/2,sx:2.1,sy:1,sz:.6});
 // Plump rear body (the retro "bulbs") and side panels.
 part(body,ball(.32),C.paint,{y:.5,z:.36,sx:1.12,sy:.95,sz:1.55,name:'scooter-rear'});
 part(body,cap(.05,.5,8),C.cream,{y:.5,z:.34,rx:Math.PI/2,sx:7.2,sy:1,sz:1,outline:false});
 // Seat and grab handle.
 part(body,cap(.13,.42),C.seat,{y:.8,z:.18,rx:Math.PI/2,sx:1.45,sz:.55,name:'scooter-seat'});
 part(body,new THREE.TorusGeometry(.14,.018,6,14,Math.PI),C.chrome,{y:.82,z:.62,rx:-Math.PI/2,outline:false});
 // Tail light.
 part(body,ball(.06,12,8),C.tail,{y:.62,z:.86,sx:1.6,sz:.6,outline:false});
 // Steering column, round headset with the retro lamp, handlebar, grips and mirrors.
 part(body,new THREE.CylinderGeometry(.05,.06,.5,10),C.paint,{y:.86,z:-.56,rx:-.22});
 const head=pivot(body,0,1.08,-.55,'scooter-headset');
 part(head,cap(.1,.28),C.paint,{rz:Math.PI/2,sz:.9});
 part(head,new THREE.CylinderGeometry(.085,.095,.07,20),C.chrome,{y:.05,z:-.1,rx:Math.PI/2});
 part(head,new THREE.CircleGeometry(.07,20),C.lamp,{y:.05,z:-.136,ry:Math.PI,outline:false,name:'scooter-headlight'});
 part(head,new THREE.CylinderGeometry(.016,.016,.66,8),C.chrome,{rz:Math.PI/2,outline:false});
 for(const s of [-1,1]){part(head,cap(.025,.1,8),C.dark,{x:s*.33,rz:Math.PI/2});
  part(head,new THREE.CylinderGeometry(.008,.008,.24,6),C.chrome,{x:s*.22,y:.12,z:.02,rz:-s*.3,outline:false});
  part(head,new THREE.CylinderGeometry(.05,.05,.015,16),C.chrome,{x:s*.26,y:.24,z:.02,rx:Math.PI/2});}
 return scooter;
}

// Kept for compatibility with older callers; the avatar now provides its own riding pose.
export function createRiderGear(THREE){const gear=new THREE.Group();gear.name='rider-gear';gear.visible=false;return gear;}
