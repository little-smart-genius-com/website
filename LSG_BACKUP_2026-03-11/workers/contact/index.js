// ============================================================
// Cloudflare Worker — Contact Form Handler V2
// Uses MailerLite automation instead of defunct MailChannels.
//
// Flow:
//   1. Receive contact form submission (POST JSON)
//   2. Add/update subscriber in MailerLite with contact message
//   3. Trigger MailerLite automation to notify admin
//
// Environment variables (set in Cloudflare dashboard):
//   MAILERLITE_API_KEY    — MailerLite API key
//   MAILERLITE_GROUP_ID   — MailerLite group ID for contacts
//   SITE_URL              — https://littlesmartgenius.com
//   ADMIN_EMAIL           — Admin email (for reference)
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

        const errors = [];

        // ── Step 1: Add subscriber to MailerLite with contact info ──
        if (env.MAILERLITE_API_KEY && env.MAILERLITE_GROUP_ID) {
            try {
                const mlResp = await fetch(`${ML_BASE}/subscribers`, {
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
                            name: name || "Anonymous",
                            last_name: "",
                            company: `[CONTACT] ${subject}`,
                            // Store message in a custom field with preserved newlines
                            contact_message: `Sujet : ${subject}\n\nMessage :\n${message}`.substring(0, 500),
                        },
                        status: "active",
                    }),
                });

                const mlData = await mlResp.json();
                if (mlResp.ok || mlResp.status === 200 || mlResp.status === 201) {
                    console.log("MailerLite subscriber added/updated:", mlData.data?.id);
                } else {
                    console.error("MailerLite error:", JSON.stringify(mlData));
                    errors.push(`MailerLite: ${mlData.message || mlResp.status}`);
                }
            } catch (e) {
                console.error("MailerLite exception:", e.message);
                errors.push(`MailerLite exception: ${e.message}`);
            }
        }

        // ── Step 2: Send webhook to Make.com for email notification ──
        if (env.MAKECOM_WEBHOOK_URL) {
            try {
                const webhookResp = await fetch(env.MAKECOM_WEBHOOK_URL, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        type: "contact_form",
                        from_name: name,
                        from_email: email,
                        subject: subject,
                        message: message,
                        timestamp: new Date().toISOString(),
                        site: "littlesmartgenius.com",
                    }),
                });
                console.log("Webhook sent:", webhookResp.status);
            } catch (e) {
                console.error("Webhook error:", e.message);
                // Non-blocking, continue
            }
        }

        // ── Step 3: Send admin notification via MailerLite campaign API ──
        // As a fallback, we create a subscriber-level event that triggers automation
        if (env.MAILERLITE_API_KEY) {
            try {
                // Use the MailerLite "batch" endpoint to update subscriber with event
                const adminEmail = env.ADMIN_EMAIL || "contact@littlesmartgenius.com";

                // Add admin as subscriber too (if not already) with the contact data
                await fetch(`${ML_BASE}/subscribers`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Authorization": `Bearer ${env.MAILERLITE_API_KEY}`,
                    },
                    body: JSON.stringify({
                        email: adminEmail,
                        fields: {
                            name: "Admin",
                            contact_message: `Sujet : ${subject}\nDe : ${name} <${email}>\n\nMessage :\n${message}\n\nDate : ${new Date().toISOString()}`.substring(0, 500),
                        },
                        status: "active",
                    }),
                });
                console.log("Admin subscriber updated with contact message");
            } catch (e) {
                console.error("Admin notification error:", e.message);
            }
        }

        return new Response(JSON.stringify({
            success: true,
            message: "Message received! We'll reply within 24h. 💛",
        }), { status: 200, headers: corsHeaders });
    },
};

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}
