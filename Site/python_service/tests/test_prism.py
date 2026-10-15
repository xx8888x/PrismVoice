"""python -m unittest discover -s tests -t .   (run from python_service/)"""
import json
import unittest
from datetime import datetime

from prism import cluster, dedupe, feeds, perspective
from prism.extract import extract_text
from prism.pipeline import is_due, link_reprint
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
        # Yahoo-style feed: the clock time is really UTC despite the +0800 label.
        shifted = feeds.parse_entries(rss, {**SOURCE, 'pubdate_offset_minutes': 480})
        self.assertEqual(shifted[0]['published_at'], datetime(2026, 10, 15, 8, 0))


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

    def test_selector_can_pick_paragraphs_and_leave_some_out(self):
        # Yahoo layout: an empty .atoms block, the body, then a "more stories" line of links that would hide reprints.
        html = f"""<section class="module-article-body"><article>
            <div class="atoms"></div>
            <div class="atoms"><p>{self.BODY}</p><div class="ad"><p>廣告</p></div><p>第二段。</p>
            <p class="read-more-vendor">更多自由時報報導 <a href="/1">相關新聞標題</a></p></div></article></section>
            <div class="stream"><p>{self.BODY * 2}</p></div>"""
        body, extractor = extract_text(html, 'section.module-article-body .atoms > p:not(.read-more-vendor)')
        self.assertEqual(body, f'{self.BODY}\n第二段。')
        self.assertEqual(extractor, 'selector:section.module-article-body .atoms > p:not(.read-more-vendor)')

    def test_nested_selector_matches_are_not_counted_twice(self):
        html = f'<div class="body"><p>{self.BODY}</p><div class="body"><p>第二段。</p></div></div>'
        self.assertEqual(extract_text(html, '.body')[0], f'{self.BODY}\n第二段。')


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

    def test_simplified_titles_join_traditional_events(self):
        # Without conversion this DW-style title scores 0.13 against event 1 and starts a new event.
        event_id, score = cluster.best_event('蒋万安秀公文称任内曾与中央谈松机迁移 交通部列时间线还原', self.POOL)
        self.assertEqual(event_id, 1)
        self.assertGreaterEqual(score, cluster.THRESHOLD)

    def test_conversion_folds_tai_variants_and_keeps_traditional_text(self):
        self.assertEqual(cluster.to_traditional('台湾为什么着急'), '台灣為什麼著急')
        self.assertEqual(cluster.to_traditional('臺灣總統府'), cluster.to_traditional('台灣總統府'))
        self.assertEqual(cluster.to_traditional('松山機場遷建 蔣萬安'), '松山機場遷建 蔣萬安')


WIRE = ('行政院長卓榮泰今天在立法院答詢時表示，松山機場遷建涉及國家整體航空政策，必須審慎評估，'
        '他請台北市長蔣萬安提供過去市府對松山機場的評估紀錄，以及立場轉變的理由，讓中央與地方能夠在同一份資料上討論。'
        '交通部長陳世凱補充，桃園機場第三航廈完工後，整體運量仍需要時間消化，現階段沒有能力完全承接松山機場的國內線與兩岸航線，'
        '民航局也將在年底前提出完整的容量報告。國民黨立委質疑，中央對首都發展缺乏規劃，卻要求地方提出資料，'
        '卓榮泰回應，中央與地方應該合作，不是互相指責，相關會議將邀請市府共同參與。')
OTHER = ('台北市長蔣萬安今天在市議會表示，松山機場遷建是市府長期的政策主張，市府早在2023年就曾回函中央表達立場，'
         '並非選舉前才提出。他說，市府願意把所有公文公開，請中央不要只看片段。民進黨議員則認為，市府至今沒有完整的財務規劃，'
         '遷建後的土地開發也缺乏時程，要求市府在下次定期大會提出專案報告。交通部長陳世凱補充，桃園機場第三航廈完工後，'
         '整體運量仍需要時間消化，中央也會持續與市府溝通。')


class DedupeTest(unittest.TestCase):
    TITLE = '松山機場遷建 卓榮泰請蔣萬安提供過往評估紀錄及轉變理由'

    def original(self, body, id=1, title=TITLE):
        return {'id': id, 'title': title, 'body': body}

    def test_wire_reprint_with_its_own_credit_lines_is_detected(self):
        reprint = '（中央社記者溫貴香台北15日電）' + WIRE + '（編輯：林克倫）1141015' + chr(10) + '更多新聞請見聯合新聞網'
        self.assertTrue(dedupe.best_original('松機遷建 卓榮泰請蔣萬安提供過往評估紀錄及轉變理由', reprint, [self.original(WIRE)])[0])
        self.assertLessEqual(bin(dedupe.simhash(reprint) ^ dedupe.simhash(WIRE)).count('1'), dedupe.MAX_DISTANCE)

    def test_another_story_on_the_same_event_is_not_a_reprint(self):
        jaccard, containment = dedupe.overlap(WIRE, OTHER)
        self.assertGreater(jaccard, 0)  # they share a sentence, as same-event stories do
        self.assertIsNone(dedupe.best_original('蔣萬安：市府2023年就曾回函中央表達松機遷建立場', OTHER, [self.original(WIRE)])[0])

    def test_same_body_under_unrelated_titles_is_an_extraction_error_not_a_reprint(self):
        self.assertIsNone(dedupe.best_original('僑委會組調查小組 不會超過1年', WIRE, [self.original(WIRE)])[0])

    def test_best_overlap_wins_and_short_bodies_are_not_fingerprinted(self):
        trimmed, exact = self.original(WIRE[:-30], 1), self.original(WIRE, 2)
        self.assertEqual(dedupe.best_original(self.TITLE, WIRE, [trimmed, exact])[0], exact)
        self.assertIsNone(dedupe.simhash('短訊' * 50))
        self.assertIsInstance(dedupe.simhash(WIRE), int)
        self.assertLess(dedupe.simhash(WIRE), 2 ** 64)  # fits the unsigned BIGINT column


class FakeCursor:
    def __init__(self, published):
        self.published, self.statements = published, []

    def execute(self, sql, params):
        self.statements.append((' '.join(sql.split()), params))
        self.last = params

    def fetchone(self):
        return {'published_at': self.published[self.last[0]]}


class LinkReprintTest(unittest.TestCase):
    NOW = datetime(2026, 10, 15, 12, 0)

    def test_later_reprint_points_at_the_group_root(self):
        cursor = FakeCursor({10: datetime(2026, 10, 15, 8, 0)})
        root = link_reprint(cursor, 30, datetime(2026, 10, 15, 9, 0), {'id': 20, 'duplicate_of_article_id': 10}, self.NOW)
        self.assertEqual(root, 10)
        self.assertEqual(cursor.statements[-1], ('UPDATE articles SET duplicate_of_article_id = %s, updated_at = %s WHERE id = %s', (10, self.NOW, 30)))

    def test_earlier_wire_story_takes_over_as_root(self):
        cursor = FakeCursor({20: datetime(2026, 10, 15, 8, 5)})
        root = link_reprint(cursor, 30, datetime(2026, 10, 15, 8, 0), {'id': 20, 'duplicate_of_article_id': None}, self.NOW)
        self.assertEqual(root, 30)
        sql, params = cursor.statements[-1]
        self.assertIn('WHERE id = %s OR duplicate_of_article_id = %s', sql)
        self.assertEqual(params, (30, self.NOW, 20, 20))


class ScheduleTest(unittest.TestCase):
    def test_failing_sources_back_off(self):
        now = datetime(2026, 10, 15, 12, 0)
        source = {'last_fetched_at': datetime(2026, 10, 15, 11, 0), 'fetch_interval_minutes': 30, 'consecutive_failures': 0}
        self.assertTrue(is_due(source, now))
        self.assertFalse(is_due({**source, 'consecutive_failures': 2}, now))  # 30 × 4 = 120 min
        self.assertTrue(is_due({**source, 'last_fetched_at': None}, now))


if __name__ == '__main__':
    unittest.main()
