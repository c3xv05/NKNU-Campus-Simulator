import {zones} from './zones.js';
export const landcover={
 A1:{type:'forest',label:'樹林',note:'面向師大路一側為擋土牆；入口三角區為尖端朝南的水滴花圃。'},
 A2:{type:'flowers',label:'花田',note:'大部分空地為花田。'},
 A3:{type:'forest',label:'樹林',note:''},
 B1:{type:'forest',label:'樹林',note:'建築與道路以外基本為樹林。'},
 B2:{type:'forest',label:'樹林',note:'建築與道路以外基本為樹林。'},
 C2:{type:'mixed',label:'北側樹林／其餘雜草',note:'最北側道路以北為樹林；其餘非建築及道路處為雜草。'},
 C3:{type:'weeds',label:'雜草',note:'暫依本次訊息最後一句配置；前文另有樹林描述，待確認。'},
 D3:{type:'weeds',label:'雜草',note:'非建築與道路處為雜草。'}
};
export const northernRoad=[[-195,-259],[-181,-276],[-167,-289],[-121,-311],[-74,-358],[-64,-396],[-17,-427],[0,-435]];
export function zoneAt(x,z){return zones.find(q=>{const[w,n,e,s]=q.box;return x>=w&&x<e&&z>=n&&z<s;});}
export function coverAt(x,z){
 const zone=zoneAt(x,z),record=zone&&landcover[zone.id];if(!record)return 'unknown';
 if(record.type!=='mixed')return record.type;
 let boundary=-435;
 for(let i=1;i<northernRoad.length;i++){
  const a=northernRoad[i-1],b=northernRoad[i];if(x<=b[0]){const t=Math.max(0,Math.min(1,(x-a[0])/(b[0]-a[0])));boundary=a[1]+(b[1]-a[1])*t;break;}
 }
 return z<boundary?'forest':'weeds';
}
