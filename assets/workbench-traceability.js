(()=>{
  'use strict';
  for(const button of document.querySelectorAll('[data-trace-judgment]'))button.addEventListener('click',()=>{
    const row=document.getElementById('trace-'+button.dataset.traceJudgment);
    if(!row)return;
    document.querySelector('.navigation [data-open="judgment"]').click();
    row.scrollIntoView({block:'center',behavior:'smooth'});
    row.focus({preventScroll:true});
    row.classList.add('trace-highlight');
    setTimeout(()=>row.classList.remove('trace-highlight'),2500);
  });
})();
