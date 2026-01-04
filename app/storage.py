import sqlite3
import json
import os
from datetime import datetime

DB_NAME = "nutrition.db"

def get_db_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, DB_NAME)

def init_db():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            api_key TEXT,
            sugar_limit REAL DEFAULT 25.0,
            weekly_alert_enabled INTEGER DEFAULT 0,
            monthly_alert_enabled INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            meals_json TEXT, -- JSON string of meals input
            total_nutrition_json TEXT, -- JSON string of calculated totals
            risk_level TEXT,
            risk_reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('SELECT count(*) FROM user_settings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO user_settings (name, sugar_limit) VALUES (?, ?)', ("User", 25.0))

    conn.commit()
    conn.close()

def get_user_settings():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_settings LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

def update_user_settings(name, sugar_limit, weekly, monthly, api_key=None):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    if api_key is None:
        cursor.execute('''
            UPDATE user_settings 
            SET name = ?, sugar_limit = ?, weekly_alert_enabled = ?, monthly_alert_enabled = ?
            WHERE id = (SELECT id FROM user_settings LIMIT 1)
        ''', (name, sugar_limit, int(weekly), int(monthly)))
    else:
        cursor.execute('''
            UPDATE user_settings 
            SET name = ?, sugar_limit = ?, weekly_alert_enabled = ?, monthly_alert_enabled = ?, api_key = ?
            WHERE id = (SELECT id FROM user_settings LIMIT 1)
        ''', (name, sugar_limit, int(weekly), int(monthly), api_key))
        
    conn.commit()
    conn.close()

def log_daily_entry(date_str, meals, totals, risk_level, risk_reason):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM user_history WHERE date = ?', (date_str,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE user_history 
            SET meals_json = ?, total_nutrition_json = ?, risk_level = ?, risk_reason = ?, timestamp = CURRENT_TIMESTAMP
            WHERE date = ?
        ''', (json.dumps(meals), json.dumps(totals), risk_level, risk_reason, date_str))
    else:
        cursor.execute('''
            INSERT INTO user_history (date, meals_json, total_nutrition_json, risk_level, risk_reason)
            VALUES (?, ?, ?, ?, ?)
        ''', (date_str, json.dumps(meals), json.dumps(totals), risk_level, risk_reason))

    conn.commit()
    conn.close()

def get_history(limit=30):
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_history ORDER BY date DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
