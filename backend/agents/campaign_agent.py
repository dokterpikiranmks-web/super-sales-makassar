import os
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign

load_dotenv()

def run_campaign(product: dict, creatives: list = None):
    access_token = os.getenv("META_ACCESS_TOKEN")
    ad_account_id = os.getenv("META_AD_ACCOUNT_ID")
    
    FacebookAdsApi.init(app_id=None, app_secret=None, access_token=access_token)
    account = AdAccount(ad_account_id)
    
    # Meta Graph API v26 ODAX objective untuk pesan/CTWA adalah OUTCOME_ENGAGEMENT
    params = {
        "name": f"{product.get('name', 'Product')} - Auto CTWA",
        "objective": "OUTCOME_ENGAGEMENT",
        "status": Campaign.Status.paused,
        "special_ad_categories": [],
        "is_adset_budget_sharing_enabled": False,
    }
    
    campaign = account.create_campaign(params=params)
    meta_campaign_id = campaign.get_id()
    
    budget = product.get("budget_rp", 50000)
    return {
        "meta_campaign_id": meta_campaign_id,
        "name": params["name"],
        "status": "PAUSED",
        "budget_daily": budget,
        "advantage_state": "ADVANTAGE_PLUS_SALES",
        "next_action": "Approve di dashboard",
    }
