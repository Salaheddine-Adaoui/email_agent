# src/conditions.py
from typing import Literal
from src.state import EmailAgentState

def after_parse(state: EmailAgentState) -> Literal["find_contact", "handle_error"]:
    """
    Décide où aller après l'analyse de l'intention
    """
    if state.get("error"):
        return "handle_error"
    
    if state.get("intent") in ["send", "reply"]:
        return "find_contact"
    else:
        # Pour les autres intentions (read, search)
        return "find_contact"


def after_find_contact(state: EmailAgentState) -> Literal["write_email", "ask_recipient", "handle_error"]:
    """
    Décide après la recherche du contact
    """
    if state.get("error"):
        return "handle_error"
    
    if state.get("recipient_email"):
        return "write_email"
    else:
        return "ask_recipient"


def after_write_email(state: EmailAgentState) -> Literal["confirm", "handle_error"]:
    """
    Décide après la rédaction de l'email
    """
    if state.get("error"):
        return "handle_error"
    
    return "confirm"


def after_confirm(state: EmailAgentState) -> Literal["send_email", "write_email", "finish", "handle_error"]:
    """
    Décide après la confirmation
    """
    if state.get("error"):
        return "handle_error"
    
    confirmation = state.get("confirmation_response")
    
    if confirmation == "send":
        return "send_email"
    elif confirmation == "modify":
        if state.get("retry_count", 0) < state.get("max_retries", 3):
            return "write_email"
        else:
            return "handle_error"
    else:  # cancel
        return "finish"


def after_send_email(state: EmailAgentState) -> Literal["finish", "handle_error"]:
    """
    Décide après l'envoi de l'email
    """
    if state.get("error"):
        return "handle_error"
    
    return "finish"