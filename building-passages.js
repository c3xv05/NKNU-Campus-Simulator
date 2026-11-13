export function passageLevel(building,terrain){return terrain.platformHeight(building)+(building.passage.floor-1)*(building.floorHeight||3.6);}
export function passageAt(x,z,y,building,terrain,radius=0){
 const p=building.passage;if(!p)return false;const [a,b]=p.line,dx=b[0]-a[0],dz=b[1]-a[1],length=Math.hypot(dx,dz),along=((x-a[0])*dx+(z-a[1])*dz)/length,across=Math.abs((x-a[0])*dz-(z-a[1])*dx)/length,level=passageLevel(building,terrain);
 return along>=-.0001&&along<=length+.0001&&across<=p.width/2-radius&&Math.abs(y-level-.08)<.85;
}
export function passageSupportAt(x,z,y,campus,terrain){for(const a of campus.places)if(passageAt(x,z,y,a,terrain))return passageLevel(a,terrain)+.08;return null;}
