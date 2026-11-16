"""Check generated navigation, archive completeness and project-relative URLs."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

class Page(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.urls = []
        self.ids = set()
        self.article_count = 0
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "article":
            self.article_count += 1
        for key in ("href", "src"):
            if attrs.get(key):
                self.urls.append(attrs[key])

catalog = json.loads((DIST / "catalog.json").read_text())
expected = sorted(catalog, key=lambda item: (item["periodEnd"], item["id"]), reverse=True)
assert catalog == expected, "Catalog must be newest first"
pages = {path.resolve(): Page(path.read_text()) for path in DIST.rglob("*.html")}
for path, page in pages.items():
    for url in page.urls:
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc:
            continue
        assert not parsed.path.startswith("/"), f"Project Pages URL must be relative: {url}"
        target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
        assert target.is_relative_to(DIST.resolve()), f"Link escapes public site: {url}"
        assert target.is_file(), f"Missing local URL in {path.name}: {url}"
        if parsed.fragment and target in pages:
            assert unquote(parsed.fragment) in pages[target].ids, f"Missing anchor: {url}"

for item in catalog:
    source = Page((ROOT / "reports" / (item["id"] + ".html")).read_text())
    archive = pages[(DIST / "archive" / (item["id"] + ".html")).resolve()]
    assert source.article_count == archive.article_count, "Archive lost articles"
latest = (DIST / "archive" / (catalog[0]["id"] + ".html")).read_text()
homepage = (DIST / "index.html").read_text()
assert homepage == latest.replace('href="../archive/', 'href="archive/'), "Homepage differs from latest issue"
source_ids = {p.stem for p in (ROOT / "reports").glob("*.html")}
assert source_ids == {item["id"] for item in catalog}, "Register every report in reports/catalog.json"
print(f"Validated {len(pages)} pages: latest issue, archive articles, links and anchors")

from split_reports import section_content, Document, external_news_links
import re
for item in catalog:
    source = (ROOT / "reports" / (item["id"] + ".html")).read_text()
    sections = section_content(source)
    for kind, content in sections.items():
        output = (DIST / "archive" / f'{item["id"]}-{kind}.html').read_text()
        for section in content:
            if kind == 'regulatory':
                section = external_news_links(section)
            ungrouped = re.sub(r'\s+data-region-item="[^"]+"', '', output)
            assert section in ungrouped, f"Section content changed: {item['id']} {kind}"
        unwanted = "cases" if kind == "regulatory" else "regulatory"
        for section in sections[unwanted]:
            assert section not in output, f"Other section leaked: {item['id']} {kind}"
        assert 'archive-picker' not in output, "Section editions must not enter homepage navigation"
print("Section editions verified: exact content, no other section, independent files")

# Intelligence data must remain attributable and separate from formal reports.
import re
from urllib.parse import urlsplit
intelligence=json.loads((ROOT/'data/intelligence.json').read_text())
sources={s['id']:s for s in intelligence['sources']}
urls=set()
for item in intelligence['items']:
    assert item['source'] in sources and item['kind']==sources[item['source']]['kind']
    assert item['title'].strip() and urlsplit(item['url']).scheme=='https'
    assert item['url'] not in urls, 'Duplicate intelligence article URL'
    urls.add(item['url'])
    assert not item.get('published') or re.fullmatch(r'\d{4}-\d{2}(-\d{2})?',item['published'])
    assert not item.get('published') or item['published']<=intelligence['updatedAt'][:10], 'Future news date'
intelligence_html=(DIST/'intelligence.html').read_text()
from build_intelligence import intelligence_data
today_items=intelligence_data(ROOT)['items']
assert intelligence_html.count('class="news-item"')==len(today_items)
assert ('intelligence.html?v=' in (DIST/'dashboard.html').read_text())==True
window=intelligence_data(ROOT)
assert all(window['windowStart']<=i['published']<=window['displayDate'] for i in today_items)
assert not any('intelligence' in i['id'] for i in catalog), 'Do not put daily feeds in report archives'
print(f'Intelligence validated: {len(urls)} unique sourced headlines')

# Fixed six-module workbench order and attributed legislative records.
from build_legislation import legislation_data
from html import unescape
board=(DIST/'dashboard.html').read_text()
headings=[unescape(re.sub('<[^>]+>','',m)) for m in re.findall(r'<h2\b[^>]*>(.*?)</h2>',board,re.S)]
expected=['\u7acb\u6cd5\u52a8\u6001','\u5224\u4f8b\u53ca\u6267\u6cd5','\u76d1\u7ba1\u66f4\u65b0','\u56db\u4f4d\u4e00\u4f53','\u5408\u89c4\u4e8b\u9879\u5907\u5fd8','\u6bcf\u65e5\u5f85\u529e']
assert headings==expected, headings
legislation=legislation_data(ROOT)
legislation_html=(DIST/'legislation.html').read_text()
assert legislation_html.count('class="legislation-item"')==len(legislation['items'])
assert {i['jurisdiction'] for i in legislation['items']} >= {'\u9999\u6e2f','\u5185\u5730','\u7f8e\u56fd'}
for item in legislation['items']:
    assert item['stage'] and item['stageRecord'] and item['nextStep']
    for source in item['sources']:
        assert source['url'] in legislation_html, 'Lost legislative source'
print('Workbench order and legislative source attribution verified')

from build_compliance import compliance_data
compliance=compliance_data(ROOT)
assert all(any(dept in str(item.get(field,'')) for field in ('owner','participants') for dept in ('法规部','法律合规部')) for item in compliance['items'])
payload=re.search(r'<script id="compliance-data" type="application/json">(.*?)</script>',(DIST/'compliance.html').read_text(),re.S)
assert {i['id'] for i in json.loads(payload[1])['items']}=={i['id'] for i in compliance['items']}, 'Memo scope differs from displayed payload'
for filename in ['legislation.html']+[f'archive/{item["id"]}-{kind}.html' for item in catalog for kind in ('regulatory','cases')]:
    page=(DIST/filename).read_text()
    assert page.count('data-region-tab=')==3, filename
    counts={r:page.count('data-region-item="'+r+'"') for r in ('香港','内地','其他')}
    assert sum(counts.values())>0, filename
print('Regional tabs and compliance department scope verified')
