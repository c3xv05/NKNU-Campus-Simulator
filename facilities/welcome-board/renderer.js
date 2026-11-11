import {ringDistance} from '../../terrain.js';
export function boardContent(config,now=new Date()){
 const c=config.campaigns?.[config.activeCampaign],t=+now;
 const active=c&&(!c.startsAt||t>=Date.parse(c.startsAt))&&(!c.endsAt||t<Date.parse(c.endsAt));
 return {...config.defaultContent,...(active?c.content:{})};
}
export function fitBoardToRoad(config,campus){
 if(config.placement!=='entrance-road-edge')return config;
 const ring=campus.entranceApron.ring,[cx]=config.position,frontLine=[];
 for(let i=0;i<=36;i++){const x=cx-config.width/2+config.width*i/36,hits=[];
  for(let j=0;j<ring.length;j++){const a=ring[j],b=ring[(j+1)%ring.length];if(a[0]===b[0])continue;const t=(x-a[0])/(b[0]-a[0]);if(t>=0&&t<=1)hits.push(a[1]+t*(b[1]-a[1]));}
  if(!hits.length)throw new Error('迎賓看板超出入口道路邊界');frontLine.push([x,Math.min(...hits)]);
 }
 return{...config,rotation:0,position:[cx,frontLine[18][1]-config.depth/2],frontLine};
}
export function boardFootprint(c){if(c.frontLine)return [...c.frontLine,...c.frontLine.toReversed().map(([x,z])=>[x,z-c.depth-.5])];const [x,z]=c.position,w=c.width/2+.3,d=c.depth/2+.25,cs=Math.cos(c.rotation),sn=Math.sin(c.rotation);return[[-w,-d],[w,-d],[w,d],[-w,d]].map(([u,v])=>[x+u*cs+v*sn,z-u*sn+v*cs]);}
export async function addWelcomeBoard(THREE,scene,groundHeight,campus){
 const base=new URL('./',import.meta.url),response=await fetch(new URL('board.json',base));if(!response.ok)throw new Error('迎賓看板資料載入失敗');const config=fitBoardToRoad(await response.json(),campus);
 const group=new THREE.Group();group.name=config.id;const [x,z]=config.position;group.position.set(x,groundHeight(x,z),z);group.rotation.y=config.rotation;scene.add(group);
 const blockers=[],steel=new THREE.MeshStandardMaterial({color:0x53666a,roughness:.8}),concrete=new THREE.MeshStandardMaterial({color:0xbdb7a7,roughness:1});
 const boxes=[];function box(w,h,d,px,py,pz,mat,angle=0){const item={w,h,d,px,py,pz,mat,angle};boxes.push(item);return item;}
 const line=config.frontLine?.map(([px,pz])=>[px-x,pz-z])||[[-config.width/2,config.depth/2],[config.width/2,config.depth/2]],facePositions=[],uv=[];
 for(let i=1;i<line.length;i++){const a=line[i-1],b=line[i],dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz),angle=-Math.atan2(dz,dx),mx=(a[0]+b[0])/2,mz=(a[1]+b[1])/2;
  box(length+.01,.45,config.depth+.5,mx,.225,mz-(config.depth+.5)/2,concrete,angle).name='welcome-board-base';
  box(length+.01,config.height+.24,config.depth,mx,config.bottom+config.height/2,mz-config.depth/2-.025,steel,angle);
  const low=config.bottom,high=low+config.height,pa=[a[0],low,a[1]+.06],pb=[b[0],low,b[1]+.06],pc=[a[0],high,a[1]+.06],pd=[b[0],high,b[1]+.06],u=(i-1)/(line.length-1),v=i/(line.length-1);facePositions.push(...pa,...pb,...pc,...pb,...pd,...pc);uv.push(u,0,v,0,u,1,v,0,v,1,u,1);
 }
 for(const i of [1,Math.floor(line.length/2),line.length-2]){const p=line[Math.max(0,i)];box(.22,config.bottom+config.height,config.depth*.65,p[0],(config.bottom+config.height)/2,p[1]-config.depth/2-.03,steel);}
 for(const mat of [concrete,steel]){const items=boxes.filter(b=>b.mat===mat),mesh=new THREE.InstancedMesh(new THREE.BoxGeometry(1,1,1),mat,items.length),dummy=new THREE.Object3D();mesh.name=mat===concrete?'welcome-board-base':'welcome-board-frame';for(let i=0;i<items.length;i++){const b=items[i];dummy.position.set(b.px,b.py,b.pz);dummy.rotation.set(0,b.angle,0);dummy.scale.set(b.w,b.h,b.d);dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix);}mesh.instanceMatrix.needsUpdate=true;mesh.castShadow=true;mesh.receiveShadow=true;group.add(mesh);blockers.push(mesh);}
 const canvas=document.createElement('canvas');canvas.width=2048;canvas.height=320;const ctx=canvas.getContext('2d'),texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;texture.anisotropy=4;
 const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(facePositions,3));geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));geometry.computeVertexNormals();const panel=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({map:texture,polygonOffset:true,polygonOffsetFactor:-1,polygonOffsetUnits:-1}));panel.name='welcome-board-face';group.add(panel);
 const images=new Map();async function image(path){if(!path)return null;const url=new URL(path,base);if(url.origin!==location.origin)throw new Error('活動圖請放在網站內');if(!images.has(url.href))images.set(url.href,new Promise(resolve=>{const i=new Image();i.onload=()=>resolve(i);i.onerror=()=>resolve(null);i.src=url.href;}));return images.get(url.href);}
 let version=0;
 async function setContent(content){const current=++version,[logo,art]=await Promise.all([image(content.emblem?.src),image(content.artwork)]);if(current!==version)return;ctx.fillStyle=content.background;ctx.fillRect(0,0,canvas.width,canvas.height);
  if(art){const scale=Math.max(canvas.width/art.width,canvas.height/art.height),w=art.width*scale,h=art.height*scale;ctx.drawImage(art,(canvas.width-w)/2,(canvas.height-h)/2,w,h);ctx.fillStyle='#071b29bb';ctx.fillRect(0,0,canvas.width,canvas.height);}
  ctx.fillStyle=content.accent;ctx.fillRect(0,canvas.height-9,canvas.width,9);if(logo){ctx.fillStyle='#fff9ea';ctx.beginPath();ctx.arc(165,155,127,0,Math.PI*2);ctx.fill();const crop=content.emblem.crop||[0,0,logo.width,logo.height];ctx.drawImage(logo,...crop,55,45,220,220);}
  const left=logo?330:75;ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillStyle=content.accent;ctx.font='700 45px sans-serif';ctx.fillText(String(content.welcome||''),left,57,canvas.width-left-65);
  ctx.fillStyle=content.foreground;ctx.font='700 100px "Noto Sans TC",sans-serif';ctx.fillText(String(content.title||''),left,158,canvas.width-left-65);ctx.font='36px sans-serif';ctx.fillText(String(content.subtitle||''),left,251,canvas.width-left-65);texture.needsUpdate=true;group.userData.content={...content};
 }
 await document.fonts.ready;await setContent(boardContent(config));
 const ring=boardFootprint(config);return{group,blockers,config,ring,setContent,blocked(px,pz,r=.5){return ringDistance(px,pz,ring)<r;}};
}
