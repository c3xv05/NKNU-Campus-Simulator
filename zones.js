// Reference sectors only: no vegetation classification is inferred or prefilled.
export const zones = [
  {id:'A1',name:'校門至澄月池、師大路西側',box:[-446.8,180,-245,563],label:[-330,310]},
  {id:'A2',name:'校門內中央長形空地',box:[-245,180,-50,563],label:[-160,340]},
  {id:'A3',name:'清心路南段與校區東南側',box:[-50,180,457.3,563],label:[-28,235]},
  {id:'B1',name:'霽遠樓、文萃樓與歸燕食巢周邊',box:[-446.8,-70,-195,180],label:[-290,80]},
  {id:'B2',name:'宿舍東側與中央坡地',box:[-195,-70,-50,180],label:[-125,70]},
  {id:'B3',name:'圖資大樓、清心路與東側坡地',box:[-50,-70,457.3,180],label:[40,75]},
  {id:'C1',name:'教學區西側山坡',box:[-446.8,-410,-195,-70],label:[-255,-210]},
  {id:'C2',name:'致理、高斯、寰宇及生科周邊',box:[-195,-410,0,-70],label:[-115,-135]},
  {id:'C3',name:'操場、球場及東側山坡',box:[0,-410,457.3,-70],label:[155,-310]},
  {id:'D1',name:'科技大樓西側山坡',box:[-446.8,-572,-105,-410],label:[-145,-470]},
  {id:'D2',name:'科技大樓與北側道路',box:[-105,-572,50,-410],label:[-25,-510]},
  {id:'D3',name:'燕窩與東北側山坡',box:[50,-572,457.3,-410],label:[165,-455]}
];
const ns='http://www.w3.org/2000/svg';
export function svgElement(tag,attributes,parent,text) {
  const e=document.createElementNS(ns,tag);
  for(const [key,value] of Object.entries(attributes))e.setAttribute(key,value);
  if(text!==undefined)e.textContent=text;
  parent.append(e);return e;
}
export function drawZoneLayer(svg,campus,onSelect) {
  const defs=svgElement('defs',{},svg),clipId='vegetation-zones-clip';
  const clip=svgElement('clipPath',{id:clipId},defs);
  svgElement('polygon',{points:campus.boundary.map(p=>p.join(',')).join(' ')},clip);
  const layer=svgElement('g',{'aria-label':'待確認植被分區'},svg);
  const boxes=svgElement('g',{'clip-path':`url(#${clipId})`},layer),rectangles=[];
  const labels=svgElement('g',{},layer);
  zones.forEach((zone,index)=>{
    const [west,north,east,south]=zone.box;
    const group=svgElement('g',{role:'button',tabindex:0,'aria-label':`${zone.id} ${zone.name}，植被待確認`},boxes);
    const rectangle=svgElement('rect',{x:west,y:north,width:east-west,height:south-north,fill:index%2?'#8c76be':'#d6ac53','fill-opacity':.18,stroke:'#714b22','stroke-width':3,'stroke-dasharray':'8 6',cursor:'pointer'},group);
    rectangles.push(rectangle);
    const choose=()=>onSelect(zone);
    group.addEventListener('click',choose);
    group.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose();}});
    group.addEventListener('focus',()=>rectangle.setAttribute('stroke-width',6));
    group.addEventListener('blur',()=>rectangle.setAttribute('stroke-width',3));
    const badge=svgElement('g',{transform:`translate(${zone.label[0]} ${zone.label[1]})`,cursor:'pointer'},labels);
    svgElement('rect',{x:-25,y:-19,width:50,height:38,rx:9,fill:'#fff5d5',stroke:'#714b22','stroke-width':2},badge);
    svgElement('text',{'text-anchor':'middle',y:7,'font-size':22,'font-weight':800,fill:'#49371e','pointer-events':'none'},badge,zone.id);
    badge.addEventListener('click',choose);
  });
  return {layer,select(id){rectangles.forEach((r,i)=>{r.setAttribute('fill-opacity',zones[i].id===id ? .45 : .18);r.setAttribute('stroke',zones[i].id===id?'#e94712':'#714b22');});}};
}
export function drawReferenceMap(svg,campus) {
  const poly=ring=>ring.map(p=>p.join(',')).join(' ');
  svg.setAttribute('viewBox','-446.8 -572 904.1 1135');
  svgElement('rect',{x:-446.8,y:-572,width:904.1,height:1135,fill:'#dce4da'},svg);
  svgElement('polygon',{points:poly(campus.boundary),fill:'#c7d6bb',stroke:'#6f876a','stroke-width':2},svg);
  campus.water.forEach(a=>svgElement('polygon',{points:poly(a.ring),fill:'#81b5c4'},svg));
  campus.courts.forEach(a=>svgElement('polygon',{points:poly(a.ring),fill:'#9caaa1'},svg));
  campus.roads.forEach(r=>svgElement('polyline',{points:poly(r.line),fill:'none',stroke:'#82918a','stroke-width':r.width+2,'stroke-linecap':'round','stroke-linejoin':'round'},svg));
  [...campus.buildings,...campus.places].forEach(a=>{
    svgElement('polygon',{points:poly(a.ring),fill:a.height?'#4d6c7e':'#b08272'},svg);
    (a.holes||[]).forEach(r=>svgElement('polygon',{points:poly(r),fill:'#acbc9d'},svg));
  });
  svgElement('text',{x:-425,y:-525,'font-size':27,'font-weight':800,fill:'#2d433c'},svg,'N ↑');
  svgElement('text',{x:-268,y:550,'text-anchor':'middle','font-size':22,'font-weight':800,fill:'#1e403b'},svg,'校門');
  svgElement('text',{x:-305,y:5,'text-anchor':'middle','font-size':17,'font-weight':700,fill:'#193b4c',stroke:'#fff','stroke-width':4,'paint-order':'stroke'},svg,'霽遠樓');
  svgElement('text',{x:70,y:-65,'text-anchor':'middle','font-size':17,'font-weight':700,fill:'#193b4c',stroke:'#fff','stroke-width':4,'paint-order':'stroke'},svg,'圖資大樓');
  svgElement('text',{x:160,y:-230,'text-anchor':'middle','font-size':17,'font-weight':700,fill:'#193b4c',stroke:'#fff','stroke-width':4,'paint-order':'stroke'},svg,'操場');
}
