import os
import json
import datetime
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent.parent
DATA_FILE = _backend_dir / "data" / "leads.json" if (_backend_dir / "data" / "leads.json").exists() else _backend_dir.parent / "data" / "leads.json"
CONFIG_FILE = _backend_dir / "data" / "business_config.json" if (_backend_dir / "data" / "business_config.json").exists() else _backend_dir.parent / "data" / "business_config.json"

def load_business_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "location": "Makassar",
        "waba": "Kopi Robusta WABA - +62 811-443-327",
        "products": {
            "totok_saraf": {"price": 150000, "duration": "60 menit", "cogs": 20000, "target_closing": 30},
            "hipnoterapi_1sesi": {"price": 600000, "duration": "1-2 jam", "cogs": 30000, "target_closing": 20},
            "hipnoterapi_3sesi": {"price": 1500000, "duration": "3x 1-2 jam", "hemat": 300000, "cogs": 90000}
        },
        "daily_budget_per_campaign": 25000
    }

PRODUCT_CATALOG = {
    "totok_saraf": {
        "name": "Totok Saraf Makassar",
        "category": "jasa_fisik",
        "location": "Makassar",
        "price_info": "Rp 150.000 / sesi 60 menit",
        "ad_ids": [
            "120252401406790695",
            "120252346402370695",
            "120252346401370695",
            "120252346397950695"
        ],
        "campaign_ids": ["120252401399510695", "120252346394600695"],
        "keywords": ["totok", "saraf", "syaraf", "kejepit", "pegal", "leher kaku", "pinggang", "terapi fisik", "pijat"],
        "default_reply": (
            "Halo kak! Layanan Totok Saraf Makassar kami siap bantu. "
            "Sesi 60 menit Rp 150.000 sudah termasuk konsultasi + pemeriksaan saraf + terapi totok langsung. "
            "Enak badan langsung enteng kak. Keluhan di bagian mana kak? Leher/pundak/pinggang?"
        ),
        "closing_reply": (
            "Baik kak, kami siapkan jadwal sesi pemeriksaan & terapi Totok Saraf ya. "
            "Untuk hari ini atau besok, lebih nyaman ambil sesi sore (16:00) atau malam (19:00) WITA kak?"
        )
    },
    "hipnoterapi": {
        "name": "Hipnoterapi Makassar",
        "category": "jasa_mental",
        "location": "Makassar",
        "price_info": "1 Sesi Rp 600k / Paket 3 Sesi Rp 1.5jt",
        "ad_ids": [
            "120252401407350695",
            "120243464168120695",
            "120243238012320695"
        ],
        "campaign_ids": ["120252401406850695", "120242924074880695"],
        "keywords": ["hipno", "hipnoterapi", "insomnia", "susah tidur", "cemas", "anxiety", "trauma", "overthinking", "dokter pikiran", "mental"],
        "default_reply": (
            "Halo kak! Selamat datang di Klinik Hipnoterapi Dokter Pikiran Makassar.\n"
            "Kami bantu atasi insomnia, cemas, trauma dengan hipnoterapi 1-2 jam.\n"
            "Biaya 1 sesi Rp 600.000, ada bonus E-book Emotional Detox (199k) + Audio Ketenangan Jiwa (199k).\n"
            "Paling hemat Paket 3 sesi Rp 1.500.000 (hemat 300rb) + bonus pendampingan 21 hari senilai Rp 2jt untuk hasil maksimal.\n"
            "Keluhan utama kakak apa? Insomnia/cemas/trauma? Mau ambil 1 sesi dulu atau paket 3 sesi sekalian kak?"
        ),
        "closing_reply": (
            "Terima kasih sudah berbagi kak. Sesi hipnoterapi dilakukan 1-on-1 dengan privasi terjaga penuh. "
            "Untuk amankan jadwal konsultasi, mau ambil 1 sesi dulu atau langsung paket hemat 3 sesi kak?"
        )
    },
    "kopi_robusta": {
        "name": "Kopi Robusta Makassar",
        "category": "produk_fisik",
        "location": "Makassar",
        "price_info": "Rp 50.000 / 250gr",
        "ad_ids": ["120252395432280695"],
        "campaign_ids": ["120252395285930695", "120252395284200695"],
        "keywords": ["kopi", "robusta", "ngopi", "bubuk", "biji"],
        "default_reply": (
            "Halo kak! Terima kasih sudah menghubungi Kopi Robusta Makassar. "
            "Kopi Robusta (250gr) ready stock cuma Rp 50.000.\n"
            "Promo hari ini ada Gratis Ongkir se-Kota Makassar & bisa COD. "
            "Rencananya mau pesan berapa bungkus kak dan dikirim ke area mana?"
        ),
        "closing_reply": "Siap kak, pesanan Kopi Robusta dicatat ya. Mau COD atau transfer bank?"
    }
}

def load_leads() -> list:
    try:
        import database
        db_leads = database.get_all_leads()
        if db_leads:
            return db_leads
    except Exception as e:
        print(f"[CS AGENT DB ERROR]: {e}")

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
        print(f"[CS AGENT DB SAVE ERROR]: {e}")

    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)
    except:
        pass

def detect_product(ad_id: str = None, campaign_id: str = None, message_body: str = "") -> tuple:
    if ad_id:
        for p_id, p_info in PRODUCT_CATALOG.items():
            if ad_id in p_info["ad_ids"]:
                return p_id, p_info

    if campaign_id:
        for p_id, p_info in PRODUCT_CATALOG.items():
            if campaign_id in p_info["campaign_ids"]:
                return p_id, p_info

    text_lower = (message_body or "").lower()
    for p_id, p_info in PRODUCT_CATALOG.items():
        if any(kw in text_lower for kw in p_info["keywords"]):
            return p_id, p_info

    return "totok_saraf", PRODUCT_CATALOG["totok_saraf"]

def analyze_bant(message: str, product_info: dict) -> dict:
    msg_low = message.lower()
    
    has_budget = any(w in msg_low for w in ["biaya", "tarif", "harga", "berapa", "ongkir", "bayar", "transfer", "cod", "gratis", "600", "150", "paket"])
    budget_status = "qualified" if has_budget else "inquired"

    has_authority = not any(w in msg_low for w in ["tanya suami", "tanya istri", "izin orang tua"])
    authority_status = "decision_maker" if has_authority else "needs_approval"

    need_status = product_info["name"]

    is_urgent = any(w in msg_low for w in ["sekarang", "hari ini", "besok", "langsung", "cepat", "jadwal", "booking", "slot"])
    timeline_status = "immediate" if is_urgent else "flexible"

    score = 60
    if has_budget: score += 15
    if has_authority: score += 15
    if is_urgent: score += 10

    return {
        "budget": budget_status,
        "authority": authority_status,
        "need": need_status,
        "timeline": timeline_status,
        "score": min(score, 100)
    }

async def handle_incoming(payload: dict):
    try:
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        val = changes.get("value", {})
        messages = val.get("messages", [])
        
        if not messages:
            messages = [payload] if "text" in payload or "body" in payload else []

        if not messages:
            return {"status": "ignored", "reason": "No messages in payload"}

        msg_obj = messages[0]
        wa_id = msg_obj.get("from") or payload.get("wa_id", "unknown_user")
        
        if "text" in msg_obj and isinstance(msg_obj["text"], dict):
            body = msg_obj["text"].get("body", "")
        elif "body" in msg_obj:
            body = msg_obj["body"]
        else:
            body = str(msg_obj)

        referral = msg_obj.get("referral", {})
        ad_id = referral.get("source_id") or payload.get("ad_id")
        campaign_id = payload.get("campaign_id")

        prod_key, prod_info = detect_product(ad_id, campaign_id, body)
        bant = analyze_bant(body, prod_info)

        if any(w in body.lower() for w in ["booking", "jadwal", "pesan", "daftar", "deal", "transfer", "cod", "jadi", "paket"]):
            reply_text = prod_info["closing_reply"]
            stage = "closing"
        else:
            reply_text = prod_info["default_reply"]
            stage = "engaged"

        now_iso = datetime.datetime.now().isoformat()
        
        leads = load_leads()
        lead = next((l for l in leads if l.get("wa_id") == wa_id and l.get("product_key") == prod_key), None)
        
        if not lead:
            lead = {
                "id": f"lead_{len(leads) + 1}_{int(datetime.datetime.now().timestamp())}",
                "wa_id": wa_id,
                "product_key": prod_key,
                "product_name": prod_info["name"],
                "category": prod_info.get("category", "umum"),
                "location": "Makassar",
                "ad_id": ad_id,
                "created_at": now_iso,
                "last_active": now_iso,
                "status": stage,
                "bant": bant,
                "chat_history": []
            }
            leads.append(lead)
        else:
            lead["last_active"] = now_iso
            lead["bant"] = bant
            lead["location"] = "Makassar"
            if lead["status"] != "closed":
                lead["status"] = stage

        lead["chat_history"].append({
            "sender": "user",
            "message": body,
            "timestamp": now_iso,
            "ad_id": ad_id
        })
        lead["chat_history"].append({
            "sender": "cs_agent",
            "message": reply_text,
            "timestamp": now_iso
        })

        save_leads(leads)
        print(f"[CS AGENT to {wa_id} ({prod_info['name']})]: {reply_text}")

        return {
            "status": "replied",
            "product": prod_info["name"],
            "product_key": prod_key,
            "location": "Makassar",
            "ad_id": ad_id,
            "wa_id": wa_id,
            "bant": bant,
            "reply": reply_text
        }

    except Exception as e:
        print(f"[CS AGENT ERROR]: {e}")
        return {"error": str(e)}
