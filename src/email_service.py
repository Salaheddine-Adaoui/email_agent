# src/email_service.py
import os
import ssl
import smtplib
from email.message import EmailMessage
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    """Service pour envoyer des emails via SMTP."""

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() in ["1", "true", "yes"]
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ["1", "true", "yes"]
        self.from_address = os.getenv("EMAIL_FROM") or self.smtp_user

        self._validate_config()

    def _validate_config(self):
        missing = []
        if not self.smtp_host:
            missing.append("SMTP_HOST")
        if not self.smtp_port:
            missing.append("SMTP_PORT")
        if not self.smtp_user:
            missing.append("SMTP_USER")
        if not self.smtp_password:
            missing.append("SMTP_PASSWORD")

        if missing:
            raise ValueError(f"Variables d'environnement SMTP manquantes: {', '.join(missing)}")

        print(f"✅ SMTP configuré: {self.smtp_host}:{self.smtp_port} (SSL={self.smtp_use_ssl}, TLS={self.smtp_use_tls})")
    
    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Envoie un email via SMTP.
        
        Args:
            to: Adresse email du destinataire
            subject: Sujet de l'email
            body: Corps de l'email en HTML ou texte
        
        Returns:
            Dict avec le résultat
        """
        try:
            message = EmailMessage()
            message["From"] = self.from_address
            message["To"] = to
            message["Subject"] = subject
            message.set_content(body)
            message.add_alternative(body, subtype="html")

            if self.smtp_use_ssl:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=ssl.create_default_context()) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as server:
                    if self.smtp_use_tls:
                        server.starttls(context=ssl.create_default_context())
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(message)

            return {
                "status": "success",
                "message_id": None,
                "recipient": to,
                "subject": subject
            }
        except Exception as e:
            print(f"❌ Erreur SMTP: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def simulate_send(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Simule l'envoi d'un email (pour les tests sans SMTP).
        """
        print(f"""
📧 SIMULATION D'ENVOI D'EMAIL
   À: {to}
   Objet: {subject}
   Corps: {body[:100]}...
""")
        
        return {
            "status": "success",
            "message_id": "sim_123456789",
            "thread_id": "sim_thread_123",
            "recipient": to,
            "subject": subject,
            "simulated": True
        }