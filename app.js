// Initialisation des icônes Lucide
lucide.createIcons();

document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('textInput');
    const wordCount = document.getElementById('wordCount');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    const loadingState = document.getElementById('loadingState');
    const resultDashboard = document.getElementById('resultDashboard');
    
    const scoreCirclePath = document.getElementById('scoreCirclePath');
    const scoreText = document.getElementById('scoreText');
    const scoreLabel = document.getElementById('scoreLabel');
    const resetBtn = document.getElementById('resetBtn');
    
    const aiSentencesStat = document.getElementById('aiSentences');
    const readabilityStat = document.getElementById('readability');

    // Éléments d'affichage des crédits
    const navCreditsPill = document.getElementById('navCreditsPill');
    const navCreditsText = document.getElementById('navCreditsText');
    const inputCreditsText = document.getElementById('inputCreditsText');

    let currentCredits = 3;

    function updateCreditsUI(count, isLoggedIn = false) {
        currentCredits = count;
        const label = count === 1 ? '1 test' : `${count} tests`;
        const qualifier = isLoggedIn ? 'disponible' : 'gratuit';
        const qualifierPlural = isLoggedIn ? 'disponibles' : 'gratuits';
        const suffix = count > 1 ? qualifierPlural : qualifier;

        if (navCreditsText) {
            navCreditsText.textContent = `${label} ${suffix}`;
        }
        if (inputCreditsText) {
            if (count > 0) {
                inputCreditsText.textContent = `${label} ${suffix}`;
            } else {
                inputCreditsText.innerHTML = `<span style="color: var(--danger); font-weight: 600;">0 test restant - Cliquez pour recharger</span>`;
            }
        }

        if (navCreditsPill) {
            if (count <= 0) {
                navCreditsPill.classList.add('zero');
            } else {
                navCreditsPill.classList.remove('zero');
            }
        }
    }

    // Récupérer le nombre de crédits restants dès le chargement
    async function fetchCredits() {
        const token = localStorage.getItem('token');
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        try {
            const res = await fetch('/api/credits', { headers });
            if (res.ok) {
                const data = await res.json();
                updateCreditsUI(data.tests_remaining, data.is_logged_in);
            }
        } catch (e) {
            console.error("Erreur chargement crédits:", e);
        }
    }

    // Gestion de la saisie dans le textarea
    textInput.addEventListener('input', () => {
        const text = textInput.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        
        wordCount.textContent = `${words} mot${words > 1 ? 's' : ''}`;
        
        if (words >= 5) {
            analyzeBtn.removeAttribute('disabled');
        } else {
            analyzeBtn.setAttribute('disabled', 'true');
        }
    });

    // Clic sur l'indicateur de crédits pour recharger si à 0
    if (navCreditsPill) {
        navCreditsPill.addEventListener('click', () => {
            if (currentCredits <= 0) {
                showModal('paywallModal');
            } else {
                const pricingEl = document.getElementById('pricing');
                if (pricingEl) pricingEl.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }

    // Lancement de l'analyse
    analyzeBtn.addEventListener('click', () => {
        const text = textInput.value.trim();
        if (!text) return;

        // Si l'utilisateur est déjà à 0 crédit, on ouvre directement le paywall
        if (currentCredits <= 0) {
            showModal('paywallModal');
            return;
        }

        // Masquer le pied de page et afficher le loader
        analyzeBtn.parentElement.classList.add('hidden');
        textInput.disabled = true;
        resultDashboard.classList.add('hidden');
        loadingState.classList.remove('hidden');

        const token = localStorage.getItem('token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        fetch('/api/analyze', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ text: text })
        })
        .then(async response => {
            const data = await response.json();
            if (response.status === 402) {
                updateCreditsUI(0);
                showModal('paywallModal');
                resetBtn.click();
                return null;
            }
            if (!response.ok) {
                throw new Error(data.detail || "Erreur serveur");
            }
            return data;
        })
        .then(data => {
            if (!data) return;
            if (data.tests_remaining !== undefined) {
                updateCreditsUI(data.tests_remaining, data.is_logged_in);
            }
            displayAnalysis(text, data.ai_probability, data.source);
        })
        .catch(error => {
            console.error('Erreur API:', error);
            alert(error.message || "Erreur de connexion au serveur.");
            resetBtn.click();
        });
    });

    // Réinitialisation de l'analyse
    resetBtn.addEventListener('click', () => {
        textInput.value = '';
        textInput.disabled = false;
        wordCount.textContent = '0 mots';
        analyzeBtn.setAttribute('disabled', 'true');
        analyzeBtn.parentElement.classList.remove('hidden');
        resultDashboard.classList.add('hidden');
        scoreCirclePath.setAttribute('stroke-dasharray', '0, 100');
        scoreText.textContent = '0%';
        textInput.focus();
    });

    function displayAnalysis(text, aiProbability, source) {
        loadingState.classList.add('hidden');
        resultDashboard.classList.remove('hidden');

        animateScore(aiProbability);
        
        const totalSentences = text.split(/[.!?]+/).length - 1 || 1;
        const aiSentences = Math.round((aiProbability / 100) * totalSentences);
        
        aiSentencesStat.textContent = `${aiSentences} / ${totalSentences}`;
        
        if (aiProbability > 75) {
            readabilityStat.textContent = 'Robotique';
        } else if (aiProbability > 45) {
            readabilityStat.textContent = 'Mixte';
        } else {
            readabilityStat.textContent = 'Humaine';
        }
    }

    function animateScore(targetScore) {
        let currentScore = 0;
        const duration = 1400;
        const interval = 20;
        const step = targetScore / (duration / interval);

        let strokeColor = 'var(--success)';
        if (targetScore > 75) strokeColor = 'var(--danger)';
        else if (targetScore > 40) strokeColor = 'var(--warning)';

        scoreCirclePath.style.stroke = strokeColor;
        
        if (targetScore > 75) scoreLabel.textContent = "Probabilité d'IA élevée";
        else if (targetScore > 40) scoreLabel.textContent = "Mixte (IA / Humain)";
        else scoreLabel.textContent = "Texte probablement Humain";

        const timer = setInterval(() => {
            currentScore += step;
            if (currentScore >= targetScore) {
                currentScore = targetScore;
                clearInterval(timer);
            }
            
            scoreCirclePath.setAttribute('stroke-dasharray', `${currentScore}, 100`);
            scoreText.textContent = `${Math.round(currentScore)}%`;
        }, interval);
    }

    // ==========================================
    // GESTION DES MODALES ET AUTHENTIFICATION
    // ==========================================
    const modalOverlay = document.getElementById('modalOverlay');
    const loginModal = document.getElementById('loginModal');
    const registerModal = document.getElementById('registerModal');
    const profileModal = document.getElementById('profileModal');
    const paywallModal = document.getElementById('paywallModal');
    
    const loginBtnNav = document.getElementById('loginBtnNav');
    const toRegisterLink = document.getElementById('toRegisterLink');
    const toLoginLink = document.getElementById('toLoginLink');
    const paywallLoginLink = document.getElementById('paywallLoginLink');
    
    const loginEmail = document.getElementById('loginEmail');
    const loginPassword = document.getElementById('loginPassword');
    const loginSubmitBtn = document.getElementById('loginSubmitBtn');
    const loginError = document.getElementById('loginError');
    
    const regFirstName = document.getElementById('regFirstName');
    const regLastName = document.getElementById('regLastName');
    const regBirthDate = document.getElementById('regBirthDate');
    const regEmail = document.getElementById('regEmail');
    const regPassword = document.getElementById('regPassword');
    const strengthBar = document.getElementById('strengthBar');
    const strengthText = document.getElementById('strengthText');
    const registerSubmitBtn = document.getElementById('registerSubmitBtn');
    const registerError = document.getElementById('registerError');
    
    const logoutBtn = document.getElementById('logoutBtn');
    const profileBuyMoreBtn = document.getElementById('profileBuyMoreBtn');

    function hideAllModals() {
        modalOverlay.classList.add('hidden');
        loginModal.classList.add('hidden');
        registerModal.classList.add('hidden');
        profileModal.classList.add('hidden');
        paywallModal.classList.add('hidden');
        
        if (loginError) loginError.classList.add('hidden');
        if (registerError) registerError.classList.add('hidden');
    }

    function showModal(modalId) {
        hideAllModals();
        modalOverlay.classList.remove('hidden');
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.remove('hidden');
        lucide.createIcons();
    }

    window.showModal = showModal;

    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', hideAllModals);
    });

    if (toRegisterLink) {
        toRegisterLink.addEventListener('click', (e) => {
            e.preventDefault();
            showModal('registerModal');
        });
    }

    if (toLoginLink) {
        toLoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            showModal('loginModal');
        });
    }

    if (paywallLoginLink) {
        paywallLoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            showModal('loginModal');
        });
    }

    if (loginBtnNav) {
        loginBtnNav.addEventListener('click', (e) => {
            e.preventDefault();
            const token = localStorage.getItem('token');
            if (token) {
                loadAndShowProfile();
            } else {
                showModal('loginModal');
            }
        });
    }

    // Force du mot de passe
    if (regPassword) {
        regPassword.addEventListener('input', () => {
            const val = regPassword.value;
            let score = 0;
            if (val.length >= 8) score += 40;
            if (/[A-Z]/.test(val)) score += 20;
            if (/\d/.test(val)) score += 20;
            if (/[!@#$%^&*(),.?":{}|<>]/.test(val)) score += 20;
            
            let color = 'var(--danger)';
            let feedback = "Trop court";
            if (val.length < 8) {
                feedback = "Trop court (min 8 car.)";
                color = 'var(--danger)';
            } else if (score < 60) {
                feedback = "Moyen";
                color = 'var(--warning)';
            } else {
                feedback = "Fort & Sécurisé";
                color = 'var(--success)';
            }
            
            strengthBar.style.width = `${score}%`;
            strengthBar.style.backgroundColor = color;
            strengthText.textContent = feedback;
            strengthText.style.color = color;
        });
    }

    // Connexion
    if (loginSubmitBtn) {
        loginSubmitBtn.addEventListener('click', async () => {
            const email = loginEmail.value.trim();
            const password = loginPassword.value;
            
            if (!email || !password) {
                loginError.textContent = "Veuillez remplir tous les champs.";
                loginError.classList.remove('hidden');
                return;
            }
            
            loginSubmitBtn.disabled = true;
            loginError.classList.add('hidden');
            
            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Erreur de connexion.");
                
                localStorage.setItem('token', data.token);
                localStorage.setItem('first_name', data.first_name);
                localStorage.setItem('email', data.email);
                
                hideAllModals();
                updateNavbarUI();
                updateCreditsUI(data.credits, true);
                
                const pendingPlan = sessionStorage.getItem('pending_plan');
                if (pendingPlan) {
                    sessionStorage.removeItem('pending_plan');
                    startPackPurchase(pendingPlan);
                }
            } catch (e) {
                loginError.textContent = e.message;
                loginError.classList.remove('hidden');
            } finally {
                loginSubmitBtn.disabled = false;
            }
        });
    }

    // Inscription
    if (registerSubmitBtn) {
        registerSubmitBtn.addEventListener('click', async () => {
            const first_name = regFirstName.value.trim();
            const last_name = regLastName.value.trim();
            const birth_date = regBirthDate.value;
            const email = regEmail.value.trim();
            const password = regPassword.value;
            
            if (!first_name || !last_name || !birth_date || !email || !password) {
                registerError.textContent = "Veuillez remplir tous les champs.";
                registerError.classList.remove('hidden');
                return;
            }
            
            registerSubmitBtn.disabled = true;
            registerError.classList.add('hidden');
            
            try {
                const res = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({first_name, last_name, birth_date, email, password})
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Erreur de création de compte.");
                
                localStorage.setItem('token', data.token);
                localStorage.setItem('first_name', data.first_name);
                localStorage.setItem('email', data.email);
                
                hideAllModals();
                updateNavbarUI();
                updateCreditsUI(data.credits, true);
                
                const pendingPlan = sessionStorage.getItem('pending_plan');
                if (pendingPlan) {
                    sessionStorage.removeItem('pending_plan');
                    startPackPurchase(pendingPlan);
                } else {
                    alert(`Bienvenue ${first_name} ! Vos 3 tests gratuits sont prêts.`);
                }
            } catch (e) {
                registerError.textContent = e.message;
                registerError.classList.remove('hidden');
            } finally {
                registerSubmitBtn.disabled = false;
            }
        });
    }

    // Charger et afficher le profil
    async function loadAndShowProfile() {
        const token = localStorage.getItem('token');
        if (!token) return;
        
        try {
            const res = await fetch('/api/auth/profile', {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const profile = await res.json();
                document.getElementById('profFullName').textContent = `${profile.first_name} ${profile.last_name}`;
                document.getElementById('profEmail').textContent = profile.email;
                const creds = profile.credits !== undefined ? profile.credits : 0;
                document.getElementById('profCredits').textContent = `${creds} test${creds > 1 ? 's' : ''}`;
                
                showModal('profileModal');
            } else {
                localStorage.removeItem('token');
                updateNavbarUI();
                showModal('loginModal');
            }
        } catch (e) {
            console.error("Erreur profil:", e);
        }
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('token');
            localStorage.removeItem('first_name');
            localStorage.removeItem('email');
            hideAllModals();
            updateNavbarUI();
            fetchCredits();
        });
    }

    if (profileBuyMoreBtn) {
        profileBuyMoreBtn.addEventListener('click', () => {
            hideAllModals();
            const pricingEl = document.getElementById('pricing');
            if (pricingEl) pricingEl.scrollIntoView({ behavior: 'smooth' });
        });
    }

    function updateNavbarUI() {
        if (!loginBtnNav) return;
        const token = localStorage.getItem('token');
        const firstName = localStorage.getItem('first_name');
        
        if (token) {
            loginBtnNav.textContent = firstName ? `Bonjour, ${firstName}` : `Mon Compte`;
        } else {
            loginBtnNav.textContent = "Connexion";
        }
        lucide.createIcons();
    }

    // ==========================================
    // ACHAT DE PACKS DE TESTS
    // ==========================================
    async function startPackPurchase(plan) {
        const token = localStorage.getItem('token');
        let email = localStorage.getItem('email') || "";

        // Si l'utilisateur n'est pas connecté, demander son email pour lui attribuer ses tests
        if (!token && !email) {
            email = prompt("Veuillez saisir votre adresse e-mail pour recevoir vos tests :");
            if (!email || !email.includes('@')) {
                alert("Une adresse e-mail valide est requise pour créditer vos tests.");
                return;
            }
            localStorage.setItem('email', email);
        }

        try {
            const headers = { 'Content-Type': 'application/json' };
            if (token) headers['Authorization'] = `Bearer ${token}`;

            const res = await fetch('/api/payments/create-session', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ plan: plan, email: email })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Erreur de création de commande.");
            
            // Rediriger vers Stripe ou la simulation interactive
            window.location.href = data.checkout_url;
        } catch (e) {
            alert(e.message || "Erreur lors du traitement du paiement.");
            console.error("Erreur commande:", e);
        }
    }

    // Lier les boutons de la grille tarifaire
    document.querySelectorAll('.plan-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const plan = e.currentTarget.getAttribute('data-plan');
            startPackPurchase(plan);
        });
    });

    // Lier les choix de pack dans la modale de paywall
    document.querySelectorAll('.pack-choice-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const plan = e.currentTarget.getAttribute('data-plan');
            startPackPurchase(plan);
        });
    });

    // Initialisation au chargement
    updateNavbarUI();
    fetchCredits();
});
