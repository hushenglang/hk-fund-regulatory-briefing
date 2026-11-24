"""Build a separate layout proposal without replacing the current workbench."""
from html import escape
import hashlib
import json
import re
import shutil
from build_compliance import compliance_data
from build_workbench_v2 import analysis_table, monthly_memo, knowledge_cards
from split_reports import Document


def replace_panel(html,panel,body):
    doc=Document(html)
    node=next(n for n in doc.nodes if n.tag=='section' and n.attrs.get('data-panel')==panel)
    return html[:node.start]+body+html[node.end:]


def planned_card(title,url,caption,topics,icon):
    rows=''.join(f'<li><span class="headline" title="{escape(t,quote=True)}">{escape(t)}</span></li>' for t in topics)
    return f'''<a class="module active planned-library" href="{url}" data-detail="{url}" data-detail-title="{title}"><div class="module-top"><span class="module-icon" aria-hidden="true"><svg viewBox="0 0 24 24">{icon}</svg></span><h2>{title}</h2><span class="status">内容规划</span></div><div class="metric"><strong>待收录</strong></div><p class="metric-note">{caption}</p><p class="section-label">拟收录方向</p><ul class="highlights">{rows}</ul><div class="module-footer"><span>查看模块结构</span></div></a>'''


def library_page(title,intro,groups):
    nav=''.join(f'<button data-library-panel="{key}" aria-controls="{key}" aria-pressed="{str(i==0).lower()}">{label}</button>' for i,(key,label,items) in enumerate(groups))
    panels=[]
    for i,(key,label,items) in enumerate(groups):
        cards=''.join(f'<article><span class="tag">待收录 · {label}</span><h3>{escape(name)}</h3><p>{escape(detail)}</p></article>' for name,detail in items)
        panels.append(f'<section id="{key}" data-library-content{(" hidden" if i else "")}><div class="library-topics">{cards}</div></section>')
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · 内容结构预览</title><link rel="stylesheet" href="assets/workbench-v2.css"><link rel="stylesheet" href="assets/workbench-layout.css"></head><body><main class="library-preview"><span class="tag amber">内容结构预览 · 尚待收录材料</span><h1>{title}</h1><p>{intro}</p><nav class="library-nav" aria-label="资料分组">{nav}</nav>{''.join(panels)}<div class="library-sample">拟采用的资料卡格式：来源与日期 / 所属法域 / 业务场景 / 问题经过 / 可借鉴的检查点。观点、行业实践与法院或监管结论分别标注，材料经核实后再纳入。</div></main><script src="assets/workbench-library-preview.js"></script></body></html>'''


def build_workbench_layout(root,dist,catalog):
    weekly=next(i for i in catalog if '周' in i['type'])
    data=json.loads((root/'data/workbench-layout-analysis.json').read_text())
    dashboard=(dist/'dashboard.html').read_text()
    memo=compliance_data(root)['items']
    actions=[(i['title'],i['action']) for i in data['focus']]
    actions+=[('筹建合同经验库：先整理香港基金协议资料','按募投管退分类，拟收录同业解读、行业实践及纠纷分析；核实法域、来源及适用场景后形成检查清单。'),('筹建部门与前台培训资料库','拟将募集沟通、适当性、披露及协议审阅中的高频问题整理为案例卡；培训材料和使用范围待复核。')]
    html=(dist/'workbench-v2.html').read_text()
    html=html.replace('<title>法律合规工作台 · 新版预览</title>','<title>法律合规工作台 · 布局方案</title>')
    html=html.replace('<body>','<body class="layout-preview">')
    version=hashlib.sha256((root/'assets/workbench-layout.css').read_bytes()).hexdigest()[:12]
    html=html.replace('</head>',f'<link rel="stylesheet" href="assets/workbench-layout.css?v={version}"></head>')
    html=html.replace('>新版预览</span>','>布局方案</span>')
    html=re.sub(r'data-discussion="(judgment|strategy)"',r'data-discussion="layout-\1"',html)
    html=html.replace('href="dashboard.html" target="_blank" rel="noopener">打开原版工作台 ↗','href="workbench-v2.html" target="_blank" rel="noopener">打开当前版本')
    cards=knowledge_cards(dashboard)
    doc=Document(cards)
    mini=[]
    for node in (n for n in doc.nodes if n.tag=='a' and n.attrs.get('data-detail')):
        card=doc.html(node)
        title=node.attrs['data-detail-title']
        count=re.search(r'<div class="metric"><strong\b[^>]*>(.*?)</strong>',card)[1]
        unit='篇' if title=='四位一体' else '项'
        mini.append(f'<button data-open="knowledge"><strong>{title}</strong><span>{count}{unit}已收录</span></button>')
    for title in ('合同模块','培训管理'):
        mini.append(f'<button class="planned" data-open="knowledge"><strong>{title}</strong><span>内容规划 · 待收录</span></button>')
    overview=(root/'templates/workbench-layout-overview.html').read_text()
    for k,v in {'MONTHLY_MEMO':monthly_memo(memo),'MEMO_COUNT':str(len(memo)),'ACTION_COUNT':str(len(actions)),'KNOWLEDGE_MINI':''.join(mini)}.items():overview=overview.replace('{{'+k+'}}',v)
    html=replace_panel(html,'overview',overview)
    contract_icon='<path d="M5 3h11l3 3v15H5zM15 3v5h4M8 12h8m-8 4h5"/>'
    training_icon='<path d="m2 8 10-5 10 5-10 5zM6 10v7c4 3 8 3 12 0v-7M22 8v8"/>'
    cards+=planned_card('合同模块','contract-library-preview.html','香港优先 · 内地 · 美国',['募与投：认购、侧函、投资及股东协议','管与退：治理、违约、退出与争议经验'],contract_icon)
    cards+=planned_card('培训管理','training-library-preview.html','法规部及前台 · 同业解读与行业实践',['前台：募集沟通、材料使用与投资者流程','法规部：条款审阅、案例复盘与判断方法'],training_icon)
    knowledge=f'<section data-panel="knowledge" hidden><h2>知识库</h2><p class="intro">六类资料入口。合同与培训管理为新增结构预览；正式收录前分别核实来源、日期、法域与适用业务。</p><div class="knowledge-grid">{cards}</div><div id="detail" hidden><div class="detail-head"><strong id="detail-title"></strong><a id="detail-link" target="_blank" rel="noopener">单独打开</a></div><iframe id="knowledge-frame" title="知识库内容" loading="lazy"></iframe></div></section>'
    html=replace_panel(html,'knowledge',knowledge)
    if data['periodId']==weekly['id']:
        judgments=analysis_table([(data[k],label) for k,label in [('regulatory','监管趋势'),('enforcement','执法趋势')]]+[(i,'建议关注点') for i in data['focus']])
        strategies=analysis_table([(i,'策略建议 · 待确认') for i in data['strategies']],strategy=True)
        for panel,table,intro in [('judgment',judgments,'按“涉及哪类基金或业务、需要检查什么、依据是什么”表述本期判断。建议检查事项尚不代表公司存在相关问题。'),('strategy',strategies,'围绕现有基金运作、正在募资的产品、协议审阅和前台支持提出建议；是否采纳及责任安排待确认。')]:
            doc=Document(html)
            section=next(n for n in doc.nodes if n.attrs.get('data-panel')==panel)
            body=doc.html(section)
            table_node=next(n for n in doc.nodes if n.tag=='div' and n.attrs.get('class')=='table-wrap' and section.start<n.start<section.end)
            body=body.replace(doc.html(table_node),table)
            body=re.sub(r'<p class="intro">.*?</p>',f'<p class="intro">{intro}</p>',body,count=1,flags=re.S)
            html=replace_panel(html,panel,body)
    else:
        # Preserve the main workbench's pending analysis state on a new period.
        actions=[]
    doc=Document(html)
    execution=next(n for n in doc.nodes if n.attrs.get('data-panel')=='execution')
    body=doc.html(execution)
    rows=''.join(f'<tr data-task-kind="suggested"><td><span class="tag amber">研判建议</span><h3>{escape(title)}</h3><p>{escape(detail)}</p></td><td>待评估</td><td>负责人及期限待确认</td></tr>' for title,detail in actions)
    old_rows=[n for n in doc.nodes if n.tag=='tr' and n.attrs.get('data-task-kind')=='suggested' and execution.start<n.start<execution.end]
    for i,n in enumerate(old_rows):body=body.replace(doc.html(n),rows if i==0 else '',1)
    html=replace_panel(html,'execution',body)
    html=html.replace('预览版本 · 判断与策略以所列周报及知识库材料为依据 · 原版工作台继续保留','布局审核稿 · 分析沿用所列报告期知识库快照 · 合同与培训资料待收录')
    (dist/'workbench-layout-preview.html').write_text(html)
    contract_groups=[
        ('hongkong','香港优先',[
            ('募｜认购协议与侧函','拟收录募资沟通与协议不一致、投资者优惠安排、流动性条款及最惠国约定的解读和纠纷经验。'),
            ('投｜投资协议与股东协议','拟收录陈述保证、先决条件、赔偿、股东权利及投资交割中常见争议的实务分析。'),
            ('管｜投后治理与持续义务','拟收录信息权、关联交易、董事或股东决策、违约通知及治理安排的行业实践。'),
            ('退｜转让、回购与争议解决','拟收录退出条件、转让限制、优先购买权、回购履行及跨境争议执行的案例解读。')]),
        ('mainland','内地',[
            ('募投管退的协议实践','拟在香港资料框架之后补充内地基金募集、投资及退出经验，明确机构、产品和交易场景。'),
            ('跨境安排的差异提醒','同业观点与裁判结论分开记录；内地材料不直接当作香港项目的适用规则。')]),
        ('us','美国',[
            ('基金文件与投资协议经验','拟补充美国私募基金文件、侧函、投资和退出的行业解读，标明州法或联邦法背景。'),
            ('跨境项目的审阅提示','关注美国经验与香港或内地交易的可比性，提炼问题与检查点，避免直接套用条款。')])]
    training_groups=[
        ('front','前台同事',[
            ('募资沟通与材料使用','拟整理募集宣传、风险披露、材料版本控制及侧函承诺的案例卡。'),
            ('投资者流程与信息收集','拟整理KYC、投资者分类、适当性记录和与法规部协作的实务材料。'),
            ('投资与退出中的法律协作','拟整理交易早期需要法规部介入的事项、资料清单及常见谈判问题。')]),
        ('legal','法规部',[
            ('协议审阅与条款比较','拟将合同模块中的纠纷解读、行业实践整理为条款对照和审阅清单。'),
            ('监管适用判断与案例复盘','拟整理不同法域、规则状态与公司业务关联的判断方法及案例复盘材料。'),
            ('课程与版本管理','拟记录主题、适用对象、来源、复核人、版本和使用记录；本版先展示结构。')])]
    (dist/'contract-library-preview.html').write_text(library_page('合同模块','按募投管退组织资料，先香港，再内地和美国；下列为拟收录主题，不代表已有文章或个案结论。',contract_groups))
    (dist/'training-library-preview.html').write_text(library_page('培训管理','将同业解读与行业实践整理为法规部及前台同事可使用的培训资料；本版展示内容组织方式。',training_groups))
    for file in ('workbench-layout.css','workbench-library-preview.js'):shutil.copyfile(root/'assets'/file,dist/'assets'/file)
    print('Built separate layout proposal with six knowledge modules')
