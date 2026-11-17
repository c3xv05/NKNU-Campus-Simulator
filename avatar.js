import {createToonKit} from './toon.js';
// Player: close-to-real body proportions (~7.3 heads, 1.76m) in a bright, rounded cartoon style.
// Front is -z (matches the scooter and camera). update(dt,speed) drives the walk cycle.
export function createAvatar(THREE){
 const group=new THREE.Group();group.name='human-avatar';
 const {part,pivot}=createToonKit(THREE);
 const C={skin:0xf2c6a2,hair:0x3a2720,shirt:0x3d8fd8,collar:0xf4f1ea,pants:0x2e3d5e,shoe:0xf5f3ee,sole:0xe2493b,bag:0xf2b233,strap:0x9a6a1c,eye:0x231b18,helmet:0xffffff,stripe:0xe2493b};
 const cap=(r,len,seg=10)=>new THREE.CapsuleGeometry(r,len,4,seg),ball=(r,w=14,h=10)=>new THREE.SphereGeometry(r,w,h);

 // Torso and hips.
 const torso=pivot(group,0,0,0,'torso');
 const body=part(torso,cap(.15,.26),C.shirt,{y:1.22,sx:1.12,sz:.72,name:'body'});
 part(torso,new THREE.TorusGeometry(.06,.018,6,14),C.collar,{y:1.44,rx:Math.PI/2,sx:1.2,outline:false});
 const hips=part(torso,cap(.13,.08),C.pants,{y:.98,rz:Math.PI/2,sx:1,sy:1.05,sz:.85,name:'hips'});
 const backpack=part(torso,cap(.11,.16),C.bag,{y:1.22,z:.16,sx:1.35,sz:.62,name:'backpack'});
 for(const s of [-1,1])part(torso,cap(.018,.32,6),C.strap,{x:s*.1,y:1.25,z:-.01,rz:s*.12,outline:false});

 // Head.
 const headPivot=pivot(torso,0,1.47,0,'head-pivot');
 part(headPivot,new THREE.CylinderGeometry(.045,.05,.08,10),C.skin,{y:.02,outline:false});
 const head=part(headPivot,ball(.11,18,14),C.skin,{y:.16,sy:1.12,sz:1.04,name:'head'});
 part(headPivot,new THREE.SphereGeometry(.118,18,10,0,Math.PI*2,0,Math.PI*.42),C.hair,{y:.18,z:.012,rx:.28,sy:1.1,sz:1.08,name:'hair'});
 part(headPivot,ball(.112,14,10),C.hair,{y:.16,z:.03,sx:1.02,sy:1.02,sz:.95,outline:false});
 part(headPivot,cap(.03,.12,8),C.hair,{y:.235,z:-.085,rz:Math.PI/2,rx:.35,outline:false});
 for(const s of [-1,1]){part(headPivot,ball(.018,10,8),C.eye,{x:s*.042,y:.163,z:-.104,sy:1.5,sz:.6,outline:false});part(headPivot,ball(.022,8,6),C.skin,{x:s*.112,y:.155,sx:.5,outline:false});}
 const helmet=part(headPivot,new THREE.SphereGeometry(.135,18,10,0,Math.PI*2,0,Math.PI/2),C.helmet,{y:.18,sy:1.05,name:'helmet'});
 part(helmet,new THREE.TorusGeometry(.12,.012,6,20,Math.PI),C.stripe,{y:.04,rx:Math.PI/2,rz:Math.PI/2,outline:false});helmet.visible=false;

 // Limbs: shoulder/hip pivots with elbow/knee joints so the walk can bend them.
 const limbs={};
 for(const s of [-1,1]){
  const shoulder=pivot(torso,s*.205,1.4,0),upper=part(shoulder,cap(.045,.2),C.shirt,{y:-.13});
  const elbow=pivot(shoulder,0,-.28,0);part(elbow,cap(.039,.19),C.skin,{y:-.12});part(elbow,ball(.045),C.skin,{y:-.27,sz:.8});
  const hip=pivot(torso,s*.092,.94,0),thigh=part(hip,cap(.072,.3),C.pants,{y:-.21});
  const knee=pivot(hip,0,-.43,0);part(knee,cap(.06,.3),C.pants,{y:-.2});
  const ankle=pivot(knee,0,-.44,0);part(ankle,cap(.055,.14,10),C.shoe,{y:.03,z:-.04,rx:Math.PI/2,sx:1.05});part(ankle,new THREE.BoxGeometry(.11,.022,.25),C.sole,{y:-.012,z:-.04,outline:false});
  limbs[s]={shoulder,elbow,hip,knee,ankle,upper,thigh};
 }

 let riding=false,phase=0,swing=0;
 function pose(){
  const legSwing=Math.sin(phase)*.55*swing,armSwing=Math.sin(phase)*.42*swing;
  torso.position.set(0,riding?-.07:Math.abs(Math.cos(phase))*.025*swing,0);torso.rotation.x=riding?.12:-.04*swing;
  for(const s of [-1,1]){const L=limbs[s];
   if(riding){L.hip.rotation.set(1.4,0,s*.06);L.knee.rotation.set(-1.45,0,0);L.ankle.rotation.set(.1,0,0);L.shoulder.rotation.set(.95,0,s*.08);L.elbow.rotation.set(.4,0,0);continue;}
   const leg=legSwing*s;L.hip.rotation.set(leg,0,0);L.knee.rotation.set(-Math.max(0,-Math.sin(phase*1+(s>0?0:Math.PI)))*.85*swing-.04,0,0);L.ankle.rotation.set(0,0,0);
   L.shoulder.rotation.set(-armSwing*s,0,s*.06);L.elbow.rotation.set(.15+.25*swing,0,0);
  }
 }
 function setRiding(value){riding=value;helmet.visible=riding;pose();}
 // speed in m/s; stride length ~1.4m so the cycle matches ground speed.
 function update(dt,speed=0){const target=riding?0:Math.min(1,speed/4);swing+=(target-swing)*Math.min(1,dt*10);if(swing>.01)phase+=dt*Math.max(speed,1)/1.4*Math.PI;else phase=0;pose();}
 pose();
 return{group,body,head,backpack,setRiding,update,height:1.76};
}
