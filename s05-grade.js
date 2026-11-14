// Preserve S05 endpoints. Keep the main climb even and ease it beyond Gauss.
export const S05_GRADE = Object.freeze({road:218881800,gaussNorthZ:-217.239336,transitionLength:32,northernSlopeRatio:.2,core:5.4,fade:14});
export function createS05Grade(routes,height){
 const r=routes.find(r=>r.osm===S05_GRADE.road);if(!r)return null;
 const p=r.points,s=[0];for(let i=1;i<p.length;i++)s.push(s.at(-1)+Math.hypot(p[i].x-p[i-1].x,p[i].z-p[i-1].z));
 const length=s.at(-1),north=height(p[0].x,p[0].z),south=height(p.at(-1).x,p.at(-1).z);
 let gauss=0;for(let i=1;i<p.length;i++)if(p[i-1].z<=S05_GRADE.gaussNorthZ&&p[i].z>=S05_GRADE.gaussNorthZ){gauss=s[i-1]+(s[i]-s[i-1])*(S05_GRADE.gaussNorthZ-p[i-1].z)/(p[i].z-p[i-1].z);break;}
 const start=Math.max(0,gauss-S05_GRADE.transitionLength/2),end=Math.min(length,gauss+S05_GRADE.transitionLength/2),span=end-start,ratio=S05_GRADE.northernSlopeRatio;
 const integral=station=>{const t=Math.max(0,Math.min(1,(station-start)/span));return ratio*station+(1-ratio)*(span*(t*t*t-.5*t*t*t*t)+Math.max(0,station-end));};
 const total=integral(length),heightAt=station=>north+(south-north)*integral(station)/total;
 return{length,gauss,heightAt,sample(x,z){let best=null;for(let i=1;i<p.length;i++){const a=p[i-1],b=p[i],dx=b.x-a.x,dz=b.z-a.z,l=s[i]-s[i-1],t=Math.max(0,Math.min(1,((x-a.x)*dx+(z-a.z)*dz)/(l*l))),d=Math.hypot(x-a.x-t*dx,z-a.z-t*dz);if(best&&d>=best.distance)continue;const station=s[i-1]+t*l,u=Math.max(0,Math.min(1,(d-S05_GRADE.core)/(S05_GRADE.fade-S05_GRADE.core)));best={height:heightAt(station),station,weight:1-u*u*(3-2*u),distance:d};}return best;},apply(x,z,h){const q=this.sample(x,z);return h+(q.height-h)*q.weight;}};
}
