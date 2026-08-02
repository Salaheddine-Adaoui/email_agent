# src/llm_service.py
import os
import json
import re
from typing import Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    """Service pour interagir avec Ollama"""
    
    def __init__(self):
        self.llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.1:latest"),
            temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0")),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
        print(f"✅ LLM initialisé: {os.getenv('OLLAMA_MODEL', 'llama3.1:latest')}")
    
    def parse_intent(self, query: str) -> Dict[str, Any]:
        """
        Analyse la requête utilisateur pour extraire l'intention et les informations.
        """
        prompt = f"""
        Tu es un assistant qui analyse les requêtes pour envoyer des emails.
        Extrais les informations suivantes de la requête:
        
        1. intent: "send", "read", "reply", "search"
        2. recipient: le nom ou email du destinataire (si présent)
        3. subject: le sujet de l'email (si présent)
        4. body: le contenu de l'email (si présent)
        
        Réponds UNIQUEMENT au format JSON valide.
        
        Requête: "{query}"
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            # Extraire le JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(content)
            
            # Validation
            if "intent" not in result:
                result["intent"] = "send"  # Par défaut
            
            return result
            
        except Exception as e:
            print(f"❌ Erreur parsing: {e}")
            return {
                "intent": "send",
                "recipient": None,
                "subject": None,
                "body": None
            }
    
    def write_email(self, recipient: str, subject: Optional[str], body: Optional[str], context: str) -> Dict[str, str]:
        """
        Rédige un email professionnel.
        """
        prompt = f"""
        Rédige un email professionnel en français avec les informations suivantes:
        
        Destinataire: {recipient}
        Sujet proposé: {subject if subject else "À déterminer"}
        Contexte: {context}
        
        Retourne UNIQUEMENT un JSON avec:
        {{"subject": "sujet de l'email", "body": "contenu de l'email"}}
        
        L'email doit être:
        - Poli et professionnel
        - Clairement structuré
        - Adapté au contexte
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(content)
            
            return {
                "subject": result.get("subject", "Sans sujet"),
                "body": result.get("body", "Email généré automatiquement.")
            }
            
        except Exception as e:
            print(f"❌ Erreur rédaction: {e}")
            return {
                "subject": "Sujet automatique",
                "body": f"Contexte: {context}\n\nEmail généré automatiquement."
            }
    
    def format_response(self, result: Dict[str, Any]) -> str:
        """
        Formate la réponse finale pour l'utilisateur.
        """
        if result.get("email_sent"):
            return f"""
✅ Email envoyé avec succès !
   À: {result.get('recipient_email')}
   Objet: {result.get('subject')}
   ID: {result.get('email_id', 'N/A')}
"""
        
        if result.get("error"):
            return f"""
❌ Une erreur est survenue:
   {result.get('error')}
"""
        
        if result.get("confirmation_response") == "cancel":
            return "❌ Envoi annulé par l'utilisateur."
        
        if result.get("confirmation_response") == "modify":
            return "🔄 Modification demandée."
        
        return "✅ Action terminée avec succès."