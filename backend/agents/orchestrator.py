
from langgraph.graph import StateGraph, END
from typing import TypedDict
class AgentState(TypedDict):
    product: dict
    research: dict
    creatives: list
    campaign: dict
    leads: list
def research_node(state: AgentState):
    from .research_agent import run_research
    state["research"] = run_research(state["product"])
    return state
def creative_node(state: AgentState):
    from .creative_agent import run_creative
    state["creatives"] = run_creative(state["product"], state["research"])
    return state
def campaign_node(state: AgentState):
    from .campaign_agent import run_campaign
    state["campaign"] = run_campaign(state["product"], state["creatives"])
    return state
def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("research", research_node)
    graph.add_node("creative", creative_node)
    graph.add_node("campaign", campaign_node)
    graph.set_entry_point("research")
    graph.add_edge("research", "creative")
    graph.add_edge("creative", "campaign")
    graph.add_edge("campaign", END)
    return graph.compile()
def run_full_flow(product: dict):
    app = build_graph()
    result = app.invoke({"product": product})
    return {"message": "Flow selesai, campaign PAUSED nunggu approval kamu", "result": result}
