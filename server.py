import os
import sqlite3
import random
import string
import hashlib
import secrets
import re
import asyncio
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
import stripe

# Configuration Stripe
stripe_key = os.getenv("STRIPE_API_KEY", "").strip()
stripe.api_key = stripe_key if stripe_key else None

app = FastAPI(title="VerifIA Backend - Détecteur IA SaaS")

# Catalogue des packs de tests (Micro-paiements pay-as-you-go)
PACK_PLANS = {
    "pack_2": {
        "name": "Pack Découverte (2 Tests)",
        "tests": 2,
        "price_cents": 100,  # 1.00 € / $1
        "price_str": "1,00 €"
    },
    "pack_5": {
        "name": "Pack Populaire (5 Tests)",
        "tests": 5,
        "price_cents": 200,  # 2.00 € / $2
        "price_str": "2,00 €"
    },
    "pack_10": {
        "name": "Pack Économique (10 Tests)",
        "tests": 10,
        "price_cents": 400,  # 4.00 € / $4
        "price_str": "4,00 €"
    }
}

# ==========================================
# BASE DE DONNÉES ET GESTION DES UTILISATEURS
# ==========================================

def init_db():
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    
    c.execute("PRAGMA table_info(users)")
    cols = [col[1] for col in c.fetchall()]
    if cols and "password_hash" not in cols:
        print("[DB] Ancienne structure legacy de table users détectée. Mise à niveau du schéma...")
        c.execute("DROP TABLE IF EXISTS users")
        c.execute("DROP TABLE IF EXISTS sessions")

    # Création table utilisateurs avec crédits (3 tests offerts par défaut)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY, 
        password_hash TEXT,
        first_name TEXT,
        last_name TEXT,
        birth_date TEXT,
        credits INTEGER DEFAULT 3,
        created_at TEXT
    )''')
    
    # Migration douce si credits manque
    c.execute("PRAGMA table_info(users)")
    cols = [col[1] for col in c.fetchall()]
    if "credits" not in cols:
        try:
            c.execute("ALTER TABLE users ADD COLUMN credits INTEGER DEFAULT 3")
        except Exception:
            pass
            
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY, 
        email TEXT,
        created_at TEXT
    )''')

    c.execute("PRAGMA table_info(sessions)")
    sess_cols = [col[1] for col in c.fetchall()]
    if "created_at" not in sess_cols:
        try:
            c.execute("ALTER TABLE sessions ADD COLUMN created_at TEXT")
        except Exception:
            pass
    
    # Suivi d'utilisation anonyme par IP (3 tests gratuits max)
    c.execute('''CREATE TABLE IF NOT EXISTS usage (
        ip TEXT PRIMARY KEY, 
        count INTEGER DEFAULT 0,
        last_used TEXT
    )''')

    c.execute("PRAGMA table_info(usage)")
    usage_cols = [col[1] for col in c.fetchall()]
    if "last_used" not in usage_cols:
        try:
            c.execute("ALTER TABLE usage ADD COLUMN last_used TEXT")
        except Exception:
            pass
    
    # Historique des commandes / paiements
    c.execute('''CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        email TEXT,
        plan TEXT,
        tests_added INTEGER,
        amount_cents INTEGER,
        created_at TEXT
    )''')
    
    conn.commit()
    conn.close()

init_db()

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

def get_user_by_token(token: str):
    if not token:
        return None
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("SELECT email FROM sessions WHERE token=?", (token,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    email = row[0]
    
    c.execute("SELECT first_name, last_name, birth_date, credits FROM users WHERE email=?", (email,))
    user_row = c.fetchone()
    conn.close()
    if not user_row:
        return None
    return {
        "email": email, 
        "first_name": user_row[0],
        "last_name": user_row[1],
        "birth_date": user_row[2],
        "credits": user_row[3] if user_row[3] is not None else 0
    }

# ==========================================
# MODÈLES PYDANTIC
# ==========================================

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

class PaymentSessionRequest(BaseModel):
    plan: str
    email: Optional[str] = None

# ==========================================
# ENDPOINTS D'AUTHENTIFICATION & PROFILS
# ==========================================

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
        
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 8 caractères.")
        
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    
    c.execute("SELECT email FROM users WHERE email=?", (email,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Cet e-mail est déjà utilisé.")
        
    password_hash = hash_password(password)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 3 tests offerts à la création du compte
    initial_credits = 3
    c.execute(
        "INSERT INTO users (email, password_hash, first_name, last_name, birth_date, credits, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (email, password_hash, first_name, last_name, birth_date, initial_credits, now_str)
    )
    
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    c.execute("INSERT INTO sessions (token, email, created_at) VALUES (?, ?, ?)", (token, email, now_str))
    
    conn.commit()
    conn.close()
    
    return {
        "token": token, 
        "email": email, 
        "first_name": first_name, 
        "last_name": last_name, 
        "credits": initial_credits
    }

@app.post("/api/auth/login")
async def login_user(req: LoginRequest):
    email = req.email.lower().strip()
    password = req.password
    
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("SELECT password_hash, first_name, last_name, birth_date, credits FROM users WHERE email=?", (email,))
    row = c.fetchone()
    
    if not row or not verify_password(password, row[0]):
        conn.close()
        raise HTTPException(status_code=400, detail="Adresse e-mail ou mot de passe incorrect.")
        
    first_name, last_name, birth_date, credits = row[1], row[2], row[3], row[4]
    credits = credits if credits is not None else 0
    
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO sessions (token, email, created_at) VALUES (?, ?, ?)", (token, email, now_str))
    
    conn.commit()
    conn.close()
    
    return {
        "token": token, 
        "email": email, 
        "first_name": first_name, 
        "last_name": last_name, 
        "credits": credits
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

@app.get("/api/credits")
async def get_credits_status(request: Request, Authorization: Optional[str] = Header(None)):
    """ Permet au frontend de connaître immédiatement le nombre de tests restants """
    user = None
    if Authorization and Authorization.startswith("Bearer "):
        token = Authorization.split(" ")[1]
        user = get_user_by_token(token)
        
    if user:
        return {
            "is_logged_in": True,
            "email": user["email"],
            "first_name": user["first_name"],
            "tests_remaining": max(0, user["credits"])
        }
    else:
        client_ip = request.client.host
        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        c.execute("SELECT count FROM usage WHERE ip=?", (client_ip,))
        row = c.fetchone()
        conn.close()
        used = row[0] if row else 0
        remaining = max(0, 3 - used)
        return {
            "is_logged_in": False,
            "tests_remaining": remaining
        }

# ==========================================
# MOTEUR D'ANALYSE ET GESTION DES QUOTAS
# ==========================================

@app.post("/api/analyze")
async def analyze_text(request_data: TextRequest, req: Request, Authorization: Optional[str] = Header(None)):
    user = None
    if Authorization and Authorization.startswith("Bearer "):
        token = Authorization.split(" ")[1]
        user = get_user_by_token(token)

    conn = sqlite3.connect("app.db")
    c = conn.cursor()

    if user:
        # Mode Utilisateur Connecté: basé sur les crédits
        current_credits = user.get("credits", 0)
        if current_credits <= 0:
            conn.close()
            raise HTTPException(
                status_code=402, 
                detail="Vous n'avez plus de tests disponibles. Choisissez un pack pour continuer."
            )
        # Décrémenter 1 test
        c.execute("UPDATE users SET credits = credits - 1 WHERE email=?", (user["email"],))
        conn.commit()
        remaining_tests = current_credits - 1
    else:
        # Mode Anonyme / Invité: basé sur l'adresse IP (3 tests offerts)
        client_ip = req.client.host
        c.execute("SELECT count FROM usage WHERE ip=?", (client_ip,))
        row = c.fetchone()
        count = row[0] if row else 0
        
        if count >= 3:
            conn.close()
            raise HTTPException(
                status_code=402, 
                detail="Vous avez utilisé vos 3 tests gratuits. Choisissez un pack de tests pour continuer."
            )
            
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if row:
            c.execute("UPDATE usage SET count=count+1, last_used=? WHERE ip=?", (now_str, client_ip))
        else:
            c.execute("INSERT INTO usage (ip, count, last_used) VALUES (?, 1, ?)", (client_ip, now_str))
        conn.commit()
        remaining_tests = 3 - (count + 1)

    conn.close()

    text = request_data.text.strip()
    if len(text) < 10:
        raise HTTPException(status_code=400, detail="Le texte est trop court (minimum 10 caractères).")

    # Tentative d'analyse avec l'API Gemini si configurée
    gemini_result = None
    try:
        gemini_result = await gemini_verification(text)
    except Exception as e:
        print(f"[GEMINI ERROR] {e}. Bascule vers l'analyse experte locale.")

    if gemini_result is not None:
        result = gemini_result
    else:
        result = local_expert_analysis(text)

    # Ajouter le nombre de tests restants dans la réponse
    result["tests_remaining"] = remaining_tests
    result["is_logged_in"] = bool(user)
    return result

# ==========================================
# MOTEURS DE DÉTECTION (GEMINI + HEURISTIQUE)
# ==========================================

import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
gemini_model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"[GEMINI INIT WARNING] Impossible d'initialiser Gemini: {e}")

async def ask_gemini(text: str):
    if not gemini_model:
        return None
        
    prompt = f"""Tu es un expert mondial en analyse stylométrique et détection de modèles d'IA (ChatGPT, Claude, Gemini).
Analyse le texte suivant et évalue s'il a été rédigé par une intelligence artificielle.
Repère les caractéristiques typiques : syntaxe trop régulière, manque d'aspérités humaines, transitions mécaniques, vocabulaire poli et standardisé.
Réponds STRICTEMENT par le mot 'OUI' (si c'est très probablement une IA) ou 'NON' (si c'est rédigé par un humain).
Texte : '{text}'"""

    try:
        response = await asyncio.to_thread(gemini_model.generate_content, prompt)
        resp_lower = response.text.strip().lower()
        if "oui" in resp_lower[:10]:
            return True
        if "non" in resp_lower[:10]:
            return False
        return None
    except Exception as e:
        print(f"[GEMINI CALL ERROR] {e}")
        return None

async def gemini_verification(text: str):
    is_ai = await ask_gemini(text)
    if is_ai is None:
        return None

    local_res = local_expert_analysis(text)
    local_score = local_res["ai_probability"]

    if is_ai:
        final_probability = max(78.0, (82.0 * 0.6) + (local_score * 0.4))
    else:
        if local_score >= 70:
            final_probability = local_score * 0.8
        else:
            final_probability = local_score * 0.35

    return {
        "ai_probability": round(min(99.0, max(1.0, final_probability)), 2),
        "source": "Modèle Neuronal Hybride (Gemini + Stylométrie)"
    }

def local_expert_analysis(text: str):
    """ Analyse stylométrique avancée et équilibrée """
    text_lower = text.lower()
    score = 12.0  # Base neutre
    
    # 1. Expressions sur-représentées dans les réponses des LLM
    llm_tells = [
        "il est important de noter", "il convient de souligner", 
        "en définitive", "dans un monde où", "à l'ère du numérique",
        "catalyseur", "naviguer dans le paysage", "un voyage vers",
        "il est primordial de", "force est de constater", "n'hésitez pas à",
        "chatgpt", "intelligence artificielle", "modèle de langage"
    ]
    tells_matches = sum(1 for tell in llm_tells if tell in text_lower)
    score += tells_matches * 12
    
    # 2. Analyse structurelle typique
    if re.search(r':\s*\n\s*[-*•]', text):
        score += 15
    if len(re.findall(r'(?:^|\n)\s*\d+\.\s', text)) >= 2:
        score += 15
        
    # Conclusion explicite
    if re.search(r'(?:^|\n)(?:En conclusion|En résumé|Pour conclure)\s*[:,]', text, re.IGNORECASE):
        score += 20

    # 3. Variance de la longueur des phrases (Burstiness)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 5]
    if len(sentences) >= 3:
        lengths = [len(s.split()) for s in sentences]
        avg_len = sum(lengths) / len(lengths)
        variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
        
        # Faible variance = rythme régulier de l'IA
        if variance < 15:
            score += 25
        elif variance < 30:
            score += 12
        elif variance > 80:
            score -= 15  # Rythme varié et humain
            
        if avg_len > 24:
            score += 10
            
    # 4. Diversité lexicale
    words = [w for w in re.findall(r'\b\w+\b', text_lower) if len(w) > 3]
    if len(words) > 15:
        unique_words = len(set(words))
        diversity = unique_words / len(words)
        if diversity < 0.50:
            score += 18
            
    score = max(5.0, min(95.0, score))
    # Variation d'aléa stylométrique stable
    hash_shift = (sum(ord(c) for c in text[:40]) % 7) - 3
    final_score = max(2.0, min(98.0, score + hash_shift))
    
    return {
        "ai_probability": round(final_score, 2),
        "source": "Analyse Stylométrique Experte"
    }

# ==========================================
# PAIEMENTS ET RECHARGE DE CRÉDITS
# ==========================================

@app.post("/api/payments/create-session")
async def create_payment_session(req: PaymentSessionRequest, request: Request, Authorization: Optional[str] = Header(None)):
    user = None
    if Authorization and Authorization.startswith("Bearer "):
        token = Authorization.split(" ")[1]
        user = get_user_by_token(token)
        
    email = user["email"] if user else (req.email or "").strip().lower()
    if not email:
        raise HTTPException(
            status_code=400, 
            detail="Une adresse e-mail ou une connexion est requise pour attribuer vos tests."
        )
        
    plan = req.plan.lower().strip()
    if plan not in PACK_PLANS:
        raise HTTPException(status_code=400, detail="Pack sélectionné invalide.")
        
    plan_info = PACK_PLANS[plan]
    order_id = "ord_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=16))
    
    origin = str(request.base_url).rstrip('/')
    if "localhost" not in origin and "127.0.0.1" not in origin:
        origin = origin.replace("http://", "https://")

    # Recharger stripe.api_key au cas où elle a été injectée dans l'environnement
    current_stripe_key = os.getenv("STRIPE_API_KEY", "").strip()
    if current_stripe_key:
        stripe.api_key = current_stripe_key

    # Sécurité absolue : Empêcher tout achat si la vraie clé Stripe n'est pas configurée
    if not stripe.api_key or stripe.api_key == "mock":
        raise HTTPException(
            status_code=503,
            detail="Le service de paiement Stripe n'est pas encore configuré. Veuillez ajouter votre clé secrète STRIPE_API_KEY (sk_live_... ou sk_test_...) dans les variables d'environnement sur Render."
        )

    try:
        session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f"VerifIA - {plan_info['name']}",
                    },
                    'unit_amount': plan_info['price_cents'],
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
        print(f"[STRIPE ERROR] {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Erreur lors de la création de la session Stripe : {str(e)}"
        )

@app.get("/api/payments/confirm")
async def confirm_payment(email: str, plan: str, session_id: Optional[str] = None):
    email = email.lower().strip()
    plan = plan.lower().strip()
    
    if plan not in PACK_PLANS:
        raise HTTPException(status_code=400, detail="Pack inconnu.")
        
    plan_info = PACK_PLANS[plan]
    tests_to_add = plan_info["tests"]
    
    current_stripe_key = os.getenv("STRIPE_API_KEY", "").strip()
    if current_stripe_key:
        stripe.api_key = current_stripe_key

    # Sécurité : Vérification OBLIGATOIRE et STRICTE auprès des serveurs Stripe
    if not stripe.api_key or stripe.api_key == "mock":
        raise HTTPException(status_code=503, detail="Vérification impossible : clé Stripe non configurée.")

    if not session_id or not session_id.startswith("cs_"):
        raise HTTPException(
            status_code=400, 
            detail="Identifiant de session Stripe invalide ou manquant. Aucun crédit n'a été attribué."
        )
        
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status != "paid":
            raise HTTPException(
                status_code=402, 
                detail="Le paiement n'a pas été validé par Stripe ou a été refusé par votre banque."
            )
    except Exception as e:
        print(f"[STRIPE VERIFY ERROR] {e}")
        raise HTTPException(
            status_code=400, 
            detail=f"Impossible de valider ce paiement auprès de Stripe : {str(e)}"
        )
        
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    
    # Table anti-double crédit (évite de réattribuer des crédits si l'URL de succès est rechargée)
    c.execute("CREATE TABLE IF NOT EXISTS processed_sessions (session_id TEXT PRIMARY KEY, created_at TEXT)")
    c.execute("SELECT session_id FROM processed_sessions WHERE session_id=?", (session_id,))
    if c.fetchone():
        conn.close()
        return RedirectResponse(url=f"/payment-success.html?plan={plan}&tests={tests_to_add}&email={email}")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO processed_sessions (session_id, created_at) VALUES (?, ?)", (session_id, now_str))

    # Vérifier si l'utilisateur existe déjà
    c.execute("SELECT credits FROM users WHERE email=?", (email,))
    row = c.fetchone()
    
    if row:
        new_credits = (row[0] or 0) + tests_to_add
        c.execute("UPDATE users SET credits=? WHERE email=?", (new_credits, email))
    else:
        # Création d'un profil pré-activé pour cet e-mail avec ses tests achetés + 3 offerts
        new_credits = 3 + tests_to_add
        c.execute(
            "INSERT INTO users (email, password_hash, first_name, last_name, birth_date, credits, created_at) VALUES (?, '', 'Membre', '', '', ?, ?)",
            (email, new_credits, now_str)
        )
        
    c.execute(
        "INSERT INTO payments (order_id, email, plan, tests_added, amount_cents, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, email, plan, tests_to_add, plan_info["price_cents"], now_str)
    )
    conn.commit()
    conn.close()
    
    return RedirectResponse(url=f"/payment-success.html?plan={plan}&tests={tests_to_add}&email={email}")

# ==========================================
# PAGES STATIQUES
# ==========================================

@app.get("/checkout-simulation.html")
async def read_checkout_simulation():
    raise HTTPException(status_code=403, detail="Le mode simulation est désactivé pour des raisons de sécurité. Tous les paiements passent par Stripe Checkout officiel.")

@app.get("/payment-success.html")
async def read_payment_success():
    return FileResponse("payment-success.html")

app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def read_index():
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    print("Démarrage de VerifIA sur http://localhost:8000")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
