# src/nodes.py
import json
from typing import Dict, Any
from src.state import EmailAgentState
from src.llm_service import LLMService
from src.email_service import EmailService
from src.contacts_service import ContactsService

# Initialisation des services
llm_service = LLMService()
email_service = EmailService()
contacts_service = ContactsService()

def parse_intent_node(state: EmailAgentState) -> Dict[str, Any]:
    """
    Nœud 1: Analyse la requête utilisateur
    """
    print("🔍 Analyse de la requête...")
    
    query = state["user_query"]
    
    # Analyser avec le LLM
    parsed = llm_service.parse_intent(query)
    
    return {
        **state,
        "intent": parsed.get("intent", "send"),
        "recipient": parsed.get("recipient"),
        "subject": parsed.get("subject"),
        "body": parsed.get("body"),
        "status": "processing"
    }


def find_contact_node(state: EmailAgentState) -> Dict[str, Any]:
    """
    Nœud 2: Recherche le contact
    """
    print("🔎 Recherche du contact...")
    
    recipient = state.get("recipient")
    if not recipient:
        return {
            **state,
            "error": "Destinataire non spécifié",
            "status": "error"
        }
    
    # Vérifier si c'est déjà un email
    if "@" in recipient and "." in recipient:
        return {
            **state,
            "recipient_email": recipient,
            "status": "processing"
        }
    
    # Rechercher dans les contacts
    contact = contacts_service.find_contact(recipient)
    
    if contact:
        return {
            **state,
            "recipient_email": contact["email"],
            "recipient_name": contact["name"],
            "status": "processing"
        }
    else:
        # Chercher des contacts similaires
        similar = contacts_service.search_contacts(recipient)
        if similar:
            return {
                **state,
                "error": f"Contact '{recipient}' non trouvé. Suggestions: {', '.join([c['name'] for c in similar])}",
                "status": "error",
                "similar_contacts": similar
            }
        
        return {
            **state,
            "error": f"Contact '{recipient}' non trouvé dans la base",
            "status": "error"
        }


def write_email_node(state: EmailAgentState) -> Dict[str, Any]:
    """
    Nœud 3: Rédige l'email si nécessaire
    """
    print("✍️ Rédaction de l'email...")
    
    # Si déjà complet, passer
    if state.get("body") and state.get("subject"):
        return {
            **state,
            "status": "confirming"
        }
    
    # Rédiger avec le LLM
    recipient = state.get("recipient_name") or state.get("recipient_email")
    context = state.get("user_query")
    
    email = llm_service.write_email(
        recipient=recipient,
        subject=state.get("subject"),
        body=state.get("body"),
        context=context
    )
    
    return {
        **state,
        "subject": email.get("subject"),
        "body": email.get("body"),
        "status": "confirming",
        "confirmation_requested": True
    }


def confirm_node(state: EmailAgentState) -> Dict[str, Any]:
    """
    Nœud 4: Demande confirmation
    """
    print("📝 En attente de confirmation...")
    
    # Afficher un aperçu
    print("\n📧 APERÇU DE L'EMAIL")
    print("=" * 50)
    print(f"À: {state.get('recipient_email')}")
    print(f"Objet: {state.get('subject')}")
    print("-" * 50)
    print(state.get('body'))
    print("=" * 50)
    
    # Simuler une confirmation pour l'automatisation
    # En production, on attendrait une réponse utilisateur
    confirmation = input("\nConfirmer l'envoi ? (o/n/m pour modifier): ").strip().lower()
    
    if confirmation in ["o", "oui", "yes", "y"]:
        return {
            **state,
            "confirmation_response": "send",
            "status": "sending"
        }
    elif confirmation in ["m", "modifier", "modify"]:
        return {
            **state,
            "confirmation_response": "modify",
            "status": "processing",
            "retry_count": state.get("retry_count", 0) + 1
        }
    else:
        return {
            **state,
            "confirmation_response": "cancel",
            "status": "done",
            "result_message": "Envoi annulé"
        }


def send_email_node(state: EmailAgentState) -> Dict[str, Any]:
    """
    Nœud 5: Envoie l'email
    """
    print("📤 Envoi de l'email...")
    
    result = email_service.send_email(
        to=state["recipient_email"],
        subject=state["subject"],
        body=state["body"]
    )
    
    if result.get("status") == "success":
        return {
            **state,
            "email_sent": True,
            "email_id": result.get("message_id"),
            "status": "done",
            "result_message": f"Email envoyé à {state['recipient_email']}"
        }
    else:
        return {
            **state,
            "error": result.get("error", "Erreur d'envoi"),
            "status": "error"
        }


def handle_error_node(state: EmailAgentState) -> Dict[str, Any]:
    """
    Nœud d'erreur: Gère les erreurs
    """
    print(f"❌ Erreur: {state.get('error', 'Erreur inconnue')}")
    
    # Incrémenter le compteur d'erreurs
    error_count = state.get("error_count", 0) + 1
    
    # Si trop d'erreurs, abandonner
    if error_count >= state.get("max_retries", 3):
        return {
            **state,
            "status": "error",
            "result_message": f"Abandon après {error_count} erreurs: {state.get('error')}"
        }
    
    return {
        **state,
        "error_count": error_count,
        "status": "error",
        "result_message": f"Erreur: {state.get('error')}"
    }


def finish_node(state: EmailAgentState) -> Dict[str, Any]:
    """
    Nœud final: Prépare la réponse
    """
    print("🏁 Terminé !")
    
    if state.get("email_sent"):
        message = f"✅ Email envoyé avec succès à {state.get('recipient_email')}"
    elif state.get("error"):
        message = f"❌ {state.get('error')}"
    else:
        message = state.get("result_message", "Action terminée")
    
    return {
        **state,
        "status": "done",
        "result_message": message
    }