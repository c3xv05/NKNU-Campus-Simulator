// Phone-only HUD layout shared by both campuses. Tablets and desktops keep the
// original layout: only coarse-pointer screens that are narrow (portrait phone)
// or short (landscape phone) collapse the left tool column behind a ☰ button.
export const PHONE_HUD_QUERY='(pointer:coarse) and (max-width:600px), (pointer:coarse) and (max-height:500px)';

export function mountMobileHud({tools,touchRight,mobileControls=[],sheetItems=[],travelMenu}){
  const query=matchMedia(PHONE_HUD_QUERY);
  const toggle=document.createElement('button');
  toggle.id='hudMenuButton';toggle.type='button';toggle.setAttribute('aria-controls',tools.id);
  // Placed right after the tool column so the start overlay, later in the DOM, still covers it.
  tools.after(toggle);
  // Ride/speed controls move next to the right-thumb buttons on phones; markers remember their desktop slot.
  const slot=document.createElement('div');slot.id='hudThumbSlot';touchRight.prepend(slot);
  const remember=(elements,target,prepend)=>elements.filter(Boolean).map(element=>{const marker=document.createComment('mobile-hud');element.before(marker);return{element,marker,target,prepend};});
  // sheetItems (e.g. a campus switcher shown elsewhere on wider screens) move to the top of the ☰ sheet.
  const homes=[...remember(mobileControls,slot,false),...remember(sheetItems,tools,true)];
  const isOpen=()=>document.body.classList.contains('hud-open');
  function setOpen(open){
    open=open&&query.matches;
    document.body.classList.toggle('hud-open',open);
    toggle.setAttribute('aria-expanded',String(open));
    toggle.setAttribute('aria-label',open?'關閉選單':'開啟選單：傳送與切換校區');
    toggle.textContent=open?'✕':'☰';
    if(open&&travelMenu)travelMenu.open=true;
  }
  function apply(){
    const phone=query.matches;
    document.body.classList.toggle('phone-hud',phone);
    for(const {element,marker,target,prepend} of homes){if(!phone)marker.after(element);else if(prepend)target.prepend(element);else target.append(element);}
    setOpen(false);
  }
  toggle.addEventListener('click',()=>setOpen(!isOpen()));
  // Any action in the sheet (a destination, aerial view) closes it so the result is visible.
  tools.addEventListener('click',event=>{if(isOpen()&&event.target.closest('button'))setOpen(false);});
  addEventListener('keydown',event=>{if(event.key==='Escape'&&isOpen())setOpen(false);});
  query.addEventListener('change',apply);
  apply();
  return{setOpen,isOpen};
}
