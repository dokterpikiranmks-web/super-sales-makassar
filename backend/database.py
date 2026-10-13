import os
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_DIR = Path(__file__).resolve().parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_PATH = DB_DIR / "leads.db"
LEADS_JSON_PATH = DB_DIR / "leads.json"

def get_connection():
    conn = sqlite3.connect(str(SQLITE_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            product TEXT NOT NULL,
            product_key TEXT NOT NULL,
            name TEXT,
            wa TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Baru',
            location TEXT DEFAULT 'Makassar',
            ad_id TEXT,
            bant JSON,
            chat_history JSON,
            fu_history JSON,
            created_at TEXT,
            last_active TEXT
        )
    """)
    conn.commit()

    # Check if DB has rows; if empty, migrate from leads.json
    cursor.execute("SELECT COUNT(*) FROM leads")
    count = cursor.fetchone()[0]
    if count == 0:
        migrate_from_json(conn)
    conn.close()

def migrate_from_json(conn=None):
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    candidates = [
        LEADS_JSON_PATH,
        Path(__file__).resolve().parent.parent / "data" / "leads.json"
    ]
    json_file = next((f for f in candidates if f.exists()), None)
    
    if json_file:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                items = json.load(f)
            cursor = conn.cursor()
            for l in items:
                pk = l.get("product_key", "totok_saraf")
                p_name = "Totok Saraf Makassar" if pk == "totok_saraf" else ("Hipnoterapi Makassar" if pk == "hipnoterapi" else "Kopi Robusta Makassar")
                # Map status to Baru/Terlibat/Follow-Up/Closing
                raw_st = (l.get("status") or "follow_up").lower()
                status_map = {
                    "new": "Baru",
                    "engaged": "Terlibat",
                    "follow_up": "Follow-Up",
                    "closing": "Closing",
                    "closed": "Closing"
                }
                mapped_status = status_map.get(raw_st, "Follow-Up")

                cursor.execute("""
                    INSERT OR REPLACE INTO leads (
                        id, product, product_key, name, wa, status, location, ad_id, bant, chat_history, fu_history, created_at, last_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    l.get("id"),
                    p_name,
                    pk,
                    l.get("name") or f"Pasien {l.get('wa_id')}",
                    l.get("wa_id"),
                    mapped_status,
                    l.get("location") or "Makassar",
                    l.get("ad_id"),
                    json.dumps(l.get("bant", {})),
                    json.dumps(l.get("chat_history", [])),
                    json.dumps(l.get("fu_history", [])),
                    l.get("created_at"),
                    l.get("last_active")
                ))
            conn.commit()
            print(f"[DATABASE] Migrated {len(items)} leads from {json_file}")
        except Exception as e:
            print(f"[DATABASE ERROR] Failed migration: {e}")

    if should_close:
        conn.close()

def get_all_leads() -> List[Dict[str, Any]]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")
    rows = cursor.fetchall()
    leads = []
    for r in rows:
        d = dict(r)
        d["wa_id"] = d.get("wa")
        d["product_name"] = d.get("product")
        try:
            d["bant"] = json.loads(d.get("bant") or "{}")
        except:
            d["bant"] = {}
        try:
            d["chat_history"] = json.loads(d.get("chat_history") or "[]")
        except:
            d["chat_history"] = []
        try:
            d["fu_history"] = json.loads(d.get("fu_history") or "[]")
        except:
            d["fu_history"] = []
        leads.append(d)
    conn.close()
    return leads

def upsert_lead(lead_dict: Dict[str, Any]):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    pk = lead_dict.get("product_key", "totok_saraf")
    p_name = lead_dict.get("product") or lead_dict.get("product_name") or ("Totok Saraf Makassar" if pk == "totok_saraf" else "Hipnoterapi Makassar")
    wa = lead_dict.get("wa") or lead_dict.get("wa_id", "")
    st = lead_dict.get("status", "Follow-Up")
    
    cursor.execute("""
        INSERT OR REPLACE INTO leads (
            id, product, product_key, name, wa, status, location, ad_id, bant, chat_history, fu_history, created_at, last_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lead_dict.get("id"),
        p_name,
        pk,
        lead_dict.get("name") or f"Pasien {wa}",
        wa,
        st,
        lead_dict.get("location") or "Makassar",
        lead_dict.get("ad_id"),
        json.dumps(lead_dict.get("bant", {})),
        json.dumps(lead_dict.get("chat_history", [])),
        json.dumps(lead_dict.get("fu_history", [])),
        lead_dict.get("created_at"),
        lead_dict.get("last_active")
    ))
    conn.commit()
    conn.close()

    # Also sync to JSON file as secondary backup
    try:
        all_l = get_all_leads()
        with open(LEADS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(all_l, f, indent=2, ensure_ascii=False)
    except:
        pass
