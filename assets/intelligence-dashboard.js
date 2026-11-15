(()=>{
'use strict';
function refresh(){
 const card=document.querySelector('[data-intelligence-date]');if(!card)return;
 const day=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
 card.hidden=card.dataset.intelligenceDate!==day;
 card.closest('.grid').classList.toggle('without-intelligence',card.hidden);
}
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});setInterval(refresh,60000);refresh();
})();
