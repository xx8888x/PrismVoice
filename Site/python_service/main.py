import feedparser
import pymysql
import hashlib
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random
import uuid

import os
env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
env_vars = {}
try:
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.strip().split('=', 1)
                env_vars[k.strip()] = v.strip()
except Exception as e:
    print("Error reading .env:", e)

DB_CONFIG = {
    'host': env_vars.get('DB_HOST', '127.0.0.1'),
    'port': int(env_vars.get('DB_PORT', 3307)),
    'user': env_vars.get('DB_USERNAME', 'mediaweb'),
    'password': env_vars.get('DB_PASSWORD', ''),
    'database': env_vars.get('DB_DATABASE', 'mediaweb'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# 1. ?游?憭?啗?靘?
RSS_FEEDS = [
    {'name': '?臬??啗?蝬?(UDN)', 'url': 'https://udn.com/news/rssfeed/6638'},
    {'name': 'Yahoo 憟?啗?', 'url': 'https://tw.news.yahoo.com/rss/'},
    {'name': '?祈??啗?蝬?(PTS)', 'url': 'https://news.pts.org.tw/xml/newsfeed.xml'}
]

def fetch_full_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Prism/1.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        article_body = soup.find('section', class_='article-content__editor') or soup.find('article') or soup.find('main') or soup.find('body')
        if article_body:
            paragraphs = article_body.find_all('p')
            return '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        return ""
    except Exception as e:
        return ""

class MockAIClient:
    def __init__(self):
        pass

    def analyze(self, title, full_text):
        combined_text = title + "\n" + full_text
        score = 0
        confidence = 0.55
        reason = "AI 隤甇斤??勗?蝡銝剔?嚗?＊?炊??

        if any(w in combined_text for w in ["?舀?", "??", "?拙?", "甇?"]):
            score = random.choice([1, 2])
            confidence = random.uniform(0.7, 0.95)
            reason = "AI ?斗嚗???急迤?Ｚ??舀??扯?敶?蝡??韐???
        elif any(w in combined_text for w in ["??", "?降", "?拍征", "鞎", "銝遛"]):
            score = random.choice([-1, -2])
            confidence = random.uniform(0.7, 0.95)
            reason = "AI ?斗嚗???曇??Ｘ?撘瑞??降??瘞??蝡??????
        elif any(w in combined_text for w in ["?剛降", "鞈芰?", "?拇扔"]):
            score = -1
            confidence = 0.65
            reason = "AI ?斗嚗?蝡??箔?隢詨?鞈芰?嚗??輻??望?靽??漲??

        return {
            "score": score,
            "confidence": round(confidence, 2),
            "evidence": full_text[:120] + "..." if full_text else title,
            "reason": reason,
            "actor": "Mock AI (璅⊥璅∪?)",
            "method": "auto"
        }

ai_client = MockAIClient()

# 4. ?啣虜?扔蝡臬?隤方郎??(Webhook)
def send_webhook_alert(title, source, score):
    # Mock Webhook URL (靘? Slack, Discord, ??芸遣??Line Bot)
    webhook_url = "https://httpbin.org/post" 
    payload = {
        "text": f"? [閫暺郎?崧 ?潛璆萇垢?炊?勗?嚗n靘?: {source}\n璅?: {title}\nAI ?文??: {score} (?航撣嗆?撘瑞??身蝡)"
    }
    try:
        requests.post(webhook_url, json=payload, timeout=5)
        print(f"--> [?冽?] 撌脩?扔蝡臬?隤方郎?? {title}")
    except Exception as e:
        print(f"Webhook ?潮仃?? {e}")

# 2. ?芸?鈭辣?黎瞍?瘜?(Clustering)
def assign_event_cluster(cursor, article_title):
    # ???餈?50 蝑?隞嗡??脰?璅?瘥?
    cursor.execute("SELECT id, title FROM news_events ORDER BY id DESC LIMIT 50")
    recent_events = cursor.fetchall()
    
    # 蝪∪???祉隡澆漲閮? (閮??勗??箇????靘?撖血?銝?? TF-IDF ??Embedding)
    best_match_id = None
    best_score = 0.3 # ?訾撮摨阡?瑼?    
    chars_a = set(article_title)
    for event in recent_events:
        chars_b = set(event['title'])
        overlap = len(chars_a & chars_b)
        score = overlap / min(len(chars_a), len(chars_b)) if min(len(chars_a), len(chars_b)) > 0 else 0
        if score > best_score:
            best_score = score
            best_match_id = event['id']
            
    if best_match_id:
        return best_match_id
        
    # 憒?瘝??寥???隞塚??芸??萄遣?唬?隞?    cluster_key = str(uuid.uuid4())
    dimensions = json.dumps([{
        "key": "dim_general",
        "name": "?輻???隞嗆?漲",
        "question": "閰脣撠??潭迨鈭辣??摨西??身蝡?箔?嚗?,
        "left": "撘瑞???/鞈芰?",
        "right": "?典??舀?/霅瑁"
    }])
    cursor.execute("""
        INSERT INTO news_events (cluster_key, title, description, dimensions, is_demo, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
    """, (cluster_key, article_title, 'AI ?芸??黎撱箇????隞?, dimensions, False))
    return cursor.lastrowid

def process_feeds():
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            for feed_info in RSS_FEEDS:
                print(f"Fetching RSS: {feed_info['name']}")
                feed = feedparser.parse(feed_info['url'])
                for entry in feed.entries[:10]: # ?箔? Demo嚗?甈⊥???10 蝭?                    url = entry.link
                    url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
                    
                    cursor.execute("SELECT id FROM articles WHERE url_hash = %s", (url_hash,))
                    if cursor.fetchone():
                        continue 
                    
                    title = entry.title
                    published_at = datetime.now()
                    try:
                        if hasattr(entry, 'published_parsed'):
                            published_at = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    except:
                        pass
                    
                    full_text = fetch_full_text(url)
                    analysis = ai_client.analyze(title, full_text)
                    
                    # 閫貊璆萇垢?炊霅血 (??圈? +2 ??-2)
                    if abs(analysis['score']) == 2:
                        send_webhook_alert(title, feed_info['name'], analysis['score'])
                    
                    # ???黎
                    event_id = assign_event_cluster(cursor, title)
                    
                    # ??閰脖?隞嗥?蝬剖漲
                    cursor.execute("SELECT dimensions FROM news_events WHERE id = %s", (event_id,))
                    event_dims = json.loads(cursor.fetchone()['dimensions'])
                    
                    assessments = {}
                    for d in event_dims:
                        assessments[d['key']] = analysis
                    
                    cursor.execute("""
                        INSERT INTO articles (news_event_id, url, url_hash, title, source, published_at, imported_at, assessments, analysis_status, revision, is_demo, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s, 1, %s, NOW(), NOW())
                    """, (event_id, url, url_hash, title, feed_info['name'], published_at, json.dumps(assessments, ensure_ascii=False), 'reviewed', False))
                    
                    print(f"Imported: {title} (Event ID: {event_id})")
                
                connection.commit()
    finally:
        connection.close()

if __name__ == "__main__":
    print("Starting Prism Python Scraper Service...")
    while True:
        try:
            process_feeds()
        except Exception as e:
            print(f"Error processing feeds: {e}")
        time.sleep(300)

