# src/graph.py
from langgraph.graph import StateGraph, END
from src.state import EmailAgentState
from src.nodes import (
    parse_intent_node,
    find_contact_node,
    write_email_node,
    confirm_node,
    send_email_node,
    handle_error_node,
    finish_node
)
from src.conditions import (
    after_parse,
    after_find_contact,
    after_write_email,
    after_confirm,
    after_send_email
)

def create_email_agent():
    """
    Crée et compile le graphe LangGraph pour l'agent email.
    """
    # 1. Créer le graphe
    workflow = StateGraph(EmailAgentState)
    
    # 2. Ajouter les nœuds
    workflow.add_node("parse_intent", parse_intent_node)
    workflow.add_node("find_contact", find_contact_node)
    workflow.add_node("write_email", write_email_node)
    workflow.add_node("confirm", confirm_node)
    workflow.add_node("send_email", send_email_node)
    workflow.add_node("handle_error", handle_error_node)
    workflow.add_node("finish", finish_node)
    
    # 3. Point d'entrée
    workflow.set_entry_point("parse_intent")
    
    # 4. Arêtes conditionnelles
    workflow.add_conditional_edges(
        "parse_intent",
        after_parse,
        {
            "find_contact": "find_contact",
            "handle_error": "handle_error"
        }
    )
    
    workflow.add_conditional_edges(
        "find_contact",
        after_find_contact,
        {
            "write_email": "write_email",
            "ask_recipient": "parse_intent",
            "handle_error": "handle_error"
        }
    )
    
    workflow.add_conditional_edges(
        "write_email",
        after_write_email,
        {
            "confirm": "confirm",
            "handle_error": "handle_error"
        }
    )
    
    workflow.add_conditional_edges(
        "confirm",
        after_confirm,
        {
            "send_email": "send_email",
            "write_email": "write_email",
            "finish": "finish",
            "handle_error": "handle_error"
        }
    )
    
    workflow.add_conditional_edges(
        "send_email",
        after_send_email,
        {
            "finish": "finish",
            "handle_error": "handle_error"
        }
    )
    
    # 5. Arêtes statiques
    workflow.add_edge("handle_error", "finish")
    workflow.add_edge("finish", END)
    
    # 6. Compiler
    return workflow.compile()


def get_graph_visualization():
    """
    Retourne une représentation ASCII du graphe pour la documentation.
    """
    return """
┌──────────────────────────────────────────────────────────────────┐
│                    AGENT EMAIL - LANGGRAPH                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                               │
│  │ parse_intent │                                               │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐     ┌─────────────────┐                      │
│  │ find_contact │────▶│ ask_recipient   │ (si non trouvé)     │
│  └──────┬───────┘     └─────────────────┘                      │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │ write_email  │                                               │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │   confirm    │                                               │
│  └──────┬───────┘                                               │
│         │                                                       │
│    ┌────┴────┬──────────┐                                      │
│    ▼         ▼          ▼                                      │
│  send     write     finish                                     │
│  email     retry                                               │
│    │                                                           │
│    └───────────▶ finish                                        │
│                                                                  │
│  ┌──────────────┐                                               │
│  │ handle_error │──▶ finish                                    │
│  └──────────────┘                                               │
└──────────────────────────────────────────────────────────────────┘
"""