// ============================================================
// Cloudflare Worker — Contact Form Handler
// Replaces: netlify/functions/contact.js
//
// Environment variables (set in Cloudflare dashboard):
//   MAILERLITE_API_KEY    — MailerLite API key
//   MAILERLITE_GROUP_ID   — MailerLite group ID
//   SITE_URL              — https://littlesmartgenius.com
//   ADMIN_EMAIL           — Your email address to receive contact messages
// ============================================================

const ML_BASE = "https://connect.mailerlite.com/api";

const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Content-Type": "application/json",
};

export default {
    async fetch(request, env) {
        // Handle CORS preflight
        if (request.method === "OPTIONS") {
            return new Response(null, { status: 204, headers: corsHeaders });
        }

        if (request.method !== "POST") {
            return new Response(JSON.stringify({ error: "Method not allowed" }), {
                status: 405, headers: corsHeaders,
            });
        }

        let data;
        try {
            data = await request.json();
        } catch {
            return new Response(JSON.stringify({ error: "Invalid JSON" }), {
                status: 400, headers: corsHeaders,
            });
        }

        const email = (data.email || "").trim();
        const name = (data.name || "").trim();
        const subject = (data.subject || "Contact from littlesmartgenius.com").trim();
        const message = (data.message || "").trim();

        if (!email || !message) {
            return new Response(JSON.stringify({ error: "Email and message are required" }), {
                status: 400, headers: corsHeaders,
            });
        }

        // ── Send notification email to admin via MailChannels ──
        try {
            await sendEmail({
                to: env.ADMIN_EMAIL || "contact@littlesmartgenius.com",
                from: "contact@littlesmartgenius.com",
                fromName: "Little Smart Genius Contact",
                subject: `[Contact] ${subject}`,
                html: `
                    <h2>New Contact Message</h2>
                    <p><strong>From:</strong> ${escapeHtml(name)} &lt;${escapeHtml(email)}&gt;</p>
                    <p><strong>Subject:</strong> ${escapeHtml(subject)}</p>
                    <hr/>
                    <p>${escapeHtml(message).replace(/\n/g, '<br>')}</p>
                    <hr/>
                    <p style="color:#999;font-size:12px;">Sent from littlesmartgenius.com contact form</p>
                `,
            });
        } catch (e) {
            console.error("Email send error:", e.message);
            // Don't block — continue to MailerLite
        }

        // ── Add to MailerLite ──
        if (env.MAILERLITE_API_KEY && env.MAILERLITE_GROUP_ID) {
            try {
                await fetch(`${ML_BASE}/subscribers`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Authorization": `Bearer ${env.MAILERLITE_API_KEY}`,
                    },
                    body: JSON.stringify({
                        email,
                        groups: [env.MAILERLITE_GROUP_ID],
                        fields: {
                            name,
                            last_message: `[${subject}] ${message}`.substring(0, 500),
                        },
                    }),
                });
            } catch (e) {
                console.error("MailerLite error:", e.message);
            }
        }

        return new Response(JSON.stringify({
            success: true,
            message: "Message received! We'll reply within 24h. 💛",
        }), { status: 200, headers: corsHeaders });
    },
};

// ── MailChannels Email Sender ──
async function sendEmail({ to, from, fromName, subject, html }) {
    const res = await fetch("https://api.mailchannels.net/tx/v1/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            personalizations: [{ to: [{ email: to }] }],
            from: { email: from, name: fromName },
            subject,
            content: [{ type: "text/html", value: html }],
        }),
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(`MailChannels error ${res.status}: ${text.substring(0, 200)}`);
    }
    return res;
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}
