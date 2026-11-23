"""Build an additional review workbench; preserve the existing dashboard."""
from html import escape
import hashlib
import json
import re
import shutil
from build_dashboard import extract_highlights
from build_compliance import compliance_data
from split_reports import section_content
from build_legislation import legislation_data
from build_intelligence import intelligence_data

PURPOSE='提升立法及监管动态跟踪、判例与执法案例研究、合规事项落实的效率与质量，为公司业务提供及时、准确、可执行的法律合规支持。'
STANDARD='以适用法律法规及监管要求为基础，结合公司的业务模式、牌照范围和风险状况，参考行业良好实践。重点关注信息收集的完整性、权威性与时效性，专业判断的准确性，以及合规措施的可操作性、执行及时性和留痕完整性。'
THEMES=[
 ('digital','业务流程数字化','无纸|代币|结算|CAT','本期材料反映证券登记、结算及数据流程持续调整。应结合实际使用的交易和托管安排判断影响范围。','优先核对业务衔接与责任分工','梳理认购、登记、托管及结算流程，与服务机构核对适用安排和切换要求；涉及新业务时先确认适用范围。'),
 ('aml','客户尽调与反洗钱','反洗钱|FATF|尽调|客户身份|洗钱','本期材料涉及反洗钱风险识别。需核对相关风险变化是否影响现有客户、交易或地域敞口。','按风险变化开展针对性核查','核对客户及地域风险分类、筛查规则和尽调材料，评估是否需要调整监测或补充审查。'),
 ('controls','基金治理与投资者保护','投资者|募集|利益冲突|披露|档案|欺诈|投顾','本期案例涉及基金经营或投资者保护事项，可作为检视募集、披露及内部控制的参考，不能据此直接推断全行业执法强弱。','围绕实际风险开展内控抽查','结合案例核查募资及宣传授权、投资者档案、披露及审批记录；对确认的问题提出整改与培训建议。')
]


def build_workbench_v2(root,dist,catalog):
    weekly=next(i for i in catalog if '周' in i['type'])
    records=[]
    for kind,parts in section_content((root/'reports'/f'{weekly["id"]}.html').read_text()).items():
        for title,detail,category in extract_highlights(parts,kind):records.append(dict(kind=kind,title=title,detail=detail))
    for i in legislation_data(root)['items']:
        records.append(dict(kind='legislation',title=i['title'],detail=i['summary'],url='legislation.html'))
    for i in intelligence_data(root)['items']:
        records.append(dict(kind='intelligence',title=i.get('titleZh') or i['title'],detail='',url=i['url']))
    themes=[]
    for key,title,pattern,judgment,strategy,action in THEMES:
        evidence=[r for r in records if re.search(pattern,r['title']+' '+r['detail'],re.I)]
        if evidence:themes.append(dict(id=key,title=title,judgment=judgment,strategy=strategy,action=action,evidence=evidence[:3]))
    def evidence_html(t):
        links=[]
        for r in t['evidence']:
            url=escape(r.get('url') or ('archive/'+weekly['id']+'-'+r['kind']+'.html'),quote=True)
            links.append(f'<li><a href="{url}" target="_blank" rel="noopener noreferrer">{escape(r["title"])} ↗</a></li>')
        return '<ul class="evidence">'+''.join(links)+'</ul>'
    signal_cards=[]
    for kind,label in [('regulatory','监管趋势'),('cases','执法趋势')]:
        selected=[r for r in records if r['kind']==kind]
        title_list=evidence_html({'evidence':selected[:2]})
        note='关注规则实施与业务流程衔接，核对适用主体、实施节点及操作安排。' if kind=='regulatory' else '结合个案识别控制缺口，区分调查、指控、处分与裁定，并核对相关留痕。'
        signal_cards.append(f'<article class="card"><span class="tag">本期侧重点</span><h3>{label}</h3><p>本期已收录{len(selected)}项材料。{note}</p><details><summary>代表材料</summary>{title_list}</details></article>')
    judgments=''.join(f'<article class="card"><span class="tag">本期观察</span><h3>{t["title"]}</h3><p>{t["judgment"]}</p><details><summary>查看依据</summary>{evidence_html(t)}</details><button class="text-button" data-open="strategy">查看策略建议 →</button></article>' for t in themes)
    strategies=''.join(f'<article class="card"><span class="tag">策略建议 · 待复核</span><h3>{t["strategy"]}</h3><p>{t["action"]}</p><details><summary>对应材料</summary>{evidence_html(t)}</details><button class="text-button" data-open="execution">查看建议行动项 →</button></article>' for t in themes)
    knowledge=[('立法动态','法律、法案与审议进展','legislation.html'),('判例及执法','香港、内地及其他法域案例',f'archive/{weekly["id"]}-cases.html'),('监管更新','规则、指引、通函及公告',f'archive/{weekly["id"]}-regulatory.html'),('四位一体','律所 Insights 与全球法律AI','intelligence.html')]
    knowledge=[(title,caption,url+'?v='+hashlib.sha256((dist/url).read_bytes()).hexdigest()[:12]) for title,caption,url in knowledge]
    knowledge_html=''.join(f'<button class="card knowledge-card" data-detail="{url}" data-detail-title="{title}"><span class="tag">知识库</span><h3>{title}</h3><p>{caption}</p><span class="entry">查看内容 →</span></button>' for title,caption,url in knowledge)
    memo=compliance_data(root)['items'];rows=[]
    for t in themes:
        rows.append(f'<tr data-task-kind="suggested"><td><span class="tag amber">研判建议</span><strong>{t["strategy"]}</strong><p>{t["action"]}</p><button class="text-button" data-open="judgment">依据：{t["title"]} →</button></td><td>待评估</td><td>负责人及期限待确认</td></tr>')
    for i in memo:
        status='待确认' if i['sourceStatus']=='文档未注明' or i.get('monthlyDay') else i['sourceStatus']
        rows.append(f'<tr data-task-kind="existing"><td><span class="tag">年度备忘</span><strong>{escape(i["title"])}</strong></td><td>{escape(status)}</td><td>{escape(i["owner"])}<br><span class="muted">{escape(i["deadlineText"])}</span></td></tr>')
    dashboard=(dist/'dashboard.html').read_text()
    daily=re.search(r'<section class="module daily-panel".*?</section>',dashboard,re.S)[0]
    daily=daily.replace('class="module daily-panel"','class="card daily-panel"')
    html=(root/'templates/workbench-v2.html').read_text()
    values={'PERIOD':weekly['label'],'PURPOSE':PURPOSE,'STANDARD':STANDARD,'KNOWLEDGE':knowledge_html,'REGULATORY_SIGNALS':''.join(signal_cards),'JUDGMENTS':judgments or '<p>本期暂无可归纳的研判主题。</p>','STRATEGIES':strategies or '<p>本期暂无新增策略建议。</p>','TASKS':''.join(rows),'DAILY':daily,'NEWS_COUNT':str(len(records)),'MEMO_COUNT':str(len(memo)),'SUGGESTED_COUNT':str(len(themes)),'SIGNALS':''.join(f'<li>{t["title"]}</li>' for t in themes),'VERSION':hashlib.sha256((root/'assets/workbench-v2.js').read_bytes()+(root/'assets/workbench-v2.css').read_bytes()).hexdigest()[:12]}
    for k,v in values.items():html=html.replace('{{'+k+'}}',v)
    (dist/'workbench-v2.html').write_text(html)
    for file in ('workbench-v2.js','workbench-v2.css'):shutil.copyfile(root/'assets'/file,dist/'assets'/file)
    print(f'Built additional workbench preview: {weekly["id"]}; {len(themes)} proposed actions')
