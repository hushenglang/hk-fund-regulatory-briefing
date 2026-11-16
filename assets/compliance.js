/* Read-only source-calendar reminders, evaluated in Hong Kong time. */
(() => {
  const payload = document.getElementById('compliance-data');
  if (!payload) return;
  const data = JSON.parse(payload.textContent);
  const parts = new Intl.DateTimeFormat('en-CA', {timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
  const part = key => parts.find(p => p.type === key).value;
  const today = `${part('year')}-${part('month')}-${part('day')}`;
  const year = Number(part('year'));
  const month = part('month');
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const items = data.items.filter(item => ['owner','participants'].some(field => /法规部|法律合规部/.test(String(item[field]||'')))).map(item => {
    const monthly = Boolean(item.monthlyDay);
    const status = monthly || item.sourceStatus === '文档未注明' ? '待确认' : item.sourceStatus === '已完成' ? '已完成' : '待进行';
    const date = monthly ? `${data.year}-${month}-${String(item.monthlyDay).padStart(2,'0')}` : item.dates.find(d => d >= today) || item.dates.at(-1) || '';
    const days = date ? Math.round((Date.parse(date+'T00:00:00Z')-Date.parse(today+'T00:00:00Z'))/86400000) : null;
    let timing = '';
    if (monthly) timing = `${data.year}年${Number(month)}月完成情况待确认`;
    else if (item.dateKind === 'target') timing = days < 0 ? '已过目标日，待确认进度' : days === 0 ? '目标日期为今天' : `${days}天后到目标日`;
    else if (status !== '已完成' && item.dateKind === 'start') timing = days >= 0 ? `${days}天后启动` : '已到启动日，待确认进度';
    else if (status !== '已完成' && item.conditional) timing = '具体期限须按财年核实';
    else if (status !== '已完成' && days !== null) timing = days < 0 ? '已过文档日期，待确认进度' : days === 0 ? '文档日期为今天' : `${days}天后到期`;
    return {...item,status,date,days,timing};
  });
  const pending = items.filter(i => i.status === '待进行');
  const confirm = items.filter(i => i.status === '待确认');
  const completed = items.filter(i => i.status === '已完成');
  const set = (id, value) => {const element = document.getElementById(id); if (element) element.textContent = value;};
  set('compliance-pending',pending.length);
  set('compliance-followup',pending.length+confirm.length);
  set('compliance-total',items.length);
  set('compliance-confirm',confirm.length);
  set('compliance-completed',completed.length);
  set('compliance-asof',today);
  set('annual-review-note',data.annualReviewNote||'');
  const monitoring = items.filter(i => i.group === '定期监控');
  set('compliance-card-note',`${data.year}年度 · ${items.length}项备忘 · ${monitoring.length}项定期监控`);
  const preview = document.getElementById('compliance-preview');
  if (preview) {
    const first = [...confirm,...pending].sort((a,b)=>a.date.localeCompare(b.date))[0];
    const rows = first ? [{title:first.title,text:`${first.date.slice(5).replace('-','/')}${first.dateKind==='start'?'启动':''} · ${first.monthlyDay?'FRR 本月完成情况待确认':first.title}`}] : [];
    if (monitoring.length) rows.push({title:'定期监控计划目标日期：12月31日；原频率继续保留',text:`12/31目标 · ${monitoring.length}项定期监控待确认`});
    else rows.push(...[...confirm,...pending].filter(i=>i!==first).slice(0,1).map(i=>({title:i.title,text:`${i.date.slice(5).replace('-','/')} · ${i.title}`})));
    preview.innerHTML=rows.map(i=>`<li><span class="headline" title="${escape(i.title)}">${escape(i.text)}</span></li>`).join('');
  }
  if (year !== data.year) {
    set('compliance-card-note',`${data.year}年历史清单，须更新年度资料`);
    set('compliance-calendar-warning',`当前为${year}年，所载清单为${data.year}年；未自动滚动年度或续认已完成状态。`);
  }
  const tbody = document.getElementById('compliance-rows');
  if (!tbody) return;
  let filter = '待跟进';
  let query = '';
  let group = '全部';
  const render = () => {
    const visible = items.filter(i => (filter==='全部'||(filter==='待跟进'?i.status!=='已完成':i.status===filter)) && (group==='全部'||i.group===group) && [i.title,i.category,i.owner,i.participants,i.scope||'',i.output||'',i.escalation||''].join(' ').toLowerCase().includes(query));
    tbody.innerHTML = visible.map(i => `<tr><td><strong>${escape(i.title)}</strong><small>${escape(i.group||'监管日历')} · ${escape(i.category)}</small>${i.scope?`<details class="monitoring-detail"><summary>监控范围及输出</summary><p><b>范围：</b>${escape(i.scope)}</p><p><b>输出：</b>${escape(i.output)}</p><p><b>升级触发：</b>${escape(i.escalation)}</p></details>`:''}</td><td>${escape(i.deadlineText)}<small>${escape(i.timing)}</small>${i.monthlyDay ? '<small>本月提醒：'+escape(i.date)+'</small>' : ''}</td><td>${escape(i.frequency)}</td><td>${escape(i.owner)}<small>配合：${escape(i.participants)}</small></td><td><span class="pill ${i.status==='已完成'?'done':'pending'}">${escape(i.status)}</span><small>文档记录：${escape(i.sourceStatus)}</small></td></tr>`).join('');
    set('compliance-empty',visible.length ? '' : '此筛选条件下没有事项。');
    set('compliance-showing',`${visible.length} / ${items.length} 项`);
    document.querySelectorAll('[data-compliance-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.complianceFilter===filter)));
  };
  document.querySelectorAll('[data-compliance-filter]').forEach(b=>b.addEventListener('click',()=>{filter=b.dataset.complianceFilter;render();}));
  const search = document.getElementById('compliance-search');
  search?.addEventListener('input',()=>{query=search.value.trim().toLowerCase();render();});
  document.getElementById('compliance-group')?.addEventListener('change',event=>{group=event.target.value;render();});
  render();
})();
