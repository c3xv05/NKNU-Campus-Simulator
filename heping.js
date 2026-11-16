import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js';
import {createAvatar} from './avatar.js';
import {createScooter} from './scooter.js';
import {mountCampusSwitcher} from './campus-switcher.js';
import {createHepingWorld} from './heping-world.js';
import {isDeveloper} from './developer-auth.js';
import {mountDeveloperCoordinates} from './developer-coordinates.js';
import {ringDistance} from './planar.js';
const $=id=>document.getElementById(id);
mountCampusSwitcher('heping',[$('top'),$('panel')]);
try{await start();}catch(error){$('notice').textContent='校園載入失敗，請重新整理後再試。';$('play').textContent='載入失敗';console.error(error);}
async function start(){
 const response=await fetch('./campuses/heping/campus.json');if(!response.ok)throw Error('和平校區圖資載入失敗');const data=await response.json(),world=createHepingWorld(data);
 const scene=new THREE.Scene();scene.background=new THREE.Color('#a4d8ec');scene.fog=new THREE.Fog('#a4d8ec',380,1000);
 const camera=new THREE.PerspectiveCamera(60,innerWidth/innerHeight,.1,1300);
 const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setSize(innerWidth,innerHeight);renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.outputColorSpace=THREE.SRGBColorSpace;$('scene').append(renderer.domElement);
 scene.add(new THREE.HemisphereLight(0xffffff,0x6c8560,2.5));const sun=new THREE.DirectionalLight(0xfff3d9,2.3);sun.position.set(-180,300,100);scene.add(sun);
 const material=color=>new THREE.MeshStandardMaterial({color,roughness:.9}),obstacles=[];
 function meshTriangles(tris,color,y){const vertices=tris.flatMap(t=>t.flatMap(([x,z])=>[x,y,z]));const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));geometry.computeVertexNormals();const mat=material(color);mat.side=THREE.DoubleSide;const mesh=new THREE.Mesh(geometry,mat);scene.add(mesh);return mesh;}
 function shape(ring){const s=new THREE.Shape();ring.forEach(([x,z],i)=>i?s.lineTo(x,-z):s.moveTo(x,-z));s.closePath();return s;}
 function polygon(ring,color,y=0){const geometry=new THREE.ShapeGeometry(shape(ring));geometry.rotateX(-Math.PI/2);const mesh=new THREE.Mesh(geometry,material(color));mesh.position.y=y;scene.add(mesh);return mesh;}
 // Cut the surrounding ground at the campus boundary; no hidden near-coplanar plane.
 meshTriangles(data.surrounding,'#93a884',0);
 // Ground is cut to exactly the pavement/building boundaries at their shared y=0.
 meshTriangles(data.ground,'#97b887',0);meshTriangles(data.track,'#b36a56',0);meshTriangles(data.road,'#62696a',0);meshTriangles(data.paths,'#ded8c7',0);
 for(const court of data.courts){polygon(court.ring,court.sport==='swimming'?'#4cabc4':court.sport==='soccer'?'#649d6d':'#b58169');
  if(court.sport!=='swimming'){const points=court.ring.map(([x,z])=>new THREE.Vector3(x,.018,z));points.push(points[0]);scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineBasicMaterial({color:'#e9e5ca'})));}}
 for(const b of data.buildings){
  const g=new THREE.ExtrudeGeometry(shape(b.ring),{depth:b.height,bevelEnabled:false});g.rotateX(-Math.PI/2);const mesh=new THREE.Mesh(g,material(b.color));mesh.name='heping-building-'+b.id;scene.add(mesh);obstacles.push(mesh);
  // Simple floor bands; facade details remain unverified approximations.
  const edgeMaterial=new THREE.LineBasicMaterial({color:'#8b9797'});
  for(let level=1;level<b.levels;level++){const pts=b.ring.map(([x,z])=>new THREE.Vector3(x,level*3.6,z));pts.push(pts[0]);scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),edgeMaterial));}
  const p=new THREE.Vector3();new THREE.Box3().setFromObject(mesh).getCenter(p);
  const canvas=document.createElement('canvas');canvas.width=512;canvas.height=80;const ctx=canvas.getContext('2d');ctx.fillStyle='#102a38dd';ctx.fillRect(0,0,512,80);ctx.font='32px sans-serif';ctx.textAlign='center';ctx.fillStyle='white';ctx.fillText(b.name,256,52);const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;const label=new THREE.Sprite(new THREE.SpriteMaterial({map:texture,transparent:true,depthTest:true}));label.position.set(p.x,b.height+4,p.z);label.scale.set(26,4,1);scene.add(label);
 }
 // Deterministic trees only in mapped green areas; excluded from all travel surfaces.
 const trunkMat=material('#78614b'),leafMat=material('#437557');let seed=176;
 const random=()=>((seed=(seed*1664525+1013904223)>>>0)/4294967296);
 for(const green of data.greens){const xs=green.ring.map(p=>p[0]),zs=green.ring.map(p=>p[1]);
  for(let x=Math.min(...xs)+3;x<Math.max(...xs);x+=10)for(let z=Math.min(...zs)+3;z<Math.max(...zs);z+=10){
   const px=x+(random()-.5)*4,pz=z+(random()-.5)*4;
   if(ringDistance(px,pz,green.ring)!==0||world.blocked(px,pz,2)||data.road.concat(data.paths).some(t=>ringDistance(px,pz,t)<3))continue;
   if(data.places.some(p=>Math.hypot(p.position[0]-px,p.position[1]-pz)<3))continue;world.trees.push({x:px,z:pz});
   const trunk=new THREE.Mesh(new THREE.CylinderGeometry(.22,.3,3,6),trunkMat);trunk.position.set(px,1.5,pz);scene.add(trunk);const leaf=new THREE.Mesh(new THREE.IcosahedronGeometry(2.8,0),leafMat);leaf.position.set(px,4,pz);scene.add(leaf);
  }
 }
 const avatar=createAvatar(THREE),player=new THREE.Group(),scooter=createScooter(THREE);player.add(avatar.group,scooter);scene.add(player);player.position.set(data.spawn[0],0,data.spawn[1]);
 let active=false,riding=false,aerial=false,yaw=0,pitch=.3,speed=0,selected=null,previous=performance.now(),time=0;
 const orbit=new THREE.Vector3(player.position.x,0,player.position.z),keys=new Set(),stick={x:0,y:0};let visits=new Set();
 try{const saved=JSON.parse(localStorage.getItem('nknu-heping-visited-v1')||'[]');if(Array.isArray(saved))visits=new Set(saved.filter(id=>data.buildings.some(b=>b.id===id)));}catch{}
 window.campusDeveloperContext=()=>({campus:'heping',page:'和平校區',position:{x:player.position.x,y:0,z:player.position.z},mode:aerial?'aerial':riding?'scooter':'walk',view:{yaw,pitch},...(aerial?{aerial:{center:{x:orbit.x,y:0,z:orbit.z},height:190}}:{})});
 const coordinates=mountDeveloperCoordinates({container:$('tools'),isDeveloper,getContext:window.campusDeveloperContext});
 window.addEventListener('campus-developer-dialog',()=>stop());
 const stop=()=>{keys.clear();stick.x=stick.y=0;speed=0;$('knob').style.transform='';};
 const updateProgress=()=>{$('progress').textContent=`已探索 ${visits.size} / ${data.buildings.length} 個地標`;};updateProgress();
 function travel(id){const place=id==='gate'?{name:'和平一路側入口',position:data.spawn}:data.places.find(p=>p.id===id);if(!place)return;const [x,z]=place.position;if(world.blocked(x,z,riding?.8:.35)){showInfo('此處暫無安全落點');return;}player.position.set(x,0,z);orbit.set(x,0,z);stop();showInfo('已抵達 '+place.name);drawMaps();}
 function showInfo(message){$('info').textContent=message;time=3;}
 for(const place of [{id:'gate',name:'和平一路側入口'},...data.places]){const button=document.createElement('button');button.type='button';button.textContent=place.name;button.onclick=()=>travel(place.id);$('destinations').append(button);}
 function toggleRide(){if(aerial)return;if(!riding&&world.blocked(player.position.x,player.position.z,.8)){showInfo('請先移至較寬的空地再騎車');return;}riding=!riding;avatar.setRiding(riding);scooter.visible=riding;stop();$('ride').textContent=riding?'🚶 下車步行':'🛵 騎機車';$('ride').setAttribute('aria-pressed',String(riding));}
 $('ride').onclick=toggleRide;
 $('aerial').onclick=()=>{aerial=!aerial;orbit.copy(player.position);stop();$('aerial').setAttribute('aria-pressed',String(aerial));$('aerial').textContent=aerial?'返回地面':'空中觀察';$('ride').disabled=aerial;showInfo(aerial?'空中觀察 · 搖桿或WASD平移，拖曳環看':'已返回原地');};
 $('play').disabled=false;$('play').textContent='開始探索';$('play').onclick=()=>{active=true;$('start').hidden=true;stop();};
 const mapDialog=$('mapDialog');function openMap(){stop();drawMaps();mapDialog.showModal();}$('mapOpen').onclick=openMap;$('mapClose').onclick=()=>mapDialog.close();mapDialog.addEventListener('close',stop);
 $('mapTravel').onclick=()=>{if(selected){travel(selected);mapDialog.close();}};
 for(const b of data.buildings){const button=document.createElement('button');button.type='button';button.textContent=b.name;button.dataset.place=b.id;button.setAttribute('aria-pressed','false');button.onclick=()=>select(b.id);$('buildingList').append(button);}
 function select(id){selected=id;const b=data.buildings.find(b=>b.id===id);$('selection').textContent=`${b.name} · ${visits.has(id)?'已探索':'未探索'}（OSM輪廓；外觀近似）`;$('mapTravel').disabled=false;for(const button of $('buildingList').children)button.setAttribute('aria-pressed',String(button.dataset.place===id));drawMaps();}
 const xs=data.boundary.map(p=>p[0]),zs=data.boundary.map(p=>p[1]);const west=Math.min(...xs)-15,east=Math.max(...xs)+15,north=Math.min(...zs)-15,south=Math.max(...zs)+15;
 function drawMap(canvas){const ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height,scale=Math.min(w/(east-west),h/(south-north)),ox=(w-(east-west)*scale)/2,oy=(h-(south-north)*scale)/2;
  const point=([x,z])=>[ox+(x-west)*scale,oy+(z-north)*scale];
  function poly(ring,color){ctx.beginPath();ring.forEach((p,i)=>{const [x,y]=point(p);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.closePath();ctx.fillStyle=color;ctx.fill();}
  ctx.fillStyle='#b6c7a9';ctx.fillRect(0,0,w,h);for(const t of data.campusTriangles)poly(t,'#95b684');for(const t of data.road)poly(t,'#727a79');for(const t of data.paths)poly(t,'#e1dccc');for(const t of data.track)poly(t,'#b36a56');for(const c of data.courts)poly(c.ring,c.sport==='swimming'?'#4cabc4':'#b58169');for(const b of data.buildings){poly(b.ring,b.id===selected?'#f4c75d':visits.has(b.id)?'#297760':'#31596f');if(w>300){const px=b.ring.reduce((s,p)=>s+p[0],0)/b.ring.length,pz=b.ring.reduce((s,p)=>s+p[1],0)/b.ring.length,[x,y]=point([px,pz]);ctx.font='12px sans-serif';ctx.textAlign='center';ctx.fillStyle='#102a38';ctx.fillText(b.name,x,y);}}
  const target=aerial?orbit:player.position,[x,y]=point([target.x,target.z]);ctx.save();ctx.translate(x,y);ctx.rotate(-yaw);ctx.fillStyle='#ffdf68';ctx.strokeStyle='#253d43';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(0,-8);ctx.lineTo(6,6);ctx.lineTo(-6,6);ctx.closePath();ctx.fill();ctx.stroke();ctx.restore();ctx.fillStyle='#193941';ctx.font=`bold ${w>300?18:13}px sans-serif`;ctx.textAlign='left';ctx.fillText('N ↑',8,20);
  canvas.mapPoint=point;
 }
 function drawMaps(){drawMap($('map'));if(mapDialog.open)drawMap($('largeMap'));}
 $('largeMap').onclick=event=>{const canvas=$('largeMap'),rect=canvas.getBoundingClientRect();
  // Canvas is letterboxed by object-fit; account for the actual image rectangle.
  const s=Math.min(rect.width/canvas.width,rect.height/canvas.height),left=rect.left+(rect.width-canvas.width*s)/2,top=rect.top+(rect.height-canvas.height*s)/2;
  const px=(event.clientX-left)/s,py=(event.clientY-top)/s;const candidates=data.buildings.map(b=>{const points=b.ring.map(canvas.mapPoint),x=points.reduce((a,p)=>a+p[0],0)/points.length,y=points.reduce((a,p)=>a+p[1],0)/points.length;return{id:b.id,d:Math.hypot(x-px,y-py)};}).sort((a,b)=>a.d-b.d);if(candidates[0]?.d<55)select(candidates[0].id);
 };
 addEventListener('keydown',event=>{if(['INPUT','TEXTAREA','SELECT'].includes(event.target.tagName))return;if(event.code==='Escape')return;if(!active)return;if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space'].includes(event.code))event.preventDefault();if(event.repeat)return;
  if(event.code==='KeyM'){mapDialog.open?mapDialog.close():openMap();return;}if(mapDialog.open)return;if(event.code==='KeyR')toggleRide();keys.add(event.code);
 });addEventListener('keyup',event=>keys.delete(event.code));addEventListener('blur',stop);document.addEventListener('visibilitychange',stop);
 let drag=null;renderer.domElement.addEventListener('pointerdown',event=>{if(!active||mapDialog.open)return;drag={id:event.pointerId,x:event.clientX,y:event.clientY};renderer.domElement.setPointerCapture(event.pointerId);});
 renderer.domElement.addEventListener('pointermove',event=>{if(!drag||drag.id!==event.pointerId)return;yaw-=(event.clientX-drag.x)*.005;pitch=THREE.MathUtils.clamp(pitch+(event.clientY-drag.y)*.004,-.15,1.1);drag.x=event.clientX;drag.y=event.clientY;});
 for(const name of ['pointerup','pointercancel','lostpointercapture'])renderer.domElement.addEventListener(name,()=>drag=null);
 let joystickPointer=null;const joystick=$('joystick');
 function updateStick(event){const r=joystick.getBoundingClientRect(),dx=(event.clientX-r.left-r.width/2)/(r.width*.35),dy=(event.clientY-r.top-r.height/2)/(r.height*.35),length=Math.max(1,Math.hypot(dx,dy));stick.x=dx/length;stick.y=-dy/length;$('knob').style.transform=`translate(${stick.x*r.width*.28}px,${-stick.y*r.height*.28}px)`;}
 joystick.onpointerdown=event=>{if(!active||mapDialog.open)return;joystickPointer=event.pointerId;joystick.setPointerCapture(event.pointerId);updateStick(event);};joystick.onpointermove=event=>{if(event.pointerId===joystickPointer)updateStick(event);};for(const name of ['pointerup','pointercancel','lostpointercapture'])joystick.addEventListener(name,()=>{joystickPointer=null;stick.x=stick.y=0;$('knob').style.transform='';});
 for(const [id,key] of [['turnL','ArrowLeft'],['turnR','ArrowRight']]){const button=$(id);button.onpointerdown=event=>{if(!active||mapDialog.open)return;button.setPointerCapture(event.pointerId);keys.add(key);};for(const name of ['pointerup','pointercancel','lostpointercapture'])button.addEventListener(name,()=>keys.delete(key));}
 addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);});
 const ray=new THREE.Raycaster(),target=new THREE.Vector3(),cameraTarget=new THREE.Vector3();
 function animate(now){requestAnimationFrame(animate);const dt=Math.min((now-previous)/1000,.05);previous=now;
  if(active&&!mapDialog.open&&!window.campusDeveloper?.isOpen()&&!document.hidden){let forward=(keys.has('KeyW')||keys.has('ArrowUp')?1:0)-(keys.has('KeyS')||keys.has('ArrowDown')?1:0)+stick.y,side=(keys.has('KeyD')?1:0)-(keys.has('KeyA')?1:0)+stick.x;
   yaw+=((keys.has('ArrowLeft')?1:0)-(keys.has('ArrowRight')?1:0))*dt*1.6;
   if(riding&&!aerial){speed=THREE.MathUtils.clamp(speed+forward*dt*5,-3,10);if(Math.abs(forward)<.05)speed*=Math.exp(-dt*2);yaw-=side*dt*1.4*Math.min(1,Math.abs(speed)/2);const dx=-Math.sin(yaw)*speed*dt,dz=-Math.cos(yaw)*speed*dt;if(!world.move(player.position,dx,dz,.8))speed=0;}
   else{const length=Math.max(1,Math.hypot(forward,side)),v=aerial?45:keys.has('ShiftLeft')||keys.has('ShiftRight')?7:3.5;forward/=length;side/=length;const dx=(-Math.sin(yaw)*forward+Math.cos(yaw)*side)*v*dt,dz=(-Math.cos(yaw)*forward-Math.sin(yaw)*side)*v*dt;if(aerial){orbit.x=THREE.MathUtils.clamp(orbit.x+dx,west,east);orbit.z=THREE.MathUtils.clamp(orbit.z+dz,north,south);}else world.move(player.position,dx,dz);speed=0;}
   player.rotation.y=yaw;
   if(!aerial){const near=data.buildings.find(b=>ringDistance(player.position.x,player.position.z,b.ring)<12);if(near&&!visits.has(near.id)){visits.add(near.id);try{localStorage.setItem('nknu-heping-visited-v1',JSON.stringify([...visits]));}catch{}updateProgress();}if(time<=0)$('info').textContent=near?`${near.name} · 外觀量體初版`:'靠近建築查看名稱';}time-=dt;
  }
  target.copy(aerial?orbit:player.position);target.y=aerial?0:1.6;
  if(aerial){const distance=210;cameraTarget.set(target.x+Math.sin(yaw)*distance*.45,target.y+190,target.z+Math.cos(yaw)*distance*.45);}
  else{const distance=riding?8:5;cameraTarget.set(target.x+Math.sin(yaw)*distance*Math.cos(pitch),target.y+2+Math.sin(pitch)*distance,target.z+Math.cos(yaw)*distance*Math.cos(pitch));const direction=cameraTarget.clone().sub(target),length=direction.length();ray.set(target,direction.normalize());ray.far=length;const hit=ray.intersectObjects(obstacles,false)[0];if(hit)cameraTarget.copy(target).addScaledVector(direction,Math.max(.5,hit.distance-.3));}
  camera.position.copy(cameraTarget);camera.lookAt(target);$('speed').textContent=aerial?'空中觀察':riding?`${Math.abs(speed*3.6).toFixed(0)} km/h`:'步行';coordinates.update(now);drawMaps();renderer.render(scene,camera);
 }
 drawMaps();requestAnimationFrame(animate);
}
