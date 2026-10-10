# 🛡️ VerifIA - Détecteur de Contenu IA (SaaS Pay-As-You-Go)

**VerifIA** est un outil SaaS moderne conçu pour analyser et détecter l'utilisation de modèles d'intelligence artificielle (ChatGPT, GPT-4, Claude 3.5, Gemini) dans les textes.

---

## 💎 Modèle Économique & Tarification (Pay-As-You-Go)

* 🎁 **Essai Gratuit (3 Tests offerts)** : 3 analyses complètes offertes par utilisateur/IP, sans carte bancaire.
* ⚡ **Pack Découverte (1,00 €)** : +2 tests supplémentaires (0,50€ / test).
* ⭐ **Pack Populaire (2,00 €)** : +5 tests supplémentaires (0,40€ / test - Économie de 20%).
* 🔥 **Pack Économique (4,00 €)** : +10 tests supplémentaires (0,40€ / test - Idéal pour longs devoirs / mémoires).

*Aucun abonnement récurrent ni prélèvement automatique : les crédits sont utilisables sans limite de temps.*

---

## 💳 Système de Paiement (Double Mode)

1. **Mode Simulation Interactive** : Prêt à l'emploi sans configuration. Si aucune clé Stripe n'est renseignée, le parcours d'achat redirige vers une interface interactive de simulation avec validation des crédits.
2. **Mode Réel Stripe Checkout** : Renseignez simplement `STRIPE_API_KEY` dans votre fichier `.env` pour activer les paiements sécurisés par Carte Bancaire, Apple Pay et Google Pay.

---

## ⚙️ Configuration & Démarrage Local

### 1. Variables d'environnement
Créez un fichier `.env` à la racine (ou copiez `.env.example`) :
```env
# Clé d'API Google Gemini (Gratuite sur https://aistudio.google.com/app/apikey)
GEMINI_API_KEY="votre_cle_gemini"

# Clé secrète Stripe (Optionnelle, laisser vide pour le mode simulation)
STRIPE_API_KEY=""
```

### 2. Démarrer le serveur
```bash
python server.py
```
L'application démarre sur `http://localhost:8000`.

---

## 🌐 Déploiement : Vercel vs Render / Railway

### Est-ce une bonne idée d'héberger sur Vercel ?
* **Non pour le backend SQLite** : Vercel est une plateforme conçue pour le frontend (Next.js/React). Ses fonctions serverless sont **stateless (sans état persistant)**. Votre fichier de base de données `app.db` (utilisateurs, crédits) serait effacé ou verrouillé à chaque requête.
* **Recommandation optimale : Render.com ou Railway.app**
  * Ces plateformes font tourner le serveur Python FastAPI en continu.
  * Votre base de données SQLite ou PostgreSQL gratuite reste active en permanence.
  * Déploiement 100% gratuit en connectant votre dépôt GitHub.

---

## 🔍 Comment être visible sur Google pour "IA detector for free" ?

1. **Acheter un Nom de Domaine Personnalisé** (ex: `verif-ia.com` ou `detecteur-ia-gratuit.fr` à ~10€/an). Google favorise massivement les vrais noms de domaine par rapport aux sous-domaines gratuits (`.vercel.app` ou `.onrender.com`).
2. **Balises SEO & Schema Structuré** : `index.html` est déjà configuré avec les métadonnées OpenGraph, Twitter Cards et le balisage structuré `SoftwareApplication` de Schema.org.
3. **Section FAQ intégrée** : Une section FAQ ciblée sur les requêtes fréquentes ("Puis-je tester gratuitement ?", "Détecte-t-il ChatGPT ?") est incluse pour capter les Featured Snippets de Google.
4. **Google Search Console** : Dès que votre site est en ligne avec son nom de domaine, soumettez l'URL sur [Google Search Console](https://search.google.com/search-console) pour demander l'indexation immédiate.
