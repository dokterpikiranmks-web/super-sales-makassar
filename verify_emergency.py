import urllib.request
import json
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("META_ACCESS_TOKEN")
act = os.getenv("META_AD_ACCOUNT_ID")

print("=== 1. VERIFIKASI BUDGET AD SETS ===")
for as_id in ["120252401406550695", "120252401407000695"]:
    url = f"https://graph.facebook.com/v26.0/{as_id}?fields=id,name,daily_budget,status,targeting&access_token={token}"
    d = json.loads(urllib.request.urlopen(url).read().decode())
    budget = int(d["daily_budget"])
    print(f"- {d['name']}: Daily Budget = Rp {budget} | Status = {d['status']}")

print("\n=== 2. VERIFIKASI AD COPY & STATUS ===")
for ad_id in ["120252401406790695", "120252401407350695"]:
    url = f"https://graph.facebook.com/v26.0/{ad_id}?fields=id,name,status,creative{{id,name,object_story_spec}}&access_token={token}"
    d = json.loads(urllib.request.urlopen(url).read().decode())
    cr = d.get("creative", {})
    ld = cr.get("object_story_spec", {}).get("link_data", {})
    msg = ld.get("message", "")
    has_usp = "USP:" in msg
    print(f"Ad: {d['name']} | Status: {d['status']}")
    print(f"Title: {ld.get('name')}")
    print(f"Mengandung 'USP:': {has_usp}")
    print("Primary Text:")
    print(msg)
    print("---")

print("\n=== 3. VERIFIKASI IKLAN NON-ARCHIVED ===")
url_ads = f"https://graph.facebook.com/v26.0/{act}/ads?fields=id,name,status&limit=50&access_token={token}"
ads = json.loads(urllib.request.urlopen(url_ads).read().decode()).get("data", [])
active_or_paused = [a for a in ads if a["status"] != "ARCHIVED"]
print(f"Total Iklan Tersisa (Non-Archived): {len(active_or_paused)}")
for a in active_or_paused:
    print(f"- ID: {a['id']} | Nama: {a['name']} | Status: {a['status']}")
