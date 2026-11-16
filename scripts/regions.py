"""Jurisdiction tabs for workbench detail pages; source contents remain intact."""
import hashlib
from html import escape, unescape
import re
import shutil
from urllib.parse import urlsplit

REGIONS=('香港','内地','其他')


def region_group(jurisdiction):
    if jurisdiction in ('香港','Hong Kong','HK'):return '香港'
    if jurisdiction in ('内地','中国内地','中国大陆','Mainland China','CN'):return '内地'
    return '其他'


def classify_region(html):
    explicit=re.search(r'data-jurisdiction=["\']([^"\']+)',html)
    if explicit:return region_group(explicit[1])
    # Classify by issuing authority, not by a company name or investment target.
    for url in re.findall(r'href\s*=\s*["\'](https?://[^"\']+)',html,re.I):
        host=(urlsplit(unescape(url)).hostname or '').lower()
        if any(host==d or host.endswith('.'+d) for d in ('sfc.hk','hkex.com.hk','hkma.gov.hk','info.gov.hk','legco.gov.hk','icac.org.hk','judiciary.hk','hklii.hk')):return '香港'
        if host.endswith('.gov.cn') or any(host==d or host.endswith('.'+d) for d in ('amac.org.cn','sse.com.cn','szse.cn','court.gov.cn')):return '内地'
        if any(host==d or host.endswith('.'+d) for d in ('sec.gov','finra.org','justice.gov','fca.org.uk','mas.gov.sg','asic.gov.au')):return '其他'
    text=unescape(re.sub('<[^>]+>',' ',html))
    if re.search(r'中国证监会|证监局|人民银行|国家金融监督|最高人民法院',text):return '内地'
    if re.search(r'\b(?:SEC|FINRA|FCA|MAS|ASIC)\b|美国|英国|新加坡',text):return '其他'
    if re.search(r'香港|港交所|联交所|金管局|廉署|证监会|\b(?:SFC|HKEX|HKMA|MMT)\b',text):return '香港'
    return '其他'


def annotate_regions(html):
    from split_reports import Document
    doc=Document(html);targets=[];counts=dict.fromkeys(REGIONS,0)
    for node in doc.nodes:
        if node.tag=='article' or node.tag=='tr' and any(n.tag=='td' for n in node.children):
            region=classify_region(doc.html(node));counts[region]+=1
            targets.append((node.start+len(node.tag)+1,' data-region-item="'+region+'"'))
    for pos,attr in sorted(targets,reverse=True):html=html[:pos]+attr+html[pos:]
    return html,counts


def region_tabs(counts,label):
    buttons=''.join(f'<button type="button" data-region-tab="{r}" aria-pressed="{str(n==0).lower()}">{r}<span>{counts.get(r,0)}</span></button>' for n,r in enumerate(REGIONS))
    return f'<div class="region-switch" data-region-label="{escape(label,quote=True)}"><div class="region-tabs" role="group" aria-label="按法域切换">{buttons}</div><p class="region-empty" role="status" hidden></p></div>'


def region_assets(root,prefix=''):
    css=hashlib.sha256((root/'assets/regions.css').read_bytes()).hexdigest()[:12]
    js=hashlib.sha256((root/'assets/regions.js').read_bytes()).hexdigest()[:12]
    return f'<link rel="stylesheet" href="{prefix}assets/regions.css?v={css}"><script defer src="{prefix}assets/regions.js?v={js}"></script>'


def copy_region_assets(root,dist):
    (dist/'assets').mkdir(exist_ok=True)
    for file in ('regions.css','regions.js'):shutil.copyfile(root/'assets'/file,dist/'assets'/file)
