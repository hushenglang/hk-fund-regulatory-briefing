"""Render the public intelligence module without requiring network at build time."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from html import escape
import hashlib
import json
import shutil


def intelligence_data(root, today=None):
    data=json.loads((root/'data/intelligence.json').read_text())
    editorial=json.loads((root/'data/intelligence-editorial.json').read_text()) if (root/'data/intelligence-editorial.json').exists() else {}
    for item in data['items']:
        item.update(editorial.get(item['url'],{}))
    today = today or datetime.now(ZoneInfo('Asia/Hong_Kong')).date().isoformat()
    data['displayDate'] = today
    data['windowStart'] = (date.fromisoformat(today) - timedelta(days=6)).isoformat()
    data['items'] = [i for i in data['items'] if len(i.get('published') or '') == 10 and data['windowStart'] <= i['published'] <= today]
    return data


def intelligence_version(root):
    today = datetime.now(ZoneInfo('Asia/Hong_Kong')).date().isoformat()
    return hashlib.sha256(today.encode() + b''.join(p.read_bytes() for p in [root/'data/intelligence.json',root/'assets/intelligence.js',root/'templates/intelligence.html',root/'data/intelligence-editorial.json',root/'scripts/build_intelligence.py'])).hexdigest()[:12]


def dashboard_card(root):
    data=intelligence_data(root)
    previews=[]
    for kind,label in [('insights','律所'),('ai','AI')]:
        item=next((i for i in data['items'] if i['kind']==kind),None)
        if item:
            title=item.get('titleZh') or item['title']
            previews.append(f'<li><span class="headline" title="{escape(title,quote=True)}">{label} · {escape(title)}</span></li>')
    if not previews:
        previews.append('<li><span class="headline">近7天暂无更新</span></li>')
    records = escape(json.dumps([{k:i[k] for k in ('kind','published')} | {'title':i.get('titleZh') or i['title']} for i in data['items']],ensure_ascii=False),quote=True)
    date=data['updatedAt'][:10]
    law=sum(i['kind']=='insights' for i in data['items'])
    ai=len(data['items'])-law
    return f'''<a class="module active intelligence" data-intelligence-items="{records}" href="intelligence.html?v={intelligence_version(root)}" aria-label="查看四位一体及法律AI资讯"><div class="module-top"><span class="module-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M4 5h16v14H4zM8 9h8M8 13h5M16 13h1M8 16h8"/></svg></span><h2>四位一体 + 法律AI</h2><time class="status" datetime="{date}" title="最近检索日期（香港时间）">{date.replace('-','.')}</time></div><div class="metric"><strong data-intelligence-total>{len(data['items'])}</strong><span>篇</span></div><p class="metric-note" data-intelligence-note>近7天 · 律所 Insights {law} · 法律AI {ai}</p><p class="section-label">近7天关注</p><ul class="highlights" data-intelligence-previews>{''.join(previews)}</ul><div class="module-footer"><span>进入资讯模块</span><span aria-hidden="true">→</span></div></a>'''


def build_intelligence(root,dist):
    data=intelligence_data(root)
    template=(root/'templates/intelligence.html').read_text()
    payload=json.dumps(data,ensure_ascii=False).replace('<','\\u003c')
    sources={s['id']:s for s in data['sources']}
    cards=[]
    for item in data['items']:
        source=sources[item['source']]
        title=item.get('titleZh') or item['title']
        date=item.get('published') or '日期未注明'
        original=f'<p class="original">{escape(item["title"])}</p>' if item.get('titleZh') else ''
        cards.append(f'''<article class="news-item" data-kind="{item['kind']}" data-source="{item['source']}" data-date="{item.get('published') or ''}"><div class="news-meta"><span class="source">{escape(source['name'])}</span><time>{escape(date)}</time><span class="type">{'律所观点' if item['kind']=='insights' else '官方公告' if source['adapter']!='rss' else '行业报道'}</span></div><h2><a href="{escape(item['url'],quote=True)}" target="_blank" rel="noopener noreferrer">{escape(title)} <span aria-hidden="true">↗</span></a></h2>{original}</article>''')
    opts=''.join(f'<option value="{s["id"]}">{escape(s["name"])}</option>' for s in data['sources'])
    statuses=[]
    for s in data['sources']:
        label={'ok':'读取成功','partial':'部分读取','error':'读取失败'}[s['status']]
        last=(s.get('lastSuccessAt') or '')[:10] or '暂无'
        statuses.append(f'<li><a href="{escape(s["url"],quote=True)}" target="_blank" rel="noopener noreferrer">{escape(s["name"])}</a><span>{label} · 最近成功 {last}</span></li>')
    script_version=hashlib.sha256((root/'assets/intelligence.js').read_bytes()).hexdigest()[:12]
    for key,value in {'ITEMS':''.join(cards),'SOURCES':opts,'SOURCE_STATUS':''.join(statuses),'UPDATED':data['updatedAt'][:16].replace('T',' '),'PAYLOAD':payload,'SCRIPT_VERSION':script_version}.items():
        template=template.replace('{{'+key+'}}',value)
    (dist/'intelligence.html').write_text(template)
    shutil.copyfile(root/'assets/intelligence.js',dist/'assets/intelligence.js')
    print(f'Built intelligence module: {len(data["items"])} headlines')
