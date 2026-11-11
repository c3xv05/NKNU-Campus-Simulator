// Names checked against NKNU's campus map and shuttle route documentation.
export const ROAD_NAME_SOURCE='https://w3.nknu.edu.tw/images/files/yt_01_map.pdf';
export const roadNames=[
 {name:'師大路一段',ids:[399030880],official:true,note:'主路名見校方交通資料；本段定位參考OSM'},
 {name:'師大路二段',ids:[399030881],official:true},
 {name:'師大路三段',ids:[293423728],official:true},
 {name:'師大路四段',ids:[218881800],official:true},
 {name:'詠霽路',ids:[293423729,382869349],official:true},
 {name:'清心路',ids:[218881793,218881798,293423731],official:true},
 {name:'向陽路',ids:[218881795],official:true},
 {name:'環手星月大道',ids:[218881799,293423735,399830914],official:true},
 {name:'莘學路',ids:[218881794],official:false,note:'OSM路名，校方資料尚待核對'}
];
export function roadName(id){return roadNames.find(r=>r.ids.includes(id))?.name||'未命名聯絡道路';}
export function lineLength(line){let result=0;for(let i=1;i<line.length;i++)result+=Math.hypot(line[i][0]-line[i-1][0],line[i][1]-line[i-1][1]);return result;}
export function linePoint(line,t=.5){const target=lineLength(line)*t;let sum=0;for(let i=1;i<line.length;i++){const a=line[i-1],b=line[i],len=Math.hypot(b[0]-a[0],b[1]-a[1]);if(sum+len>=target||i===line.length-1){const u=Math.max(0,Math.min(1,(target-sum)/(len||1)));let angle=Math.atan2(b[1]-a[1],b[0]-a[0])*180/Math.PI;if(angle>90)angle-=180;if(angle< -90)angle+=180;return{x:a[0]+(b[0]-a[0])*u,z:a[1]+(b[1]-a[1])*u,angle};}sum+=len;}return{x:line[0][0],z:line[0][1],angle:0};}
export function roadLabels(campus){return roadNames.filter(n=>n.official).flatMap(n=>{const routes=campus.roads.filter(r=>n.ids.includes(r.osm)).sort((a,b)=>lineLength(b.line)-lineLength(a.line));const selected=n.name==='清心路'?routes.slice(0,2):routes.slice(0,1);return selected.map(r=>({...linePoint(r.line,n.name==='詠霽路'?.32:.5),name:n.name,road:r.osm}));});}
export function svgRoadLabels(svg,campus){const ns='http://www.w3.org/2000/svg',g=document.createElementNS(ns,'g');g.setAttribute('class','road-name-labels');g.setAttribute('pointer-events','none');for(const p of roadLabels(campus)){const t=document.createElementNS(ns,'text');for(const [k,v] of Object.entries({x:p.x,y:p.z-7,'text-anchor':'middle','font-size':19,'font-weight':700,fill:'#243b43',stroke:'#fff9df','stroke-width':4,'paint-order':'stroke',transform:`rotate(${p.angle} ${p.x} ${p.z-7})`}))t.setAttribute(k,v);t.textContent=p.name;g.append(t);}svg.append(g);return g;}
export function svgApron(svg,campus,fill='#52595a'){const a=campus.entranceApron;if(!a?.ring)return;const p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',[a.ring,...(a.holes||[])].map(r=>'M '+r.map(v=>v.join(' ')).join(' L ')+' Z').join(' '));p.setAttribute('fill',fill);p.setAttribute('fill-rule','evenodd');svg.append(p);return p;}
