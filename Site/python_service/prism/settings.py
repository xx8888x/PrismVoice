import os
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parents[2]
SHARED_DIR = Path(os.environ.get('PRISM_SHARED_PATH', SITE_ROOT / 'shared'))
ENV_FILE = Path(os.environ.get('PRISM_ENV_FILE', SITE_ROOT / 'backend' / '.env'))

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) PrismBot/1.0 (+local news perspective research)'
HTTP_TIMEOUT = 15
# Pause between article page requests so a single run never hammers one site.
REQUEST_DELAY_SECONDS = 1.0


def read_env_file(path=ENV_FILE):
    values = {}
    try:
        with open(path, encoding='utf-8') as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
                    value = value[1:-1]
                values[key.strip()] = value
    except FileNotFoundError:
        pass
    return values


def db_config():
    import pymysql
    env = read_env_file()
    get = lambda key, default: os.environ.get(key, env.get(key, default))
    return {
        'host': get('DB_HOST', '127.0.0.1'),
        'port': int(get('DB_PORT', 3307)),
        'user': get('DB_USERNAME', 'mediaweb'),
        'password': get('DB_PASSWORD', ''),
        'database': get('DB_DATABASE', 'mediaweb'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        'autocommit': False,
    }


def alert_webhook_url():
    # Off unless configured: alerts carry article titles to a third party.
    return os.environ.get('PRISM_ALERT_WEBHOOK_URL') or read_env_file().get('PRISM_ALERT_WEBHOOK_URL') or None
