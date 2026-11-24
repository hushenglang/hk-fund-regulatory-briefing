"""Add explicitly sourced judgments, linked strategies and learning references."""
from html import escape as e
import hashlib
import json
import re
from urllib.parse import urlsplit
from build_workbench_layout import replace_panel
from split_reports import Document


def validate_reasoning(data):
    groups={name:{x['id']:x for x in data[name]} for name in ('knowledge','judgments','strategies','training')}
    for name in groups:
        if len(groups[name])!=len(data[name]):raise ValueError(f'Duplicate {name} IDs')
    for item in data['knowledge']:
        if urlsplit(item['url']).scheme!='https':raise ValueError('Evidence must link to an HTTPS source')
    for item in data['judgments']+data['training']:
        if not item['sourceIds'] or any(k not in groups['knowledge'] for k in item['sourceIds']):raise ValueError('Missing knowledge evidence')
    for item in data['strategies']:
        if not item['judgmentIds'] or any(j not in groups['judgments'] for j in item['judgmentIds']):raise ValueError('Strategy must link to a judgment')
    return groups


def evidence(ids,knowledge):
    return ''.join(f'<div class="trace-evidence"><span>{e(knowledge[k]["module"])} · {e(k)}</span><a href="{e(knowledge[k]["url"],quote=True)}" target="_blank" rel="noopener noreferrer">{e(knowledge[k]["title"])}</a><small>{e(knowledge[k]["date"])} · {e(knowledge[k]["kind"])}</small><p>{e(knowledge[k]["fact"])}</p></div>' for k in ids)


def render_judgments(data,knowledge):
    rows=[]
    for j in data['judgments']:
        rows.append(f'<tr id="trace-{e(j["id"])}" tabindex="-1"><td>{evidence(j["sourceIds"],knowledge)}</td><td><span class="tag">{e(j["id"])} · {e(j["category"])}</span><h3>{e(j["title"])}</h3><p>{e(j["observation"])}</p></td><td><p>{e(j["impact"])}</p><p class="trace-boundary">{e(j["qualification"])}</p></td></tr>')
    return '<div class="table-wrap"><table class="review-table trace-table judgment-trace" aria-label="知识库到判断的依据链"><thead><tr><th>知识库事实与来源</th><th>趋势或风险判断</th><th>业务影响及判断边界</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'


def render_strategies(data,judgments):
    rows=[]
    for s in data['strategies']:
        linked=''.join(f'<button class="trace-link" data-trace-judgment="{e(j)}"><span>{e(j)}</span>{e(judgments[j]["title"])}</button>' for j in s['judgmentIds'])
        rows.append(f'<tr id="trace-{e(s["id"])}"><td>{linked}</td><td><span class="tag">{e(s["id"])} · 建议待确认</span><h3>{e(s["title"])}</h3><p>{e(s["rationale"])}</p></td><td><p>{e(s["condition"])}</p><details><summary>建议行动</summary><p>{e(s["action"])}</p><button class="text-button" data-open="execution">查看执行清单</button></details></td></tr>')
    return '<div class="table-wrap"><table class="review-table trace-table strategy-trace" aria-label="判断到策略的对应关系"><thead><tr><th>对应判断 · 点击追溯</th><th>策略选择与理由</th><th>适用条件及建议行动</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'


def library_shell(title,intro,nav,panels,version):
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><link rel="stylesheet" href="assets/workbench-v2.css"><link rel="stylesheet" href="assets/workbench-layout.css"><link rel="stylesheet" href="assets/workbench-learning.css?v={version}"></head><body><main class="library-preview"><h1>{title}</h1><p>{intro}</p>{nav}{panels}</main><script src="assets/workbench-library-preview.js"></script></body></html>'


def render_libraries(data,knowledge,dist,version):
    contracts=[k for k in data['knowledge'] if k['module']=='合同模块']
    nav='';panels=''
    for index,region in enumerate(('香港','内地','美国')):
        key='region-'+str(index)
        nav+=f'<button data-library-panel="{key}" aria-controls="{key}" aria-pressed="{str(index==0).lower()}">{region}{"优先" if index==0 else ""}</button>'
        cards=[]
        for k in contracts:
            if k['region']!=region:continue
            cards.append(f'<article id="{k["id"]}" class="reference-card"><div class="reference-meta">{e(k["id"])} · {e(k["publisher"])} · {e(k["date"])} · {e(k["kind"])}</div><h3><a href="{e(k["url"],quote=True)}" target="_blank" rel="noopener noreferrer">{e(k["title"])}</a></h3><span class="tag">{e(k["stages"])}</span><p>{e(k["summary"])}</p><p><b>风险点：</b>{e(k["pitfall"])}</p><p><b>可讨论的检查点：</b>{e(k["check"])}</p><p class="reference-scope">{e(k["scope"])}</p><small>收录核对日期：{e(k["reviewedAt"])}</small></article>')
        panels+=f'<section id="{key}" data-library-content{(" hidden" if index else "")}>'+''.join(cards)+'</section>'
    (dist/'contract-library-preview.html').write_text(library_shell('合同模块','首批公开实务参考资料。按香港、内地、美国分类；历史材料与未注明日期的材料明确标识，不作为本周新闻或现行规则清单。','<nav class="library-nav">'+nav+'</nav>',panels,version))
    nav='';panels=''
    for index,audience in enumerate(('前台同事','法规部')):
        key='audience-'+str(index);nav+=f'<button data-library-panel="{key}" aria-controls="{key}" aria-pressed="{str(index==0).lower()}">{audience}</button>'
        cards=[]
        for t in data['training']:
            if audience not in t['audiences']:continue
            items=''.join('<li>'+e(x)+'</li>' for x in t['objectives'])
            cards.append(f'<article class="reference-card"><span class="tag amber">{e(t["status"])}</span><h3>{e(t["id"])} · {e(t["title"])}</h3><ul>{items}</ul><p><b>讨论练习：</b>{e(t["exercise"])}</p><details><summary>参考来源</summary>{evidence(t["sourceIds"],knowledge)}</details></article>')
        panels+=f'<section id="{key}" data-library-content{(" hidden" if index else "")}>'+''.join(cards)+'</section>'
    (dist/'training-library-preview.html').write_text(library_shell('培训管理','基于已收录来源编制的培训提纲草稿，待部门复核后使用；未安排课程、未记录出席或CPT学时。','<nav class="library-nav">'+nav+'</nav>',panels,version))
    return contracts


def enrich_workbench_layout(root,dist):
    data=json.loads((root/'data/workbench-reasoning.json').read_text());groups=validate_reasoning(data)
    catalog=json.loads((root/'reports/catalog.json').read_text())
    latest=max((x for x in catalog if '周' in x['type']),key=lambda x:x['periodEnd'])
    current=data['periodId']==latest['id']
    html=(dist/'workbench-layout-preview.html').read_text()
    version=hashlib.sha256((root/'assets/workbench-learning.css').read_bytes()+(root/'assets/workbench-traceability.js').read_bytes()).hexdigest()[:12]
    html=html.replace('</head>',f'<link rel="stylesheet" href="assets/workbench-learning.css?v={version}"></head>')
    html=html.replace('</body>',f'<script src="assets/workbench-traceability.js?v={version}"></script></body>')
    for panel,table,intro in [('judgment',render_judgments(data,groups['knowledge']),'先列知识库事实，再形成趋势或风险判断，并说明业务影响。下列是分析归纳，不代表公司已存在相关缺口。'),('strategy',render_strategies(data,groups['judgments']),'每项策略说明对应哪个判断、为什么采用，以及适用条件。点击对应判断可回看其知识库依据；未确认适用性的事项不直接转为正式任务。')]:
        if not current:continue
        doc=Document(html);section=next(n for n in doc.nodes if n.attrs.get('data-panel')==panel);body=doc.html(section)
        old=next(n for n in doc.nodes if n.tag=='div' and n.attrs.get('class')=='table-wrap' and section.start<n.start<section.end)
        body=body.replace(doc.html(old),table)
        body=re.sub(r'<p class="intro">.*?</p>',f'<p class="intro">{intro}</p>',body,count=1,flags=re.S)
        html=replace_panel(html,panel,body)
    contracts=render_libraries(data,groups['knowledge'],dist,version)
    # Fill the two existing collection cards and overview counters without changing the four established cards.
    doc=Document(html)
    for node in sorted((n for n in doc.nodes if n.tag=='a' and 'planned-library' in n.attrs.get('class','').split()),key=lambda n:n.start,reverse=True):
        body=doc.html(node);is_contract='contract-library' in node.attrs.get('href','');count=len(contracts) if is_contract else len(data['training'])
        body=body.replace('planned-library','learning-library').replace('内容规划','公开参考' if is_contract else '提纲草稿').replace('<strong>待收录</strong>',f'<strong>{count}</strong><span>{"篇参考" if is_contract else "份草稿"}</span>').replace('拟收录方向','资料范围' if is_contract else '培训主题').replace('查看模块结构','查看参考资料' if is_contract else '查看培训提纲')
        topics=['侧函：合同主体、文件联动及承诺管理','回购退出：触发条件、责任主体与执行路径'] if is_contract else ['无纸化市场、侧函与MFN、回购退出','三份提纲草稿，待部门复核后使用']
        highlights='<ul class="highlights">'+''.join('<li><span class="headline">'+e(t)+'</span></li>' for t in topics)+'</ul>'
        body=re.sub(r'<ul class="highlights">.*?</ul>',highlights,body,flags=re.S)
        html=html[:node.start]+body+html[node.end:]
    html=html.replace('class="planned"','class="learning"')
    html=html.replace('六类资料入口。合同与培训管理为新增结构预览；正式收录前分别核实来源、日期、法域与适用业务。','六类资料入口。合同库收录公开实务参考；培训库为基于来源整理的提纲草稿，待部门复核。')
    html=html.replace('<strong>合同模块</strong><span>内容规划 · 待收录</span>','<strong>合同模块</strong><span>3篇公开参考</span>').replace('<strong>培训管理</strong><span>内容规划 · 待收录</span>','<strong>培训管理</strong><span>3份提纲草稿</span>')
    html=html.replace('先落实港股登记衔接，继续跟踪基金税制修例','香港证券登记与持有方式向无纸化转型').replace('已实施事项：核对无纸证券登记与托管操作。审议中事项：跟踪香港基金税制修例，按最终条文评估产品及架构影响。','J1：无纸化市场影响证券持有及相关操作；存量证券分阶段参与。基金税制修例另在立法模块持续跟踪。')
    html=html.replace('募集披露、投资者档案及关联方管理值得先检查','本期私募执法样本关注披露、合同履行与利益冲突').replace('本期案例提示：对照协议检查实际操作，核查适当性、利益冲突及人员资历记录；跨法域案例作为控制参考。','J2：多项内地监管措施涉及日常治理与投资者保护；仅属本期样本观察，不据此推断执法力度变化。')
    html=html.replace('港股基金：托管行是否需要调整登记及公司行动流程。','J1：市场无纸化对基金持有及托管安排的影响。').replace('在募基金：宣传材料、认购协议和侧函是否一致。','J3：侧函与其他文件、投资者权利的联动风险。').replace('法律AI：先用于公开资讯，敏感材料另行评估。','J4：退出条款及责任主体对投资回收的影响。')
    html=html.replace('先审现有产品、在募基金与近期交易。','S1 ← J1：分阶段适配市场无纸化。').replace('按募投管退积累香港优先的协议风险清单。','S2 ← J2：围绕披露及利益冲突开展定向抽查。').replace('把高频问题整理为部门及前台培训材料。','S3／S4 ← J3／J4：管理侧函承诺及退出可行性。')
    html=html.replace('5项建议待评估',f'{len(data["strategies"]) if current else 0}项建议待评估')
    doc=Document(html);section=next(n for n in doc.nodes if n.attrs.get('data-panel')=='execution');body=doc.html(section)
    rows=''.join(f'<tr data-task-kind="suggested"><td><span class="tag amber">{s["id"]} · 对应 {"、".join(s["judgmentIds"])}</span><h3>{e(s["title"])}</h3><p>{e(s["action"])}</p><button class="text-button" data-open="strategy">查看策略依据</button></td><td>待评估</td><td>负责人及期限待确认</td></tr>' for s in (data['strategies'] if current else []))
    old=[n for n in doc.nodes if n.tag=='tr' and n.attrs.get('data-task-kind')=='suggested' and section.start<n.start<section.end]
    for i,n in enumerate(old):body=body.replace(doc.html(n),rows if i==0 else '',1)
    html=replace_panel(html,'execution',body)
    html=html.replace('布局审核稿 · 分析沿用所列报告期知识库快照 · 合同与培训资料待收录','分析可追溯至知识库来源 · 策略与执行建议待确认 · 培训提纲待复核')
    if not current:
        doc=Document(html)
        focus=next(n for n in doc.nodes if n.attrs.get('class')=='overview-focus')
        original=doc.html(focus)
        updated='<div class="overview-focus">'+''.join('<article class="brief-card"><h2>'+label+'</h2><p>本期分析待更新，请先查看知识库。</p></article>' for label in ('立法与监管趋势','执法趋势','建议关注点','策略方向'))+'</div>'
        html=html.replace(original,updated,1)
    (dist/'workbench-layout-preview.html').write_text(html)
    for name in ('workbench-learning.css','workbench-traceability.js'):(dist/'assets'/name).write_bytes((root/'assets'/name).read_bytes())
    print('Built evidence-linked judgments, strategies, 3 references and 3 training drafts')
