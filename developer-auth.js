const KEY='nknu-developer-session-v1';let enabled=false;try{enabled=sessionStorage.getItem(KEY)==='active';}catch{}
export function isDeveloper(){return enabled;}
function setEnabled(value){enabled=value;try{if(value)sessionStorage.setItem(KEY,'active');else sessionStorage.removeItem(KEY);}catch{}globalThis.dispatchEvent?.(new CustomEvent('campus-developer-auth',{detail:{enabled}}));}
export function loginDeveloper(pin){if(pin!=='0315')return false;setEnabled(true);return true;}
export function logoutDeveloper(){setEnabled(false);}
