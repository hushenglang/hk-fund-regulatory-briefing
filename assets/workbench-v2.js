(()=>{
'use strict';
const panels=[...document.querySelectorAll('[data-panel]')];
function open(id){if(!panels.some(p=>p.dataset.panel===id))id='overview';for(const p of panels)p.hidden=p.dataset.panel!==id;for(const b of document.querySelectorAll('.navigation button'))b.setAttribute('aria-pressed',String(b.dataset.open===id));history.replaceState(null,'','#'+id);}
for(const b of document.querySelectorAll('[data-open]'))b.addEventListener('click',()=>open(b.dataset.open));
for(const b of document.querySelectorAll('[data-detail]'))b.addEventListener('click',()=>{document.getElementById('detail').hidden=false;document.getElementById('knowledge-frame').src=b.dataset.detail;document.getElementById('knowledge-frame').title=b.dataset.detailTitle;document.getElementById('detail-title').textContent=b.dataset.detailTitle;document.getElementById('detail-link').href=b.dataset.detail;document.getElementById('detail').scrollIntoView({behavior:'smooth',block:'start'});});
for(const b of document.querySelectorAll('[data-task-filter]'))b.addEventListener('click',()=>{for(const row of document.querySelectorAll('[data-task-kind]'))row.hidden=b.dataset.taskFilter!=='all'&&row.dataset.taskKind!==b.dataset.taskFilter;for(const button of document.querySelectorAll('[data-task-filter]'))button.setAttribute('aria-pressed',String(button===b));});
window.addEventListener('hashchange',()=>open(location.hash.slice(1)));open(location.hash.slice(1));
})();
