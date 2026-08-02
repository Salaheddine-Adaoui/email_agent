# main.py
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Ajouter src au PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.graph import create_email_agent
from src.state import EmailAgentState
from src.llm_service import LLMService

# Initialisation
load_dotenv()
init(autoreset=True)

def print_header():
    """Affiche l'en-tête du programme"""
    print(Fore.CYAN + "=" * 60)
    print(Fore.CYAN + "📧 AGENT GESTIONNAIRE D'EMAILS")
    print(Fore.CYAN + "   Architecture LangGraph + Ollama")
    print(Fore.CYAN + "=" * 60)
    print(Fore.YELLOW + "\n💡 Commandes disponibles:")
    print(Fore.WHITE + "   • Envoie un email à [nom] pour [sujet]")
    print(Fore.WHITE + "   • Dis bonjour à [nom]")
    print(Fore.WHITE + "   • Écris un email de remerciement à [nom]")
    print(Fore.WHITE + "   • Voir les contacts")
    print(Fore.WHITE + "   • Ajouter un contact [nom] [email]")
    print(Fore.WHITE + "   • exit / quit / q")
    print(Fore.CYAN + "-" * 60)

def print_result(result: dict):
    """Affiche le résultat de l'agent"""
    print(Fore.GREEN + "\n🤖 Agent:")
    print("-" * 40)
    
    if result.get("email_sent"):
        print(Fore.GREEN + f"✅ Email envoyé avec succès !")
        print(Fore.WHITE + f"   À: {result.get('recipient_email')}")
        print(Fore.WHITE + f"   Objet: {result.get('subject')}")
        if result.get("email_id"):
            print(Fore.WHITE + f"   ID: {result.get('email_id')}")
    elif result.get("error"):
        print(Fore.RED + f"❌ Erreur: {result.get('error')}")
    elif result.get("confirmation_response") == "cancel":
        print(Fore.YELLOW + "❌ Envoi annulé")
    elif result.get("confirmation_response") == "modify":
        print(Fore.YELLOW + "🔄 Modification demandée")
    else:
        print(Fore.WHITE + result.get("result_message", "Action terminée"))
    
    print(Fore.CYAN + "-" * 40)

def show_contacts():
    """Affiche la liste des contacts"""
    from src.contacts_service import ContactsService
    contacts = ContactsService()
    
    # Récupérer tous les contacts
    import sqlite3
    conn = sqlite3.connect(contacts.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, company FROM contacts ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        print(Fore.CYAN + "\n📋 Contacts disponibles:")
        print("-" * 40)
        for name, email, company in rows:
            print(Fore.WHITE + f"  • {name} ({email})" + (f" - {company}" if company else ""))
        print(Fore.CYAN + "-" * 40)
    else:
        print(Fore.YELLOW + "\n📋 Aucun contact trouvé")

def add_contact(name: str, email: str, company: str = ""):
    """Ajoute un contact"""
    from src.contacts_service import ContactsService
    contacts = ContactsService()
    
    result = contacts.add_contact(name, email, company)
    if result.get("status") == "success":
        print(Fore.GREEN + f"✅ Contact '{name}' ajouté avec succès")
    else:
        print(Fore.RED + f"❌ Erreur: {result.get('message')}")

def main():
    """Point d'entrée principal"""
    print_header()
    
    # Vérifier Ollama
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(Fore.GREEN + f"✅ Ollama: {', '.join([m['name'] for m in models])}")
        else:
            print(Fore.YELLOW + "⚠️  Ollama inaccessible")
    except:
        print(Fore.YELLOW + "⚠️  Ollama indisponible. Lance: ollama serve")
        return
    
    # Créer l'agent
    try:
        agent = create_email_agent()
        print(Fore.GREEN + "✅ Agent initialisé avec succès")
    except Exception as e:
        print(Fore.RED + f"❌ Erreur d'initialisation: {e}")
        return
    
    # Boucle principale
    while True:
        try:
            query = input(Fore.CYAN + f"\n[{datetime.now().strftime('%H:%M')}] " + Fore.WHITE + "👤 Vous: ").strip()
            
            if query.lower() in ["exit", "quit", "q"]:
                print(Fore.CYAN + "👋 Au revoir !")
                break
            
            if not query:
                continue
            
            # Commandes spéciales
            if query.lower().startswith("voir les contacts"):
                show_contacts()
                continue
            
            if query.lower().startswith("ajouter un contact"):
                rest = query[len("ajouter un contact"):].strip()
                if not rest:
                    print(Fore.RED + "❌ Usage: ajouter un contact [nom] [email] [company]")
                    continue

                tokens = rest.split()
                email = None
                email_index = None
                for i, token in enumerate(tokens):
                    if "@" in token:
                        email = token
                        email_index = i
                        break

                if email is None:
                    print(Fore.RED + "❌ Veuillez fournir une adresse email valide.")
                    continue

                name = " ".join(tokens[:email_index]).strip()
                company = " ".join(tokens[email_index + 1:]).strip()

                if not name:
                    print(Fore.RED + "❌ Veuillez fournir un nom pour le contact.")
                    continue

                add_contact(name, email, company)
                continue
            
            # État initial
            initial_state: EmailAgentState = {
                "messages": [],
                "user_query": query,
                "user_id": "default_user",
                "intent": "",
                "recipient": None,
                "recipient_email": None,
                "subject": None,
                "body": None,
                "confirmation_requested": False,
                "confirmation_response": None,
                "email_sent": False,
                "email_id": None,
                "result_message": None,
                "error": None,
                "error_count": 0,
                "status": "pending",
                "retry_count": 0,
                "max_retries": 3
            }
            
            # Exécuter l'agent
            result = agent.invoke(initial_state)
            
            # Afficher le résultat
            print_result(result)
            
        except KeyboardInterrupt:
            print(Fore.CYAN + "\n👋 Au revoir !")
            break
        except Exception as e:
            print(Fore.RED + f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()