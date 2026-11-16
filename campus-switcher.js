// Explicit links keep the two independent campus data sets and scene lifecycles separate.
export function mountCampusSwitcher(current, containers) {
  for (const container of containers) {
    const nav=document.createElement('nav');nav.className='campus-switcher';nav.setAttribute('aria-label','切換校區');
    for(const [id,label,href] of [['yanchao','燕巢校區','./index.html'],['heping','和平校區','./heping.html']]){
      const link=document.createElement('a');link.href=href;link.textContent=label;
      if(id===current)link.setAttribute('aria-current','page');
      nav.append(link);
    }
    container.id==='tools'?container.prepend(nav):container.append(nav);
  }
}
