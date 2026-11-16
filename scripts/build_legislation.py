"""Render verified legislative developments separately from regulatory circulars."""
from datetime import date
import hashlib
from html import escape
import json
import shutil
from regions import region_group, region_tabs, region_assets, copy_region_assets, REGIONS
from urllib.parse import urlsplit


def legislation_data(root):
    data=json.loads((root/'data/legislation.json').read_text())
    date.fromisoformat(data['verifiedAt'])
    ids=set()
    for item in data['items']:
        assert item['id'] not in ids
        ids.add(item['id'])
        date.fromisoformat(item['updateDate'])
        assert item['updateDate']<=data['verifiedAt']
        assert item['sources'] and all(urlsplit(s['url']).scheme=='https' for s in item['sources'])
    data['items'].sort(key=lambda x:(x['updateDate'],x['id']),reverse=True)
    return data


def legislation_version(root):
    return hashlib.sha256(b''.join((root/p).read_bytes() for p in ['data/legislation.json','templates/legislation.html','assets/regions.js','assets/regions.css','scripts/regions.py','scripts/build_legislation.py'])).hexdigest()[:12]


def legislation_card(root):
    data=legislation_data(root)
    rows=[];seen=set()
    for i in data['items']:
        if i['jurisdiction'] in seen:continue
        seen.add(i['jurisdiction'])
        title=i['jurisdiction']+' · '+i['title']
        rows.append(f'<li><span class="headline" title="{escape(title,quote=True)}">{escape(title)}</span></li>')
        if len(rows)==2:break
    if not rows:rows=['<li><span class="headline">暂无已核实的立法更新</span></li>']
    count=len(data['items']);regions=len({i['jurisdiction'] for i in data['items']})
    day=data['verifiedAt']
    return f'''<a class="module active legislation" href="legislation.html?v={legislation_version(root)}" aria-label="查看资管行业立法动态"><div class="module-top"><span class="module-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 3h11l3 3v15H5zM15 3v5h4M9 12h6m-6 4h6"/></svg></span><h2>立法动态</h2><time class="status" datetime="{day}" title="内容核验日期（香港时间）">{day.replace('-','.')}</time></div><div class="metric"><strong>{count}</strong><span>项</span></div><p class="metric-note">{regions}个法域 · 持续跟踪</p><p class="section-label">立法进展</p><ul class="highlights">{''.join(rows)}</ul><div class="module-footer"><span>查看立法动态</span><span aria-hidden="true">→</span></div></a>'''


def build_legislation(root,dist):
    data=legislation_data(root)
    cards=[]
    for i in data['items']:
        links=' · '.join(f'<a href="{escape(s["url"],quote=True)}" target="_blank" rel="noopener noreferrer">{escape(s["label"])} ↗</a>' for s in i['sources'])
        cards.append(f'''<article class="legislation-item" data-region-item="{region_group(i['jurisdiction'])}"><div class="news-meta"><span class="source">{escape(i['jurisdiction'])}</span><time>信息日期 {i['updateDate']}</time><span class="stage">{escape(i['stage'])}</span></div><h2>{escape(i['title'])}</h2><p class="stage-record">{escape(i['stageRecord'])}</p><p>{escape(i['summary'])}</p><p><strong>业务关注</strong>　{escape(i['businessFocus'])}</p><p class="next-step"><strong>后续节点</strong>　{escape(i['nextStep'])}</p><div class="source-links">{links}</div></article>''')
    options=''.join(f'<option>{escape(r)}</option>' for r in dict.fromkeys(i['jurisdiction'] for i in data['items']))
    html=(root/'templates/legislation.html').read_text()
    for key,value in {'ITEMS':''.join(cards),'REGIONS':options,'VERIFIED':data['verifiedAt'],'COUNT':str(len(cards)),'REGION_TABS':region_tabs({r:sum(region_group(i['jurisdiction'])==r for i in data['items']) for r in REGIONS},'立法动态'),'REGION_ASSETS':region_assets(root)}.items():
        html=html.replace('{{'+key+'}}',value)
    (dist/'legislation.html').write_text(html)
    copy_region_assets(root,dist)
    print(f'Built legislation tracker: {len(cards)} developments')
