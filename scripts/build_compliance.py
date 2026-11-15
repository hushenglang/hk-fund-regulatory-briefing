"""Build a read-only calendar from the supplied 2026 compliance document."""
import json
import shutil


def compliance_payload(root):
    data = json.loads((root / 'data/compliance-2026.json').read_text())
    assert data['year'] == 2026
    assert len(data['items']) == len({i['id'] for i in data['items']})
    return '<script id="compliance-data" type="application/json">' + json.dumps(data, ensure_ascii=False).replace('<', '\\u003c') + '</script>'


def build_compliance(root, dist):
    payload = compliance_payload(root)
    page = (root / 'templates/compliance.html').read_text().replace('{{COMPLIANCE_DATA}}', payload)
    (dist / 'compliance.html').write_text(page)
    (dist / 'assets').mkdir(exist_ok=True)
    shutil.copyfile(root / 'assets/compliance.js', dist / 'assets/compliance.js')
    print('Built 2026 compliance calendar')
