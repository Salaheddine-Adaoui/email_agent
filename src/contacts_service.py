# src/contacts_service.py
import sqlite3
import os
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

class ContactsService:
    """Service de gestion des contacts"""
    
    def __init__(self):
        self.db_path = os.getenv("DATABASE_PATH", "data/contacts.db")
        self._init_db()
    
    def _init_db(self):
        """Initialise la base de données des contacts"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                company TEXT,
                role TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Contacts par défaut pour les tests
        cursor.execute("SELECT COUNT(*) FROM contacts")
        if cursor.fetchone()[0] == 0:
            default_contacts = [
                ("Sarah", "sarah@entreprise.com", "Acme Corp", "Chef de projet"),
                ("Jean", "jean@entreprise.com", "Acme Corp", "Développeur"),
                ("Marie", "marie@entreprise.com", "Beta Inc", "Directrice"),
                ("Support", "support@entreprise.com", None, None),
                ("Client VIP", "client.vip@email.com", "Important Corp", "CEO"),
            ]
            
            for name, email, company, role in default_contacts:
                cursor.execute("""
                    INSERT INTO contacts (name, email, company, role)
                    VALUES (?, ?, ?, ?)
                """, (name, email, company, role))
        
        conn.commit()
        conn.close()
        print(f"✅ Base de contacts initialisée: {self.db_path}")
    
    def find_contact(self, name_or_email: str) -> Optional[Dict[str, str]]:
        """
        Recherche un contact par nom ou email.
        
        Args:
            name_or_email: Nom ou email du contact
        
        Returns:
            Dict avec les infos du contact ou None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Recherche par email exact ou nom partiel
        cursor.execute("""
            SELECT id, name, email, company, role
            FROM contacts
            WHERE email = ? OR LOWER(name) LIKE LOWER(?)
        """, (name_or_email, f"%{name_or_email}%"))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "company": row[3],
                "role": row[4]
            }
        
        return None
    
    def search_contacts(self, query: str) -> List[Dict[str, str]]:
        """
        Recherche des contacts par nom, email ou entreprise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, email, company, role
            FROM contacts
            WHERE LOWER(name) LIKE LOWER(?)
               OR LOWER(email) LIKE LOWER(?)
               OR LOWER(company) LIKE LOWER(?)
            LIMIT 5
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "company": row[3],
                "role": row[4]
            }
            for row in rows
        ]
    
    def add_contact(self, name: str, email: str, company: str = None, role: str = None):
        """Ajoute un nouveau contact"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO contacts (name, email, company, role)
                VALUES (?, ?, ?, ?)
            """, (name, email, company, role))
            conn.commit()
            return {"status": "success", "id": cursor.lastrowid}
        except sqlite3.IntegrityError:
            return {"status": "error", "message": "Email déjà existant"}
        finally:
            conn.close()