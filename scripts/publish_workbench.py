"""Promote the approved workbench and retain the original dashboard UI."""
from pathlib import Path


def publish_workbench(dist):
    dist=Path(dist)
    classic=dist/'dashboard-classic.html'
    if 'class="module daily-panel"' not in (dist/'dashboard.html').read_text():
        raise ValueError('Build the original dashboard before promoting the updated edition')
    classic.write_bytes((dist/'dashboard.html').read_bytes())
    page=(dist/'workbench-layout-preview.html').read_text()
    page=page.replace('<title>法律合规工作台 · 布局方案</title>','<title>法律合规工作台</title>')
    page=page.replace('>布局方案</span>','>更新版</span>')
    page=page.replace('href="workbench-v2.html" target="_blank" rel="noopener">打开当前版本','href="dashboard-classic.html" target="_blank" rel="noopener">旧版工作台')
    page=page.replace('contract-library-preview.html','contract-library.html').replace('training-library-preview.html','training-library.html')
    if '{{' in page:raise ValueError('Unresolved workbench placeholders')
    (dist/'workbench.html').write_text(page)
    (dist/'dashboard.html').write_text(page)
    preview=(dist/'workbench-layout-preview.html').read_text()
    preview=preview.replace('href="workbench-v2.html" target="_blank" rel="noopener">打开当前版本','href="dashboard.html" target="_blank" rel="noopener">打开更新版')
    (dist/'workbench-layout-preview.html').write_text(preview)
    for name in ('contract-library','training-library'):
        (dist/(name+'.html')).write_bytes((dist/(name+'-preview.html')).read_bytes())
    # The older seven-module page keeps its original-dashboard return link.
    older=(dist/'workbench-v2.html').read_text()
    older=older.replace('href="dashboard.html" target="_blank" rel="noopener">打开原版工作台','href="dashboard-classic.html" target="_blank" rel="noopener">打开原版工作台')
    (dist/'workbench-v2.html').write_text(older)
    print('Published workbench.html and default dashboard; retained dashboard-classic.html')
