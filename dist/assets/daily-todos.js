/* A date-scoped personal checklist; no server writes or cross-device sync. */
(() => {
  const inputs = [...document.querySelectorAll('[data-daily-task]')];
  if (!inputs.length) return;
  const key = 'compliance-workspace-daily-todos-v1';
  const today = () => {
    const parts = new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
    return ['year','month','day'].map(k=>parts.find(p=>p.type===k).value).join('-');
  };
  let day = today();
  const read = () => {
    try {const saved=JSON.parse(localStorage.getItem(key)); return saved?.date===day && Array.isArray(saved.done) ? saved.done : [];} catch {return [];}
  };
  const paint = () => {
    inputs.forEach(input=>input.closest('.todo-row').classList.toggle('is-done',input.checked));
    document.getElementById('daily-progress').textContent=`${inputs.filter(i=>i.checked).length} / ${inputs.length} 已完成`;
    document.getElementById('daily-date').textContent=day.replaceAll('-','.');
  };
  const restore = () => {const done=read();inputs.forEach(input=>input.checked=done.includes(input.dataset.dailyTask));paint();};
  inputs.forEach(input=>input.addEventListener('change',()=>{
    if(today()!==day){day=today();restore();return;}
    try {localStorage.setItem(key,JSON.stringify({date:day,done:inputs.filter(i=>i.checked).map(i=>i.dataset.dailyTask)}));} catch {}
    paint();
  }));
  const rollover = () => {if(today()!==day){day=today();restore();}};
  document.addEventListener('visibilitychange',rollover);
  window.addEventListener('storage',event=>{if(event.key===key){rollover();restore();}});
  setInterval(rollover,60000);
  restore();
})();
