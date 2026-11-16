"""Build a read-only calendar from the supplied 2026 compliance document."""
import json
import shutil
import hashlib


def compliance_data(root):
    data=json.loads((root/'data/compliance-2026.json').read_text())
    assert data['year']==2026
    assert len(data['items'])==len({i['id'] for i in data['items']})
    data['items']=[i for i in data['items'] if not i.get('excludedFromMemo') and any(dept in str(i.get(field,'')) for field in ('owner','participants') for dept in ('法规部','法律合规部'))]
    return data


def compliance_summary(root):
    items=compliance_data(root)['items']
    confirm=sum(bool(i.get('monthlyDay')) or i['sourceStatus']=='文档未注明' for i in items)
    completed=sum(not i.get('monthlyDay') and i['sourceStatus']=='已完成' for i in items)
    pending=len(items)-confirm-completed
    return {'TOTAL':len(items),'CONFIRM':confirm,'COMPLETED':completed,'PENDING':pending,'FOLLOWUP':pending+confirm,'MONITORING':sum(i.get('group')=='定期监控' for i in items)}


def compliance_counts(html,root):
    for key,value in compliance_summary(root).items():html=html.replace('{{COMPLIANCE_'+key+'}}',str(value))
    return html


def compliance_version(root):
    content = b''.join((root / p).read_bytes() for p in ['data/compliance-2026.json', 'assets/compliance.js', 'templates/compliance.html', 'scripts/build_compliance.py'])
    return hashlib.sha256(content).hexdigest()[:12]


def compliance_script(root):
    version = hashlib.sha256((root / 'assets/compliance.js').read_bytes()).hexdigest()[:12]
    return f'<script src="assets/compliance.js?v={version}"></script>'


def compliance_payload(root):
    data = compliance_data(root)
    return '<script id="compliance-data" type="application/json">' + json.dumps(data, ensure_ascii=False).replace('<', '\\u003c') + '</script>'


def build_compliance(root, dist):
    payload = compliance_payload(root)
    page = (root / 'templates/compliance.html').read_text().replace('{{COMPLIANCE_DATA}}', payload)
    page = compliance_counts(page,root)
    page = page.replace('<script src="assets/compliance.js"></script>', compliance_script(root))
    page = page.replace('href="dashboard.html"', f'href="dashboard.html?v={compliance_version(root)}"')
    (dist / 'compliance.html').write_text(page)
    (dist / 'assets').mkdir(exist_ok=True)
    shutil.copyfile(root / 'assets/compliance.js', dist / 'assets/compliance.js')
    print('Built 2026 compliance calendar')
