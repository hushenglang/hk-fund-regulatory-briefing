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
