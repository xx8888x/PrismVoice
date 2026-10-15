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

# 1. 擴充多方新聞來源
RSS_FEEDS = [
    {'name': '聯合新聞網 (UDN)', 'url': 'https://udn.com/news/rssfeed/6638'},
    {'name': 'Yahoo 奇摩新聞', 'url': 'https://tw.news.yahoo.com/rss/'},
    {'name': '公視新聞網 (PTS)', 'url': 'https://news.pts.org.tw/xml/newsfeed.xml'}
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
        reason = "AI 認為此篇報導立場中立，無明顯偏誤。"

        if any(w in combined_text for w in ["支持", "通過", "利多", "正面"]):
            score = random.choice([1, 2])
            confidence = random.uniform(0.7, 0.95)
            reason = "AI 判斷：內文包含正面與支持性詞彙，立場偏向贊同。"
        elif any(w in combined_text for w in ["反對", "抗議", "利空", "負面", "不滿"]):
            score = random.choice([-1, -2])
            confidence = random.uniform(0.7, 0.95)
            reason = "AI 判斷：內文呈現負面或強烈抗議的語氣，立場偏向反對。"
        elif any(w in combined_text for w in ["爭議", "質疑", "兩極"]):
            score = -1
            confidence = 0.65
            reason = "AI 判斷：文章提出了諸多質疑，對政策抱持保留態度。"

        return {
            "score": score,
            "confidence": round(confidence, 2),
            "evidence": full_text[:120] + "..." if full_text else title,
            "reason": reason,
            "actor": "Mock AI (模擬模式)",
            "method": "auto"
        }

ai_client = MockAIClient()

# 4. 異常與極端偏誤警報 (Webhook)
def send_webhook_alert(title, source, score):
    # Mock Webhook URL (例如 Slack, Discord, 或是自建的 Line Bot)
    webhook_url = "https://httpbin.org/post" 
    payload = {
        "text": f"🚨 [觀點警報] 發現極端偏誤報導！\n來源: {source}\n標題: {title}\nAI 判定分數: {score} (可能帶有強烈預設立場)"
    }
    try:
        requests.post(webhook_url, json=payload, timeout=5)
        print(f"--> [推播通知] 已發送極端偏誤警報: {title}")
    except Exception as e:
        print(f"Webhook 發送失敗: {e}")

# 2. 自動事件分群演算法 (Clustering)
def assign_event_cluster(cursor, article_title):
    # 取得最近 50 筆事件來進行標題比對
    cursor.execute("SELECT id, title FROM news_events ORDER BY id DESC LIMIT 50")
    recent_events = cursor.fetchall()
    
    # 簡單的文本相似度計算 (計算共同出現的字元比例，實務上可換成 TF-IDF 或 Embedding)
    best_match_id = None
    best_score = 0.3 # 相似度門檻
    
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
        
    # 如果沒有匹配的事件，自動創建新事件
    cluster_key = str(uuid.uuid4())
    dimensions = json.dumps([{
        "key": "dim_general",
        "name": "政策與事件支持度",
        "question": "該報導對於此事件的態度與預設立場為何？",
        "left": "強烈反對/質疑",
        "right": "全力支持/護航"
    }])
    cursor.execute("""
        INSERT INTO news_events (cluster_key, title, description, dimensions, is_demo, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
    """, (cluster_key, article_title, 'AI 自動分群建立的新聞事件', dimensions, False))
    return cursor.lastrowid

def process_feeds():
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            for feed_info in RSS_FEEDS:
                print(f"Fetching RSS: {feed_info['name']}")
                feed = feedparser.parse(feed_info['url'])
                for entry in feed.entries[:10]: # 為了 Demo，每次抓取 10 篇
                    url = entry.link
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
                    
                    # 觸發極端偏誤警報 (分數到達 +2 或 -2)
                    if abs(analysis['score']) == 2:
                        send_webhook_alert(title, feed_info['name'], analysis['score'])
                    
                    # 動態分群
                    event_id = assign_event_cluster(cursor, title)
                    
                    # 取得該事件的維度
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

