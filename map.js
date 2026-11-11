import {sidegateWalls} from './facilities/s24-sidegate/renderer.js';
import {motorPavementPlan} from './data/motor-pavement-plan.js';
import {sidewalkPlan} from './data/sidewalk-plan.js';
import {drawPlanSvg} from './surface-plans.js';
import {setupRoadReview} from './road-review.js';
import {isDeveloper} from './developer-auth.js';
import {attachMapGestures,fitMapView} from './map-gestures.js';
import {svgRoadLabels,svgApron} from './road-names.js';
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
    element('rect',{x,y:z,width:20.1,height:20.1,fill:`hsl(95 24% ${lightness}%)`},tint);
  }
  if(campus.flowerbed)element('polygon',{points:polygon(campus.flowerbed.ring),fill:'#d69baf',stroke:'#f5e6c6','stroke-width':1},svg);
  for(const area of campus.water) element('polygon',{points:polygon(area.ring),fill:'#5a9cb2'});
  for(const area of campus.courts) element('polygon',{points:polygon(area.ring),fill:'#809d88'});

  drawPlanSvg(svg,sidewalkPlan,'#e5e5dd');
  for(const road of campus.roads.filter(r=>r.width<=2.5))element('polyline',{points:polygon(road.line),fill:'none',stroke:road.width<=2.5?'#c8c3b4':'#52595a','stroke-width':road.width,'stroke-linecap':'round','stroke-linejoin':'round'});
  for(const area of [...(campus.pavedAreas||[]),...(campus.junctionFillets||[])])element('polygon',{points:polygon(area.ring),fill:'#52595a','aria-label':area.name},svg);
  drawPlanSvg(svg,motorPavementPlan,'#52595a');
  for(const area of campus.carports||[])element('polygon',{points:polygon(area.ring),fill:area.roofColor,'aria-label':area.name},svg);
  if(campus.sideGate){for(const ring of sidegateWalls(campus.sideGate))element('polygon',{points:polygon(ring),fill:'#9ba6a4'},svg);element('text',{x:campus.sideGate.center[0],y:campus.sideGate.center[1]-10,'text-anchor':'middle','font-size':14,fill:'#173c43',stroke:'#fff','stroke-width':2,'paint-order':'stroke'},svg).textContent='側門';}
  svgApron(svg,campus);
  if(campus.courtyard)element('polygon',{points:polygon(campus.courtyard.ring),fill:'#d5cebc',stroke:'#b69a65','stroke-width':1},svg);
  if(campus.welcomeBoard)element('polygon',{points:polygon(campus.welcomeBoard.ring),fill:'#eebd65','aria-label':'校門迎賓看板'},svg);
  if(campus.gatehouse)element('polygon',{points:polygon(campus.gatehouse.ring),fill:'#8d8073'},svg);
  for(const area of campus.buildings) element('polygon',{points:polygon(area.ring),fill:'#778b86'});
  places.forEach(area=>{
    element('polygon',{points:polygon(area.ring),fill:area.height?'#33556c':'#a55247'});
    if(!area.height)element('polygon',{points:polygon(area.holes[0]),fill:'#7db67e'});
  });
  element('text',{x:bounds.west+22,y:bounds.north+40,'font-size':28,'font-weight':800,fill:'#24382e'},svg,'N ↑');
  element('path',{d:`M ${bounds.east-135} ${bounds.south-30} h 100`,stroke:'#24382e','stroke-width':4});
  element('text',{x:bounds.east-85,y:bounds.south-45,'text-anchor':'middle','font-size':20,fill:'#24382e'},svg,'100 m');
  svgRoadLabels(svg,campus);
  const markers=[],buttons=[];
  const markerLayer=element('g',{});
  let mode='buildings',selectedZone=null;
  let selectedAmenity=null,selected=null,lastUpdate=-Infinity;
  const detail=element('g',{'pointer-events':'none'});
  const highlight=element('circle',{r:24,fill:'none',stroke:'#ffcf60','stroke-width':5,visibility:'hidden'},detail);
  const selectedLabel=element('text',{'text-anchor':'middle','font-size':24,'font-weight':800,fill:'#102b3a',stroke:'#fff8d6','stroke-width':7,'paint-order':'stroke',visibility:'hidden'},detail);
  const gate=document.createElementNS(ns,'text');
  gate.setAttribute('x',-268);gate.setAttribute('y',500);gate.setAttribute('text-anchor','middle');gate.setAttribute('font-size',22);gate.setAttribute('fill','#183e48');gate.textContent='校門';svg.append(gate);
  function choose(index) {
    selected=index;selectedAmenity=null;
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
  const amenityList=document.getElementById('amenityList')||document.createElement('div');amenityList.id='amenityList';if(!amenityList.parentNode)list.after(amenityList);
  const title=document.createElement('p');title.textContent='場地與設施';amenityList.append(title);
  const seen=new Set();
  const amenities=[...campus.buildings.filter(a=>a.name?.includes('警衛室')),...campus.courts,...campus.water];
  for(const area of amenities){
    const identity=area.facility||area.name;if(seen.has(identity))continue;seen.add(identity);
    const x=area.ring.reduce((s,p)=>s+p[0],0)/area.ring.length,z=area.ring.reduce((s,p)=>s+p[1],0)/area.ring.length;
    const label=element('text',{x,y:z-12,'text-anchor':'middle','font-size':17,'font-weight':700,fill:'#173c4d',stroke:'#fff','stroke-width':4,'paint-order':'stroke','pointer-events':'none'},svg,area.name);
    const button=document.createElement('button');button.type='button';button.textContent=area.name;
    button.addEventListener('click',()=>{selected=null;selectedAmenity={...area,x,z};highlight.setAttribute('cx',x);highlight.setAttribute('cy',z);highlight.setAttribute('visibility','visible');selectedLabel.textContent=area.name;selectedLabel.setAttribute('x',x);selectedLabel.setAttribute('y',z-28);selectedLabel.setAttribute('visibility','visible');svg.append(detail);update(true);});amenityList.append(button);
  }
  const link=campus.levelLink;if(link){element('polyline',{points:polygon(link.line),fill:'none',stroke:'#d89a3e','stroke-width':6},svg);element('text',{x:link.line[0][0]-8,y:link.line[0][1]+10,'font-size':15,fill:'#6a481c',stroke:'#fff','stroke-width':3,'paint-order':'stroke'},svg,'致理1F ↔ 高斯2F');}
  if(campus.bioConnection?.stairs)element('polyline',{points:polygon(campus.bioConnection.stairs.line),fill:'none',stroke:'#b5a88c','stroke-width':4,'stroke-dasharray':'2 2'},svg);
  const playerGroup=element('g',{'pointer-events':'none'});
  element('circle',{r:22,fill:'#fff9'},playerGroup);
  const arrow=element('path',{d:'M 0 -17 L -11 11 L 0 6 L 11 11 Z',fill:'#f4aa24',stroke:'#533c18','stroke-width':2},playerGroup);
  const you=element('text',{'text-anchor':'middle','font-size':20,'font-weight':800,fill:'#143344',stroke:'#fff','stroke-width':5,'paint-order':'stroke','pointer-events':'none'},svg,'你在這裡');
  const sidewalkTab=document.createElement('button');sidewalkTab.id='sidewalksMode';sidewalkTab.type='button';sidewalkTab.textContent='人行道逐段確認';sidewalkTab.hidden=true;document.getElementById('zonesMode').after(sidewalkTab);
  const review=setupRoadReview({svg,campus,list,selection,container:selection.parentElement,onLocate:points=>{view=fitMapView(points,baseView);svg.setAttribute('viewBox',`${view.x} ${view.y} ${view.width} ${view.height}`);},onSubmit:record=>{dialog.close();window.campusDeveloper?.openReport(record);}});
  function setMode(next){if(next!=='buildings'&&!isDeveloper())next='buildings';mode=next;const privateMode=next!=='buildings';review.setMode(next);markerLayer.style.display=privateMode?'none':'';detail.style.display=privateMode?'none':'';amenityList.hidden=privateMode;document.getElementById('buildingsMode').setAttribute('aria-pressed',String(!privateMode));document.getElementById('zonesMode').setAttribute('aria-pressed',String(next==='zones'));sidewalkTab.setAttribute('aria-pressed',String(next==='sidewalks'));document.getElementById('mapKey').textContent=privateMode?'開發者校正：分區依道路為界，草稿尚未套用到場景。':'藍色：未探索 · 綠色：已探索；道路名稱依校方地圖核對。';if(!privateMode)list.replaceChildren(...buttons);update(true);}
  function updateAuth(){const enabled=isDeveloper();document.getElementById('zonesMode').hidden=!enabled;sidewalkTab.hidden=!enabled;const link=document.getElementById('vegetationEditorLink');if(link)link.hidden=!enabled;if(!enabled&&mode!=='buildings')setMode('buildings');}
  window.addEventListener('campus-developer-auth',updateAuth);updateAuth();
  document.getElementById('buildingsMode').addEventListener('click',()=>setMode('buildings'));document.getElementById('zonesMode').addEventListener('click',()=>setMode('zones'));sidewalkTab.addEventListener('click',()=>setMode('sidewalks'));
  const baseView={x:bounds.west,y:bounds.north,width:bounds.east-bounds.west,height:bounds.south-bounds.north};let view={...baseView};
  const gestures=attachMapGestures(svg,{base:baseView,getView:()=>view,setView:v=>{view=v;svg.setAttribute('viewBox',`${v.x} ${v.y} ${v.width} ${v.height}`);}});
  const tools=document.createElement('div');tools.className='map-zoom-tools';for(const [label,text,action] of [['放大地圖','＋',gestures.zoomIn],['縮小地圖','－',gestures.zoomOut],['重設地圖','全校',gestures.reset]]){const b=document.createElement('button');b.type='button';b.setAttribute('aria-label',label);b.textContent=text;b.onclick=action;tools.append(b);}svg.before(tools);
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
    if(mode!=='buildings')return;
    if(selectedAmenity){
      selection.textContent=selectedAmenity.name+' · '+(selectedAmenity.kind==='lake'?'湖泊，有湖岸與水體，不能直接穿越湖面。':selectedAmenity.covered?'風雨球場，上方有遮雨棚。':selectedAmenity.tipDirection?'水滴形花圃，尖端朝南，外側道路貼著花圃。':selectedAmenity.desc||'校園建築。');
    }else if(selected!==null){
      const place=places[selected],distance=Math.round(Math.hypot(place.x-player.position.x,place.z-player.position.z));
      const difference=Math.round(terrainHeight(place.x,place.z)-player.position.y);
      const heightText=difference===0?'與目前位置高度相近':`${difference>0?'高於':'低於'}目前位置 ${Math.abs(difference)} 公尺`;
      selection.textContent=`${place.name} · ${visited.has(place.name)?'已探索':'未探索'}。直線距離約 ${distance} 公尺；${heightText}（近似地形）。`;
    }else selection.textContent=`▲ 你的位置 · 模型近似高程約 ${Math.round(player.position.y+datum)} 公尺。選擇建築查看距離與高差。`;
  }
  function open() {
    if(!isActive()||dialog.open)return;
    updateAuth();clearInput();dialog.showModal();update(true);document.getElementById('mapClose').focus();
  }
  function close(){dialog.close();}
  openButton.addEventListener('click',open);
  document.getElementById('mapClose').addEventListener('click',close);
  dialog.addEventListener('click',event=>{
    const box=dialog.getBoundingClientRect();
    if(event.target===dialog&&(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom))close();
  });
  dialog.addEventListener('close',()=>{gestures.cancel();clearInput();openButton.focus();});
  dialog.addEventListener('keydown',event=>{if(event.target.closest('input,textarea,select')){event.stopPropagation();return;}if(event.code==='KeyM'&&!event.repeat){event.preventDefault();event.stopPropagation();close();}});
  return {update,toggle(){dialog.open?close():open();}};
}
