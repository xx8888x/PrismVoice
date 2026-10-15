"""python -m unittest discover -s tests -t .   (run from python_service/)"""
import json
import unittest
from datetime import datetime

from prism import cluster, feeds, perspective
from prism.extract import extract_text
from prism.pipeline import is_due
from prism.settings import SHARED_DIR


class PerspectiveParityTest(unittest.TestCase):
    """Same cases as backend/tests/Unit/PerspectiveTest: both languages must agree on shared/perspective.json."""

    def test_shared_cases(self):
        cases = json.loads((SHARED_DIR / 'perspective_cases.json').read_text(encoding='utf-8'))
        for case in cases:
            result = perspective.assess(case['title'])
            self.assertEqual({k: v['score'] for k, v in result.items()}, case['scores'], case['title'])
            self.assertEqual({k: v['evidence'] for k, v in result.items() if v['score'] is not None}, case['evidence'], case['title'])

    def test_new_events_get_the_dimensions_compare_expects(self):
        dims = perspective.dimensions()
        self.assertEqual([d['key'] for d in dims], ['position', 'focus', 'tone'])
        self.assertTrue(all('opposition' in d for d in dims))
        self.assertEqual(dims[0]['question'], perspective.definition()['default_question'])

    def test_assessments_follow_the_event_keys(self):
        custom = [{'key': 'position'}, {'key': 'extra'}]
        result = perspective.assessments_for(custom, '政策合作')
        self.assertEqual(set(result), {'position', 'extra'})
        self.assertIsNone(result['extra']['score'])


SOURCE = {'homepage_url': 'https://www.storm.mg', 'link_pattern': r'^https://www\.storm\.mg/article/\d+',
          'link_rewrite': [r'^/(\d+)', r'https://www.storm.mg/article/\1']}


class FeedsTest(unittest.TestCase):
    def test_links_are_rewritten_normalised_and_filtered(self):
        self.assertEqual(feeds.resolve_link('/11172630?utm_source=rss', SOURCE), 'https://www.storm.mg/article/11172630')
        self.assertIsNone(feeds.resolve_link('https://evil.example/article/1', SOURCE))
        self.assertIsNone(feeds.resolve_link('', SOURCE))

    def test_tracking_parameters_are_dropped_but_real_ones_kept(self):
        self.assertEqual(feeds.normalize_url('https://www.bbc.com/a/x/trad?at_medium=RSS&at_campaign=rss#top'), 'https://www.bbc.com/a/x/trad')
        self.assertEqual(feeds.normalize_url('https://ex.com/news?id=5&utm_source=x&fbclid=y'), 'https://ex.com/news?id=5')

    def test_dates_become_utc_including_malformed_rfc822(self):
        self.assertEqual(feeds.parse_published({'published': 'Thu,15 Oct 2026 14:45:00  +0800'}), datetime(2026, 10, 15, 6, 45))
        self.assertEqual(feeds.parse_published({'published': '2026-10-15T08:00:00+08:00'}), datetime(2026, 10, 15, 0, 0))
        self.assertIsNone(feeds.parse_published({'published': 'nonsense'}))

    def test_parse_entries_skips_foreign_untitled_and_duplicate_items(self):
        rss = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
            <item><title>Story A</title><link>/101?utm_source=rss</link><pubDate>Thu, 15 Oct 2026 08:00:00 +0800</pubDate></item>
            <item><title>Story A again</title><link>/101</link></item>
            <item><title></title><link>/102</link></item>
            <item><title>Elsewhere</title><link>https://other.example/1</link></item>
            </channel></rss>"""
        rows = feeds.parse_entries(rss, SOURCE)
        self.assertEqual([(r['url'], r['title']) for r in rows], [('https://www.storm.mg/article/101', 'Story A')])
        self.assertEqual(rows[0]['published_at'], datetime(2026, 10, 15, 0, 0))


class ExtractTest(unittest.TestCase):
    BODY = '這是一段夠長的新聞內文，描述事件的經過與各方說法。' * 3

    def test_density_prefers_body_over_link_lists_and_ignores_scripts(self):
        html = f"""<html><body>
            <ul class="related"><li><p><a href="/1">相關新聞標題一二三四五六七八九十十一十二</a></p></li></ul>
            <div class="related"><p><a href="/2">相關新聞標題一二三四五六七八九十十一十二</a></p><p><a href="/3">另一則相關新聞標題一二三四五六七八九十</a></p></div>
            <div class="story"><p>{self.BODY}</p><script>var x = 1;</script><p>第二段。</p></div></body></html>"""
        body, extractor = extract_text(html)
        self.assertEqual(body, f'{self.BODY}\n第二段。')
        self.assertEqual(extractor, 'density')

    def test_selector_wins_when_it_matches(self):
        html = f'<main><p>短</p></main><div><p>{self.BODY}</p></div>'
        self.assertEqual(extract_text(html, 'main'), ('短', 'selector:main'))
        self.assertEqual(extract_text(html, 'section.missing')[0], self.BODY)


class ClusterTest(unittest.TestCase):
    POOL = [(1, '親赴政院談松機遷移 蔣萬安秀公文：2023年曾回函中央表達遷建立場'),
            (2, '颱風山陀兒明晨登陸 全台停班停課一覽'),
            (3, '台積電法說會 第三季獲利創新高')]

    def test_same_story_from_another_outlet_joins_the_event(self):
        event_id, score = cluster.best_event('蔣萬安秀公文指「任內有與中央談松機遷移」 交通部列時間線還原', self.POOL)
        self.assertEqual(event_id, 1)
        self.assertGreaterEqual(score, cluster.THRESHOLD)

    def test_unrelated_story_starts_a_new_event(self):
        self.assertIsNone(cluster.best_event('立法院三讀通過國籍法修正案', self.POOL)[0])
        self.assertIsNone(cluster.best_event('任何標題', [])[0])

    def test_bracket_tags_do_not_count_as_shared_words(self):
        self.assertNotIn('影', ''.join(cluster.bigrams('【影】颱風登陸')))


class ScheduleTest(unittest.TestCase):
    def test_failing_sources_back_off(self):
        now = datetime(2026, 10, 15, 12, 0)
        source = {'last_fetched_at': datetime(2026, 10, 15, 11, 0), 'fetch_interval_minutes': 30, 'consecutive_failures': 0}
        self.assertTrue(is_due(source, now))
        self.assertFalse(is_due({**source, 'consecutive_failures': 2}, now))  # 30 × 4 = 120 min
        self.assertTrue(is_due({**source, 'last_fetched_at': None}, now))


if __name__ == '__main__':
    unittest.main()
