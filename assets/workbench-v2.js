(()=>{
'use strict';
const panels=[...document.querySelectorAll('[data-panel]')];
function open(id){if(!panels.some(p=>p.dataset.panel===id))id='overview';for(const p of panels)p.hidden=p.dataset.panel!==id;for(const b of document.querySelectorAll('.navigation button'))b.setAttribute('aria-pressed',String(b.dataset.open===id));history.replaceState(null,'','#'+id);}
for(const b of document.querySelectorAll('[data-open]'))b.addEventListener('click',()=>{open(b.dataset.open);window.scrollTo(0,0);});
for(const b of document.querySelectorAll('[data-detail]'))b.addEventListener('click',(event)=>{if(event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;event.preventDefault();document.getElementById('detail').hidden=false;document.getElementById('knowledge-frame').src=b.dataset.detail;document.getElementById('knowledge-frame').title=b.dataset.detailTitle;document.getElementById('detail-title').textContent=b.dataset.detailTitle;document.getElementById('detail-link').href=b.dataset.detail;document.getElementById('detail').scrollIntoView({behavior:'smooth',block:'start'});});
for(const b of document.querySelectorAll('[data-task-filter]'))b.addEventListener('click',()=>{for(const row of document.querySelectorAll('[data-task-kind]'))row.hidden=b.dataset.taskFilter!=='all'&&row.dataset.taskKind!==b.dataset.taskFilter;for(const button of document.querySelectorAll('[data-task-filter]'))button.setAttribute('aria-pressed',String(button===b));});
for(const box of document.querySelectorAll('[data-discussion]')){
  const key=`workbench-feedback:${box.dataset.period}:${box.dataset.discussion}`;
  const input=box.querySelector('textarea'),status=box.querySelector('[data-feedback-status]'),list=box.querySelector('.feedback-history');
  let entries=[],agreement='';
  try{const stored=JSON.parse(localStorage.getItem(key)||'{}');entries=Array.isArray(stored.entries)?stored.entries.filter(e=>e&&typeof e.text==='string'&&typeof e.agreement==='string').slice(-50):[];input.value=typeof stored.draft==='string'?stored.draft.slice(0,6000):'';agreement=typeof stored.agreement==='string'?stored.agreement:'';}catch{status.textContent='浏览器无法读取历史意见，仍可复制内容。';}
  function persist(){try{localStorage.setItem(key,JSON.stringify({entries,draft:input.value,agreement}));return true;}catch{status.textContent='浏览器无法保存，请复制内容保留。';return false;}}
  function choices(){for(const b of box.querySelectorAll('[data-agreement]'))b.setAttribute('aria-pressed',String(b.dataset.agreement===agreement));}
  function render(){list.replaceChildren();for(const entry of entries){const li=document.createElement('li'),heading=document.createElement('strong'),body=document.createElement('p');heading.textContent=`${entry.agreement||'未选择立场'} · ${entry.time||''}`;body.textContent=entry.text;li.append(heading,body);list.append(li);}}
  for(const b of box.querySelectorAll('[data-agreement]'))b.addEventListener('click',()=>{agreement=b.dataset.agreement;choices();persist();});
  input.addEventListener('input',()=>{status.textContent='';persist();});
  box.querySelector('[data-save-feedback]').addEventListener('click',()=>{const text=input.value.trim();if(!text&&!agreement){status.textContent='请选择立场或填写意见。';return;}const old=[...entries],draft=input.value;entries.push({agreement,text,time:new Date().toLocaleString('zh-CN',{timeZone:'Asia/Hong_Kong',hour12:false})});entries=entries.slice(-50);input.value='';if(persist()){render();status.textContent='意见已保存在本浏览器，尚未发送给AI。';}else{entries=old;input.value=draft;}});
  box.querySelector('[data-copy-discussion]').addEventListener('click',async()=>{
    const panel=box.closest('[data-panel]');
    const analysis=[...panel.querySelectorAll('h2,h3,p')].filter(e=>!box.contains(e)).map(e=>e.textContent).join('\n\n');
    const notes=entries.map(e=>`${e.time} ${e.agreement}\n${e.text}`).join('\n\n');
    const draft=input.value.trim();
    const text=`请根据以下本期分析与我的意见继续讨论。\n期间：${box.dataset.period}\n模块：${panel.querySelector('h2').textContent}\n\n${analysis}\n\n引用来源：\n${[...panel.querySelectorAll('.evidence a')].map(a=>a.textContent+' '+a.href).join('\n')}\n\n已保存的意见：\n${notes||'暂无'}${draft?'\n\n当前意见草稿：'+agreement+'\n'+draft:''}`;
    try{await navigator.clipboard.writeText(text);status.textContent='已复制，可粘贴到当前聊天继续讨论。';}catch{status.textContent='未能复制，请允许浏览器访问剪贴板后重试。';}
  });
  choices();render();
}
window.addEventListener('hashchange',()=>open(location.hash.slice(1)));open(location.hash.slice(1));
})();
