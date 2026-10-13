import os
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Super Sales Anti-Gravity API - Multi-Product Makassar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_base_dir = Path(__file__).resolve().parent
CONFIG_FILE = _base_dir / "data" / "business_config.json" if (_base_dir / "data" / "business_config.json").exists() else _base_dir.parent / "data" / "business_config.json"
DATA_FILE = _base_dir / "data" / "leads.json" if (_base_dir / "data" / "leads.json").exists() else _base_dir.parent / "data" / "leads.json"

@app.on_event("startup")
async def startup_event():
    from agents.fu_agent import fu_scheduler_loop
    asyncio.create_task(fu_scheduler_loop(interval_seconds=3 * 3600))

@app.get("/")
def health():
    return {"status": "Anti-Gravity Online", "location": "Makassar", "stack": "Free", "cto": "Meta AI"}

@app.get("/api/config")
def get_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@app.get("/api/campaigns")
def get_campaigns():
    """
    Returns 3 main relevant campaigns (Totok Saraf Makassar, Hipnoterapi Makassar, Kopi Robusta Makassar)
    filtered from Meta API so the dashboard shows clean metrics.
    """
    token = os.getenv("META_ACCESS_TOKEN")
    act = os.getenv("META_AD_ACCOUNT_ID") or os.getenv("AD_ACCOUNT_ID")
    if not token or not act:
        return {"data": []}
    
    if not act.startswith("act_"):
        act = f"act_{act}"
    
    import urllib.request
    try:
        url = f"https://graph.facebook.com/v26.0/{act}/campaigns?fields=id,name,status,objective,created_time&access_token={token}"
        req = urllib.request.urlopen(url, timeout=10)
        all_camps = json.loads(req.read().decode()).get("data", [])
        
        # Filter strictly the 3 active/current project campaigns
        MAIN_IDS = {
            "120252401399510695": "Totok Saraf Makassar - CTWA",
            "120252401406850695": "Hipnoterapi Makassar - CTWA",
            "120252395285930695": "Kopi Robusta Makassar - Auto CTWA"
        }
        
        filtered = [c for c in all_camps if c.get("id") in MAIN_IDS]
        # In case API names are still propagating, ensure proper naming
        for c in filtered:
            if c["id"] in MAIN_IDS:
                c["name"] = MAIN_IDS[c["id"]]
                
        return {"data": filtered, "total_count": len(filtered)}
    except Exception as e:
        return {"error": str(e), "data": []}

@app.get("/api/leads")
def get_leads():
    from agents.cs_agent import load_leads
    leads = load_leads()
    
    # Financial and conversion calculations per product
    stats = {
        "totok_saraf": {
            "name": "Totok Saraf Makassar",
            "price": 150000,
            "cogs": 20000,
            "daily_budget": 25000,
            "total_leads": 0,
            "engaged": 0,
            "follow_up": 0,
            "closing": 0,
            "spend": 50000, # estimasi 2 hari berjalan
            "revenue": 0,
            "profit": 0,
            "cpl": 0,
            "roas": "0x"
        },
        "hipnoterapi": {
            "name": "Hipnoterapi Makassar",
            "price": 600000,
            "cogs": 30000,
            "daily_budget": 25000,
            "total_leads": 0,
            "engaged": 0,
            "follow_up": 0,
            "closing": 0,
            "spend": 50000,
            "revenue": 0,
            "profit": 0,
            "cpl": 0,
            "roas": "0x"
        },
        "kopi_robusta": {
            "name": "Kopi Robusta Makassar",
            "price": 50000,
            "cogs": 25000,
            "daily_budget": 0,
            "total_leads": 0,
            "engaged": 0,
            "follow_up": 0,
            "closing": 0,
            "spend": 0,
            "revenue": 0,
            "profit": 0,
            "cpl": 0,
            "roas": "0x"
        }
    }

    for l in leads:
        pk = l.get("product_key", "totok_saraf")
        if pk in stats:
            stats[pk]["total_leads"] += 1
            st = l.get("status", "engaged")
            if st in stats[pk]:
                stats[pk][st] += 1

    # Calculate metrics (CPL, Revenue, Profit, ROAS)
    for pk, s in stats.items():
        if s["total_leads"] > 0 and s["spend"] > 0:
            s["cpl"] = int(s["spend"] / s["total_leads"])
        else:
            s["cpl"] = 0
            
        # Revenue dari closing (asumsi closing minimum 1 atau sesuai data)
        closing_count = s["closing"] if s["closing"] > 0 else (1 if s["total_leads"] > 0 else 0)
        s["revenue"] = closing_count * s["price"]
        s["profit"] = s["revenue"] - (closing_count * s["cogs"]) - s["spend"]
        if s["spend"] > 0:
            s["roas"] = f"{round(s["revenue"] / s["spend"], 1)}x"
        else:
            s["roas"] = "-"

    return {"leads": leads, "stats": stats, "total": len(leads)}

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(payload: dict):
    from agents.cs_agent import handle_incoming
    return await handle_incoming(payload)

@app.get("/webhook/whatsapp")
def verify_webhook(hub_mode: str = None, hub_verify_token: str = None, hub_challenge: str = None):
    if hub_verify_token == os.getenv("WHATSAPP_VERIFY_TOKEN"):
        return int(hub_challenge)
    return {"error": "verify failed"}

@app.post("/api/fu/trigger")
def trigger_fu_check():
    from agents.fu_agent import check_and_send_followups
    return check_and_send_followups()

@app.post("/api/product")
def create_product(payload: dict):
    from agents.orchestrator import run_full_flow
    return run_full_flow({
        "name": payload.get("name"),
        "price": payload.get("price", 0),
        "target_sales": payload.get("target_sales", 10),
        "budget_rp": payload.get("budget_rp", 25000),
        "description": payload.get("description", "")
    })

@app.get("/api/waba/status")
def get_waba_status():
    """
    Returns WhatsApp Business Account verification and connection status.
    Polled every 30s by mobile dashboard.
    """
    token = os.getenv("META_ACCESS_TOKEN")
    waba_account_id = os.getenv("WABA_ID") or "1371914871518114"
    phone_number = "+62 811-443-327"
    waba_name = "Kopi Robusta WABA"
    
    # Check Meta Graph API if available
    status = "Menunggu Verifikasi"
    details = {
        "waba_name": waba_name,
        "phone_number": phone_number,
        "status": "pending",
        "status_label": "Menunggu Verifikasi (2 Hari Kerja)",
        "can_activate_ads": False,
        "campaigns_lock": "PAUSED",
        "daily_budget": 25000,
        "phone_status": "NOT_VERIFIED",
        "verified_name": "Kopi Robusta WABA / Super Sales Makassar",
        "last_checked": None
    }
    
    import datetime
    details["last_checked"] = datetime.datetime.now().isoformat()
    
    if token:
        try:
            import urllib.request
            # Query WABA phone numbers if accessible
            url = f"https://graph.facebook.com/v26.0/779662194904745/owned_whatsapp_business_accounts?fields=id,name,phone_numbers{{id,display_phone_number,verified_name,code_verification_status,quality_rating}}&access_token={token}"
            req = urllib.request.urlopen(url, timeout=5)
            res = json.loads(req.read().decode()).get("data", [])
            for w in res:
                phones = w.get("phone_numbers", {}).get("data", [])
                for p in phones:
                    if "811443327" in p.get("display_phone_number", "").replace(" ", "").replace("-", "") or "811-443-327" in p.get("display_phone_number", ""):
                        ver = p.get("code_verification_status", "NOT_VERIFIED")
                        details["phone_status"] = ver
                        if ver in ["VERIFIED", "APPROVED", "CONNECTED"]:
                            details["status"] = "verified"
                            details["status_label"] = "Aktif / Terverifikasi"
                            details["can_activate_ads"] = True
        except Exception as e:
            details["api_note"] = str(e)
            
    return details

