import os
import json
import asyncio
import datetime
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent.parent
DATA_FILE = _backend_dir / "data" / "leads.json" if (_backend_dir / "data" / "leads.json").exists() else _backend_dir.parent / "data" / "leads.json"

def load_leads() -> list:
    try:
        import database
        db_leads = database.get_all_leads()
        if db_leads:
            return db_leads
    except Exception as e:
        print(f"[FU AGENT DB ERROR]: {e}")

    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_leads(leads: list):
    try:
        import database
        for l in leads:
            database.upsert_lead(l)
    except Exception as e:
        print(f"[FU AGENT DB SAVE ERROR]: {e}")

    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)
    except:
        pass

def get_followup_message(lead: dict, elapsed_hours: float) -> str:
    prod_key = lead.get("product_key", "totok_saraf")
    
    if elapsed_hours >= 24:
        # Template Follow-up 24 Jam
        if prod_key == "totok_saraf":
            return "Kak, pegalnya jangan ditahan kelamaan, nanti jadi saraf kejepit. Slot besok pagi masih ada."
        elif prod_key == "hipnoterapi":
            return "Kak, kebanyakan klien yang sembuh total ambil Paket 3 sesi Rp 1,5jt (hemat 300rb) karena ada pendampingan 21 hari Rp 2jt. Hasilnya lebih permanen. Mau saya keep slot untuk Paket 3 sesi kak?"
        elif prod_key == "kopi_robusta":
            return "Promo gratis ongkir Makassar hari terakhir kak"
        else:
            return "Halo kak, penawaran promo kami di Makassar masih tersedia hari ini ya kak."
    elif elapsed_hours >= 3:
        # Template Follow-up 3 Jam
        if prod_key == "totok_saraf":
            return "Halo kak, slot Totok Saraf Makassar sore ini jam 4 & 7 masih ada kak. Mau booking jam berapa? Sesi 60 menit Rp 150rb sudah termasuk pemeriksaan."
        elif prod_key == "hipnoterapi":
            return "Kak, untuk insomnia & cemasnya, sesi 1-2 jam Rp 600rb sudah termasuk bonus E-book + Audio senilai 398rb. Mau coba 1 sesi dulu kak?"
        elif prod_key == "kopi_robusta":
            return "Halo kak, jadi pesan Kopi nya berapa?"
        else:
            return "Halo kak, ada yang bisa kami bantu lagi mengenai layanannya?"
            
    return None

def check_and_send_followups():
    leads = load_leads()
    now = datetime.datetime.now()
    updated = False
    processed_count = 0

    for lead in leads:
        if lead.get("status") in ["closed", "lost"]:
            continue

        last_active_str = lead.get("last_active") or lead.get("created_at")
        try:
            last_active = datetime.datetime.fromisoformat(last_active_str)
        except Exception:
            continue

        elapsed = (now - last_active).total_seconds() / 3600.0
        fu_history = lead.get("fu_history", [])
        
        sent_24h = any(item.get("stage") == "24h" for item in fu_history)
        sent_3h = any(item.get("stage") == "3h" for item in fu_history)

        stage_to_send = None
        if elapsed >= 24 and not sent_24h:
            stage_to_send = "24h"
        elif elapsed >= 3 and not sent_3h:
            stage_to_send = "3h"

        if stage_to_send:
            msg = get_followup_message(lead, elapsed)
            if msg:
                now_iso = now.isoformat()
                print(f"[FU AGENT -> {lead.get('wa_id')} ({lead.get('product_name')}) ({stage_to_send})]: {msg}")
                
                lead.setdefault("chat_history", []).append({
                    "sender": "fu_agent",
                    "message": msg,
                    "timestamp": now_iso,
                    "stage": stage_to_send
                })

                lead.setdefault("fu_history", []).append({
                    "stage": stage_to_send,
                    "sent_at": now_iso,
                    "message": msg
                })

                lead["status"] = "follow_up"
                updated = True
                processed_count += 1

    if updated:
        save_leads(leads)

    return {"processed": processed_count, "checked_at": now.isoformat()}

async def fu_scheduler_loop(interval_seconds: int = 3 * 3600):
    print(f"[FU AGENT] Scheduler started. Checking every {interval_seconds} seconds.")
    while True:
        try:
            check_and_send_followups()
        except Exception as e:
            print(f"[FU AGENT ERROR]: {e}")
        await asyncio.sleep(interval_seconds)
