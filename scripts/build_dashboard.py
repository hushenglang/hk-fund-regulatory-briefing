"""Build an independent dashboard from the latest weekly report's sections."""
import re
import shutil
import os
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape, unescape
from split_reports import Document, section_content
from build_compliance import compliance_payload


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
    revision = 'HEAD' if os.environ.get('GITHUB_ACTIONS') else 'origin/main'
    try:
        timestamp = subprocess.check_output(['git', 'log', revision, '-1', '--format=%cI', '--', f'reports/{weekly["id"]}.html'], cwd=root, stderr=subprocess.DEVNULL, text=True).strip()
        updated = datetime.fromisoformat(timestamp).astimezone(ZoneInfo('Asia/Hong_Kong')).date().isoformat()
        updated_label = updated.replace('-', '.')
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        updated, updated_label = '', '更新日期待确认'
    cards = []
    icons = {
        'regulatory': '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6m-6 4h6m-6 4h4"/>',
        'cases': '<path d="m14 3 7 7m-9-5 7 7M5 21l10-10m-5-4 7 7M3 21h8"/>'
    }
    for kind, label in [('regulatory', '监管更新'), ('cases', '判例及执法')]:
        rows = []
        for title, detail, category in data[kind][:2]:
            rows.append(f'<li><span class="headline" title="{escape(title, quote=True)}">{escape(title)}</span></li>')
        count = len(data[kind])
        cards.append(f'''<a class="module active" href="archive/{weekly['id']}-{kind}.html" aria-label="查看最新周报的{label}，共{count}项">
<div class="module-top"><span class="module-icon" aria-hidden="true"><svg viewBox="0 0 24 24">{icons[kind]}</svg></span><h2>{label}</h2><time class="status update-date" datetime="{updated}" title="内容更新日期（香港时间）">{updated_label}</time></div>
<div class="metric"><strong>{count}</strong><span>项</span></div><p class="metric-note">本期收录</p>
<p class="section-label">要点速览</p><ul class="highlights">{''.join(rows)}</ul><div class="module-footer"><span>进入模块</span><span aria-hidden="true">→</span></div></a>''')
    template = (root / 'templates/dashboard.html').read_text()
    for key, value in {'ISSUE_LABEL': escape(weekly['label']), 'ISSUE_ID': weekly['id'], 'MODULES': ''.join(cards)}.items():
        template = template.replace('{{' + key + '}}', value)
    template = template.replace('</body>', compliance_payload(root) + '<script src="assets/compliance.js"></script><script src="assets/daily-todos.js"></script></body>')
    (dist / 'assets').mkdir(exist_ok=True)
    shutil.copyfile(root / 'assets/daily-todos.js', dist / 'assets/daily-todos.js')
    (dist / 'dashboard.html').write_text(template)
    print(f'Built dashboard from latest weekly report: {weekly["id"]}')
