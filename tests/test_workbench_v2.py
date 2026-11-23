import hashlib
import json
from datetime import datetime
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_workbench_v2 import build_workbench_v2,monthly_memo
from build_compliance import compliance_data


class WorkbenchTests(unittest.TestCase):
    def test_monthly_memo_distinguishes_dates_and_start_reminders(self):
        memo=compliance_data(ROOT)['items']
        november=monthly_memo(memo,datetime(2026,11,23))
        self.assertIn('本月暂无固定日期事项',november)
        self.assertIn('下月准备 · 非本月到期事项',november)
        self.assertIn('12月31日起开始',november)
        self.assertNotIn('基金费用监控',november)
        december=monthly_memo(memo,datetime(2026,12,1))
        self.assertNotIn('本月暂无固定日期事项',december)
        self.assertIn('12月31日（目标日）',december)

    def test_build_preserves_original_and_does_not_reuse_stale_analysis(self):
        catalog=sorted(json.loads((ROOT/'reports/catalog.json').read_text()),key=lambda i:i['periodEnd'],reverse=True)
        original=ROOT/'dist/dashboard.html'
        before=hashlib.sha256(original.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            dist=Path(tmp);(dist/'assets').mkdir();(dist/'archive').mkdir()
            (dist/'dashboard.html').write_bytes(original.read_bytes())
            for name in ('legislation.html','intelligence.html'):(dist/name).write_bytes((ROOT/'dist'/name).read_bytes())
            for file in (ROOT/'dist/archive').glob('*.html'):(dist/'archive'/file.name).write_bytes(file.read_bytes())
            build_workbench_v2(ROOT,dist,catalog)
            html=(dist/'workbench-v2.html').read_text()
            self.assertNotIn('{{',html)
            overview=html.split('<section data-panel="overview">')[1].split('<section data-panel="purpose"')[0]
            self.assertNotIn('工作模块',overview)
            self.assertNotIn('工作目标',overview)
            self.assertIn('监管趋势',overview)
            self.assertIn('合规事项备忘',overview)
            self.assertEqual(html.count('data-discussion='),2)
            import build_workbench_v2 as module
            loads=module.json.loads
            def stale(text,*args,**kwargs):
                data=loads(text,*args,**kwargs)
                if isinstance(data,dict) and 'periodId' in data:data['periodId']='2000-01-01'
                return data
            with patch.object(module.json,'loads',side_effect=stale):build_workbench_v2(ROOT,dist,catalog)
            self.assertIn('本期分析待更新',(dist/'workbench-v2.html').read_text())
            self.assertEqual(hashlib.sha256((dist/'dashboard.html').read_bytes()).hexdigest(),before)
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),before)


if __name__=='__main__':unittest.main()
