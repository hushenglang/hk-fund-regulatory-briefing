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
for item in catalog:
    source = (ROOT / "reports" / (item["id"] + ".html")).read_text()
    sections = section_content(source)
    for kind, content in sections.items():
        output = (DIST / "archive" / f'{item["id"]}-{kind}.html').read_text()
        for section in content:
            if kind == 'regulatory':
                section = external_news_links(section)
            assert section in output, f"Section content changed: {item['id']} {kind}"
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
