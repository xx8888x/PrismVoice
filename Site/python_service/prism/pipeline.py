"""The only ingestion path: active sources → new articles with full text, an event, and first-pass assessments.

Reprints (same body as an earlier article, see dedupe.py) are kept but point at the earliest original through
articles.duplicate_of_article_id, and join that original's event.

Laravel owns the schema (migrations) and serves the API; this module only writes rows that
match it. Analysis status is always 'unreviewed': nothing automatic counts as reviewed.
"""
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone

import pymysql
import requests

from . import cluster, dedupe, feeds, perspective
from .extract import fetch_article
from .settings import HTTP_TIMEOUT, REQUEST_DELAY_SECONDS, USER_AGENT, alert_webhook_url

log = logging.getLogger('prism')

EVENT_DESCRIPTION = '依標題相似度自動分群；可人工移動文章修正。時間軸使用報導發布時間，不等同事件發生時間。'
MAX_BACKOFF_EXPONENT = 4


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def load_source(row):
    if isinstance(row.get('link_rewrite'), str):
        row['link_rewrite'] = json.loads(row['link_rewrite'])
    return row


def is_due(source, now):
    if source['last_fetched_at'] is None:
        return True
    # Back off exponentially while a feed keeps failing, capped at 16x the normal interval.
    factor = 2 ** min(source['consecutive_failures'], MAX_BACKOFF_EXPONENT)
    return source['last_fetched_at'] + timedelta(minutes=source['fetch_interval_minutes'] * factor) <= now


def select_sources(conn, slug=None):
    with conn.cursor() as cursor:
        if slug:
            cursor.execute('SELECT * FROM sources WHERE slug = %s', (slug,))
        else:
            cursor.execute('SELECT * FROM sources WHERE is_active = 1 ORDER BY id')
        return [load_source(row) for row in cursor.fetchall()]


def cluster_candidates(cursor, published_at):
    window = timedelta(days=cluster.WINDOW_DAYS)
    cursor.execute("""
        SELECT a.news_event_id, a.title FROM articles a JOIN news_events e ON e.id = a.news_event_id
        WHERE a.is_demo = 0 AND e.is_demo = 0 AND a.published_at BETWEEN %s AND %s
        ORDER BY a.published_at DESC LIMIT 800
    """, (published_at - window, published_at + window))
    return [(row['news_event_id'], row['title']) for row in cursor.fetchall()]


def find_original(cursor, title, body, fingerprint, published_at):
    """The stored article this body reprints (best overlap within the clustering window), or None."""
    if fingerprint is None:
        return None
    window = timedelta(days=cluster.WINDOW_DAYS)
    cursor.execute("""
        SELECT a.id, a.news_event_id, a.published_at, a.duplicate_of_article_id, a.title, c.body FROM articles a
        JOIN article_contents c ON c.article_id = a.id
        WHERE a.is_demo = 0 AND c.simhash IS NOT NULL AND BIT_COUNT(c.simhash ^ %s) <= %s AND a.published_at BETWEEN %s AND %s
    """, (fingerprint, dedupe.MAX_DISTANCE, published_at - window, published_at + window))
    return dedupe.best_original(title, body, cursor.fetchall())[0]


def link_reprint(cursor, article_id, published_at, original, now):
    """Point the article at its group's earliest member; if the article is older, it becomes the root instead. Returns the root id."""
    root_id = original['duplicate_of_article_id'] or original['id']
    cursor.execute('SELECT published_at FROM articles WHERE id = %s', (root_id,))
    if published_at < cursor.fetchone()['published_at']:
        # Feeds are read in source order, so a wire story often arrives after the outlet that reprinted it.
        cursor.execute('UPDATE articles SET duplicate_of_article_id = %s, updated_at = %s WHERE id = %s OR duplicate_of_article_id = %s',
                       (article_id, now, root_id, root_id))
        return article_id
    cursor.execute('UPDATE articles SET duplicate_of_article_id = %s, updated_at = %s WHERE id = %s', (root_id, now, article_id))
    return root_id


def find_or_create_event(cursor, title, published_at, now, original=None):
    if original is not None:
        # A reprint belongs with its original, whatever its re-edited title would cluster with.
        event_id, score = original['news_event_id'], 1.0
    else:
        event_id, score = cluster.best_event(title, cluster_candidates(cursor, published_at))
    if event_id is not None:
        cursor.execute('SELECT dimensions FROM news_events WHERE id = %s', (event_id,))
        return event_id, json.loads(cursor.fetchone()['dimensions']), score
    dimensions = perspective.dimensions()
    cursor.execute("""
        INSERT INTO news_events (cluster_key, title, description, dimensions, is_demo, created_at, updated_at)
        VALUES (%s, %s, %s, %s, 0, %s, %s)
    """, (f'auto-{uuid.uuid4().hex}', title[:255], EVENT_DESCRIPTION, json.dumps(dimensions, ensure_ascii=False), now, now))
    return cursor.lastrowid, dimensions, score


def insert_content(cursor, article_id, content, now, fingerprint=None, ignore_existing=False):
    """fingerprint stays NULL until the article has been checked for reprints, so backfill_duplicates can find unchecked rows."""
    body = content['body']
    cursor.execute(f"""
        INSERT {'IGNORE' if ignore_existing else ''} INTO article_contents
            (article_id, status, body, char_count, body_hash, simhash, extractor, http_status, error, fetched_at, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (article_id, content['status'], body, len(body or ''), hashlib.sha256(body.encode('utf-8')).hexdigest() if body else None,
          fingerprint, content['extractor'], content['http_status'], content['error'], now, now, now))


def import_article(conn, source, row, content):
    """Insert one article and its content in a single transaction. Returns the new event id or None if it already existed."""
    now = utcnow()
    published_at = row['published_at'] or now
    url_hash = hashlib.sha256(row['url'].encode('utf-8')).hexdigest()
    body = content['body'] if content['status'] == 'ok' else None
    fingerprint = dedupe.simhash(body)
    try:
        with conn.cursor() as cursor:
            original = find_original(cursor, row['title'], body, fingerprint, published_at)
            event_id, dimensions, score = find_or_create_event(cursor, row['title'], published_at, now, original)
            assessments = perspective.assessments_for(dimensions, row['title'])
            cursor.execute("""
                INSERT INTO articles (news_event_id, source_id, url, url_hash, title, source, author, category, published_at,
                                      imported_at, assessments, analysis_status, revision, is_demo, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'unreviewed', 1, 0, %s, %s)
            """, (event_id, source['id'], row['url'], url_hash, row['title'], source['name'], row['author'], row['category'],
                  published_at, now, json.dumps(assessments, ensure_ascii=False), now, now))
            article_id = cursor.lastrowid
            insert_content(cursor, article_id, content, now, fingerprint)
            root_id = link_reprint(cursor, article_id, published_at, original, now) if original else None
        conn.commit()
    except pymysql.err.IntegrityError as error:
        conn.rollback()
        if error.args and error.args[0] == 1062:  # duplicate url_hash: another run got there first
            return None
        raise
    except Exception:
        conn.rollback()
        raise
    maybe_alert(source, row, assessments)
    reprint = f', 轉載組原稿 #{root_id}' if root_id else ''
    log.info('  + [%s] %s → event %s (similarity %.2f, body %s%s)', source['slug'], row['title'][:50], event_id, score, content['status'], reprint)
    return event_id


def article_exists(conn, url):
    with conn.cursor() as cursor:
        cursor.execute('SELECT 1 FROM articles WHERE url_hash = %s', (hashlib.sha256(url.encode('utf-8')).hexdigest(),))
        return cursor.fetchone() is not None


def record_fetch(conn, source, error=None):
    now = utcnow()
    with conn.cursor() as cursor:
        if error is None:
            cursor.execute('UPDATE sources SET last_fetched_at = %s, last_success_at = %s, consecutive_failures = 0, last_error = NULL, updated_at = %s WHERE id = %s',
                           (now, now, now, source['id']))
        else:
            cursor.execute('UPDATE sources SET last_fetched_at = %s, consecutive_failures = consecutive_failures + 1, last_error = %s, updated_at = %s WHERE id = %s',
                           (now, str(error)[:2000], now, source['id']))
    conn.commit()


def run_source(conn, source, http=None):
    http = http or requests.Session()
    counts = {'created': 0, 'skipped': 0, 'full_text': 0}
    try:
        response = http.get(source['feed_url'], headers={'User-Agent': USER_AGENT}, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        rows = feeds.parse_entries(response.content, source)[:source['max_items_per_fetch']]
        for row in rows:
            if article_exists(conn, row['url']):
                counts['skipped'] += 1
                continue
            content = fetch_article(row['url'], source.get('content_selector'), http)
            time.sleep(REQUEST_DELAY_SECONDS)
            if import_article(conn, source, row, content) is None:
                counts['skipped'] += 1
                continue
            counts['created'] += 1
            counts['full_text'] += content['status'] == 'ok'
    except Exception as error:
        conn.rollback()
        record_fetch(conn, source, error)
        log.warning('[%s] 擷取失敗：%s', source['slug'], error)
        return {**counts, 'error': str(error)}
    record_fetch(conn, source)
    log.info('[%s] 新增 %d、略過 %d、全文成功 %d', source['slug'], counts['created'], counts['skipped'], counts['full_text'])
    return counts


def run_due(conn, slug=None, force=False):
    now = utcnow()
    results = {}
    for source in select_sources(conn, slug):
        if force or is_due(source, now):
            results[source['slug']] = run_source(conn, source)
    return results


def backfill_contents(conn, limit=100, http=None):
    """Fetch full text for articles imported before article_contents existed (or whose fetch row is missing)."""
    http = http or requests.Session()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT a.id, a.url, s.content_selector FROM articles a LEFT JOIN sources s ON s.id = a.source_id
            LEFT JOIN article_contents c ON c.article_id = a.id
            WHERE c.article_id IS NULL AND a.is_demo = 0 AND a.url IS NOT NULL ORDER BY a.id LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
    counts = {'ok': 0, 'empty': 0, 'failed': 0}
    for row in rows:
        content = fetch_article(row['url'], row['content_selector'], http)
        time.sleep(REQUEST_DELAY_SECONDS)
        with conn.cursor() as cursor:
            insert_content(cursor, row['id'], content, utcnow(), ignore_existing=True)
        conn.commit()
        counts[content['status']] += 1
    log.info('全文回補：%s', counts)
    return counts


def backfill_duplicates(conn):
    """Check stored bodies that were never fingerprinted (older imports, backfilled content), oldest first.

    Links reprints like import does, but leaves events alone: those rows may already carry manual moves or reviews.
    """
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT a.id, a.news_event_id, a.published_at, a.title, c.body FROM articles a JOIN article_contents c ON c.article_id = a.id
            WHERE a.is_demo = 0 AND c.status = 'ok' AND c.simhash IS NULL AND c.char_count >= %s ORDER BY a.published_at, a.id
        """, (dedupe.MIN_CHARS,))
        rows = cursor.fetchall()
    counts = {'checked': 0, 'reprints': 0, 'other_event': 0}
    for row in rows:
        now = utcnow()
        fingerprint = dedupe.simhash(row['body'])
        with conn.cursor() as cursor:
            original = find_original(cursor, row['title'], row['body'], fingerprint, row['published_at'])
            cursor.execute('UPDATE article_contents SET simhash = %s, updated_at = %s WHERE article_id = %s', (fingerprint, now, row['id']))
            if original:
                link_reprint(cursor, row['id'], row['published_at'], original, now)
                counts['reprints'] += 1
                if original['news_event_id'] != row['news_event_id']:
                    counts['other_event'] += 1
                    log.warning('轉載與原稿不在同一事件：文章 %s（事件 %s）↔ 文章 %s（事件 %s）',
                                row['id'], row['news_event_id'], original['id'], original['news_event_id'])
        conn.commit()
        counts['checked'] += 1
    log.info('轉載回補：%s', counts)
    return counts


def maybe_alert(source, row, assessments):
    url = alert_webhook_url()
    strong = [key for key, a in assessments.items() if a.get('score') is not None and abs(a['score']) == 2 and a.get('confidence', 0) >= 0.6]
    if not url or not strong:
        return
    try:
        requests.post(url, json={'text': f"[稜鏡] 強烈判定（{', '.join(strong)}）\n來源：{source['name']}\n標題：{row['title']}\n{row['url']}"}, timeout=5)
    except requests.RequestException as error:
        log.warning('Webhook 發送失敗：%s', error)
