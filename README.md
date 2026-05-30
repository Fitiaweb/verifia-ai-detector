# 🛡️ VerifIA - Détecteur de Contenu IA (SaaS complet)

**VerifIA** est un outil SaaS moderne, haut de gamme et performant, conçu pour analyser instantanément n'importe quel texte afin de détecter l'utilisation de modèles d'intelligence artificielle (comme ChatGPT, Claude, ou Gemini). 

L'application combine une **heuristique experte locale** (burstiness, diversité lexicale, tics linguistiques de l'IA) et le modèle officiel de pointe **Gemini 1.5 Flash** (via API) pour offrir une précision inégalée.

---

## 💎 Modèle Économique & Tarifs Stratégiques

Pour attirer les utilisateurs et maximiser les ventes, VerifIA propose une grille tarifaire très attractive :
*   **Offre Découverte (Gratuit)** : 3 analyses offertes (sans carte requise) pour tester la qualité de notre service avec l'expert local.
*   **Plan Pro Mensuel (4,99 € / mois)** : Analyses 100% illimitées via l'API neuronale Gemini, pas de limite de mots, sans aucun engagement. *Le prix d'un café par mois.*
*   **Plan Pro Annuel (29,99 € / an)** : Tout le contenu illimité et le support prioritaire pour seulement **2,50 € / mois** (soit **50 % d'économie** par rapport au plan mensuel). *Paiement unique, hautement incitatif.*

---

## 💳 Intégration Revolut Merchant (Double Mode)

VerifIA dispose d'une intégration complète avec la passerelle de paiement sécurisée **Revolut Merchant Gateway** :

1.  **Mode Réel (Production / Sandbox)** : Génère de véritables sessions de paiement Revolut conformes aux normes PCI-DSS, supportant les cartes de crédit, Apple Pay, Google Pay et Revolut Pay directement sur les pages hébergées de Revolut.
2.  **Mode Simulation Interactive** : Si aucune clé Revolut n'est configurée, l'application bascule en mode simulation avec une superbe interface de paiement fictive Revolut. Cela permet de tester de bout en bout l'expérience utilisateur et l'activation premium en local.

---

## 🛠️ Lancement Local et Test Rapide

### 1. Prérequis
Installez les dépendances Python nécessaires (FastAPI, Uvicorn, Google Generative AI) :
```bash
pip install fastapi uvicorn google-generativeai pydantic
```

### 2. Démarrer le serveur
Exécutez simplement le script `server.py` :
```bash
python server.py
```
Le serveur démarrera sur **`http://localhost:8000`**. Ouvrez ce lien dans votre navigateur.

---

## 🚀 Configuration en Mode Production (Revolut & Gemini)

Pour passer VerifIA en conditions réelles, configurez simplement vos variables d'environnement dans un fichier `.env` ou sur votre hébergeur :

```env
# Clé d'API officielle de Gemini
GEMINI_API_KEY="VOTRE_CLE_API_GEMINI"

# Vos identifiants Revolut Business (Merchant Portal)
REVOLUT_MERCHANT_TOKEN="VOTRE_CLE_API_REVOLUT"
REVOLUT_SANDBOX="False"
```

---

## 🌐 Hébergement et Déploiement Public

Le projet est livré clé en main, prêt pour la production.

### 1. Héberger le code sur GitHub (Findable depuis internet)
Pour rendre le projet trouvable sur internet, créez un dépôt vide sur votre compte GitHub (nom recommandé : `verifia-ai-detector`) puis exécutez ces commandes :
```bash
# Ajouter l'adresse de votre dépôt GitHub distant
git remote add origin https://github.com/VOTRE_PSEUDO/verifia-ai-detector.git

# Renommer la branche principale en main
git branch -M main

# Pousser votre projet sur GitHub
git push -u origin main
```

### 2. Déployer l'application en ligne gratuitement
Comme le projet comporte un serveur backend Python (FastAPI) et une base de données locale (SQLite), il ne peut pas être hébergé sur GitHub Pages (qui ne supporte que le HTML statique). En revanche, vous pouvez le déployer en **5 minutes et 100% gratuitement** sur l'un de ces hébergeurs :

#### Option A : Render.com (Recommandé & Ultra-simple)
1. Créez un compte gratuit sur [Render](https://render.com/).
2. Cliquez sur **New +** puis **Web Service**.
3. Connectez votre compte GitHub et sélectionnez votre dépôt `verifia-ai-detector`.
4. Configurez les informations suivantes :
   *   **Runtime** : `Python`
   *   **Build Command** : `pip install -r requirements.txt` (créez un fichier `requirements.txt` contenant `fastapi`, `uvicorn`, `google-generativeai`, `pydantic`).
   *   **Start Command** : `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. Ajoutez vos variables d'environnement dans l'onglet **Environment** (`GEMINI_API_KEY`, etc.).
6. Cliquez sur **Deploy**. Votre site sera en ligne avec une adresse gratuite du type `https://verifia-ai-detector.onrender.com` !

#### Option B : Railway.app
1. Créez un compte sur [Railway](https://railway.app/).
2. Cliquez sur **New Project** -> **Deploy from GitHub repo**.
3. Choisissez le dépôt `verifia-ai-detector`.
4. Ajoutez vos variables d'environnement dans Railway. Le déploiement s'effectue automatiquement en arrière-plan à chaque mise à jour sur GitHub !
