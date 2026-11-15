"""Build an independent dashboard from the latest weekly report's sections."""
import re
from html import escape, unescape
from split_reports import Document, section_content


def plain(html):
    html = re.sub(r'<a\b[^>]*>.*?</a>', '', html, flags=re.S)
    return re.sub(r'\s+', ' ', unescape(re.sub('<[^>]*>', '', html))).strip()


def sentence(text):
    first = ''
    for part in re.split(r'(?<=[。！？])', text):
        first += part
        if len(first) >= 45:
            break
    return first if len(first) <= 110 else first[:108] + '…'


def extract_highlights(htmls, kind):
    doc = Document(''.join(htmls))
    articles = [n for n in doc.nodes if n.tag == 'article']
    records = []
    if kind == 'cases':
        for row in (n for n in doc.nodes if n.tag == 'tr'):
            cells = [n for n in row.children if n.tag == 'td']
            if len(cells) != 5:
                continue
            detail = doc.html(cells[4])
            first = re.search(r'<p\b[^>]*>(.*?)</p>', detail, re.S)
            records.append((plain(doc.html(cells[2])), sentence(plain(first[1] if first else detail)), plain(doc.html(cells[3]))))
    if not records:
        for article in articles:
            html = doc.html(article)
            heading = re.search(r'<h3\b[^>]*>(.*?)</h3>', html, re.S)
            paragraph = re.search(r'<p\b[^>]*>(.*?)</p>', html, re.S)
            if heading:
                records.append((plain(heading[1]), sentence(plain(paragraph[1])) if paragraph else '', ''))
    if not records:
        raise ValueError(f'No dashboard highlights found for {kind}')
    return records


def build_dashboard(root, dist, catalog):
    weekly = next((i for i in catalog if '周' in i['type']), None)
    if weekly is None:
        raise ValueError('Dashboard requires a weekly report')
    sections = section_content((root / 'reports' / (weekly['id'] + '.html')).read_text())
    data = {kind: extract_highlights(content, kind) for kind, content in sections.items()}
    cards = []
    for number, kind, label, caption in [('01', 'regulatory', '监管更新', '关注规则变化与业务影响'), ('02', 'cases', '判例及执法', '关注监管措施与执法启示')]:
        rows = []
        for title, detail, category in data[kind][:3]:
            badge = f'<span class="category">{escape(category)}</span>' if category else ''
            rows.append(f'<li>{badge}<h3>{escape(title)}</h3><p>{escape(detail)}</p></li>')
        count = len(data[kind])
        cards.append(f'''<a class="module active" href="archive/{weekly['id']}-{kind}.html" aria-label="查看最新周报的{label}，共{count}项">
<div class="module-top"><span class="number">{number}</span><span class="count">{count:02d} 项</span></div>
<h2>{label}<span class="arrow" aria-hidden="true">↗</span></h2><p class="caption">{caption}</p>
<ul class="highlights">{''.join(rows)}</ul><div class="module-footer">查看全部{label}<span aria-hidden="true">→</span></div></a>''')
    template = (root / 'templates/dashboard.html').read_text()
    for key, value in {'ISSUE_LABEL': escape(weekly['label']), 'ISSUE_ID': weekly['id'], 'MODULES': ''.join(cards)}.items():
        template = template.replace('{{' + key + '}}', value)
    (dist / 'dashboard.html').write_text(template)
    print(f'Built dashboard from latest weekly report: {weekly["id"]}')
