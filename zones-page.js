import {isDeveloper,logoutDeveloper} from './developer-auth.js';
import {drawReferenceMap} from './zones.js';
import {setupRoadReview} from './road-review.js';
import {attachMapGestures,fitMapView} from './map-gestures.js';
import {readDrafts,DRAFT_KEY,issueLink} from './developer-store.js';
const $=id=>document.getElementById(id);function sync(){const ok=isDeveloper();$('lock').hidden=ok;$('reviewPage').hidden=!ok;$('reviewLogout').hidden=!ok;return ok;}
$('reviewLogout').onclick=logoutDeveloper;window.addEventListener('campus-developer-auth',sync);
if(sync()){
 const r=await fetch('./data/campus.json');if(!r.ok)throw new Error('校園資料讀取失敗');const campus=await r.json(),svg=$('zoneMap');drawReferenceMap(svg,campus);
 const review=setupRoadReview({svg,campus,list:$('zoneList'),selection:$('mapSelection'),container:$('reviewForm'),onLocate:points=>{view=fitMapView(points,base);svg.setAttribute('viewBox',`${view.x} ${view.y} ${view.width} ${view.height}`);},onSubmit:({title,body})=>{const d={id:crypto.randomUUID(),type:'report',title,body,createdAt:new Date().toISOString(),context:{page:'道路分區與人行道校正'}};try{const records=readDrafts(localStorage);records.unshift(d);localStorage.setItem(DRAFT_KEY,JSON.stringify(records));}catch{}const url=issueLink(d);if(url.length<=7500){window.open(url,'_blank','noopener');}else{navigator.clipboard?.writeText(body).then(()=>alert('內容已複製，請貼入 GitHub 回報。')).catch(()=>alert('請使用複製全部回覆，再貼入 GitHub。'));window.open('https://github.com/c3xv05/NKNU-Campus-Simulator/issues/new','_blank','noopener');}}});
 function mode(value){review.setMode(value);$('regionsTab').setAttribute('aria-pressed',String(value==='zones'));$('sidewalksTab').setAttribute('aria-pressed',String(value==='sidewalks'));}
 $('regionsTab').onclick=()=>mode('zones');$('sidewalksTab').onclick=()=>mode('sidewalks');mode('zones');
 const base={x:-446.8,y:-572,width:904.1,height:1135};let view={...base};const gesture=attachMapGestures(svg,{base,getView:()=>view,setView:v=>{view=v;svg.setAttribute('viewBox',`${v.x} ${v.y} ${v.width} ${v.height}`);}});$('reviewZoomIn').onclick=gesture.zoomIn;$('reviewZoomOut').onclick=gesture.zoomOut;$('reviewZoomReset').onclick=gesture.reset;
}
