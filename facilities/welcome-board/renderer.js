export function boardContent(config,now=new Date()){
 const c=config.campaigns?.[config.activeCampaign],t=+now;
 const active=c&&(!c.startsAt||t>=Date.parse(c.startsAt))&&(!c.endsAt||t<Date.parse(c.endsAt));
 return {...config.defaultContent,...(active?c.content:{})};
}
export function boardFootprint(c){const [x,z]=c.position,w=c.width/2+.3,d=c.depth/2+.25,cs=Math.cos(c.rotation),sn=Math.sin(c.rotation);return[[-w,-d],[w,-d],[w,d],[-w,d]].map(([u,v])=>[x+u*cs+v*sn,z-u*sn+v*cs]);}
export async function addWelcomeBoard(THREE,scene,groundHeight){
 const base=new URL('./',import.meta.url),response=await fetch(new URL('board.json',base));if(!response.ok)throw new Error('迎賓看板資料載入失敗');const config=await response.json();
 const group=new THREE.Group();group.name=config.id;const [x,z]=config.position;group.position.set(x,groundHeight(x,z),z);group.rotation.y=config.rotation;scene.add(group);
 const blockers=[],steel=new THREE.MeshStandardMaterial({color:0x53666a,roughness:.8}),concrete=new THREE.MeshStandardMaterial({color:0xbdb7a7,roughness:1});
 function box(w,h,d,px,py,mat){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);m.position.set(px,py,0);m.castShadow=true;m.receiveShadow=true;group.add(m);blockers.push(m);return m;}
 box(config.width+.6,.45,config.depth+.5,0,.225,concrete).name='welcome-board-base';
 for(const side of [-1,1])box(.22,config.bottom+config.height,config.depth*.65,side*(config.width/2-.7),(config.bottom+config.height)/2,steel);
 box(config.width+.24,config.height+.24,config.depth,0,config.bottom+config.height/2,steel);
 const canvas=document.createElement('canvas');canvas.width=2048;canvas.height=320;const ctx=canvas.getContext('2d'),texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;texture.anisotropy=4;
 const panel=new THREE.Mesh(new THREE.PlaneGeometry(config.width,config.height),new THREE.MeshBasicMaterial({map:texture}));panel.position.set(0,config.bottom+config.height/2,config.depth/2+.015);panel.name='welcome-board-face';group.add(panel);
 const images=new Map();async function image(path){if(!path)return null;const url=new URL(path,base);if(url.origin!==location.origin)throw new Error('活動圖請放在網站內');if(!images.has(url.href))images.set(url.href,new Promise(resolve=>{const i=new Image();i.onload=()=>resolve(i);i.onerror=()=>resolve(null);i.src=url.href;}));return images.get(url.href);}
 let version=0;
 async function setContent(content){const current=++version,[logo,art]=await Promise.all([image(content.emblem?.src),image(content.artwork)]);if(current!==version)return;ctx.fillStyle=content.background;ctx.fillRect(0,0,canvas.width,canvas.height);
  if(art){const scale=Math.max(canvas.width/art.width,canvas.height/art.height),w=art.width*scale,h=art.height*scale;ctx.drawImage(art,(canvas.width-w)/2,(canvas.height-h)/2,w,h);ctx.fillStyle='#071b29bb';ctx.fillRect(0,0,canvas.width,canvas.height);}
  ctx.fillStyle=content.accent;ctx.fillRect(0,canvas.height-9,canvas.width,9);if(logo){ctx.fillStyle='#fff9ea';ctx.beginPath();ctx.arc(165,155,127,0,Math.PI*2);ctx.fill();const crop=content.emblem.crop||[0,0,logo.width,logo.height];ctx.drawImage(logo,...crop,55,45,220,220);}
  const left=logo?330:75;ctx.textAlign='left';ctx.textBaseline='middle';ctx.fillStyle=content.accent;ctx.font='700 45px sans-serif';ctx.fillText(String(content.welcome||''),left,57,canvas.width-left-65);
  ctx.fillStyle=content.foreground;ctx.font='700 100px "Noto Sans TC",sans-serif';ctx.fillText(String(content.title||''),left,158,canvas.width-left-65);ctx.font='36px sans-serif';ctx.fillText(String(content.subtitle||''),left,251,canvas.width-left-65);texture.needsUpdate=true;group.userData.content={...content};
 }
 await document.fonts.ready;await setContent(boardContent(config));
 return{group,blockers,config,ring:boardFootprint(config),setContent,blocked(px,pz,r=.5){const dx=px-x,dz=pz-z,cs=Math.cos(config.rotation),sn=Math.sin(config.rotation);return Math.abs(dx*cs-dz*sn)<config.width/2+.3+r&&Math.abs(dx*sn+dz*cs)<config.depth/2+.25+r;}};
}
