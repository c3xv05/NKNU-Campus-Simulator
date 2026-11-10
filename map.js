import {landcover,coverAt} from './landcover.js';
import {zones,drawZoneLayer} from './zones.js';
export function setupCampusMap({campus,places,player,visited,bounds,terrainHeight,datum,clearInput,getYaw,isActive}) {
  const dialog=document.getElementById('mapDialog'),svg=document.getElementById('largeMap');
  const list=document.getElementById('buildingList'),selection=document.getElementById('mapSelection');
  const openButton=document.getElementById('mapOpen');
  const ns='http://www.w3.org/2000/svg';
  function element(tag,attributes,parent=svg,text) {
    const node=document.createElementNS(ns,tag);
    for(const [key,value] of Object.entries(attributes))node.setAttribute(key,value);
    if(text!==undefined)node.textContent=text;
    parent.append(node);return node;
  }
  svg.setAttribute('viewBox',`${bounds.west} ${bounds.north} ${bounds.east-bounds.west} ${bounds.south-bounds.north}`);
  const polygon=(ring)=>ring.map(p=>p.join(',')).join(' ');
  element('rect',{x:bounds.west,y:bounds.north,width:bounds.east-bounds.west,height:bounds.south-bounds.north,fill:'#b6c7a9'});
  const defs=element('defs',{}),clip=element('clipPath',{id:'campusClip'},defs);
  element('polygon',{points:polygon(campus.boundary)},clip);
  const tint=element('g',{'clip-path':'url(#campusClip)'});
  for(let z=bounds.north;z<bounds.south;z+=20) for(let x=bounds.west;x<bounds.east;x+=20){
    const lightness=Math.max(43,Math.min(80,78-(terrainHeight(x,z)+datum-45)*.3));
    element('rect',{x,y:z,width:20.1,height:20.1,fill:({forest:'#77956c',flowers:'#c9b28c',weeds:'#a8b37a'})[coverAt(x,z)]||`hsl(95 24% ${lightness}%)`},tint);
  }
  for(const area of campus.water) element('polygon',{points:polygon(area.ring),fill:'#5a9cb2'});
  for(const area of campus.courts) element('polygon',{points:polygon(area.ring),fill:'#809d88'});
  for(const road of campus.roads) element('polyline',{points:polygon(road.line),fill:'none',stroke:'#797e79','stroke-width':road.width+2,'stroke-linecap':'round','stroke-linejoin':'round'});
  for(const area of campus.buildings) element('polygon',{points:polygon(area.ring),fill:'#778b86'});
  places.forEach(area=>{
    element('polygon',{points:polygon(area.ring),fill:area.height?'#33556c':'#a55247'});
    if(!area.height)element('polygon',{points:polygon(area.holes[0]),fill:'#7db67e'});
  });
  element('text',{x:bounds.west+22,y:bounds.north+40,'font-size':28,'font-weight':800,fill:'#24382e'},svg,'N ↑');
  element('path',{d:`M ${bounds.east-135} ${bounds.south-30} h 100`,stroke:'#24382e','stroke-width':4});
  element('text',{x:bounds.east-85,y:bounds.south-45,'text-anchor':'middle','font-size':20,fill:'#24382e'},svg,'100 m');
  const markers=[],buttons=[];
  const markerLayer=element('g',{});
  let mode='buildings',selectedZone=null;
  let selected=null,lastUpdate=-Infinity;
  const detail=element('g',{'pointer-events':'none'});
  const highlight=element('circle',{r:24,fill:'none',stroke:'#ffcf60','stroke-width':5,visibility:'hidden'},detail);
  const selectedLabel=element('text',{'text-anchor':'middle','font-size':24,'font-weight':800,fill:'#102b3a',stroke:'#fff8d6','stroke-width':7,'paint-order':'stroke',visibility:'hidden'},detail);
  const gate=document.createElementNS(ns,'text');
  gate.setAttribute('x',-268);gate.setAttribute('y',500);gate.setAttribute('text-anchor','middle');gate.setAttribute('font-size',22);gate.setAttribute('fill','#183e48');gate.textContent='校門';svg.append(gate);
  function choose(index) {
    selected=index;
    const place=places[index];
    highlight.setAttribute('cx',place.x);highlight.setAttribute('cy',place.z);highlight.setAttribute('visibility','visible');
    selectedLabel.setAttribute('x',Math.max(bounds.west+100,Math.min(bounds.east-100,place.x)));
    selectedLabel.setAttribute('y',place.z-32);selectedLabel.textContent=place.name;selectedLabel.setAttribute('visibility','visible');
    svg.append(detail);
    update(true);
  }
  places.forEach((place,index)=>{
    const group=element('g',{class:'map-place',role:'button',tabindex:0,'aria-label':`${index+1} ${place.name}`},markerLayer);
    const circle=element('circle',{cx:place.x,cy:place.z,r:18,fill:'#255b77',stroke:'#fff','stroke-width':3},group);
    element('text',{x:place.x,y:place.z+5,'text-anchor':'middle','font-size':15,'font-weight':800,fill:'#fff','pointer-events':'none'},group,index+1);
    group.addEventListener('click',()=>choose(index));
    group.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();choose(index);}});
    markers.push(circle);
    const button=document.createElement('button');button.type='button';
    const number=document.createElement('span');number.className='place-number';number.textContent=index+1;
    const name=document.createElement('span');name.textContent=place.name;
    button.append(number,name);button.addEventListener('click',()=>choose(index));list.append(button);buttons.push(button);
  });
  const playerGroup=element('g',{'pointer-events':'none'});
  element('circle',{r:22,fill:'#fff9'},playerGroup);
  const arrow=element('path',{d:'M 0 -17 L -11 11 L 0 6 L 11 11 Z',fill:'#f4aa24',stroke:'#533c18','stroke-width':2},playerGroup);
  const you=element('text',{'text-anchor':'middle','font-size':20,'font-weight':800,fill:'#143344',stroke:'#fff','stroke-width':5,'paint-order':'stroke','pointer-events':'none'},svg,'你在這裡');
  const zoneButtons=zones.map(zone=>{
    const button=document.createElement('button');button.type='button';
    button.textContent=`${zone.id} · ${zone.name}`;button.setAttribute('aria-pressed','false');
    button.addEventListener('click',()=>chooseZone(zone));return button;
  });
  const zoneLayer=drawZoneLayer(svg,campus,chooseZone,landcover);
  svg.insertBefore(zoneLayer.layer,markerLayer);
  zoneLayer.layer.style.display='none';
  function chooseZone(zone) {
    selectedZone=zone;zoneLayer.select(zone.id);
    zoneButtons.forEach((b,i)=>{b.classList.toggle('selected',zones[i].id===zone.id);b.setAttribute('aria-pressed',String(zones[i].id===zone.id));});
    update(true);
  }
  function setMode(next) {
    mode=next;
    const zoning=mode==='zones';
    document.getElementById('mapKey').textContent=zoning?'植被依實地回饋配置；未提供區域保留待確認。':'藍色：未探索 · 綠色：已探索；底色深淺表示近似高低起伏。';
    zoneLayer.layer.style.display=zoning?'':'none';markerLayer.style.display=zoning?'none':'';detail.style.display=zoning?'none':'';
    document.getElementById('buildingsMode').setAttribute('aria-pressed',String(!zoning));
    document.getElementById('zonesMode').setAttribute('aria-pressed',String(zoning));
    list.replaceChildren(...(zoning?zoneButtons:buttons));update(true);
  }
  document.getElementById('buildingsMode').addEventListener('click',()=>setMode('buildings'));
  document.getElementById('zonesMode').addEventListener('click',()=>setMode('zones'));
  function update(force=false) {
    if(!dialog.open)return;
    const now=performance.now();if(!force&&now-lastUpdate<150)return;lastUpdate=now;
    playerGroup.setAttribute('transform',`translate(${player.position.x} ${player.position.z})`);
    arrow.setAttribute('transform',`rotate(${-getYaw()*180/Math.PI})`);
    you.setAttribute('x',player.position.x);you.setAttribute('y',player.position.z-29);
    places.forEach((place,index)=>{
      const found=visited.has(place.name);
      markers[index].setAttribute('fill',found?'#117d65':'#255b77');
      buttons[index].classList.toggle('visited',found);buttons[index].classList.toggle('selected',selected===index);
      buttons[index].setAttribute('aria-pressed',String(selected===index));
      buttons[index].setAttribute('aria-label',`${place.name}，${found?'已探索':'未探索'}`);
    });
    if(mode==='zones'){
      selection.textContent=selectedZone
        ? `${selectedZone.id}｜${selectedZone.name}。${landcover[selectedZone.id]?.label||'植被待確認'}；${landcover[selectedZone.id]?.note||'可補充道路兩側差異。'}`
        : '北方朝上。已依回饋標示樹林、花田與雜草；B3、C1、D1、D2 保留待確認。C3 暫依最後描述配置為雜草。';
    }else if(selected!==null){
      const place=places[selected],distance=Math.round(Math.hypot(place.x-player.position.x,place.z-player.position.z));
      const difference=Math.round(terrainHeight(place.x,place.z)-player.position.y);
      const heightText=difference===0?'與目前位置高度相近':`${difference>0?'高於':'低於'}目前位置 ${Math.abs(difference)} 公尺`;
      selection.textContent=`${place.name} · ${visited.has(place.name)?'已探索':'未探索'}。直線距離約 ${distance} 公尺；${heightText}（近似地形）。`;
    }else selection.textContent=`▲ 你的位置 · 衛星估計高程約 ${Math.round(player.position.y+datum)} 公尺。選擇建築查看距離與高差。`;
  }
  function open() {
    if(!isActive()||dialog.open)return;
    clearInput();dialog.showModal();update(true);document.getElementById('mapClose').focus();
  }
  function close(){dialog.close();}
  openButton.addEventListener('click',open);
  document.getElementById('mapClose').addEventListener('click',close);
  dialog.addEventListener('click',event=>{
    const box=dialog.getBoundingClientRect();
    if(event.target===dialog&&(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom))close();
  });
  dialog.addEventListener('close',()=>{clearInput();openButton.focus();});
  dialog.addEventListener('keydown',event=>{if(event.code==='KeyM'&&!event.repeat){event.preventDefault();event.stopPropagation();close();}});
  return {update,toggle(){dialog.open?close():open();}};
}
