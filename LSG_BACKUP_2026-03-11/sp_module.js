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

    if (!toast || !icon || !content) return;

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

    // Durée d'affichage (8 secondes) — track timeout so real toasts can cancel it
    if (_currentToastTimeout) clearTimeout(_currentToastTimeout);
    _currentToastTimeout = setTimeout(() => {
        toast.classList.remove('visible');
        _currentToastTimeout = null;
    }, 8000);
}

// --- Démarrage et Boucle Aléatoire ---

// Queue for real events (priority over fake ones)
const _realEventQueue = [];
let _currentToastTimeout = null;

function startRandomLoop() {
    // Priority: show real events first
    if (_realEventQueue.length > 0) {
        const realEvent = _realEventQueue.shift();
        _showRealToast(realEvent);
    } else {
        showSocialProof();
    }

    // Random delay 10-30 seconds
    const randomDelay = Math.floor(Math.random() * (30000 - 10000 + 1)) + 10000;
    setTimeout(startRandomLoop, randomDelay);
}

// Geo cache for real user country
let _userGeoCache = null;

async function _detectUserCountry() {
    if (_userGeoCache) return _userGeoCache;

    // Check sessionStorage first
    const cached = sessionStorage.getItem('lsg_user_geo');
    if (cached) {
        try { _userGeoCache = JSON.parse(cached); return _userGeoCache; } catch (e) { }
    }

    try {
        const resp = await fetch('https://ipapi.co/json/', { signal: AbortSignal.timeout(3000) });
        const data = await resp.json();
        if (data.country_name && data.country_code) {
            _userGeoCache = { name: data.country_name, code: data.country_code.toLowerCase() };
            sessionStorage.setItem('lsg_user_geo', JSON.stringify(_userGeoCache));
            return _userGeoCache;
        }
    } catch (e) { }

    // Fallback: use timezone to guess country
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
    const tzMap = {
        'America/New_York': { name: 'USA', code: 'us' },
        'America/Chicago': { name: 'USA', code: 'us' },
        'America/Los_Angeles': { name: 'USA', code: 'us' },
        'America/Denver': { name: 'USA', code: 'us' },
        'America/Toronto': { name: 'Canada', code: 'ca' },
        'America/Vancouver': { name: 'Canada', code: 'ca' },
        'Europe/London': { name: 'United Kingdom', code: 'gb' },
        'Europe/Paris': { name: 'France', code: 'fr' },
        'Europe/Berlin': { name: 'Germany', code: 'de' },
        'Australia/Sydney': { name: 'Australia', code: 'au' },
        'Australia/Melbourne': { name: 'Australia', code: 'au' },
        'Africa/Casablanca': { name: 'Morocco', code: 'ma' },
    };
    _userGeoCache = tzMap[tz] || { name: 'USA', code: 'us' };
    sessionStorage.setItem('lsg_user_geo', JSON.stringify(_userGeoCache));
    return _userGeoCache;
}

// Show a REAL event toast (from actual user activity)
async function _showRealToast(event) {
    const toast = document.getElementById('social-proof-toast');
    const icon = document.getElementById('sp-icon');
    const content = document.getElementById('sp-content');
    if (!toast || !icon || !content) return;

    const geo = await _detectUserCountry();
    const actionText = event.type === 'email' ? 'Just received' : 'Just downloaded';
    const actionIcon = event.type === 'email' ? '📧' : '📥';

    icon.innerText = actionIcon;
    content.innerHTML = `
        <div class="flex flex-col">
            <span class="text-[10px] text-green-500 font-bold uppercase tracking-wide mb-0.5 flex items-center gap-1">
                <img src="https://flagcdn.com/w40/${geo.code}.png"
                     srcset="https://flagcdn.com/w80/${geo.code}.png 2x"
                     width="16" height="12"
                     alt="${geo.name}"
                     class="rounded-[2px] shadow-sm object-cover"
                     style="display:inline-block; vertical-align:middle;">
                From ${geo.name}
                <svg class="w-3 h-3 ml-1" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
            </span>
            <span class="text-xs font-bold text-slate-700 dark:text-slate-200 leading-tight">
                ${actionText} <span class="text-brand">${event.name}</span>
            </span>
            <span class="text-[10px] text-slate-400 mt-1 font-mono tracking-tighter opacity-80">
                ${event.maskedEmail || ''}
            </span>
        </div>
    `;

    // Clear any existing timeout and show
    if (_currentToastTimeout) clearTimeout(_currentToastTimeout);
    toast.classList.add('visible');
    _currentToastTimeout = setTimeout(() => {
        toast.classList.remove('visible');
        _currentToastTimeout = null;
    }, 15000);
}

/**
 * Public API — Call this from freebies.html to show real activity.
 * @param {string} productName - Name of the freebie
 * @param {string} actionType - 'download' or 'email'
 * @param {string} [email] - User email (will be masked)
 * @param {number} [delay=0] - Delay in ms before showing (e.g. wait for modal to close)
 */
function showRealSocialProof(productName, actionType, email, delay) {
    // Mask the real email for privacy
    let masked = '';
    if (email) {
        const parts = email.split('@');
        if (parts.length === 2) {
            const user = parts[0];
            const domain = parts[1].split('.')[0];
            const stars = '*'.repeat(Math.floor(Math.random() * 5) + 5);
            const lastTwo = user.length >= 2 ? user.slice(-2) : user;
            masked = stars + lastTwo + '@' + domain + '.***';
        }
    }

    const event = { name: productName, type: actionType, maskedEmail: masked };

    function _interruptAndShow() {
        const toast = document.getElementById('social-proof-toast');
        // If a fake toast is currently showing, kill it immediately
        if (toast && toast.classList.contains('visible')) {
            if (_currentToastTimeout) { clearTimeout(_currentToastTimeout); _currentToastTimeout = null; }
            toast.classList.remove('visible');
            // Brief pause for hide transition, then show real toast
            setTimeout(() => { _showRealToast(event); }, 400);
        } else {
            _showRealToast(event);
        }
    }

    // If delay requested (e.g. wait for modal to close), schedule it
    if (delay && delay > 0) {
        setTimeout(_interruptAndShow, delay);
    } else {
        _interruptAndShow();
    }
}

// Premier lancement rapide après 3 secondes
setTimeout(startRandomLoop, 3000);