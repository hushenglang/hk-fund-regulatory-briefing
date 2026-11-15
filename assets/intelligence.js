(()=>{
'use strict';
const data=JSON.parse(document.getElementById('intelligence-data').textContent);
const rows=[...document.querySelectorAll('.news-item')],buttons=[...document.querySelectorAll('.tabs button')];
const source=document.getElementById('source-filter'),search=document.getElementById('news-search');
let kind=null;
function today(){return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());}
function render(){
 const day=today(),current=data.items.filter(i=>i.published===day);
 const available=['insights','ai'].filter(k=>current.some(i=>i.kind===k));
 if(!available.includes(kind))kind=available[0]||null;
 for(const button of buttons){const k=button.dataset.kind;button.hidden=!available.includes(k);button.setAttribute('aria-pressed',String(k===kind));document.getElementById(k+'-count').textContent=current.filter(i=>i.kind===k).length;}
 document.querySelector('.board').hidden=!current.length;
 document.getElementById('no-updates').hidden=!!current.length;
 const ids=new Set(current.filter(i=>i.kind===kind).map(i=>i.source));
 if(source.value!=='all'&&!ids.has(source.value))source.value='all';
 for(const option of source.options)option.hidden=option.value!=='all'&&!ids.has(option.value);
 const query=search.value.trim().toLocaleLowerCase();let shown=0;
 for(const row of rows){const visible=row.dataset.date===day&&row.dataset.kind===kind&&(source.value==='all'||row.dataset.source===source.value)&&row.textContent.toLocaleLowerCase().includes(query);row.hidden=!visible;if(visible)shown++;}
 document.getElementById('results-count').textContent='今日 '+shown+' 篇';
 document.getElementById('empty').hidden=shown>0;
}
for(const button of buttons)button.addEventListener('click',()=>{kind=button.dataset.kind;source.value='all';render();});
source.addEventListener('change',render);search.addEventListener('input',render);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)render();});
setInterval(render,60000);render();
})();
