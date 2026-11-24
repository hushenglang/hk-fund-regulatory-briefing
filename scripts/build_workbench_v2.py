"""Build an additional review workbench; preserve the existing dashboard."""
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape
import hashlib
import json
import re
import shutil
from build_dashboard import extract_highlights
from build_compliance import compliance_data
from split_reports import Document, section_content
from build_legislation import legislation_data
from build_intelligence import intelligence_data

PURPOSE='提升立法及监管动态跟踪、判例与执法案例研究、合规事项落实的效率与质量，为公司业务提供及时、准确、可执行的法律合规支持。'
STANDARD='以适用法律法规及监管要求为基础，结合公司的业务模式、牌照范围和风险状况，参考行业良好实践。重点关注信息收集的完整性、权威性与时效性，专业判断的准确性，以及合规措施的可操作性、执行及时性和留痕完整性。'


def source_html(item):
    return '<ul class="evidence">'+''.join(f'<li><a href="{escape(url,quote=True)}" target="_blank" rel="noopener noreferrer">{escape(title)}</a></li>' for title,url in item.get('sources',[]))+'</ul>'


def analysis_table(items,strategy=False):
    rows=[]
    for item,label in items:
        text=f'<p>{escape(item["summary"])}</p>'
        if item.get('analysis'):
            text+=f'<details class="full-analysis"><summary>展开完整分析</summary><p>{escape(item["analysis"])}</p></details>'
        if item.get('outcome'):
            text+=f'<p class="outcome"><strong>预期效果：</strong>{escape(item["outcome"])}</p>'
        evidence=f'<details><summary>{len(item.get("sources",[]))}项材料</summary>{source_html(item)}</details>'
        rows.append(f'<tr><td><span class="tag">{label}</span><h3>{escape(item["title"])}</h3></td><td>{text}</td><td>{evidence}</td></tr>')
    heading='策略方向' if strategy else '判断事项'
    detail='建议及预期效果' if strategy else '分析与建议'
    return f'<div class="table-wrap"><table class="review-table" aria-label="本期{heading}列表"><thead><tr><th scope="col">{heading}</th><th scope="col">{detail}</th><th scope="col">材料依据</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'


def knowledge_cards(dashboard):
    """Reuse the original dashboard cards, including their dates and previews."""
    doc=Document(dashboard)
    cards=[]
    for node in doc.nodes:
        if node.tag!='a' or 'module' not in node.attrs.get('class','').split():continue
        card=doc.html(node)
        title=re.search(r'<h2>(.*?)</h2>',card)
        if not title or title[1] not in ('立法动态','判例及执法','监管更新','四位一体'):continue
        attrs=f' data-detail="{escape(node.attrs["href"],quote=True)}" data-detail-title="{escape(title[1],quote=True)}"'
        cards.append(card.replace('<a ','<a'+attrs+' ',1))
    if len(cards)!=4:raise ValueError('Expected four original knowledge cards')
    return ''.join(cards)


def monthly_memo(items,now=None):
    now=now or datetime.now(ZoneInfo('Asia/Hong_Kong'))
    month=now.strftime('%Y-%m')
    selected=[i for i in items if any(d.startswith(month) for d in i.get('dates',[])) or i.get('monthlyDay')]
    content=''.join(f'<li><strong>{escape(i["title"])}</strong><span>{escape(i["deadlineText"])} · {escape(i["sourceStatus"])}</span></li>' for i in selected)
    if not content:content='<li class="empty">现有备忘中，本月暂无固定日期事项；临时及事件触发事项另行确认。</li>'
    next_date=(now.replace(day=28).date().toordinal()+4)
    from datetime import date
    next_month=date.fromordinal(next_date).strftime('%Y-%m')
    upcoming=[i for i in items if any(d.startswith(next_month) for d in i.get('dates',[])) and i.get('group')!='定期监控' and i['sourceStatus']!='已完成']
    prep=''.join(f'<li>{escape(i["title"])}<span>{escape(i["deadlineText"])}</span></li>' for i in upcoming)
    if prep:content+=f'<li class="memo-subtitle">下月准备 · 非本月到期事项</li>{prep}'
    return f'<article class="card monthly-memo"><div class="section-heading"><h2>{now.year}年{now.month}月合规事项备忘</h2><button class="text-button" data-open="execution">查看完整备忘</button></div><ul class="memo-list">{content}</ul></article>'


def discussion(panel,period):
    return f'''<section class="card discussion" data-discussion="{panel}" data-period="{escape(period,quote=True)}" aria-label="{'判断' if panel=='judgment' else '策略'}讨论区">
<div class="section-heading"><h3>讨论与反馈</h3><span class="tag amber">AI对话待配置</span></div>
<p class="discussion-note">记录你对本期分析的意见。接入模型服务后可在此继续对话；目前不会自动回复或发送内容。</p>
<div class="feedback-choices" role="group" aria-label="是否认可本期分析"><button type="button" data-agreement="同意" aria-pressed="false">同意</button><button type="button" data-agreement="部分同意" aria-pressed="false">部分同意</button><button type="button" data-agreement="不同意" aria-pressed="false">不同意</button><button type="button" data-agreement="希望进一步讨论" aria-pressed="false">希望进一步讨论</button></div>
<label class="feedback-label" for="feedback-{panel}">你的意见或想讨论的问题</label><textarea id="feedback-{panel}" rows="2" maxlength="6000" placeholder="例如：我同意该方向，但建议结合现有产品和客户结构进一步判断优先级。"></textarea>
<div class="discussion-actions"><button class="primary-button" type="button" data-save-feedback>保存意见</button><button class="secondary-button" type="button" data-copy-discussion>复制分析与反馈</button><span role="status" aria-live="polite" data-feedback-status></span></div>
<p class="discussion-note">反馈仅保存在当前浏览器，不同步给同事；你可复制到当前聊天继续讨论。</p><ol class="feedback-history" aria-label="已保存的反馈"></ol></section>'''


def build_workbench_v2(root,dist,catalog):
    weekly=next(i for i in catalog if '周' in i['type'])
    records=[]
    for kind,parts in section_content((root/'reports'/f'{weekly["id"]}.html').read_text()).items():
        for title,detail,category in extract_highlights(parts,kind):records.append(dict(kind=kind,title=title,detail=detail))
    legislation=legislation_data(root)
    intelligence=intelligence_data(root)
    for i in legislation['items']:records.append(dict(kind='legislation',title=i['title'],detail=i['summary']))
    for i in intelligence['items']:records.append(dict(kind='intelligence',title=i.get('titleZh') or i['title'],detail=''))
    analysis=json.loads((root/'data/workbench-analysis.json').read_text())
    current=analysis['periodId']==weekly['id']
    if current:
        trends=analysis_table([(analysis[k],label) for k,label in [('regulatory','监管趋势'),('enforcement','执法趋势')]]+[(i,'建议关注点') for i in analysis['focus']])
        focuses=''
        strategies=analysis_table([(i,'策略建议 · 待确认') for i in analysis['strategies']],strategy=True)
        overview=''.join(f'<article class="card overview-trend"><div class="section-heading"><h2>{label}</h2><button class="text-button" data-open="judgment">查看分析</button></div><h3>{escape(analysis[k].get("overviewTitle",analysis[k]["title"]))}</h3><p>{escape(analysis[k].get("overviewSummary",analysis[k]["summary"]))}</p></article>' for k,label in [('regulatory','监管趋势'),('enforcement','执法趋势')])
        overview+='<article class="card"><div class="section-heading"><h2>建议关注点</h2><button class="text-button" data-open="judgment">查看详情</button></div><ul class="overview-list">'+''.join(f'<li><strong>{escape(i["title"])}</strong></li>' for i in analysis['focus'])+'</ul></article>'
        overview+='<article class="card"><div class="section-heading"><h2>策略方向</h2><button class="text-button" data-open="strategy">查看详情</button></div><ul class="overview-list">'+''.join(f'<li><strong>{escape(i["title"])}</strong></li>' for i in analysis['strategies'])+'</ul></article>'
        actions=analysis['focus']
    else:
        # Never pass off the previous period's synthesis as analysis of a new report.
        pending='<article class="card"><h3>本期分析待更新</h3><p>知识库已更新，尚未完成本期归纳；请先查看资料。上一期分析不会自动沿用为本期判断。</p><button class="text-button" data-open="knowledge">查看知识库</button></article>'
        overview=trends=strategies=pending
        focuses='';actions=[]
    memo=compliance_data(root)['items'];rows=[]
    for i in actions:
        rows.append(f'<tr data-task-kind="suggested"><td><span class="tag amber">研判建议</span><strong>{escape(i["title"])}</strong><p>{escape(i["action"])}</p><button class="text-button" data-open="judgment">查看分析依据</button></td><td>待评估</td><td>负责人及期限待确认</td></tr>')
    for i in memo:
        status='待确认' if i['sourceStatus']=='文档未注明' or i.get('monthlyDay') else i['sourceStatus']
        rows.append(f'<tr data-task-kind="existing"><td><span class="tag">年度备忘</span><strong>{escape(i["title"])}</strong></td><td>{escape(status)}</td><td>{escape(i["owner"])}<br><span class="muted">{escape(i["deadlineText"])}</span></td></tr>')
    dashboard=(dist/'dashboard.html').read_text()
    daily=re.search(r'<section class="module daily-panel".*?</section>',dashboard,re.S)[0].replace('class="module daily-panel"','class="card daily-panel"')
    html=(root/'templates/workbench-v2.html').read_text()
    values={'PERIOD':weekly['label'],'PURPOSE':PURPOSE,'STANDARD':STANDARD,'KNOWLEDGE':knowledge_cards(dashboard),'OVERVIEW':overview,'MONTHLY_MEMO':monthly_memo(memo),'REGULATORY_SIGNALS':trends,'JUDGMENTS':focuses,'STRATEGIES':strategies,'TASKS':''.join(rows),'DAILY':daily,'JUDGMENT_DISCUSSION':discussion('judgment',weekly['id']),'STRATEGY_DISCUSSION':discussion('strategy',weekly['id']),'VERSION':hashlib.sha256((root/'assets/workbench-v2.js').read_bytes()+(root/'assets/workbench-v2.css').read_bytes()).hexdigest()[:12]}
    for k,v in values.items():html=html.replace('{{'+k+'}}',v)
    (dist/'workbench-v2.html').write_text(html)
    for file in ('workbench-v2.js','workbench-v2.css'):shutil.copyfile(root/'assets'/file,dist/'assets'/file)
    print(f'Built additional workbench preview: {weekly["id"]}; {len(actions)} proposed actions')
