(()=>{
'use strict';
const controls=document.querySelector('[data-region-label]');if(!controls)return;
const buttons=[...controls.querySelectorAll('[data-region-tab]')],items=[...document.querySelectorAll('[data-region-item]')],search=document.querySelector('[data-region-search]');
let region='香港';
function render(){
 const query=(search?.value||'').trim().toLocaleLowerCase();let visible=0;
 for(const item of items){const show=item.dataset.regionItem===region&&item.textContent.toLocaleLowerCase().includes(query);item.hidden=!show;if(show)visible++;}
 for(const button of buttons){button.setAttribute('aria-pressed',String(button.dataset.regionTab===region));button.querySelector('span').textContent=items.filter(i=>i.dataset.regionItem===button.dataset.regionTab).length;}
 for(const table of document.querySelectorAll('table')){const rows=[...table.querySelectorAll('tr[data-region-item]')];if(rows.length){const wrap=table.closest('.table-wrap');(wrap||table).hidden=rows.every(r=>r.hidden);}}
 const empty=controls.querySelector('.region-empty');empty.hidden=visible>0;empty.textContent=query?'当前栏目下没有符合搜索条件的内容':'本期暂无'+region+'的'+controls.dataset.regionLabel;
 document.querySelectorAll('[data-region-content]').forEach(el=>el.hidden=visible===0);
 const count=document.getElementById('results-count');if(count)count.textContent='显示 '+visible+' 项';
}
for(const button of buttons)button.addEventListener('click',()=>{region=button.dataset.regionTab;if(search)search.value='';render();});
search?.addEventListener('input',render);render();
})();
