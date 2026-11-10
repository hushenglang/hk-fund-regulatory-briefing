"""Generate a static latest-issue homepage and navigable, permanent archives."""
import json
import re
from html import escape
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
catalog = json.loads((ROOT / "reports/catalog.json").read_text())
catalog.sort(key=lambda item: (item["periodEnd"], item["id"]), reverse=True)
assert catalog and len({item["id"] for item in catalog}) == len(catalog)
for item in catalog:
    assert re.fullmatch(r"[a-z0-9-]+", item["id"])
    assert date.fromisoformat(item["periodEnd"]).isoformat() == item["periodEnd"]
    assert (ROOT / "reports" / (item["id"] + ".html")).is_file()

NAV_CSS = """
<style id="archive-navigation">
.print-issue{display:none}
.archive-control{display:flex;align-items:center;gap:15px;position:relative;flex-shrink:0}
.latest-link{font-size:11px;color:var(--muted);white-space:nowrap}
.archive-picker{position:relative;text-align:left;z-index:20}
.archive-picker summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:9px;padding:8px 0 8px 10px;color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;white-space:nowrap}
.archive-picker summary::-webkit-details-marker{display:none}
.archive-picker summary::after{content:"";width:5px;height:5px;border-right:1px solid var(--muted);border-bottom:1px solid var(--muted);transform:rotate(45deg);margin:0 3px 4px 2px;transition:transform .15s}
.archive-picker[open] summary::after{transform:rotate(225deg);margin-top:5px}
.archive-picker summary:hover{color:var(--blue)}
.archive-picker summary:focus-visible,.archive-list a:focus-visible,.latest-link:focus-visible{outline:2px solid var(--blue);outline-offset:4px;border-radius:2px}
.archive-list{position:absolute;right:0;top:calc(100% + 8px);width:290px;padding:9px;background:#fffefa;border:1px solid var(--line);border-radius:8px;box-shadow:0 12px 36px #23323d12;max-height:min(65vh,480px);overflow-y:auto}
.archive-list h2{font:10px/1.5 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;color:var(--muted);padding:7px 10px 9px;letter-spacing:.1em}
.archive-list a{display:block;padding:12px 10px;border-radius:4px;line-height:1.6;text-decoration:none}
.archive-list a:hover,.archive-list a[aria-current=page]{background:#f1f2ed;color:var(--ink)}
.archive-list .issue-line{display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:13px;font-weight:500}
.archive-list .issue-caption{display:block;margin-top:3px;color:var(--muted);font-size:10px}
.archive-list .latest-badge{color:var(--blue);font-size:9px;font-weight:400;flex-shrink:0}
@media(max-width:600px){.heading{flex-wrap:wrap;gap:8px}.archive-control{margin-left:auto;gap:12px}.archive-picker summary{font-size:12px}.archive-list{width:min(290px,calc(100vw - 36px))}.latest-link{font-size:10px}}
@media print{.archive-control{display:none!important}.print-issue{display:block;font-size:12pt;color:#23323d}}
</style>
"""

NAV_JS = """
<script>
(()=>{const picker=document.querySelector('.archive-picker');if(!picker)return;
document.addEventListener('click',event=>{if(!picker.contains(event.target))picker.open=false});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&picker.open){picker.open=false;picker.querySelector('summary').focus()}});
picker.addEventListener('toggle',()=>picker.querySelector('summary').setAttribute('aria-expanded',String(picker.open)));
})();
</script>
"""

def render(item, homepage=False):
    page = (ROOT / "reports" / (item["id"] + ".html")).read_text()
    prefix = "" if homepage else "../"
    links = []
    for i, entry in enumerate(catalog):
        current = ' aria-current="page"' if entry["id"] == item["id"] else ""
        badge = '<span class="latest-badge">最新</span>' if i == 0 else ""
        url = prefix + "archive/" + entry["id"] + ".html"
        links.append(f'<a href="{url}"{current}><span class="issue-line">{escape(entry["label"])}{badge}</span><span class="issue-caption">{escape(entry["type"])} · {escape(entry["title"])}</span></a>')
    back = f'<a class="latest-link" href="{prefix}index.html">返回最新一期</a>' if item["id"] != catalog[0]["id"] else ""
    nav = f'<div class="archive-control">{back}<details class="archive-picker"><summary aria-expanded="false" aria-label="当前期：{escape(item["label"])}，选择历史简报">{escape(item["label"])}</summary><nav class="archive-list" aria-label="历史简报"><h2>历史简报</h2>{"".join(links)}</nav></details></div>'
    page, count = re.subn(r'<div class="period">.*?</div>', lambda _: nav + f'<span class="print-issue">{escape(item["label"])}</span>', page, count=1, flags=re.S)
    assert count == 1, f"Missing issue control location: {item['id']}"
    page = page.replace("</head>", NAV_CSS + "</head>")
    page = page.replace("</body>", NAV_JS + "</body>")
    return page

(DIST / "archive").mkdir(parents=True, exist_ok=True)
for item in catalog:
    (DIST / "archive" / (item["id"] + ".html")).write_text(render(item))
(DIST / "index.html").write_text(render(catalog[0], homepage=True))
(DIST / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
print(f"Built homepage: {catalog[0]['id']}; {len(catalog)} archived reports")
