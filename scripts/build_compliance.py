"""Build a read-only calendar from the supplied 2026 compliance document."""
import json
import shutil
import hashlib


def compliance_version(root):
    content = b''.join((root / p).read_bytes() for p in ['data/compliance-2026.json', 'assets/compliance.js', 'templates/compliance.html'])
    return hashlib.sha256(content).hexdigest()[:12]


def compliance_script(root):
    version = hashlib.sha256((root / 'assets/compliance.js').read_bytes()).hexdigest()[:12]
    return f'<script src="assets/compliance.js?v={version}"></script>'


def compliance_payload(root):
    data = json.loads((root / 'data/compliance-2026.json').read_text())
    assert data['year'] == 2026
    assert len(data['items']) == len({i['id'] for i in data['items']})
    return '<script id="compliance-data" type="application/json">' + json.dumps(data, ensure_ascii=False).replace('<', '\\u003c') + '</script>'


def build_compliance(root, dist):
    payload = compliance_payload(root)
    page = (root / 'templates/compliance.html').read_text().replace('{{COMPLIANCE_DATA}}', payload)
    page = page.replace('<script src="assets/compliance.js"></script>', compliance_script(root))
    page = page.replace('href="dashboard.html"', f'href="dashboard.html?v={compliance_version(root)}"')
    (dist / 'compliance.html').write_text(page)
    (dist / 'assets').mkdir(exist_ok=True)
    shutil.copyfile(root / 'assets/compliance.js', dist / 'assets/compliance.js')
    print('Built 2026 compliance calendar')
