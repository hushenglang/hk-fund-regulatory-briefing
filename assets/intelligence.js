(()=>{
'use strict';
const data=JSON.parse(document.getElementById('intelligence-data').textContent);
const rows=[...document.querySelectorAll('.news-item')],buttons=[...document.querySelectorAll('.tabs button')];
const source=document.getElementById('source-filter'),range=document.getElementById('date-filter'),search=document.getElementById('news-search');
let kind='insights';
for(const k of ['insights','ai'])document.getElementById(k+'-count').textContent=data.items.filter(i=>i.kind===k).length;
function render(){
 const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
 const cutoff=range.value==='all'?'':new Date(Date.parse(today+'T00:00:00Z')-(Number(range.value)-1)*86400000).toISOString().slice(0,10);
 const query=search.value.trim().toLocaleLowerCase();let shown=0;
 for(const row of rows){
  const date=row.dataset.date;
  const visible=row.dataset.kind===kind&&(source.value==='all'||row.dataset.source===source.value)&&(!cutoff||(date.length===10&&date>=cutoff&&date<=today))&&row.textContent.toLocaleLowerCase().includes(query);
  row.hidden=!visible;if(visible)shown++;
 }
 document.getElementById('results-count').textContent='显示 '+shown+' 篇';
 document.getElementById('empty').hidden=shown>0;
 const ids=new Set(data.sources.filter(s=>s.kind===kind).map(s=>s.id));
 for(const option of source.options)option.hidden=option.value!=='all'&&!ids.has(option.value);
}
for(const button of buttons)button.addEventListener('click',()=>{kind=button.dataset.kind;source.value='all';for(const b of buttons)b.setAttribute('aria-pressed',String(b===button));render();});
for(const input of [source,range])input.addEventListener('change',render);
search.addEventListener('input',render);render();
})();
