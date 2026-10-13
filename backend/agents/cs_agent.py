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
    return {}

PRODUCT_CATALOG = {
    "totok_saraf": {
        "name": "Totok Saraf Makassar",
        "category": "jasa_komplementer_fisik",
        "location": "Makassar",
        "price_info": "Rp 150.000 / 60 menit (Konsultasi + Pemeriksaan + Sesi Terapi)",
        "ad_ids": [
            "120252401406790695",
            "120252346402370695",
            "120252346401370695",
            "120252346397950695"
        ],
        "campaign_ids": ["120252401399510695", "120252346394600695"],
        "keywords": ["totok", "saraf", "syaraf", "kejepit", "pegal", "leher kaku", "pinggang", "terapi fisik", "pijat", "nyeri"]
    },
    "hipnoterapi": {
        "name": "Hipnoterapi Klinis Dokter Pikiran Makassar",
        "category": "jasa_komplementer_mental",
        "location": "Makassar",
        "price_info": "1 Sesi Rp 600k / Paket Intensif 3 Sesi Rp 1.5jt",
        "ad_ids": [
            "120252401407350695",
            "120243464168120695",
            "120243238012320695"
        ],
        "campaign_ids": ["120252401406850695", "120242924074880695"],
        "keywords": ["hipno", "hipnoterapi", "insomnia", "susah tidur", "cemas", "anxiety", "trauma", "overthinking", "dokter pikiran", "mental", "stres", "psikologis"]
    },
    "kopi_robusta": {
        "name": "Kopi Robusta Makassar",
        "category": "produk_fisik",
        "location": "Makassar",
        "price_info": "Rp 50.000 / 250gr",
        "ad_ids": ["120252395432280695"],
        "campaign_ids": ["120252395285930695", "120252395284200695"],
        "keywords": ["kopi", "robusta", "ngopi", "bubuk", "biji"]
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

    score = 65
    if has_budget: score += 15
    if has_authority: score += 10
    if is_urgent: score += 10

    return {
        "budget": budget_status,
        "authority": authority_status,
        "need": need_status,
        "timeline": timeline_status,
        "score": min(score, 100)
    }

def generate_professional_reply(prod_key: str, message_body: str, chat_history: list = None) -> tuple:
    """
    SOP WAJIB KESEHATAN KOMPLEMENTER KLINIK DOKTER PIKIRAN:
    1. Sapa formal hangat: "Selamat siang Pak/Bu, terima kasih telah menghubungi [Nama Produk]"
    2. Tanya keluhan langsung tanpa tebak: "Maaf Pak/Bu, keluhannya apa?"
    3. Setelah leads cerita: Jawab CERDAS sesuai DNA, hubungkan keluhan dengan mekanisme terapi secara umum,
       tanpa mendiagnosa individu + cantumkan disclaimer komplementer.
    4. Baru tawarkan: "Jika berkenan, kami bisa bantu jadwalkan sesi terapi untuk pemeriksaan lebih lanjut. Bapak/Ibu berkenan hari apa?"
    5. Booking dengan 2 pilihan jam.
    """
    config = load_business_config()
    prod_conf = config.get("products", {}).get(prod_key, {})
    
    nama_produk = prod_conf.get("nama") or ("Totok Saraf Makassar" if prod_key == "totok_saraf" else "Hipnoterapi Klinis Dokter Pikiran Makassar")
    disclaimer = prod_conf.get("disclaimer") or "Kami tidak mendiagnosa dan tidak menggantikan pemeriksaan medis. Silakan tetap konsultasi dokter untuk kondisi medis Bapak/Ibu."
    
    body_low = (message_body or "").lower().strip()
    
    # Deteksi gender sapaan jika ada indikasi spesifik, default "Pak/Bu" atau "Bapak/Ibu"
    sapaan = "Pak" if any(w in body_low for w in ["bapak", "saya bapak", "pria", "ayah"]) else ("Bu" if any(w in body_low for w in ["ibu", "mama", "istri", "wanita"]) else "Bapak/Ibu")
    sapaan_singkat = "Pak/Bu" if sapaan == "Bapak/Ibu" else sapaan

    # Kata kunci indikasi keluhan spesifik
    has_keluhan_totok = any(w in body_low for w in ["saraf", "syaraf", "kejepit", "pinggang", "punggung", "leher", "kaku", "pegal", "nyeri", "otot", "kaki", "bahu", "tulang"])
    has_keluhan_hipno = any(w in body_low for w in ["insomnia", "tidur", "cemas", "anxiety", "trauma", "overthinking", "stres", "pikiran", "takut", "mental", "panik", "psikosomatis"])
    has_booking = any(w in body_low for w in ["booking", "jadwal", "slot", "hari ini", "besok", "jam", "daftar", "bisa kapan", "tarif", "harga", "biaya", "paket"])

    # STEP 5 / CLOSING: Leads sudah ingin atur jadwal
    if has_booking and (has_keluhan_totok or has_keluhan_hipno or len(chat_history or []) >= 2):
        if prod_key == "totok_saraf":
            reply = (
                f"Baik {sapaan_singkat}, terima kasih atas konfirmasinya. "
                f"Sesi terapi komplementer Totok Saraf Makassar berdurasi 60 menit (Rp 150.000) mencakup konsultasi, pemeriksaan titik saraf, dan penanganan terapi langsung. "
                f"Sebagai informasi, terapis kami pria profesional berseragam medis, menggunakan sarung tangan steril, dan {sapaan} tetap mengenakan pakaian lengkap di ruang terapi higienis. "
                f"{disclaimer}\n\n"
                f"Untuk jadwal pemeriksaan langsung, {sapaan} berkenan sesi hari ini jam 16.00 atau besok jam 10.00 WITA?"
            )
        elif prod_key == "hipnoterapi":
            reply = (
                f"Terima kasih informasinya {sapaan_singkat}. "
                f"Sesi hipnoterapi klinis dilakukan secara privat 1-on-1 (durasi 1-2 jam) bersama Terapis Pria C.Ht. bersertifikasi resmi untuk merilis akar masalah emosi secara saintifik.\n"
                f"Tersedia pilihan 1 sesi (Rp 600.000) atau Paket Intensif 3 sesi (Rp 1.500.000) yang disertai pendampingan 21 hari.\n"
                f"{disclaimer}\n\n"
                f"Untuk amankan jadwal konsultasi klinis, {sapaan} lebih nyaman mengambil jadwal hari ini jam 16.00 atau besok jam 10.00 WITA?"
            )
        else:
            reply = f"Baik {sapaan_singkat}, kami siap proses pesanan Kopi Robusta Makassar. Mohon info alamat tujuan dan metode pembayaran (COD/Transfer) ya Pak/Bu."
        return reply, "closing"

    # STEP 3: Leads sudah menceritakan keluhan -> Jawab CERDAS sesuai DNA + Disclaimer + Tawarkan Jadwal
    if (prod_key == "totok_saraf" and has_keluhan_totok) or (prod_key == "hipnoterapi" and has_keluhan_hipno):
        if prod_key == "totok_saraf":
            # Ekstrak area keluhan
            area = "punggung dan pinggang" if "pinggang" in body_low or "punggung" in body_low else ("leher dan pundak" if "leher" in body_low or "pundak" in body_low else "titik saraf dan otot")
            reply = (
                f"Terima kasih atas informasinya {sapaan_singkat}. "
                f"Untuk keluhan di area {area} seperti yang {sapaan} sampaikan, metode totok saraf pada umumnya bekerja dengan merangsang titik-titik saraf komplementer untuk membantu melancarkan sirkulasi peredaran darah, meredakan ketegangan otot dalam, dan mendukung fungsi saraf sebagai terapi pendamping pemulihan tubuh.\n\n"
                f"Ini adalah terapi komplementer akupresur ya {sapaan_singkat}, bukan pengganti pemeriksaan medis dokter. {disclaimer}\n\n"
                f"Untuk penanganan yang tepat sasaran, terapis pria profesional kami perlu melakukan pemeriksaan fisik langsung terlebih dahulu. "
                f"Jika berkenan, {sapaan} lebih leluasa mengambil jadwal sesi pemeriksaan hari ini jam 16.00 atau besok jam 10.00 WITA?"
            )
        else:
            keluhan_tipe = "insomnia dan kesulitan tidur" if "tidur" in body_low or "insomnia" in body_low else ("kecemasan berlebih dan overthinking" if "cemas" in body_low or "overthinking" in body_low else "beban psikologis dan trauma masa lalu")
            reply = (
                f"Terima kasih telah berbagi {sapaan_singkat}. "
                f"Untuk keluhan terkait {keluhan_tipe} yang {sapaan} rasakan, metode hipnoterapi klinis bekerja secara saintifik dengan membimbing gelombang otak ke kondisi relaksasi dalam (alfa-theta). Mekanisme ini membantu mengakses dan merestrukturisasi akar stres di alam bawah sadar serta menstabilkan respon sistem saraf tanpa ketergantungan obat.\n\n"
                f"Layanan ini murni terapi komplementer psikologis klinis terstandar ilmiah ya {sapaan_singkat}, tanpa unsur mistis atau gaib. {disclaimer}\n\n"
                f"Untuk langkah pemulihan terbaik, kami bisa jadwalkan sesi konsultasi dan terapi privat 1-on-1. {sapaan} berkenan jadwal sesi hari ini jam 16.00 atau besok pagi jam 10.00 WITA?"
            )
        return reply, "engaged"

    # STEP 1 & 2: First contact / Tanya langsung tanpa tebak
    if prod_key == "totok_saraf":
        reply = (
            f"Selamat siang {sapaan_singkat}, terima kasih telah menghubungi {nama_produk}. "
            f"Kami adalah layanan terapi komplementer akupresur untuk membantu mendukung pemulihan saraf dan fisik di Makassar.\n\n"
            f"Maaf {sapaan_singkat}, keluhan yang dirasakan saat ini apa?"
        )
    elif prod_key == "hipnoterapi":
        reply = (
            f"Selamat siang {sapaan_singkat}, terima kasih telah menghubungi {nama_produk}. "
            f"Kami membantu pemulihan insomnia, kecemasan, dan trauma melalui metode hipnoterapi klinis terstandar ilmiah.\n\n"
            f"Maaf {sapaan_singkat}, keluhan utama yang sedang dialami apa?"
        )
    else:
        reply = (
            f"Selamat siang {sapaan_singkat}, terima kasih telah menghubungi Kopi Robusta Makassar. "
            f"Ada yang bisa kami bantu informasikan terkait produk kopi robusta kami Pak/Bu?"
        )
    
    return reply, "engaged"

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

        now_iso = datetime.datetime.now().isoformat()
        leads = load_leads()
        lead = next((l for l in leads if l.get("wa_id") == wa_id and l.get("product_key") == prod_key), None)
        
        existing_history = lead.get("chat_history", []) if lead else []
        reply_text, stage = generate_professional_reply(prod_key, body, existing_history)

        if not lead:
            lead = {
                "id": f"lead_{len(leads) + 1}_{int(datetime.datetime.now().timestamp())}",
                "wa_id": wa_id,
                "wa": wa_id,
                "name": f"Pasien {wa_id}",
                "product_key": prod_key,
                "product": prod_info["name"],
                "product_name": prod_info["name"],
                "category": prod_info.get("category", "komplementer"),
                "location": "Makassar",
                "ad_id": ad_id,
                "created_at": now_iso,
                "last_active": now_iso,
                "status": "Closing" if stage == "closing" else "Terlibat",
                "bant": bant,
                "chat_history": []
            }
            leads.append(lead)
        else:
            lead["last_active"] = now_iso
            lead["bant"] = bant
            lead["location"] = "Makassar"
            if lead["status"] != "Closing":
                lead["status"] = "Closing" if stage == "closing" else "Terlibat"

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
        print(f"[CS AGENT to {wa_id} ({prod_info['name']})]:\n{reply_text}\n")

        return {
            "status": "replied",
            "product": prod_info["name"],
            "product_key": prod_key,
            "location": "Makassar",
            "ad_id": ad_id,
            "wa_id": wa_id,
            "bant": bant,
            "stage": stage,
            "reply": reply_text
        }

    except Exception as e:
        print(f"[CS AGENT ERROR]: {e}")
        return {"error": str(e)}
