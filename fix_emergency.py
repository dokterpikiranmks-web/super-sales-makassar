import urllib.request
import json
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("META_ACCESS_TOKEN")
act = os.getenv("META_AD_ACCOUNT_ID")

def post_meta(endpoint, payload):
    url = f"https://graph.facebook.com/v26.0/{endpoint}"
    payload["access_token"] = token
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())

# STEP 3: BUAT AD CREATIVE BARU TANPA KATA 'USP:'

# Creative Totok Saraf (Hijau)
totok_text = (
    "Pegal & Syaraf Kejepit Gak Hilang?\n"
    "Totok Saraf Makassar 60 Menit Rp 150rb (Konsultasi + Periksa + Terapi).\n"
    "Terapis Pria, Pakai Sarung Tangan Steril, Pasien Tetap Baju Lengkap.\n"
    "Ruang Spa Higienis, Badan Langsung Enteng.\n"
    "Chat WA cek slot hari ini."
)

cr_totok_clean = {
    "name": "Creative - Totok Saraf Makassar (Clean Copy No USP)",
    "object_story_spec": {
        "page_id": "900257366696347",
        "link_data": {
            "link": "https://wa.me/62811443327",
            "image_hash": "414bbf881e355a923fe20e87cbfbec5f",
            "message": totok_text,
            "name": "Booking Totok Saraf Makassar Hari Ini",
            "call_to_action": {
                "type": "WHATSAPP_MESSAGE",
                "value": {"app_destination": "WHATSAPP"}
            }
        }
    }
}
res_cr1 = post_meta(f"{act}/adcreatives", cr_totok_clean)
cr1_id = res_cr1["id"]
print("NEW CLEAN TOTOK CREATIVE ID:", cr1_id)

# Pasang ke Ad Totok Saraf & PAUSED
res_ad1 = post_meta("120252401406790695", {
    "name": "Ad - Totok Saraf Makassar (Pria Hijau)",
    "creative": {"creative_id": cr1_id},
    "status": "PAUSED"
})
print("AD TOTOK UPDATED TO CLEAN COPY:", res_ad1)

# Creative Hipnoterapi (Biru)
hipno_text = (
    "Insomnia & Cemas Berlebih?\n"
    "Klinik Hipnoterapi Dokter Pikiran Makassar, Terapi Privat 1-2 Jam oleh Terapis Pria.\n"
    "1 Sesi Rp 600rb | Paket 3 Sesi Rp 1,5jt (Hemat 300rb).\n"
    "Bonus E-book + Audio Rp 398rb + Pendampingan 21 Hari Rp 2jt (paket 3 sesi).\n"
    "Chat WA untuk tanya-jawab awal."
)

cr_hipno_clean = {
    "name": "Creative - Hipnoterapi Makassar (Clean Copy)",
    "object_story_spec": {
        "page_id": "900257366696347",
        "link_data": {
            "link": "https://wa.me/62811443327",
            "image_hash": "28481f8a531fc0ee607f5e26fe90c91c",
            "message": hipno_text,
            "name": "Atasi Insomnia & Cemas - Hipnoterapi Makassar",
            "call_to_action": {
                "type": "WHATSAPP_MESSAGE",
                "value": {"app_destination": "WHATSAPP"}
            }
        }
    }
}
res_cr2 = post_meta(f"{act}/adcreatives", cr_hipno_clean)
cr2_id = res_cr2["id"]
print("NEW CLEAN HIPNOTERAPI CREATIVE ID:", cr2_id)

# Pasang ke Ad Hipnoterapi & PAUSED
res_ad2 = post_meta("120252401407350695", {
    "name": "Ad - Hipnoterapi Makassar (Pria Biru)",
    "creative": {"creative_id": cr2_id},
    "status": "PAUSED"
})
print("AD HIPNOTERAPI UPDATED TO CLEAN COPY:", res_ad2)

# STEP 4: CLEANUP - ARSIPKAN IKLAN LAMA
print("STEP 4: Archiving old non-active ads...")
url_ads = f"https://graph.facebook.com/v26.0/{act}/ads?fields=id,name,status&limit=50&access_token={token}"
req_ads = urllib.request.urlopen(url_ads)
all_ads = json.loads(req_ads.read().decode()).get("data", [])
keep_ids = {"120252401406790695", "120252401407350695"}

for a in all_ads:
    if a["id"] not in keep_ids and a["status"] != "ARCHIVED":
        try:
            r_arch = post_meta(a["id"], {"status": "ARCHIVED"})
            print(f"Archived ad {a['id']} ({a['name']}):", r_arch)
        except Exception as e:
            print(f"Failed archiving {a['id']}:", e)
