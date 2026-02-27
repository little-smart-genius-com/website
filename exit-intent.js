/**
 * Exit-Intent Popup — Little Smart Genius
 * Shows a non-intrusive popup offering free resources when a visitor
 * (without saved email) tries to leave the page.
 * Include this script on ALL pages via <script src="exit-intent.js"></script>
 */
(function () {
    'use strict';

    // Only show for desktop (mouseleave detection)
    // On mobile, show after 60 seconds of browsing instead
    const SHOW_DELAY_MOBILE = 60000;
    const SESSION_KEY = 'lsg_exit_shown';
    const EMAIL_KEY = 'lsg_user_data';

    // Don't show if user already has email stored
    function hasStoredEmail() {
        const dataStr = localStorage.getItem(EMAIL_KEY);
        if (!dataStr) return false;
        try {
            const data = JSON.parse(dataStr);
            if (new Date().getTime() > data.expiry) {
                localStorage.removeItem(EMAIL_KEY);
                return false;
            }
            return true;
        } catch (e) { return false; }
    }

    // Don't show more than once per session
    function alreadyShown() {
        return sessionStorage.getItem(SESSION_KEY) === 'true';
    }

    function markShown() {
        sessionStorage.setItem(SESSION_KEY, 'true');
    }

    // Inject CSS + HTML
    function createPopup() {
        const style = document.createElement('style');
        style.textContent = `
            #exit-popup-overlay {
                display: none;
                position: fixed;
                inset: 0;
                background: rgba(0,0,0,0.5);
                backdrop-filter: blur(4px);
                z-index: 9999;
                align-items: center;
                justify-content: center;
                opacity: 0;
                transition: opacity 0.3s;
            }
            #exit-popup-overlay.active {
                display: flex;
                opacity: 1;
            }
            #exit-popup-card {
                background: #fff;
                border-radius: 24px;
                max-width: 440px;
                width: 90%;
                padding: 40px 30px 30px;
                text-align: center;
                position: relative;
                box-shadow: 0 25px 60px rgba(0,0,0,0.15);
                transform: scale(0.9) translateY(20px);
                transition: transform 0.3s ease;
                border: 1px solid #E2E8F0;
            }
            #exit-popup-overlay.active #exit-popup-card {
                transform: scale(1) translateY(0);
            }
            .dark #exit-popup-card {
                background: #1E293B;
                border-color: #334155;
            }
            #exit-popup-close {
                position: absolute;
                top: 12px;
                right: 16px;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                border: none;
                background: #F1F5F9;
                color: #94A3B8;
                font-size: 18px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
            }
            .dark #exit-popup-close {
                background: #334155;
                color: #94A3B8;
            }
            #exit-popup-close:hover {
                background: #FEE2E2;
                color: #EF4444;
            }
            .exit-popup-emoji { font-size: 48px; margin-bottom: 16px; }
            .exit-popup-title {
                font-size: 22px;
                font-weight: 800;
                color: #1E293B;
                margin-bottom: 8px;
                font-family: 'Outfit', sans-serif;
            }
            .dark .exit-popup-title { color: #F8FAFC; }
            .exit-popup-desc {
                font-size: 14px;
                color: #64748B;
                line-height: 1.6;
                margin-bottom: 24px;
                max-width: 360px;
                margin-left: auto;
                margin-right: auto;
            }
            .exit-popup-cta {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 14px 32px;
                background: #F48C06;
                color: #fff;
                font-weight: 700;
                font-size: 14px;
                border: none;
                border-radius: 14px;
                cursor: pointer;
                transition: all 0.2s;
                text-decoration: none;
                box-shadow: 0 4px 15px rgba(244,140,6,0.3);
                font-family: 'Outfit', sans-serif;
            }
            .exit-popup-cta:hover {
                filter: brightness(1.1);
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(244,140,6,0.4);
            }
            .exit-popup-subtext {
                margin-top: 14px;
                font-size: 11px;
                color: #94A3B8;
            }
        `;
        document.head.appendChild(style);

        // Detect if we are inside a subfolder (e.g. articles/) and adjust link prefix
        var linkPrefix = '';
        var pathParts = window.location.pathname.replace(/\\/g, '/').split('/');
        // If the HTML file is inside a subfolder like /articles/xxx.html, we need ../
        if (pathParts.length > 2 && pathParts[pathParts.length - 2] === 'articles') {
            linkPrefix = '../';
        }

        const overlay = document.createElement('div');
        overlay.id = 'exit-popup-overlay';
        overlay.innerHTML = `
            <div id="exit-popup-card">
                <button id="exit-popup-close" title="Close">×</button>
                <div class="exit-popup-emoji">🎁</div>
                <div class="exit-popup-title">Wait! Don't Leave Empty-Handed!</div>
                <p class="exit-popup-desc">
                    We have <strong>40+ free educational printables</strong> waiting for you — 
                    puzzles, worksheets, coloring pages and more. 
                    It's <strong style="color:#F48C06">100% free</strong>, no strings attached!
                </p>
                <a class="exit-popup-cta" href="${linkPrefix}freebies.html">
                    🎉 Grab My Free Resources
                </a>
                <p class="exit-popup-subtext">New free content added every Sunday!</p>
            </div>
        `;
        document.body.appendChild(overlay);

        // Close handlers
        document.getElementById('exit-popup-close').addEventListener('click', closePopup);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) closePopup();
        });

        // If already on freebies page, change CTA
        if (window.location.pathname.includes('freebies')) {
            const cta = overlay.querySelector('.exit-popup-cta');
            cta.textContent = '📥 Browse & Download Now';
            cta.href = '#activities-grid';
            cta.addEventListener('click', function () {
                closePopup();
            });
        }
    }

    function showPopup() {
        if (hasStoredEmail() || alreadyShown()) return;
        markShown();

        const overlay = document.getElementById('exit-popup-overlay');
        if (!overlay) return;
        overlay.style.display = 'flex';
        requestAnimationFrame(() => {
            overlay.classList.add('active');
        });

        // GA4 event
        if (typeof gtag === 'function') {
            gtag('event', 'exit_intent_shown', {
                'event_category': 'engagement',
                'event_label': window.location.pathname
            });
        }
    }

    function closePopup() {
        const overlay = document.getElementById('exit-popup-overlay');
        if (!overlay) return;
        overlay.classList.remove('active');
        setTimeout(() => { overlay.style.display = 'none'; }, 300);
    }

    // Desktop: detect mouse leaving viewport (top)
    function initDesktop() {
        let triggered = false;
        document.addEventListener('mouseleave', function (e) {
            if (e.clientY < 5 && !triggered) {
                triggered = true;
                showPopup();
            }
        });
    }

    // Mobile: show after 60 seconds of browsing
    function initMobile() {
        setTimeout(() => {
            showPopup();
        }, SHOW_DELAY_MOBILE);
    }

    // Init
    function init() {
        if (hasStoredEmail() || alreadyShown()) return;

        createPopup();

        if (window.matchMedia('(hover: hover)').matches) {
            initDesktop();
        } else {
            initMobile();
        }
    }

    // Wait for DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
