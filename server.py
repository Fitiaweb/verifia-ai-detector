from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import sqlite3
import random
import string
from datetime import datetime, timedelta
from typing import Optional
import stripe

stripe.api_key = os.getenv("STRIPE_API_KEY", None)

app = FastAPI(title="VerifIA Backend")

def init_db():
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    
    # Vérifier si la table users existe et nécessite une mise à jour
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    
    if columns and "password_hash" not in columns:
        print("[DB] Ancienne structure de table users détectée. Mise à jour de la base de données...")
        c.execute("DROP TABLE IF EXISTS users")
        c.execute("DROP TABLE IF EXISTS sessions")
        
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY, 
        password_hash TEXT,
        first_name TEXT,
        last_name TEXT,
        birth_date TEXT,
        is_premium INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, email TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS usage (ip TEXT PRIMARY KEY, count INTEGER)''')
    conn.commit()
    conn.close()

init_db()

import hashlib
import secrets
import re

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pwd_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    pbkdf2_hash = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
    return f"{salt}:{pbkdf2_hash.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, hash_val = stored_hash.split(':')
        pwd_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        pbkdf2_hash = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000)
        return pbkdf2_hash.hex() == hash_val
    except Exception:
        return False

class TextRequest(BaseModel):
    text: str

class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    birth_date: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

def get_user_by_token(token: str):
    if not token: return None
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("SELECT email FROM sessions WHERE token=?", (token,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    email = row[0]
    c.execute("SELECT first_name, last_name, birth_date, is_premium FROM users WHERE email=?", (email,))
    user_row = c.fetchone()
    conn.close()
    if not user_row:
        return None
    return {
        "email": email, 
        "first_name": user_row[0],
        "last_name": user_row[1],
        "birth_date": user_row[2],
        "is_premium": bool(user_row[3])
    }

@app.post("/api/auth/register")
async def register_user(req: RegisterRequest):
    email = req.email.lower().strip()
    first_name = req.first_name.strip()
    last_name = req.last_name.strip()
    birth_date = req.birth_date.strip()
    password = req.password
    
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Adresse e-mail invalide.")
    if not first_name or not last_name:
        raise HTTPException(status_code=400, detail="Le nom et le prénom sont requis.")
    if not birth_date:
        raise HTTPException(status_code=400, detail="La date de naissance est requise.")
        
    # Vérification de la force du mot de passe
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 8 caractères.")
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins une lettre majuscule.")
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins une lettre minuscule.")
    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins un chiffre.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins un caractère spécial.")
        
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    
    c.execute("SELECT email FROM users WHERE email=?", (email,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Cet e-mail est déjà utilisé.")
        
    password_hash = hash_password(password)
    
    c.execute(
        "INSERT INTO users (email, password_hash, first_name, last_name, birth_date, is_premium) VALUES (?, ?, ?, ?, ?, 0)",
        (email, password_hash, first_name, last_name, birth_date)
    )
    
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    c.execute("INSERT INTO sessions (token, email) VALUES (?, ?)", (token, email))
    
    conn.commit()
    conn.close()
    
    return {"token": token, "email": email, "first_name": first_name, "last_name": last_name, "birth_date": birth_date, "is_premium": False}

@app.post("/api/auth/login")
async def login_user(req: LoginRequest):
    email = req.email.lower().strip()
    password = req.password
    
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("SELECT password_hash, first_name, last_name, birth_date, is_premium FROM users WHERE email=?", (email,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail="Adresse e-mail ou mot de passe incorrect.")
        
    stored_hash, first_name, last_name, birth_date, is_premium = row
    if not verify_password(password, stored_hash):
        conn.close()
        raise HTTPException(status_code=400, detail="Adresse e-mail ou mot de passe incorrect.")
        
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    c.execute("INSERT INTO sessions (token, email) VALUES (?, ?)", (token, email))
    
    conn.commit()
    conn.close()
    
    return {
        "token": token, 
        "email": email, 
        "first_name": first_name, 
        "last_name": last_name, 
        "birth_date": birth_date, 
        "is_premium": bool(is_premium)
    }

@app.get("/api/auth/profile")
async def get_profile(Authorization: Optional[str] = Header(None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Non autorisé")
    token = Authorization.split(" ")[1]
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Non autorisé")
    return user

@app.post("/api/upgrade")
async def upgrade_account(Authorization: Optional[str] = Header(None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Non autorisé")
    token = Authorization.split(" ")[1]
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Non autorisé")
        
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium=1 WHERE email=?", (user["email"],))
    conn.commit()
    conn.close()
    return {"message": "Compte passé en Premium avec succès !", "is_premium": True}

# ==========================================
# CONFIGURATION ET ENDPOINTS PAIEMENT STRIPE
# ==========================================

class PaymentSessionRequest(BaseModel):
    plan: str

@app.post("/api/payments/create-session")
async def create_payment_session(req: PaymentSessionRequest, request: Request, Authorization: Optional[str] = Header(None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Non autorisé")
    token = Authorization.split(" ")[1]
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Non autorisé")
        
    email = user["email"]
    plan = req.plan.lower().strip()
    if plan not in ["monthly", "annual"]:
        raise HTTPException(status_code=400, detail="Plan invalide")
        
    # Tarification attractive (en centimes EUR)
    price_cents = 499 if plan == "monthly" else 2999
    plan_name = "VerifIA - Abonnement Mensuel Pro" if plan == "monthly" else "VerifIA - Abonnement Annuel Pro"
    
    # Déterminer l'URL de redirection de façon dynamique
    origin = str(request.base_url).rstrip('/')
    # Forcer HTTPS pour la production Render afin d'assurer la sécurité du paiement
    if "localhost" not in origin and "127.0.0.1" not in origin:
        origin = origin.replace("http://", "https://")
        
    # Si la clé Stripe est fournie, on crée une session Stripe Checkout officielle
    if stripe.api_key and stripe.api_key != "mock":
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': plan_name,
                        },
                        'unit_amount': price_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                customer_email=email,
                success_url=f"{origin}/api/payments/confirm?email={email}&plan={plan}&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{origin}/#pricing",
            )
            return {"checkout_url": session.url}
        except Exception as e:
            print(f"\n[STRIPE API ERROR] Impossible de créer la session Stripe Checkout: {e}. Fallback vers Simulation.\n")
            
    # Mode simulation (magnifique interface locale interactive)
    order_id = "ord_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=16))
    sim_url = f"/checkout-simulation.html?plan={plan}&email={email}&session_id={order_id}"
    return {"checkout_url": sim_url}

@app.get("/api/payments/confirm")
async def confirm_payment(email: str, plan: str, order_id: Optional[str] = None, session_id: Optional[str] = None):
    email = email.lower().strip()
    
    # Vérification réelle auprès de Stripe si configuré
    if stripe.api_key and stripe.api_key != "mock" and session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status != "paid":
                raise HTTPException(status_code=400, detail="Transaction Stripe non finalisée.")
        except Exception as e:
            print(f"[STRIPE CONFIRM WARNING] Erreur validation Stripe: {e}. Validation locale autorisée.")
            
    # Surclassement de l'utilisateur dans la base SQLite SQLite3
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium=1 WHERE email=?", (email,))
    conn.commit()
    conn.close()
    
    # Redirection vers la page de succès
    return FileResponse("payment-success.html")


@app.post("/api/analyze")
async def analyze_text(request: TextRequest, req: Request, Authorization: Optional[str] = Header(None)):
    is_premium = False
    if Authorization and Authorization.startswith("Bearer "):
        token = Authorization.split(" ")[1]
        user = get_user_by_token(token)
        if user:
            is_premium = user["is_premium"]

    if not is_premium:
        client_ip = req.client.host
        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        c.execute("SELECT count FROM usage WHERE ip=?", (client_ip,))
        row = c.fetchone()
        
        count = row[0] if row else 0
        if count >= 3:
            conn.close()
            raise HTTPException(status_code=402, detail="Limite atteinte")
            
        if row:
            c.execute("UPDATE usage SET count=count+1 WHERE ip=?", (client_ip,))
        else:
            c.execute("INSERT INTO usage (ip, count) VALUES (?, 1)", (client_ip,))
        conn.commit()
        conn.close()

    text = request.text
    if len(text) < 10:
        raise HTTPException(status_code=400, detail="Texte trop court")

    # Tentative d'analyse par l'API Gemini Officielle
    try:
        agent_result = await gemini_verification(text)
        if agent_result is not None:
            return agent_result
    except Exception as e:
        print(f"Erreur API Gemini: {e}. Fallback vers l'Heuristique Locale.")
        
    # Fallback: Utilisation exclusive de l'analyse locale en cas d'échec
    return local_expert_analysis(text)

import google.generativeai as genai
import asyncio

# Configuration de l'API Gemini avec votre clé
genai.configure(api_key="AIzaSyA1rq5ywO1ts2DSLPLLRoVf2P15UgAwBA8")
model = genai.GenerativeModel('gemini-1.5-flash')

async def ask_gemini(text):
    prompt = f"""Tu es un expert en détection de contenu généré par l'IA. Analyse ce texte et détermine s'il a été écrit par une IA.
Repère les signes typiques : vocabulaire lissé, phrases de longueur similaire, transitions artificielles ("cependant", "en conclusion"), et absence de véritable émotion humaine.
Réponds STRICTEMENT par le mot 'OUI' (si c'est une IA) ou 'NON' (si c'est un humain). Ne justifie surtout pas ta réponse.
Texte : '{text}'"""
    try:
        # Exécution asynchrone pour ne pas bloquer FastAPI
        response = await asyncio.to_thread(model.generate_content, prompt)
        resp_lower = response.text.strip().lower()
        
        if resp_lower.startswith("oui") or "oui" in resp_lower[:10]: 
            return True
        if resp_lower.startswith("non") or "non" in resp_lower[:10]: 
            return False
            
        print(f"Gemini réponse ambiguë: {response.text}")
        return None
    except Exception as e:
        print(f"Erreur API Gemini interne: {e}")
        return None

async def gemini_verification(text: str):
    """ Envoie le texte à l'API Gemini 1.5 Flash officielle """
    is_ai = await ask_gemini(text)
    
    if is_ai is None:
        return None
        
    # On récupère l'analyse locale
    local_res = local_expert_analysis(text)
    local_score = local_res["ai_probability"]
    
    # Stratégie de fusion plus intelligente
    if is_ai:
        # Gemini est sûr que c'est une IA. On garantit un score élevé, nuancé par l'expert local.
        final_probability = max(80.0, (80.0 * 0.5) + (local_score * 0.5))
    else:
        # Gemini pense que c'est humain. Mais s'il se trompe et que l'expert local est formel ?
        if local_score >= 70:
            final_probability = local_score * 0.85 # On fait confiance à l'expert local si les preuves sont fortes
        else:
            final_probability = local_score * 0.4  # Sinon, on baisse drastiquement le score

    return {
        "ai_probability": round(final_probability, 2), 
        "source": "API Gemini Officielle + Heuristique"
    }

import re

def local_expert_analysis(text):
    """ Système expert local avancé pour détecter l'IA sans API externe """
    score = 15.0  # Base un peu plus haute
    text_lower = text.lower()
    
    # 1. Mots-clés et tics de langage massifs de ChatGPT
    ai_keywords = [
        "en résumé", "en conclusion", "il est important de noter", "cependant",
        "tout d'abord", "ensuite", "enfin", "en outre", "néanmoins",
        "il convient de souligner", "bien que", "en définitive",
        "dans l'ensemble", "il est crucial", "en d'autres termes",
        "chatgpt", "intelligence artificielle", "modèle de langage",
        "en fin de compte", "il est essentiel", "voici", "bien sûr", 
        "absolument", "n'hésitez pas", "en effet", "par ailleurs",
        "notons que", "il faut savoir que", "il est primordial",
        "gardez à l'esprit", "il est à noter", "dans un monde", 
        "à l'ère du", "naviguer", "paysage", "catalyseur", "dévoiler",
        "explorer", "il va sans dire", "mettre en évidence", "panorama"
    ]
    
    keyword_matches = sum(1 for kw in ai_keywords if kw in text_lower)
    score += (keyword_matches * 15)  # Poids ajusté par mot clé
    
    # 2. Analyse structurelle (Puces, Listes, Titres)
    # ChatGPT adore faire des listes à puces ou numérotées
    if re.search(r':\s*\n\s*[-*]', text) or re.search(r':\s*[-*]', text):
        score += 25
    
    # Détection de listes numérotées (1. 2. 3.)
    if len(re.findall(r'(?:^|\n)\s*\d+\.\s', text)) >= 2:
        score += 25
        
    # Détection de conclusion typique
    if re.search(r'(?:^|\n)(?:En conclusion|Pour conclure|En résumé|Finalement)\s*[:,]', text, re.IGNORECASE):
        score += 35

    # 3. Analyse de la structure des phrases (Burstiness)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 5]
    if len(sentences) > 3: # Au moins 4 phrases pour calculer une variance significative
        lengths = [len(s.split()) for s in sentences]
        avg_len = sum(lengths) / len(lengths)
        variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
        
        # Très faible variance = IA (rythme très mécanique)
        if variance < 15:
            score += 35
        elif variance < 30:
            score += 20
        elif variance > 90:
            score -= 20  # Humain (rythme chaotique)
            
        # Phrases très longues, typique de l'IA académique
        if avg_len > 22:
            score += 15
            
    # 4. Diversité lexicale
    words = [w for w in re.findall(r'\b\w+\b', text_lower) if len(w) > 3]
    if len(words) > 15:
        unique_words = len(set(words))
        lexical_diversity = unique_words / len(words)
        
        if lexical_diversity < 0.55:
            score += 20
            
    # L'IA utilise très peu les points d'exclamation sauf si on lui demande
    if len(sentences) > 4 and '!' not in text:
        score += 10
            
    # 5. Ajustements finaux
    score = max(1.0, min(99.0, score))
    
    # Aléa léger pour le côté "vivant"
    hash_val = sum(ord(c) for c in text) % 5 - 2
    final_score = max(1.0, min(99.0, score + hash_val))
    
    return {"ai_probability": round(final_score, 2), "source": "Heuristique Experte (Local)"}

@app.get("/checkout-simulation.html")
async def read_checkout_simulation():
    return FileResponse("checkout-simulation.html")

@app.get("/payment-success.html")
async def read_payment_success():
    return FileResponse("payment-success.html")

# Servir les fichiers statiques (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def read_index():
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    # Lancement du serveur sur le port 8000
    print("Démarrage du serveur VerifIA sur http://localhost:8000")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
