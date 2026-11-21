"""
Database layer for FindHome Ukraine
Supports MySQL (MariaDB) with SQLite graceful fallback.
"""
import os, json, uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_TYPE_ENV = os.getenv("DB_TYPE", "").strip().lower()
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "lookingforhome")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "LookingForHome2026!")
MYSQL_DB = os.getenv("MYSQL_DB", "findhome_ukraine")
SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "findhome.db")

SUBDIVISIONS = [["Київ (Печерськ, Поділ, Шевченківський)", "KYI"], ["Львівська область (Львів, Центр, Сихів)", "LVI"], ["Одеська область (Одеса, Приморський, Аркадія)", "ODE"], ["Дніпропетровська область (Дніпро)", "DNI"], ["Харківська область (Харків)", "KHR"], ["Івано-Франківська область (Івано-Франківськ)", "IFR"], ["Вінницька область (Вінниця)", "VIN"], ["Запорізька область (Запоріжжя)", "ZAP"]]
INITIAL_PROPERTIES = [{"title": "Простора 4-кімнатна квартира біля метро Золоті Ворота в Києві", "subdivision": "Київ (Печерськ, Поділ, Шевченківський)", "subdivision_code": "KYI", "city": "Київ", "address": "вул. Ярославів Вал, 14, Київ", "neighborhood": "Шевченківський район", "latitude": 50.4509, "longitude": 30.5126, "total_rent": 42000, "bedrooms": 4, "bathrooms": 2, "surface": 130, "portal": "DOM.RIA Україна", "url": "https://dom.ria.com/uk/orenda/kyiv-yaroslaviv-val-1", "desc": "Царський будинок з високими стелями. 4 світлі окремі спальні, автономне опалення, система фільтрації води, швидкісний оптоволоконний інтернет.", "contact_name": "Kyiv Urban Living", "contact_phone": "+34 603 331 391", "contact_agency": "Столична Нерухомість"}, {"title": "Австрійський люкс 3-кімнатний біля Оперного театру у Львові", "subdivision": "Львівська область (Львів, Центр, Сихів)", "subdivision_code": "LVI", "city": "Львів", "address": "просп. Свободи, 26, Львів", "neighborhood": "Галицький район", "latitude": 49.8419, "longitude": 24.0282, "total_rent": 34000, "bedrooms": 3, "bathrooms": 2, "surface": 110, "portal": "Flatfy Україна", "url": "https://flatfy.ua/orenda/lviv-svobody-2", "desc": "Історична кам'яниця. Збережена ліпнина, паркет з масиву, балкон на проспект, окрема зона для роботи та коворкінгу.", "contact_name": "Lviv Co-Housing", "contact_phone": "+34 603 331 391", "contact_agency": "Галицький Дім"}, {"title": "Сучасний 4-кімнатний пентхаус з терасою біля моря в Одесі", "subdivision": "Одеська область (Одеса, Приморський, Аркадія)", "subdivision_code": "ODE", "city": "Одеса", "address": "Французький бульвар, 60, Одеса", "neighborhood": "Приморський / Аркадія", "latitude": 46.4428, "longitude": 30.7615, "total_rent": 39000, "bedrooms": 4, "bathrooms": 2, "surface": 140, "portal": "OLX Нерухомість", "url": "https://www.olx.ua/d/uk/nedvizhimost/odesa-french-boulevard-3", "desc": "Вид на Чорне море. Закрита територія комплексу, підземний паркінг, генератор у будинку, кондиціонер у кожній кімнаті.", "contact_name": "Odessa Sea Living", "contact_phone": "+34 603 331 391", "contact_agency": "Чорноморська Рієлті"}]

_ACTIVE_ENGINE = None

def get_connection():
    global _ACTIVE_ENGINE
    if DB_TYPE_ENV != "sqlite":
        try:
            import pymysql
            conn = pymysql.connect(
                host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD,
                database=MYSQL_DB, charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor, autocommit=True, connect_timeout=3
            )
            _ACTIVE_ENGINE = "mysql"
            return "mysql", conn
        except Exception:
            pass

    import sqlite3
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    _ACTIVE_ENGINE = "sqlite"
    return "sqlite", conn

def init_db():
    engine, conn = get_connection()
    c = conn.cursor()
    if engine == "mysql":
        c.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id VARCHAR(64) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            city VARCHAR(100) NOT NULL,
            subdivision VARCHAR(100) NOT NULL,
            subdivision_code VARCHAR(20),
            address VARCHAR(255),
            neighborhood VARCHAR(100),
            latitude DOUBLE,
            longitude DOUBLE,
            total_rent DOUBLE NOT NULL,
            ideal_roommates INT DEFAULT 4,
            bedrooms INT NOT NULL,
            bathrooms INT NOT NULL,
            surface INT NOT NULL,
            has_elevator TINYINT(1) DEFAULT 1,
            is_exterior TINYINT(1) DEFAULT 1,
            is_furnished TINYINT(1) DEFAULT 1,
            has_terrace TINYINT(1) DEFAULT 0,
            has_air_con TINYINT(1) DEFAULT 0,
            source_portal VARCHAR(100),
            source_url VARCHAR(500),
            property_type VARCHAR(50) DEFAULT 'apartment',
            images TEXT,
            contact_name VARCHAR(120),
            contact_phone VARCHAR(50),
            contact_email VARCHAR(120),
            contact_agency VARCHAR(120),
            rent_per_person DOUBLE NOT NULL,
            status VARCHAR(30) DEFAULT 'available',
            created_at VARCHAR(100)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id VARCHAR(64) PRIMARY KEY,
            ip VARCHAR(64), country VARCHAR(100), country_code VARCHAR(10),
            region VARCHAR(100), city VARCHAR(100), latitude DOUBLE, longitude DOUBLE,
            path VARCHAR(255), method VARCHAR(10), status_code INT,
            user_agent VARCHAR(500), device_type VARCHAR(50), created_at VARCHAR(100)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS whatsapp_logs (
            id VARCHAR(64) PRIMARY KEY,
            sender_phone VARCHAR(50), sender_name VARCHAR(100),
            message_body TEXT, response_body TEXT, created_at VARCHAR(100)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
    else:
        c.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id TEXT PRIMARY KEY, title TEXT, description TEXT, city TEXT, subdivision TEXT, subdivision_code TEXT,
            address TEXT, neighborhood TEXT, latitude REAL, longitude REAL, total_rent REAL, ideal_roommates INTEGER,
            bedrooms INTEGER, bathrooms INTEGER, surface INTEGER, has_elevator INTEGER, is_exterior INTEGER,
            is_furnished INTEGER, has_terrace INTEGER, has_air_con INTEGER, source_portal TEXT, source_url TEXT,
            property_type TEXT, images TEXT, contact_name TEXT, contact_phone TEXT, contact_email TEXT,
            contact_agency TEXT, rent_per_person REAL, status TEXT, created_at TEXT
        );
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS access_logs (
            id TEXT PRIMARY KEY, ip TEXT, country TEXT, country_code TEXT, region TEXT, city TEXT,
            latitude REAL, longitude REAL, path TEXT, method TEXT, status_code INTEGER, user_agent TEXT,
            device_type TEXT, created_at TEXT
        );
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS whatsapp_logs (
            id TEXT PRIMARY KEY, sender_phone TEXT, sender_name TEXT, message_body TEXT, response_body TEXT, created_at TEXT
        );
        """)
        conn.commit()

    # Seed properties if empty
    c.execute("SELECT COUNT(*) FROM properties")
    row = c.fetchone()
    cnt = row["COUNT(*)"] if isinstance(row, dict) else row[0]
    if cnt == 0:
        for p in INITIAL_PROPERTIES:
            pid = f"prop-{uuid.uuid4().hex[:8]}"
            rpp = round(p["total_rent"] / max(1, p["bedrooms"]))
            now_iso = datetime.now().isoformat()
            imgs = json.dumps(["static/images/hero-home.png", "static/images/card-1.png", "static/images/card-2.png"])
            if engine == "mysql":
                c.execute("""
                INSERT INTO properties (
                    id, title, description, city, subdivision, subdivision_code, address, neighborhood,
                    latitude, longitude, total_rent, ideal_roommates, bedrooms, bathrooms, surface,
                    has_elevator, is_exterior, is_furnished, has_terrace, has_air_con, source_portal,
                    source_url, property_type, images, contact_name, contact_phone, contact_email,
                    contact_agency, rent_per_person, status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 1, 1, 0, 1, %s, %s, 'apartment', %s, %s, %s, 'support@lookingforhome.duckdns.org', %s, %s, 'available', %s)
                """, (
                    pid, p["title"], p["desc"], p["city"], p["subdivision"], p["subdivision_code"], p["address"], p["neighborhood"],
                    p["latitude"], p["longitude"], p["total_rent"], p["bedrooms"], p["bedrooms"], p["bathrooms"], p["surface"],
                    p["portal"], p["url"], imgs, p["contact_name"], p["contact_phone"], p["contact_agency"], rpp, now_iso
                ))
            else:
                c.execute("""
                INSERT INTO properties (
                    id, title, description, city, subdivision, subdivision_code, address, neighborhood,
                    latitude, longitude, total_rent, ideal_roommates, bedrooms, bathrooms, surface,
                    has_elevator, is_exterior, is_furnished, has_terrace, has_air_con, source_portal,
                    source_url, property_type, images, contact_name, contact_phone, contact_email,
                    contact_agency, rent_per_person, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 1, 0, 1, ?, ?, 'apartment', ?, ?, ?, 'support@lookingforhome.duckdns.org', ?, ?, 'available', ?)
                """, (
                    pid, p["title"], p["desc"], p["city"], p["subdivision"], p["subdivision_code"], p["address"], p["neighborhood"],
                    p["latitude"], p["longitude"], p["total_rent"], p["bedrooms"], p["bedrooms"], p["bathrooms"], p["surface"],
                    p["portal"], p["url"], imgs, p["contact_name"], p["contact_phone"], p["contact_agency"], rpp, now_iso
                ))
        if engine != "mysql":
            conn.commit()

    c.close()
    conn.close()

def get_properties(city=None, subdivision=None, portal=None, min_bedrooms=None, max_total_rent=None) -> List[Dict[str, Any]]:
    engine, conn = get_connection()
    c = conn.cursor()
    q = "SELECT * FROM properties WHERE 1=1"
    params = []
    if city:
        q += " AND LOWER(city) LIKE %s" if engine == "mysql" else " AND LOWER(city) LIKE ?"
        params.append(f"%{city.lower()}%")
    if subdivision:
        q += " AND subdivision_code = %s" if engine == "mysql" else " AND subdivision_code = ?"
        params.append(subdivision)
    if portal:
        q += " AND source_portal = %s" if engine == "mysql" else " AND source_portal = ?"
        params.append(portal)
    if min_bedrooms:
        q += " AND bedrooms >= %s" if engine == "mysql" else " AND bedrooms >= ?"
        params.append(min_bedrooms)
    if max_total_rent:
        q += " AND total_rent <= %s" if engine == "mysql" else " AND total_rent <= ?"
        params.append(max_total_rent)

    c.execute(q, tuple(params))
    rows = c.fetchall()
    res = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("images"), str):
            try:
                d["images"] = json.loads(d["images"])
            except Exception:
                d["images"] = []
        res.append(d)
    c.close()
    conn.close()
    return res

def get_property(property_id: str) -> Optional[Dict[str, Any]]:
    engine, conn = get_connection()
    c = conn.cursor()
    q = "SELECT * FROM properties WHERE id = %s" if engine == "mysql" else "SELECT * FROM properties WHERE id = ?"
    c.execute(q, (property_id,))
    row = c.fetchone()
    c.close()
    conn.close()
    if row:
        d = dict(row)
        if isinstance(d.get("images"), str):
            try:
                d["images"] = json.loads(d["images"])
            except Exception:
                d["images"] = []
        return d
    return None

def record_whatsapp_log(phone, name, msg, reply):
    try:
        engine, conn = get_connection()
        c = conn.cursor()
        lid = f"wsp-{uuid.uuid4().hex[:8]}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if engine == "mysql":
            c.execute("INSERT INTO whatsapp_logs (id, sender_phone, sender_name, message_body, response_body, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                      (lid, phone, name, msg, reply, now))
        else:
            c.execute("INSERT INTO whatsapp_logs (id, sender_phone, sender_name, message_body, response_body, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                      (lid, phone, name, msg, reply, now))
            conn.commit()
        c.close()
        conn.close()
    except Exception:
        pass

def get_whatsapp_logs(limit=50):
    try:
        engine, conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM whatsapp_logs ORDER BY created_at DESC LIMIT %s" if engine == "mysql" else f"SELECT * FROM whatsapp_logs ORDER BY created_at DESC LIMIT {limit}", ((limit,) if engine == "mysql" else ()))
        rows = c.fetchall()
        c.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

def record_access_log(ip, country, country_code, region, city, latitude, longitude, path, method, status_code, user_agent, device_type):
    try:
        engine, conn = get_connection()
        c = conn.cursor()
        lid = f"log-{uuid.uuid4().hex[:8]}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if engine == "mysql":
            c.execute("""
            INSERT INTO access_logs (id, ip, country, country_code, region, city, latitude, longitude, path, method, status_code, user_agent, device_type, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (lid, ip, country, country_code, region, city, latitude, longitude, path, method, status_code, user_agent, device_type, now))
        else:
            c.execute("""
            INSERT INTO access_logs (id, ip, country, country_code, region, city, latitude, longitude, path, method, status_code, user_agent, device_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (lid, ip, country, country_code, region, city, latitude, longitude, path, method, status_code, user_agent, device_type, now))
            conn.commit()
        c.close()
        conn.close()
    except Exception:
        pass

def get_access_logs(limit=100):
    try:
        engine, conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM access_logs ORDER BY created_at DESC LIMIT %s" if engine == "mysql" else f"SELECT * FROM access_logs ORDER BY created_at DESC LIMIT {limit}", ((limit,) if engine == "mysql" else ()))
        rows = c.fetchall()
        c.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []
