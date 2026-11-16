"""Check jurisdiction decisions and department scope without losing report content."""
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from regions import classify_region,annotate_regions,region_group
from build_compliance import compliance_data

class RegionTests(unittest.TestCase):
    def test_authority_controls_cross_border_classification(self):
        self.assertEqual(classify_region('<article>中国证监会对赴港上市公司反馈<a href="https://www.csrc.gov.cn/x">原文</a></article>'),'内地')
        self.assertEqual(classify_region('<tr><td>中国21世纪教育被联交所处分</td><td><a href="https://www.hkex.com.hk/x">原文</a></td></tr>'),'香港')
        self.assertEqual(classify_region('<article>SEC调查香港相关企业<a href="https://www.sec.gov/x">原文</a></article>'),'其他')
        self.assertEqual(region_group('美国'),'其他')

    def test_annotations_keep_body_and_table_headers(self):
        source='<section><article>香港证监会</article><article>中国证监会</article><table><thead><tr><th>日期</th></tr></thead><tbody><tr><td>SEC</td></tr></tbody></table></section>'
        marked,counts=annotate_regions(source)
        self.assertEqual(counts,{'香港':1,'内地':1,'其他':1})
        self.assertEqual(re.sub(r'\s+data-region-item="[^"]+"','',marked),source)
        self.assertIn('<thead><tr><th>日期</th></tr></thead>',marked)

class ComplianceScopeTests(unittest.TestCase):
    def test_owner_or_participant_involvement_retains_item(self):
        rows=[dict(id='owner',owner='法规部/运营部',participants='财务部'),dict(id='participant',owner='财务部',participants='法规部、行政管理人'),dict(id='neither',owner='财务部/RO',participants='Auditor'),dict(id='title_only',owner='财务部',participants='-',title='法规部相关参考')]
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'data').mkdir();path=root/'data/compliance-2026.json';path.write_text(json.dumps({'year':2026,'items':rows}));original=path.read_bytes()
            filtered=compliance_data(root)
            self.assertEqual([i['id'] for i in filtered['items']],['owner','participant'])
            self.assertEqual(path.read_bytes(),original)

if __name__=='__main__':unittest.main()
