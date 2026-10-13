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
            return "Selamat siang Pak/Bu, keluhan nyeri atau pegalnya sebaiknya tidak dibiarkan berlarut agar peredaran darah dan fungsi saraf segera terbantu pulih. Untuk pemeriksaan dan sesi terapi langsung oleh terapis profesional kami, besok pagi masih tersedia slot jam 10.00 WITA. Bapak/Ibu berkenan kami jadwalkan?"
        elif prod_key == "hipnoterapi":
            return "Selamat siang Pak/Bu, sebagian besar klien kami yang ingin pemulihan insomnia atau kecemasan secara tuntas memilih Paket 3 Sesi Klinis (Rp 1.500.000, hemat Rp 300rb) dengan pendampingan komprehensif 21 hari senilai Rp 2jt agar hasilnya lebih permanen di alam bawah sadar. Apakah Bapak/Ibu berkenan kami siapkan jadwalnya?"
        elif prod_key == "kopi_robusta":
            return "Selamat siang Pak/Bu, sekadar menginfokan promo gratis ongkir area Makassar berlaku hingga hari ini. Bapak/Ibu berkenan memesan?"
        else:
            return "Selamat siang Pak/Bu, apakah ada informasi tambahan yang dapat kami bantu terkait jadwal terapi Bapak/Ibu?"
    elif elapsed_hours >= 3:
        # Template Follow-up 3 Jam
        if prod_key == "totok_saraf":
            return "Selamat siang Pak/Bu, untuk terapi Totok Saraf Makassar, slot hari ini jam 16.00 WITA atau besok jam 10.00 WITA masih tersedia. Sesi 60 menit Rp 150.000 sudah termasuk konsultasi, pemeriksaan titik saraf, dan terapi dengan sarung tangan medis. Bapak/Ibu berkenan jam berapa?"
        elif prod_key == "hipnoterapi":
            return "Selamat siang Pak/Bu, untuk penanganan keluhan insomnia atau kecemasan, sesi hipnoterapi klinis 1-2 jam (Rp 600.000) sudah mencakup bonus audio relaksasi & e-book senilai Rp 398.000. Bapak/Ibu berkenan kami jadwalkan hari ini jam 16.00 atau besok jam 10.00 WITA?"
        elif prod_key == "kopi_robusta":
            return "Selamat siang Pak/Bu, apakah ada yang bisa kami bantu untuk pemesanan Kopi Robusta Makassar?"
        else:
            return "Selamat siang Pak/Bu, ada yang bisa kami bantu lagi mengenai jadwal konsultasi?"
            
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
