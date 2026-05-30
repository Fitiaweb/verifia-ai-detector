// Initialize Lucide icons
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

    // Input handling
    textInput.addEventListener('input', () => {
        const text = textInput.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        
        wordCount.textContent = `${words} mot${words > 1 ? 's' : ''}`;
        
        if (words >= 10) {
            analyzeBtn.removeAttribute('disabled');
        } else {
            analyzeBtn.setAttribute('disabled', 'true');
        }
    });

    // Mock API Analysis
    analyzeBtn.addEventListener('click', () => {
        const text = textInput.value.trim();
        if (!text) return;

        // Hide input footer, show loading
        analyzeBtn.parentElement.classList.add('hidden');
        textInput.disabled = true;
        resultDashboard.classList.add('hidden');
        loadingState.classList.remove('hidden');

        // Appel à la véritable API Backend
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
                showModal('paywallModal');
                resetBtn.click();
                return;
            }
            if (!response.ok) {
                throw new Error(data.detail || "Erreur serveur");
            }
            return data;
        })
        .then(data => {
            if (!data) return;
            if (data.status_code === 503) {
                alert(data.error);
                resetBtn.click();
            } else {
                displayAnalysis(text, data.ai_probability, data.source);
            }
        })
        .catch(error => {
            console.error('Erreur API:', error);
            alert(error.message || "Erreur de connexion au serveur.");
            resetBtn.click();
        });
    });

    // Reset
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

    function displayAnalysis(text, fakeAiProbability, source) {
        // Hide loading, show results
        loadingState.classList.add('hidden');
        resultDashboard.classList.remove('hidden');
        
        console.log("Source de l'analyse:", source);

        animateScore(fakeAiProbability);
        
        // Update stats
        const totalSentences = text.split(/[.!?]+/).length - 1 || 1;
        const aiSentences = Math.round((fakeAiProbability / 100) * totalSentences);
        
        aiSentencesStat.textContent = `${aiSentences} / ${totalSentences}`;
        
        if (fakeAiProbability > 70) {
            readabilityStat.textContent = 'Robotique';
        } else if (fakeAiProbability > 40) {
            readabilityStat.textContent = 'Complexe';
        } else {
            readabilityStat.textContent = 'Naturelle';
        }
    }

    function animateScore(targetScore) {
        let currentScore = 0;
        const duration = 1500; // 1.5s
        const interval = 20;
        const step = targetScore / (duration / interval);

        // Update stroke color based on score
        let strokeColor = 'var(--success)';
        if (targetScore > 75) strokeColor = 'var(--danger)';
        else if (targetScore > 40) strokeColor = 'var(--warning)';

        scoreCirclePath.style.stroke = strokeColor;
        
        if (targetScore > 75) scoreLabel.textContent = "Probabilité d'IA élevée";
        else if (targetScore > 40) scoreLabel.textContent = "Mix Humain/IA possible";
        else scoreLabel.textContent = "Texte probablement Humain";

        const timer = setInterval(() => {
            currentScore += step;
            if (currentScore >= targetScore) {
                currentScore = targetScore;
                clearInterval(timer);
            }
            
            // Format circle path
            scoreCirclePath.setAttribute('stroke-dasharray', `${currentScore}, 100`);
            scoreText.textContent = `${Math.round(currentScore)}%`;
        }, interval);
    }

    // Modal & Auth Logic
    const modalOverlay = document.getElementById('modalOverlay');
    const authModal = document.getElementById('authModal');
    const verifyModal = document.getElementById('verifyModal');
    const paywallModal = document.getElementById('paywallModal');
    
    const loginBtnNav = document.getElementById('loginBtnNav');
    const paywallLoginBtn = document.getElementById('paywallLoginBtn');
    
    // Auth elements
    const emailInput = document.getElementById('emailInput');
    const sendCodeBtn = document.getElementById('sendCodeBtn');
    const authError = document.getElementById('authError');
    
    const codeInput = document.getElementById('codeInput');
    const verifyCodeBtn = document.getElementById('verifyCodeBtn');
    const verifyError = document.getElementById('verifyError');
    
    // Pay elements
    const payBtn = document.getElementById('payBtn');
    const paywallError = document.getElementById('paywallError');
    
    let currentEmail = '';

    function hideAllModals() {
        modalOverlay.classList.add('hidden');
        authModal.classList.add('hidden');
        verifyModal.classList.add('hidden');
        paywallModal.classList.add('hidden');
        authError.classList.add('hidden');
        verifyError.classList.add('hidden');
        paywallError.classList.add('hidden');
    }

    function showModal(modalId) {
        hideAllModals();
        modalOverlay.classList.remove('hidden');
        document.getElementById(modalId).classList.remove('hidden');
    }

    // Global expose for fetch catch block
    window.showModal = showModal;

    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', hideAllModals);
    });

    if (loginBtnNav) {
        loginBtnNav.addEventListener('click', (e) => {
            e.preventDefault();
            showModal('authModal');
        });
    }

    if (paywallLoginBtn) {
        paywallLoginBtn.addEventListener('click', () => {
            showModal('authModal');
        });
    }

    if (sendCodeBtn) {
        sendCodeBtn.addEventListener('click', async () => {
            const email = emailInput.value.trim();
            if (!email) return;
            
            sendCodeBtn.disabled = true;
            authError.classList.add('hidden');
            
            try {
                const res = await fetch('/api/auth/request-code', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email})
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail);
                
                currentEmail = email;
                showModal('verifyModal');
            } catch (e) {
                authError.textContent = e.message;
                authError.classList.remove('hidden');
            } finally {
                sendCodeBtn.disabled = false;
            }
        });
    }

    // Helper pour mettre à jour l'interface utilisateur de la navbar
    function updateNavbarUI() {
        if (!loginBtnNav) return;
        
        const token = localStorage.getItem('token');
        const isPremium = localStorage.getItem('is_premium') === 'true';
        
        if (token) {
            if (isPremium) {
                loginBtnNav.innerHTML = `Mon Compte <span class="badge-pro"><i data-lucide="sparkles" style="width: 10px; height: 10px;"></i>Pro</span>`;
            } else {
                loginBtnNav.innerHTML = `Mon Compte`;
            }
        } else {
            loginBtnNav.textContent = "Connexion";
        }
        lucide.createIcons();
    }

    if (verifyCodeBtn) {
        verifyCodeBtn.addEventListener('click', async () => {
            const code = codeInput.value.trim();
            if (!code) return;
            
            verifyCodeBtn.disabled = true;
            verifyError.classList.add('hidden');
            
            try {
                const res = await fetch('/api/auth/verify-code', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: currentEmail, code})
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail);
                
                localStorage.setItem('token', data.token);
                localStorage.setItem('is_premium', data.is_premium);
                
                hideAllModals();
                updateNavbarUI();
                
                // Vérifier s'il y a une action d'abonnement en attente
                const pendingPlan = sessionStorage.getItem('pending_plan');
                if (pendingPlan) {
                    sessionStorage.removeItem('pending_plan');
                    startSubscriptionFlow(pendingPlan);
                } else {
                    alert("Connecté avec succès !");
                }
            } catch (e) {
                verifyError.textContent = e.message;
                verifyError.classList.remove('hidden');
            } finally {
                verifyCodeBtn.disabled = false;
            }
        });
    }

    // Lancer le flux d'abonnement Revolut (Création de session backend + Redirection)
    async function startSubscriptionFlow(plan) {
        const token = localStorage.getItem('token');
        if (!token) {
            // Mettre en mémoire le plan choisi et demander la connexion
            sessionStorage.setItem('pending_plan', plan);
            showModal('authModal');
            return;
        }

        try {
            // Identifier le bouton de tarification
            const btn = document.querySelector(`.plan-btn[data-plan="${plan}"]`) || payBtn;
            let originalHTML = "";
            if (btn) {
                originalHTML = btn.innerHTML;
                btn.disabled = true;
                btn.innerHTML = `<span class="loader" style="width: 16px; height: 16px; display: inline-block; margin-right: 8px;"></span> Redirection...`;
            }

            const res = await fetch('/api/payments/create-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ plan })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Erreur de création de commande.");
            
            // Rediriger le client vers le checkout Revolut (réel ou simulé)
            window.location.href = data.checkout_url;
        } catch (e) {
            alert(e.message || "Erreur lors du traitement du paiement.");
            console.error("Erreur de paiement:", e);
            
            // Restaurer le bouton
            const btn = document.querySelector(`.plan-btn[data-plan="${plan}"]`) || payBtn;
            if (btn && originalHTML) {
                btn.disabled = false;
                btn.innerHTML = originalHTML;
            }
        }
    }

    // Relier les boutons des cartes de tarification
    document.querySelectorAll('.plan-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const plan = e.currentTarget.getAttribute('data-plan');
            startSubscriptionFlow(plan);
        });
    });

    if (payBtn) {
        // Depuis le paywall, on souscrit par défaut à l'offre Annuelle Pro (le meilleur rapport qualité/prix !)
        payBtn.addEventListener('click', async () => {
            startSubscriptionFlow('annual');
        });
    }

    // Vérifier l'état de l'authentification et du premium au chargement de la page
    async function checkAuthStateOnLoad() {
        const token = localStorage.getItem('token');
        if (!token) {
            updateNavbarUI();
            return;
        }

        try {
            const res = await fetch('/api/auth/profile', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (res.ok) {
                const profile = await res.json();
                localStorage.setItem('is_premium', profile.is_premium);
            } else {
                // Token invalide ou expiré
                localStorage.removeItem('token');
                localStorage.removeItem('is_premium');
            }
        } catch (e) {
            console.error("Erreur de rafraîchissement profil:", e);
        } finally {
            updateNavbarUI();
        }
    }

    checkAuthStateOnLoad();
});
