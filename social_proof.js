// social_proof.js

// 1. Liste pondérée des pays (USA, UK, CA, AU apparaissent 3x plus souvent)
const spCountries = [
    // --- LES "BIG 4" (Forte Fréquence x3) ---
    { name: "USA", code: "us" }, { name: "USA", code: "us" }, { name: "USA", code: "us" },
    { name: "United Kingdom", code: "gb" }, { name: "United Kingdom", code: "gb" }, { name: "United Kingdom", code: "gb" },
    { name: "Canada", code: "ca" }, { name: "Canada", code: "ca" }, { name: "Canada", code: "ca" },
    { name: "Australia", code: "au" }, { name: "Australia", code: "au" }, { name: "Australia", code: "au" },

    // --- AUTRES PAYS (Fréquence Normale x1) ---
    { name: "France", code: "fr" },
    { name: "Germany", code: "de" },
    { name: "Spain", code: "es" },
    { name: "Italy", code: "it" },
    { name: "Brazil", code: "br" },
    { name: "Japan", code: "jp" },
    { name: "Morocco", code: "ma" },
    { name: "India", code: "in" },
    { name: "Mexico", code: "mx" },
    { name: "Netherlands", code: "nl" },
    { name: "Sweden", code: "se" },
    { name: "Belgium", code: "be" },
    { name: "Switzerland", code: "ch" },
    { name: "UAE", code: "ae" },
    { name: "New Zealand", code: "nz" },
    { name: "Ireland", code: "ie" },
    { name: "South Africa", code: "za" }
];

// 2. Liste étendue de fournisseurs d'emails (Internationaux & Locaux)
const spProviders = [
    // Global
    "gmail", "gmail", "gmail", "hotmail", "outlook", "yahoo", "icloud", "me", "msn", "aol", "protonmail",
    // USA
    "comcast", "verizon", "sbcglobal", "att", "bellsouth", "cox",
    // UK
    "btinternet", "virginmedia", "sky", "talktalk", "blueyonder",
    // Canada
    "rogers", "sympatico", "shaw", "telus", "videotron",
    // Australia
    "bigpond", "optusnet", "iinet", "westnet", "ozemail",
    // Europe
    "orange", "wanadoo", "free", "t-online", "libero"
];

// 3. Générateur d'email masqué (Structure réaliste)
function generateMaskedEmail() {
    const provider = spProviders[Math.floor(Math.random() * spProviders.length)];
    
    // Extensions de domaine intelligentes selon le provider
    let tld = "com";
    if (["btinternet", "virginmedia", "sky", "talktalk", "blueyonder"].includes(provider)) tld = "co.uk";
    else if (["bigpond", "optusnet", "iinet", "westnet", "ozemail"].includes(provider)) tld = "com.au";
    else if (["rogers", "sympatico", "shaw", "telus", "videotron"].includes(provider)) tld = "ca";
    else if (["orange", "wanadoo", "free"].includes(provider)) tld = "fr";
    else if (provider === "t-online") tld = "de";
    else if (provider === "libero") tld = "it";

    const visibleChars = "abcdefghijklmnopqrstuvwxyz0123456789";
    const char1 = visibleChars[Math.floor(Math.random() * visibleChars.length)];
    const char2 = visibleChars[Math.floor(Math.random() * visibleChars.length)];
    
    // 5 à 9 astérisques aléatoires pour varier la longueur
    const stars = "*".repeat(Math.floor(Math.random() * 5) + 5);
    
    // On masque aussi le TLD pour plus de mystère : .***
    return `${stars}${char1}${char2}@${provider}.***`;
}

// 4. Fonction principale d'affichage
function showSocialProof() {
    // Sécurité : si les données ne sont pas encore là, on attend
    if (typeof activitiesData === 'undefined') return;

    // Sélection
    const countryObj = spCountries[Math.floor(Math.random() * spCountries.length)];
    const item = activitiesData[Math.floor(Math.random() * activitiesData.length)];
    const email = generateMaskedEmail();

    // DOM Elements
    const toast = document.getElementById('social-proof-toast');
    const icon = document.getElementById('sp-icon');
    const content = document.getElementById('sp-content');

    if(!toast || !icon || !content) return;

    // Mise à jour Icone
    icon.innerText = item.icon; 
    
    // Mise à jour Contenu (Avec Drapeau)
    content.innerHTML = `
        <div class="flex flex-col">
            <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wide mb-0.5 flex items-center gap-1.5">
                <img src="https://flagcdn.com/w40/${countryObj.code}.png" 
                     srcset="https://flagcdn.com/w80/${countryObj.code}.png 2x" 
                     width="16" height="12" 
                     alt="${countryObj.name}" 
                     class="rounded-[2px] shadow-sm object-cover" 
                     style="display:inline-block; vertical-align:middle;">
                From ${countryObj.name}
            </span>
            <span class="text-xs font-bold text-slate-700 dark:text-slate-200 leading-tight">
                Just downloaded <span class="text-brand">${item.name}</span>
            </span>
            <span class="text-[10px] text-slate-400 mt-1 font-mono tracking-tighter opacity-80">
                ${email}
            </span>
        </div>
    `;

    // Animation Entrée
    toast.classList.add('visible');

    // Durée d'affichage (8 secondes)
    setTimeout(() => {
        toast.classList.remove('visible');
    }, 8000); 
}

// --- Démarrage et Boucle Aléatoire ---

function startRandomLoop() {
    // 1. Lance l'affichage
    showSocialProof();

    // 2. Calcule un temps d'attente aléatoire entre 10s (10000ms) et 30s (30000ms)
    // Formule : Math.random() * (max - min) + min
    const randomDelay = Math.floor(Math.random() * (30000 - 10000 + 1)) + 10000;

    // 3. Planifie la prochaine exécution
    setTimeout(startRandomLoop, randomDelay);
}

// Premier lancement rapide après 3 secondes pour accrocher l'utilisateur
setTimeout(startRandomLoop, 3000);