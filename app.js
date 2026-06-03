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
    const loginModal = document.getElementById('loginModal');
    const registerModal = document.getElementById('registerModal');
    const profileModal = document.getElementById('profileModal');
    const paywallModal = document.getElementById('paywallModal');
    
    const loginBtnNav = document.getElementById('loginBtnNav');
    const paywallLoginBtn = document.getElementById('paywallLoginBtn');
    
    // Switch links
    const toRegisterLink = document.getElementById('toRegisterLink');
    const toLoginLink = document.getElementById('toLoginLink');
    
    // Login form elements
    const loginEmail = document.getElementById('loginEmail');
    const loginPassword = document.getElementById('loginPassword');
    const loginSubmitBtn = document.getElementById('loginSubmitBtn');
    const loginError = document.getElementById('loginError');
    
    // Register form elements
    const regFirstName = document.getElementById('regFirstName');
    const regLastName = document.getElementById('regLastName');
    const regBirthDate = document.getElementById('regBirthDate');
    const regEmail = document.getElementById('regEmail');
    const regPassword = document.getElementById('regPassword');
    const strengthBar = document.getElementById('strengthBar');
    const strengthText = document.getElementById('strengthText');
    const registerSubmitBtn = document.getElementById('registerSubmitBtn');
    const registerError = document.getElementById('registerError');
    
    // Profile elements
    const logoutBtn = document.getElementById('logoutBtn');
    
    // Pay elements
    const payBtn = document.getElementById('payBtn');
    const paywallError = document.getElementById('paywallError');

    function hideAllModals() {
        modalOverlay.classList.add('hidden');
        loginModal.classList.add('hidden');
        registerModal.classList.add('hidden');
        profileModal.classList.add('hidden');
        paywallModal.classList.add('hidden');
        
        loginError.classList.add('hidden');
        registerError.classList.add('hidden');
        paywallError.classList.add('hidden');
    }

    function showModal(modalId) {
        hideAllModals();
        modalOverlay.classList.remove('hidden');
        document.getElementById(modalId).classList.remove('hidden');
    }

    window.showModal = showModal;

    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', hideAllModals);
    });

    // Link triggers
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

    // Modal navigation trigger
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

    if (paywallLoginBtn) {
        paywallLoginBtn.addEventListener('click', () => {
            showModal('loginModal');
        });
    }

    // Password strength visual indicator
    if (regPassword) {
        regPassword.addEventListener('input', () => {
            const val = regPassword.value;
            let score = 0;
            let feedback = "";
            
            if (val.length >= 8) score += 20;
            if (/[A-Z]/.test(val)) score += 20;
            if (/[a-z]/.test(val)) score += 20;
            if (/\d/.test(val)) score += 20;
            if (/[!@#$%^&*(),.?":{}|<>]/.test(val)) score += 20;
            
            let color = 'var(--danger)';
            if (val.length < 8) {
                feedback = "Mot de passe trop court (min 8)";
                color = 'var(--danger)';
                score = Math.min(score, 15);
            } else if (score < 60) {
                feedback = "Faible (ajoutez majuscules/chiffres)";
                color = 'var(--danger)';
            } else if (score < 100) {
                feedback = "Moyen (ajoutez un caractère spécial)";
                color = 'var(--warning)';
            } else {
                feedback = "Fort (Sécurisé)";
                color = 'var(--success)';
            }
            
            strengthBar.style.width = `${score}%`;
            strengthBar.style.backgroundColor = color;
            strengthText.textContent = feedback;
            strengthText.style.color = color;
        });
    }

    // Connect user (Login)
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
                if (!res.ok) throw new Error(data.detail || "Erreur lors de la connexion.");
                
                localStorage.setItem('token', data.token);
                localStorage.setItem('is_premium', data.is_premium);
                localStorage.setItem('first_name', data.first_name);
                
                hideAllModals();
                updateNavbarUI();
                
                // Subscription pending logic
                const pendingPlan = sessionStorage.getItem('pending_plan');
                if (pendingPlan) {
                    sessionStorage.removeItem('pending_plan');
                    startSubscriptionFlow(pendingPlan);
                } else {
                    alert(`Ravi de vous revoir, ${data.first_name} !`);
                }
            } catch (e) {
                loginError.textContent = e.message;
                loginError.classList.remove('hidden');
            } finally {
                loginSubmitBtn.disabled = false;
            }
        });
    }

    // Register user
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
                localStorage.setItem('is_premium', data.is_premium);
                localStorage.setItem('first_name', data.first_name);
                
                hideAllModals();
                updateNavbarUI();
                
                const pendingPlan = sessionStorage.getItem('pending_plan');
                if (pendingPlan) {
                    sessionStorage.removeItem('pending_plan');
                    startSubscriptionFlow(pendingPlan);
                } else {
                    alert(`Bienvenue sur VerifIA, ${first_name} !`);
                }
            } catch (e) {
                registerError.textContent = e.message;
                registerError.classList.remove('hidden');
            } finally {
                registerSubmitBtn.disabled = false;
            }
        });
    }

    // Profile Detail Modal Loader
    async function loadAndShowProfile() {
        const token = localStorage.getItem('token');
        if (!token) return;
        
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
                localStorage.setItem('first_name', profile.first_name);
                
                document.getElementById('profFullName').textContent = `${profile.first_name} ${profile.last_name}`;
                
                let formattedDate = profile.birth_date;
                try {
                    const dateParts = profile.birth_date.split('-');
                    if (dateParts.length === 3) {
                        formattedDate = `${dateParts[2]}/${dateParts[1]}/${dateParts[0]}`;
                    }
                } catch(e) {}
                document.getElementById('profBirthDate').textContent = formattedDate;
                document.getElementById('profEmail').textContent = profile.email;
                
                if (profile.is_premium) {
                    document.getElementById('profPlan').innerHTML = `Membre Pro <span class="badge-pro" style="margin-left: 10px;"><i data-lucide="sparkles" style="width: 10px; height: 10px;"></i>Pro</span>`;
                } else {
                    document.getElementById('profPlan').textContent = "Compte Standard (Gratuit)";
                }
                
                lucide.createIcons();
                showModal('profileModal');
            } else {
                localStorage.removeItem('token');
                localStorage.removeItem('is_premium');
                localStorage.removeItem('first_name');
                updateNavbarUI();
                showModal('loginModal');
            }
        } catch (e) {
            console.error("Erreur de chargement profil:", e);
            alert("Erreur de connexion lors du chargement du profil.");
        }
    }

    // Logout Action
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('token');
            localStorage.removeItem('is_premium');
            localStorage.removeItem('first_name');
            hideAllModals();
            updateNavbarUI();
            alert("Déconnexion réussie !");
        });
    }

    // Helper pour mettre à jour l'interface utilisateur de la navbar
    function updateNavbarUI() {
        if (!loginBtnNav) return;
        
        const token = localStorage.getItem('token');
        const isPremium = localStorage.getItem('is_premium') === 'true';
        const firstName = localStorage.getItem('first_name');
        
        if (token) {
            let label = firstName ? `Bonjour, ${firstName}` : `Mon Compte`;
            if (isPremium) {
                loginBtnNav.innerHTML = `${label} <span class="badge-pro"><i data-lucide="sparkles" style="width: 10px; height: 10px;"></i>Pro</span>`;
            } else {
                loginBtnNav.innerHTML = `${label}`;
            }
        } else {
            loginBtnNav.textContent = "Connexion";
        }
        lucide.createIcons();
    }

    // Lancer le flux d'abonnement Stripe (Création de session backend + Redirection)
    async function startSubscriptionFlow(plan) {
        const token = localStorage.getItem('token');
        if (!token) {
            sessionStorage.setItem('pending_plan', plan);
            showModal('loginModal');
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
            
            // Rediriger le client vers le checkout (Stripe)
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
                localStorage.setItem('first_name', profile.first_name);
            } else {
                // Token invalide ou expiré
                localStorage.removeItem('token');
                localStorage.removeItem('is_premium');
                localStorage.removeItem('first_name');
            }
        } catch (e) {
            console.error("Erreur de rafraîchissement profil:", e);
        } finally {
            updateNavbarUI();
        }
    }

    checkAuthStateOnLoad();
});
