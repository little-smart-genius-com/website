// ============================================================
// Cloudflare Worker — Newsletter Subscribe Handler
// Replaces: netlify/functions/subscribe.js
//
// Environment variables (set in Cloudflare dashboard):
//   MAILERLITE_API_KEY  — MailerLite API key
//   MAILERLITE_GROUP_ID — MailerLite group ID
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
        if (!email || !email.includes("@")) {
            return new Response(JSON.stringify({ error: "Valid email required" }), {
                status: 400, headers: corsHeaders,
            });
        }

        const payload = {
            email,
            groups: [env.MAILERLITE_GROUP_ID],
            ...(data.name && { fields: { name: data.name } }),
        };

        const resp = await fetch(`${ML_BASE}/subscribers`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": `Bearer ${env.MAILERLITE_API_KEY}`,
            },
            body: JSON.stringify(payload),
        });

        if (resp.status === 200 || resp.status === 201) {
            return new Response(JSON.stringify({ success: true, message: "You're subscribed! 🎉" }), {
                status: 200, headers: corsHeaders,
            });
        } else if (resp.status === 422) {
            return new Response(JSON.stringify({ success: true, message: "You're already subscribed!" }), {
                status: 200, headers: corsHeaders,
            });
        } else {
            const result = await resp.json().catch(() => ({}));
            console.error("MailerLite error:", resp.status, result);
            return new Response(JSON.stringify({ error: "Subscription failed. Please try again." }), {
                status: 500, headers: corsHeaders,
            });
        }
    },
};
