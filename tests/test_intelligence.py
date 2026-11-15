"""Exercise failure retention, dates and external source adapters offline."""
from datetime import datetime
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import refresh_intelligence as r

class IntelligenceTests(unittest.TestCase):
    def test_dates_and_precision(self):
        self.assertEqual(r.published('November 13, 2026'),'2026-11-13')
        self.assertEqual(r.published('2026年02月'),'2026-02')
        self.assertEqual(r.published('2026/11/10'),'2026-11-10')
        self.assertIsNone(r.published('undated'))
        self.assertEqual(r.page_date('<p class="article-date">2026/11/10</p>'),'2026-11-10')

    def test_private_funds_cards_use_published_date(self):
        card={'title':'Fund alert','url':'/resources/insights/test','date':{'startDate':'2026-11-04'}}
        data={'props':{'pageProps':{'page':{'pageData':{'insightsData':{'articles':[card]}}}}}}
        html='<script id="__NEXT_DATA__" type="application/json">'+json.dumps(data)+'</script>'
        with patch.object(r,'download',return_value=html):
            rows,_=r.collect(next(s for s in r.SOURCES if s['id']=='mofo'))
        self.assertEqual(rows[0]['published'],'2026-11-04')
        self.assertEqual(rows[0]['url'],'https://www.mofo.com/resources/insights/test')

    def test_wordpress_cr_dates_and_nested_article(self):
        html='<article class="outer"><article><h2><a href="https://example.org/a">First</a></h2><p><span class="published">2026年02月</span></p></article>\r<article><h2><a href="https://example.org/b">Second</a></h2><span class="published">2025年12月</span></article></article>'
        with patch.object(r,'download',side_effect=lambda u:html if '/fa-lv-jian-xun/' in u else ''):
            rows,_=r.collect(next(s for s in r.SOURCES if s['id']=='charltons'))
        self.assertEqual([x['published'] for x in rows],['2026-02','2025-12'])

    def test_rss_keyword_filter_and_canonical_dedup(self):
        xml='<rss><channel><item><title>New legal AI tool</title><link>https://example.org/a?utm_source=x</link><pubDate>Fri, 13 Nov 2026 10:00:00 +0000</pubDate></item><item><title>Office move</title><link>https://example.org/b</link></item></channel></rss>'
        with patch.object(r,'download',return_value=xml):
            rows,_=r.collect(next(s for s in r.SOURCES if s['id']=='lawnext'))
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['url'],'https://example.org/a')

    def test_partial_failure_preserves_history_and_rejects_future(self):
        now=datetime(2026,11,16,7,tzinfo=ZoneInfo('Asia/Hong_Kong'))
        old={'url':'https://example.org/old','title':'Old','source':'mofo','kind':'insights','published':'2026-11-01'}
        def fake(s):
            if s['id']!='harvey':raise TimeoutError()
            return [dict(url='https://example.org/new',title='New',source=s['id'],kind='ai',published='2026-11-15'),dict(url='https://example.org/future',title='Future',source=s['id'],kind='ai',published='2026-12-01')],0
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'data.json';p.write_text(json.dumps({'sources':[],'items':[old]}))
            d=r.refresh(p,fake,now)
        self.assertEqual({i['url'] for i in d['items']},{old['url'],'https://example.org/new'})
        self.assertEqual(next(s for s in d['sources'] if s['id']=='mofo')['status'],'error')

    def test_total_failure_does_not_replace_published_data(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'data.json';p.write_text('{"sources":[],"items":[]}');before=p.read_bytes()
            def fail(_):raise TimeoutError()
            with self.assertRaises(RuntimeError):r.refresh(p,fail)
            self.assertEqual(p.read_bytes(),before)

class SevenDayDisplayTests(unittest.TestCase):
    def test_seven_day_boundaries_exclude_future_and_unknown_dates(self):
        import build_intelligence as b
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'data').mkdir()
            items=[dict(title=str(d),url='https://example.org/'+str(n),published=d) for n,d in enumerate(['2026-11-16','2026-11-15','2026-11-10','2026-11-09','2026-11-17','2026-11',None])]
            path=root/'data/intelligence.json';path.write_text(json.dumps({'items':items,'sources':[]}));before=path.read_bytes()
            selected=b.intelligence_data(root,today='2026-11-16')
            self.assertEqual([i['published'] for i in selected['items']],['2026-11-16','2026-11-15','2026-11-10'])
            self.assertEqual(path.read_bytes(),before)

    def test_empty_window_keeps_card_and_article_board(self):
        import build_intelligence as b
        root=Path(__file__).resolve().parents[1]
        data={'items':[],'sources':[],'displayDate':'2026-11-16','updatedAt':'2026-11-16T07:00:00+08:00'}
        with tempfile.TemporaryDirectory() as folder,patch.object(b,'intelligence_data',return_value=data):
            dist=Path(folder);(dist/'assets').mkdir();b.build_intelligence(root,dist)
            self.assertIn('四位一体 + 法律AI',b.dashboard_card(root))
            self.assertIn('近7天暂无更新',b.dashboard_card(root))
            html=(dist/'intelligence.html').read_text()
            self.assertIn('aria-label="资讯列表">',html)
            self.assertNotIn('class="news-item"',html)

    def test_ai_only_window_keeps_both_tabs(self):
        import build_intelligence as b
        root=Path(__file__).resolve().parents[1]
        source=dict(id='harvey',name='Harvey',adapter='harvey',url='https://www.harvey.ai/blog',status='ok',lastSuccessAt='2026-11-16')
        data={'items':[dict(title='Today AI',url='https://example.org/today',source='harvey',kind='ai',published='2026-11-16')],'sources':[source],'displayDate':'2026-11-16','updatedAt':'2026-11-16T07:00:00+08:00'}
        with tempfile.TemporaryDirectory() as folder,patch.object(b,'intelligence_data',return_value=data):
            dist=Path(folder);(dist/'assets').mkdir();b.build_intelligence(root,dist)
            html=(dist/'intelligence.html').read_text()
            self.assertIn('data-kind="insights" aria-pressed="true">',html)
            self.assertIn('data-kind="ai" aria-pressed="false">',html)
            self.assertEqual(html.count('class="news-item"'),1)
            self.assertNotIn('date-filter',html)

if __name__=='__main__':unittest.main()
