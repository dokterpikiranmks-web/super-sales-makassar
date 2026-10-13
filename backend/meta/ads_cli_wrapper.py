
def get_insights(campaign_id: str):
    return {"spend":50000,"leads":8,"cpa":6250,"roas":2.8}
def trigger_capi_event(event_name: str, wa_id: str, value: int = 0):
    print(f"[MOCK CAPI] {event_name} for {wa_id} value {value}")
    return True
