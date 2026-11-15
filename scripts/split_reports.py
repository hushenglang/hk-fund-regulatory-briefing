"""Create two standalone section editions, leaving the combined report intact."""
import re
from html import escape
from html.parser import HTMLParser


class Node:
    def __init__(self, tag, attrs, start):
        self.tag, self.attrs, self.start = tag, dict(attrs), start
        self.end = start
        self.children = []


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.offsets = [0]
        for line in source.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.nodes, self.stack = [], []
        self.feed(source)

    def position(self):
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.position())
        self.nodes.append(node)
        if self.stack:
            self.stack[-1].children.append(node)
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append(node)
        else:
            node.end = self.position() + len(self.get_starttag_text())

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i].tag == tag:
                node = self.stack[i]
                node.end = self.source.index('>', self.position()) + 1
                del self.stack[i:]
                return

    def html(self, node):
        return self.source[node.start:node.end]


def section_content(source):
    doc = Document(source)
    result = {'regulatory': [], 'cases': []}
    for section in (n for n in doc.nodes if n.tag == 'section'):
        html = doc.html(section)
        heading = re.search(r'<h2\b[^>]*>(.*?)</h2>', html, re.S)
        title = re.sub('<[^>]+>', '', heading[1]) if heading else ''
        if '监管更新' in title:
            result['regulatory'].append(html)
        elif '判例及执法' in title:
            result['cases'].append(html)
        elif section.attrs.get('id') == 'threeq':
            # The original October weekly edition mixed enforcement and policy.
            articles = [n for n in doc.nodes if n.tag == 'article' and section.start < n.start < section.end]
            for article in articles:
                text = doc.html(article)
                kind = 'cases' if '执法及停牌' in text else 'regulatory'
                result[kind].append('<section class="legacy-section">' + text + '</section>')
    if not all(result.values()):
        raise ValueError('Report must contain identifiable regulatory and case sections')
    return result


def external_news_links(html):
    def update(match):
        tag = match[0]
        if not re.search(r'\bhref\s*=\s*[\"\']https?://', tag, re.I):
            return tag
        tag = re.sub(r'\s+target\s*=\s*([\"\']).*?\1', '', tag, flags=re.I)
        rel = re.search(r'\s+rel\s*=\s*([\"\'])(.*?)\1', tag, re.I)
        tokens = set(rel[2].split()) if rel else set()
        tokens.update(['noopener', 'noreferrer'])
        tag = re.sub(r'\s+rel\s*=\s*([\"\']).*?\1', '', tag, flags=re.I)
        return tag[:-1] + ' target="_blank" rel="' + ' '.join(sorted(tokens)) + '">'
    return re.sub(r'<a\b[^>]*>', update, html, flags=re.I)


def make_edition(source, item, kind, sections):
    title = {'regulatory': '监管更新', 'cases': '判例及执法'}[kind]
    doc = Document(source)
    head = doc.html(next(n for n in doc.nodes if n.tag == 'head'))
    head = re.sub(r'<title>.*?</title>', f'<title>{escape(item["label"])} 香港基金管理 · {title}</title>', head, flags=re.S)
    header = doc.html(next(n for n in doc.nodes if n.tag == 'header'))
    # Remove the combined edition's overview; it covers material not in this file.
    summaries = [n for n in doc.nodes if 'summary' in n.attrs.get('class', '').split() and header.find(doc.html(n)) >= 0]
    for node in summaries:
        header = header.replace(doc.html(node), '')
    header = re.sub(r'<span class="subtitle">.*?</span>', f'<span class="subtitle">{title}</span>', header, count=1, flags=re.S)
    if kind == 'regulatory':
        header = re.sub(r'<h1\b[^>]*>.*?</h1>', '<h1>监管更新-香港基金管理行业</h1>', header, count=1, flags=re.S)
    css = '''<style id="section-edition">
.columns,.weekly-content .columns{display:block}.columns>section:first-child>article{display:block;min-height:0}
.edition-label{font-size:11px;color:var(--muted);margin:15px 0 0}.legacy-section{margin:0!important}
.footer{border-top:1px solid var(--line);margin-top:24px}
@media print{@page{size:A4 portrait}thead{display:table-header-group}tr{break-inside:avoid}}
</style>'''
    head = head.replace('</head>', css + '</head>')
    content = ''.join(sections)
    if kind == 'regulatory':
        content = external_news_links(content)
    # A standalone edition identifies itself in the header; keep original section
    # headings, table captions, notes and official sources exactly as authored.
    body = f'<body id="top"><main class="sheet">{header}<p class="edition-label">{escape(item["type"])} · {escape(item["label"])} · {title}专版</p><div class="columns weekly-content">{content}</div><footer class="footer"><p>法律合规部 · {escape(item["label"])} · {title}</p></footer></main></body>'
    return '<!doctype html><html lang="zh-CN">' + head + body + '</html>'


def build_split_reports(root, dist, catalog):
    for item in catalog:
        source = (root / 'reports' / (item['id'] + '.html')).read_text()
        sections = section_content(source)
        for kind, content in sections.items():
            (dist / 'archive' / f'{item["id"]}-{kind}.html').write_text(make_edition(source, item, kind, content))
    print(f'Built {len(catalog) * 2} section editions; combined homepage unchanged')
