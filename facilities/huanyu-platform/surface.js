import {ringDistance} from '../../planar.js';
const cache=new WeakMap();
export function createHuanyuSurface(campus,terrain,network){
 const a=campus.huanyuAccess;if(!a||!network)return null;const saved=cache.get(network);if(saved?.campus===campus&&saved.terrain===terrain)return saved.surface;
 const building=campus.places.find(b=>b.osm===a.building),level=terrain.platformHeight(building)+(a.entranceFloor-1)*building.floorHeight,[start,end]=a.ramp.line,dx=end[0]-start[0],dz=end[1]-start[1],length=Math.hypot(dx,dz),nx=-dz/length,nz=dx/length,width=a.ramp.width,columns=Math.ceil(width)+1,rows=Math.ceil(length)+1,vertices=[],indices=[];
 for(let row=0;row<rows;row++)for(let col=0;col<columns;col++){const t=row/(rows-1),offset=(col/(columns-1)-.5)*width,x=start[0]+dx*t+nx*offset,z=start[1]+dz*t+nz*offset,road=network.surfaceHeight(start[0]+nx*offset,start[1]+nz*offset)+.185;vertices.push(Math.fround(x),Math.fround(road+(level-road)*t),Math.fround(z));}
 for(let row=0;row<rows-1;row++)for(let col=0;col<columns-1;col++){const i=row*columns+col;indices.push(i,i+columns,i+1,i+1,i+columns,i+columns+1);}
 function heightAt(x,z){if(ringDistance(x,z,a.ring)===0)return level;const t=((x-start[0])*dx+(z-start[1])*dz)/(length*length),offset=(x-start[0])*nx+(z-start[1])*nz;if(t< -1e-7||t>1+1e-7||Math.abs(offset)>width/2+1e-7)return null;const gx=Math.max(0,Math.min(columns-1,(offset/width+.5)*(columns-1))),gz=Math.max(0,Math.min(rows-1,t*(rows-1))),col=Math.min(columns-2,Math.floor(gx)),row=Math.min(rows-2,Math.floor(gz)),u=gx-col,v=gz-row,i=row*columns+col,h=k=>vertices[k*3+1];return u+v<=1?h(i)*(1-u-v)+h(i+1)*u+h(i+columns)*v:h(i+1)*(1-v)+h(i+columns)*(1-u)+h(i+columns+1)*(u+v-1);}
 const surface={level,vertices,indices,heightAt};cache.set(network,{campus,terrain,surface});return surface;
}
export function huanyuSupportAt(x,z,currentY,campus,terrain,network){const surface=createHuanyuSurface(campus,terrain,network),height=surface?.heightAt(x,z);return height!=null&&Math.abs(currentY-height-.08)<.85?height+.08:null;}
