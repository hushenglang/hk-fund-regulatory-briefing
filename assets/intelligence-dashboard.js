(()=>{
'use strict';
function refresh(){
 const card=document.querySelector('[data-intelligence-items]');if(!card)return;
 const day=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
 const start=new Date(Date.parse(day+'T00:00:00Z')-6*86400000).toISOString().slice(0,10);
 const items=JSON.parse(card.dataset.intelligenceItems).filter(i=>i.published>=start&&i.published<=day);
 const law=items.filter(i=>i.kind==='insights').length;
 card.querySelector('[data-intelligence-total]').textContent=items.length;
 card.querySelector('[data-intelligence-note]').textContent='近7天 · 律所 Insights '+law+' · 法律AI '+(items.length-law);
 const list=card.querySelector('[data-intelligence-previews]');list.replaceChildren();
 for(const [kind,label] of [['insights','律所'],['ai','AI']]){
  const item=items.find(i=>i.kind===kind);if(!item)continue;
  const li=document.createElement('li'),span=document.createElement('span');span.className='headline';span.title=item.title;span.textContent=label+' · '+item.title;li.append(span);list.append(li);
 }
 if(!items.length){const li=document.createElement('li'),span=document.createElement('span');span.className='headline';span.textContent='近7天暂无更新';li.append(span);list.append(li);}
}
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});setInterval(refresh,60000);refresh();
})();
