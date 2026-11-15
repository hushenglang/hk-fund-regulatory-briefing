"""Refresh public headline feeds. No model, API key or local computer required."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo
from split_reports import Document

ROOT = Path(__file__).resolve().parents[1]
HK = ZoneInfo('Asia/Hong_Kong')
SOURCES = [
    dict(id='kingandwood', name='金杜', kind='insights', adapter='kw', url='https://www.kingandwood.com/hk/zh/insights/latest-thinking.html'),
    dict(id='mofo', name='Morrison Foerster', kind='insights', adapter='mofo', url='https://www.mofo.com/resources/insights?backurl=%2Fcapabilities%2Fprivate-funds%23insights&linkedcontent=Private%20Funds&practicetype=practices&q=Private%20Funds'),
    dict(id='charltons', name='Charltons 易周', kind='insights', adapter='charltons', url='https://www.charltonslaw.com.cn/fa-lv-jian-xun/xiang-gang-fa-xun/'),
    dict(id='harvey', name='Harvey', kind='ai', adapter='harvey', url='https://www.harvey.ai/blog'),
    dict(id='legora', name='Legora', kind='ai', adapter='legora', url='https://legora.com/newsroom'),
    dict(id='artificiallawyer', name='Artificial Lawyer', kind='ai', adapter='rss', url='https://www.artificiallawyer.com/feed/'),
    dict(id='lawnext', name='LawNext', kind='ai', adapter='rss', url='https://www.lawnext.com/feed'),
    dict(id='legalfutures', name='Legal Futures', kind='ai', adapter='rss', url='https://www.legalfutures.co.uk/feed'),
]
AI_TERMS = re.compile(r'\bAI\b|artificial intelligence|generative|Harvey|Legora|CoCounsel|Lexis\+', re.I)
MONTHS = {m: i for i, m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'], 1)}


def plain(value):
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]*>', ' ', value or ''))).strip()


def canonical(url):
    p = urlsplit(unescape(url))
    if p.scheme not in ('http', 'https') or not p.hostname:
        raise ValueError('Invalid article URL')
    return urlunsplit(('https', p.netloc.lower(), p.path, '', ''))


def download(url):
    req = Request(url, headers={'User-Agent': 'GBAComplianceBriefing/1.0 (+public-headline-reader)', 'Accept': 'text/html,application/rss+xml,application/xml'})
    with urlopen(req, timeout=25) as response:
        body = response.read(5_000_001)
        if len(body) > 5_000_000:
            raise ValueError('Source exceeds size limit')
        return body.decode(response.headers.get_content_charset() or 'utf-8', errors='replace').replace('\r\n', '\n').replace('\r', '\n')


def published(value):
    value = plain(value)
    m = re.search(r'(20\d{2})[-/年](\d{1,2})(?:[-/月](\d{1,2}))?', value)
    if m:
        y, month, day = m.groups()
        datetime(int(y), int(month), int(day or 1))
        return f'{int(y):04}-{int(month):02}' + (f'-{int(day):02}' if day else '')
    m = re.search(r'\b(' + '|'.join(MONTHS) + r')[a-z]*\s+(\d{1,2}),?\s+(20\d{2})', value)
    if m:
        month, day, year = m.groups()
        return f'{year}-{MONTHS[month]:02}-{int(day):02}'
    try:
        return parsedate_to_datetime(value).astimezone(HK).date().isoformat()
    except (ValueError, TypeError, OverflowError):
        return None


def page_date(html):
    doc = Document(html)
    for n in doc.nodes:
        if n.tag == 'meta' and (n.attrs.get('property') or n.attrs.get('name') or '').lower() in {'article:published_time', 'date', 'pubdate', 'dc.date.issued', 'datepublished'}:
            d = published(n.attrs.get('content', ''))
            if d:
                return d
    for n in doc.nodes:
        if n.tag == 'time' or any(c in n.attrs.get('class', '').split() for c in ['article-date', 'published', 'post-date']):
            d = published(n.attrs.get('datetime', '') or doc.html(n))
            if d:
                return d
    m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', html)
    return published(m[1]) if m else None


def links(html):
    doc = Document(html)
    return [(n.attrs['href'], plain(doc.html(n))) for n in doc.nodes if n.tag == 'a' and n.attrs.get('href') and plain(doc.html(n))]


def enrich(record):
    if not record.get('published'):
        record['published'] = page_date(download(record['url']))
    return record


def collect(source):
    adapter, base = source['adapter'], source['url']
    html = download(base)
    rows = []
    if adapter == 'mofo':
        # The supplied filter is client-rendered. The practice page embeds the
        # same Private Funds insight cards, including titles and publication dates.
        html = download('https://www.mofo.com/capabilities/private-funds')
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
        cards = json.loads(m[1])['props']['pageProps']['page']['pageData']['insightsData']['articles']
        rows = [dict(title=plain(a['title']), url=urljoin(base,a['url']), published=published(a['date']['startDate'])) for a in cards]
    elif adapter == 'rss':
        root = ET.fromstring(html)
        for item in root.findall('.//item'):
            title = plain(item.findtext('title'))
            if AI_TERMS.search(title):
                rows.append(dict(title=title, url=item.findtext('link'), published=published(item.findtext('pubDate') or '')))
    elif adapter == 'charltons':
        doc = Document(html)
        for article in re.finditer(r'<article\b[^>]*>(.*?)</article>', html, re.S):
            fragment = article[0]
            m = re.search(r'<h2\b[^>]*>(.*?)</h2>', fragment, re.S)
            if m:
                anchors = links(m[1])
                if anchors:
                    url,title = anchors[0]
                    rows.append(dict(title=title,url=url,published=page_date(fragment)))
    else:
        for href, title in links(html):
            if adapter == 'kw' and re.search(r'/hk/zh/insights/latest-thinking/[^/?]+$', href) and '阅读' not in title and not href.endswith('.html'):
                href = href.removeprefix('/content/kingandwood')
                rows.append(dict(title=title,url=urljoin(base,href+'.html'),published=None))
            elif adapter == 'harvey' and re.match(r'^/blog/[^/?]+$',href) and href != '/blog/all':
                d = published(title)
                # Use dated cards only; undated featured cards may be marketing.
                if d:
                    title = re.sub(r'^(Technical|Product|Company|Insights)\s*','',title)
                    title = re.sub(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+20\d{2}.*$', '', title).strip()
                    if 'marketing' not in title.lower():
                        rows.append(dict(title=title,url=urljoin(base,href),published=d))
            elif adapter == 'legora' and '/newsroom/' in href:
                d = published(title)
                if d:
                    title = re.sub(r'^\w+\s+\d{1,2},\s+20\d{2}\s*','',title)
                    rows.append(dict(title=title,url=urljoin(base,href.removeprefix('./')),published=d))
    unique = {}
    for row in rows:
        row['url'] = canonical(row['url'])
        unique.setdefault(row['url'],row)
    rows = sorted(unique.values(), key=lambda x:x.get('published') or '', reverse=True)[:12]
    if not rows:
        raise ValueError('No article cards found; source layout may have changed')
    errors = 0
    if adapter in ('kw', 'charltons'):
        # Listing dates can be month-only: resolve against article metadata.
        for row in rows:
            try:
                d = page_date(download(row['url']))
                if d:
                    row['published'] = d
            except Exception:
                errors += 1
    for row in rows:
        row.update(source=source['id'],kind=source['kind'])
    return rows, errors


def refresh(path, fetch=collect, now=None):
    now = now or datetime.now(HK)
    stamp = now.isoformat(timespec='seconds')
    data = json.loads(path.read_text()) if path.exists() else {'schemaVersion':1,'items':[],'sources':[]}
    old_sources = {s['id']:s for s in data['sources']}
    items = {i['url']:i for i in data['items']}
    sources, successes = [], 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch,s):s for s in SOURCES}
        for future in as_completed(futures):
            spec = futures[future]
            status = {**spec,'checkedAt':stamp}
            try:
                rows, errors = future.result()
                accepted = 0
                for row in rows:
                    if row['published'] and row['published'] > now.date().isoformat():
                        continue  # Never label future-dated items as current news.
                    old = items.get(row['url'],{})
                    if not row.get('published') and old.get('published'):
                        row['published'] = old['published']
                    items[row['url']] = {**old,**row,'firstSeenAt':old.get('firstSeenAt',stamp),'lastSeenAt':stamp}
                    accepted += 1
                if not accepted:
                    raise ValueError('No current articles accepted')
                status.update(status='partial' if errors else 'ok',lastSuccessAt=stamp,received=accepted)
                successes += 1
            except Exception as exc:
                old = old_sources.get(spec['id'],{})
                status.update(status='error',lastSuccessAt=old.get('lastSuccessAt'),error=type(exc).__name__)
                print(f'WARNING {spec["name"]}: {type(exc).__name__}')
            sources.append(status)
    if not successes:
        raise RuntimeError('All sources failed; published data left unchanged')
    # Keep old entries when a source fails; retain a bounded archive per source.
    ordered = sorted(items.values(),key=lambda x:(x.get('published') or '', x['url']),reverse=True)
    kept, counts = [], {}
    for item in ordered:
        sid=item['source'];counts[sid]=counts.get(sid,0)+1
        if counts[sid]<=100:
            kept.append(item)
    data.update(updatedAt=stamp,sources=sorted(sources,key=lambda x:next(i for i,s in enumerate(SOURCES) if s['id']==x['id'])),items=kept)
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    temp.replace(path)
    print(f'Refreshed {successes}/{len(SOURCES)} sources; {len(kept)} headlines')
    return data


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'data/intelligence.json')
    refresh(parser.parse_args().output)
