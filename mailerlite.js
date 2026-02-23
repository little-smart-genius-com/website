/**
 * mailerlite.js — Client-side form handler for MailerLite
 * =========================================================
 * Detects environment automatically:
 *   - Local dev  → calls http://localhost:5555  (mailer_proxy.py)
 *   - Production → calls /subscribe and /contact (Netlify Functions)
 *
 * Features:
 *   - Newsletter subscribe (email → MailerLite group)
 *   - Contact form with math captcha anti-spam
 *   - Dual submit: MailerLite + Netlify Forms (email notifications)
 *
 * Usage: <script src="mailerlite.js" defer></script>
 */

(function () {
    "use strict";

    // ── Detect environment ──────────────────────────────────
    const isLocal = (
        location.hostname === "localhost" ||
        location.hostname === "127.0.0.1" ||
        location.protocol === "file:"
    );
    const PROXY_BASE = isLocal ? "http://localhost:5555" : "";
    const ENDPOINTS = {
        subscribe: isLocal ? `${PROXY_BASE}/subscribe` : `/.netlify/functions/subscribe`,
        contact: isLocal ? `${PROXY_BASE}/contact` : `/.netlify/functions/contact`,
    };

    // ── Utility ─────────────────────────────────────────────
    function setLoading(btn, loading) {
        btn.disabled = loading;
        btn._originalText = btn._originalText || btn.innerHTML;
        btn.innerHTML = loading
            ? '<span class="animate-pulse">Sending...</span>'
            : btn._originalText;
    }

    function showResult(container, success, message) {
        container.innerHTML = `
            <div class="mt-3 px-4 py-3 rounded-xl text-sm font-semibold ${success
                ? "bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-700"
                : "bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-700"
            }">
                ${success ? "✅" : "❌"} ${message}
            </div>`;
    }

    async function postForm(endpoint, payload) {
        const resp = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await resp.json();
        return { ok: resp.ok && data.success, message: data.message || data.error || "Unknown error" };
    }

    // ── Math Captcha ────────────────────────────────────────
    let captchaAnswer = null;

    function initCaptcha() {
        const questionEl = document.getElementById("captcha-question");
        const answerEl = document.getElementById("captcha-answer");
        const statusEl = document.getElementById("captcha-status");
        const submitBtn = document.getElementById("contact-submit-btn");

        if (!questionEl || !answerEl || !submitBtn) return;

        // Generate random math problem
        const ops = [
            { symbol: "+", fn: (a, b) => a + b },
            { symbol: "−", fn: (a, b) => a - b },
            { symbol: "×", fn: (a, b) => a * b },
        ];
        const op = ops[Math.floor(Math.random() * ops.length)];
        let a, b;
        if (op.symbol === "×") {
            a = Math.floor(Math.random() * 9) + 2;  // 2-10
            b = Math.floor(Math.random() * 9) + 2;  // 2-10
        } else if (op.symbol === "−") {
            a = Math.floor(Math.random() * 15) + 10; // 10-24
            b = Math.floor(Math.random() * 9) + 1;   // 1-9
        } else {
            a = Math.floor(Math.random() * 20) + 5;  // 5-24
            b = Math.floor(Math.random() * 15) + 3;  // 3-17
        }
        captchaAnswer = op.fn(a, b);
        questionEl.textContent = `${a} ${op.symbol} ${b} = `;

        // Validate on input
        answerEl.addEventListener("input", () => {
            const val = parseInt(answerEl.value, 10);
            if (isNaN(val)) {
                statusEl.textContent = "";
                submitBtn.disabled = true;
                return;
            }
            if (val === captchaAnswer) {
                statusEl.textContent = "✅";
                submitBtn.disabled = false;
                answerEl.classList.remove("border-red-400");
                answerEl.classList.add("border-green-400");
            } else {
                statusEl.textContent = "❌";
                submitBtn.disabled = true;
                answerEl.classList.remove("border-green-400");
                answerEl.classList.add("border-red-400");
            }
        });
    }

    function regenerateCaptcha() {
        const answerEl = document.getElementById("captcha-answer");
        const statusEl = document.getElementById("captcha-status");
        const submitBtn = document.getElementById("contact-submit-btn");
        if (answerEl) { answerEl.value = ""; answerEl.classList.remove("border-green-400", "border-red-400"); }
        if (statusEl) statusEl.textContent = "";
        if (submitBtn) submitBtn.disabled = true;
        initCaptcha();
    }

    // ── Netlify Forms dual-submit ───────────────────────────
    async function submitToNetlifyForms(payload) {
        try {
            const formData = new URLSearchParams();
            formData.append("form-name", "contact");
            formData.append("name", payload.name);
            formData.append("email", payload.email);
            formData.append("subject", payload.subject);
            formData.append("message", payload.message);
            await fetch("/", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: formData.toString(),
            });
        } catch (e) {
            // Netlify Forms submission is best-effort; don't block the UX
            console.warn("Netlify Forms submit failed (non-blocking):", e);
        }
    }

    // ── Newsletter form ─────────────────────────────────────
    function initNewsletter() {
        const form = document.getElementById("newsletter-form");
        if (!form) return;

        const btn = form.querySelector("[type=submit]");
        const result = document.getElementById("newsletter-result");
        if (!result) return;

        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = (form.querySelector("[name=email]") || form.querySelector("[type=email]"))?.value?.trim();
            if (!email) return;

            setLoading(btn, true);
            try {
                const { ok, message } = await postForm(ENDPOINTS.subscribe, { email });
                showResult(result, ok, message);
                if (ok) form.reset();
            } catch (err) {
                showResult(result, false, "Could not connect. Are you running mailer_proxy.py locally?");
                console.error(err);
            } finally {
                setLoading(btn, false);
            }
        });
    }

    // ── Contact form ────────────────────────────────────────
    function initContact() {
        const form = document.getElementById("contact-form");
        if (!form) return;

        const btn = document.getElementById("contact-submit-btn") || form.querySelector("[type=submit]");
        const result = document.getElementById("contact-result");
        if (!result) return;

        // Initialize captcha
        initCaptcha();

        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            // Double-check captcha
            const captchaInput = parseInt(document.getElementById("captcha-answer")?.value, 10);
            if (captchaAnswer === null || captchaInput !== captchaAnswer) {
                showResult(result, false, "Please solve the math problem correctly.");
                return;
            }

            const payload = {
                name: form.querySelector("[name=name]")?.value?.trim() || "",
                email: form.querySelector("[name=email]")?.value?.trim() || "",
                subject: form.querySelector("[name=subject]")?.value?.trim() || "Contact",
                message: form.querySelector("[name=message]")?.value?.trim() || "",
            };
            if (!payload.email || !payload.message) {
                showResult(result, false, "Please fill in email and message.");
                return;
            }

            setLoading(btn, true);
            try {
                // 1. Submit to MailerLite (subscriber + custom field)
                const { ok, message } = await postForm(ENDPOINTS.contact, payload);
                showResult(result, ok, message);

                // 2. Also submit to Netlify Forms (email notification)
                if (ok && !isLocal) {
                    await submitToNetlifyForms(payload);
                }

                if (ok) {
                    form.reset();
                    regenerateCaptcha(); // New captcha after successful submit
                }
            } catch (err) {
                showResult(result, false, "Could not connect. Please try again later.");
                console.error(err);
            } finally {
                setLoading(btn, false);
            }
        });
    }

    // ── Init ────────────────────────────────────────────────
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => { initNewsletter(); initContact(); });
    } else {
        initNewsletter();
        initContact();
    }
})();
