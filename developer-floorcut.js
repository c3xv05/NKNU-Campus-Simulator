// Developer aerial "floor cut": when aerial view is opened from inside a building with a walkable interior,
// a floor can be chosen and everything of that building above the chosen floor's walls is clipped away, so the
// whole floor can be inspected from the air (user 2026-11-19). Clipping is applied to cloned materials only on
// the affected meshes and fully restored when the cut is cleared.
const PLAZA_PREFIXES=['courtyard-','zhili-extension','stepped-planter','gauss-1f','zhili-gauss','compact-teaching'];

export function buildingFloors(THREE,scene,campus,terrain,osm){
 const plan=campus.planInteriors?.[osm];
 if(plan){
  const b=[...campus.places,...campus.buildings].find(a=>a.osm===osm),base=terrain.platformHeight(b),H=plan.floorHeight,slab=plan.slab||.2;
  return{key:plan.key||'zhili',name:b?.name||'',floors:plan.floors.map(f=>({label:f.label,cut:base+f.level+(plan.finish?.ceilingHeight?plan.finish.ceilingHeight-.05:H-slab-.01)})),groups:[(plan.key||'zhili')+'-interior'],plaza:true};
 }
 const j=campus.jiyuanInterior;
 if(j&&osm===j.building){
  const g=scene.getObjectByName('jiyuan-interior');if(!g)return null;g.updateMatrixWorld(true);
  const b=[...campus.places,...campus.buildings].find(a=>a.osm===osm),ground=terrain.platformHeight(b),v=new THREE.Vector3();
  return{key:'jiyuan',name:b?.name||'',floors:j.floors.map(f=>({label:f.floor+'F',cut:g.localToWorld(v.set(0,ground+f.height+j.floorHeight-.25,0)).y})),groups:['jiyuan-interior'],plaza:false};
 }
 return null;
}

export function createFloorCut(THREE,scene,renderer){
 renderer.localClippingEnabled=true;
 // Plaza decks are 0.25 m thick slabs: cut them a little lower so no deck underside is left over the floor.
 const plane=new THREE.Plane(new THREE.Vector3(0,-1,0),0),plazaPlane=new THREE.Plane(new THREE.Vector3(0,-1,0),0);let touched=[];
 function clear(){for(const m of touched){if(m.userData.floorCutOriginal){m.material=m.userData.floorCutOriginal;delete m.userData.floorCutOriginal;}}touched=[];}
 function apply(info,y){
  clear();if(!info||y==null)return;plane.constant=y;plazaPlane.constant=y-.3;
  const targets=new Map();for(const name of info.groups){const g=scene.getObjectByName(name);if(g)g.traverse(o=>{if(o.isMesh)targets.set(o,plane);});}
  if(info.plaza)scene.traverse(o=>{if(o.isMesh&&PLAZA_PREFIXES.some(p=>o.name.startsWith(p))&&!targets.has(o))targets.set(o,plazaPlane);});
  for(const [m,pl] of targets){
   m.userData.floorCutOriginal=m.material;
   const clone=mat=>{const c=mat.clone();c.clippingPlanes=[pl];c.clipShadows=true;return c;};
   m.material=Array.isArray(m.material)?m.material.map(clone):clone(m.material);touched.push(m);
  }
 }
 return{apply,clear,get active(){return touched.length>0;}};
}
