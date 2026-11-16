(()=>{
'use strict';
const rows=[...document.querySelectorAll('.legislation-item')],region=document.getElementById('region-filter'),search=document.getElementById('legislation-search');
function render(){let count=0;const q=search.value.trim().toLocaleLowerCase();for(const row of rows){const show=(region.value==='all'||row.dataset.region===region.value)&&row.textContent.toLocaleLowerCase().includes(q);row.hidden=!show;if(show)count++;}document.getElementById('results-count').textContent='显示 '+count+' 项';document.getElementById('empty').hidden=!!count;}
region.addEventListener('change',render);search.addEventListener('input',render);render();
})();
