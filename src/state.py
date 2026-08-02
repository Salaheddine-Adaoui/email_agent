# src/state.py
from typing import List, Dict, Any, Optional, TypedDict
from langchain_core.messages import BaseMessage

class EmailAgentState(TypedDict):
    """État partagé entre tous les nœuds du graphe"""
    
    # Messages
    messages: List[BaseMessage]
    
    # Requête utilisateur
    user_query: str
    user_id: str
    
    # Intention
    intent: str  # "send", "read", "reply", "search"
    
    # Informations email
    recipient: Optional[str]      # Nom ou email brut
    recipient_email: Optional[str] # Email validé
    subject: Optional[str]
    body: Optional[str]
    
    # Confirmation
    confirmation_requested: bool
    confirmation_response: Optional[str]  # "send", "modify", "cancel"
    
    # Résultat
    email_sent: bool
    email_id: Optional[str]
    result_message: Optional[str]
    
    # Erreurs
    error: Optional[str]
    error_count: int
    
    # Statut
    status: str  # "pending", "processing", "confirming", "done", "error"
    retry_count: int
    max_retries: int