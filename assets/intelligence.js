(()=>{
'use strict';
const data=JSON.parse(document.getElementById('intelligence-data').textContent);
const rows=[...document.querySelectorAll('.news-item')],buttons=[...document.querySelectorAll('.tabs button')];
const source=document.getElementById('source-filter'),search=document.getElementById('news-search');
let kind='insights';
function render(){
 const day=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
 const start=new Date(Date.parse(day+'T00:00:00Z')-6*86400000).toISOString().slice(0,10);
 const current=data.items.filter(i=>i.published>=start&&i.published<=day);
 for(const button of buttons){const k=button.dataset.kind;button.hidden=false;button.setAttribute('aria-pressed',String(k===kind));document.getElementById(k+'-count').textContent=current.filter(i=>i.kind===k).length;}
 const ids=new Set(current.filter(i=>i.kind===kind).map(i=>i.source));
 if(source.value!=='all'&&!ids.has(source.value))source.value='all';
 for(const option of source.options)option.hidden=option.value!=='all'&&!ids.has(option.value);
 const query=search.value.trim().toLocaleLowerCase();let shown=0;
 for(const row of rows){const visible=row.dataset.date>=start&&row.dataset.date<=day&&row.dataset.kind===kind&&(source.value==='all'||row.dataset.source===source.value)&&row.textContent.toLocaleLowerCase().includes(query);row.hidden=!visible;if(visible)shown++;}
 document.getElementById('results-count').textContent='近7天 '+shown+' 篇';
 const empty=document.getElementById('empty');empty.hidden=shown>0;
 empty.textContent=query||source.value!=='all'?'当前筛选下暂无资讯':'近7天暂无'+(kind==='insights'?'律所 Insights':'法律AI')+'更新';
}
for(const button of buttons)button.addEventListener('click',()=>{kind=button.dataset.kind;source.value='all';render();});
source.addEventListener('change',render);search.addEventListener('input',render);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)render();});
setInterval(render,60000);render();
})();
