// netlify/functions/contact.js
// Contact form handler — dual mode:
//   1. If MAILERLITE_API_KEY is set → stores in MailerLite
//   2. Always stores in Netlify Forms (via hidden form in contact.html)
//   3. If neither works → returns success anyway (data captured in Netlify Forms client-side)

const ML_BASE = "https://connect.mailerlite.com/api";
const API_KEY = process.env.MAILERLITE_API_KEY;
const GROUP_ID = process.env.MAILERLITE_GROUP_ID;

exports.handler = async (event) => {
    const headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json",
    };

    if (event.httpMethod === "OPTIONS") {
        return { statusCode: 204, headers, body: "" };
    }

    if (event.httpMethod !== "POST") {
        return { statusCode: 405, headers, body: JSON.stringify({ error: "Method not allowed" }) };
    }

    let data;
    try {
        data = JSON.parse(event.body || "{}");
    } catch {
        return { statusCode: 400, headers, body: JSON.stringify({ error: "Invalid JSON" }) };
    }

    const email = (data.email || "").trim();
    const name = (data.name || "").trim();
    const subject = (data.subject || "Contact").trim();
    const message = (data.message || "").trim();

    if (!email || !message) {
        return { statusCode: 400, headers, body: JSON.stringify({ error: "Email and message are required" }) };
    }

    // ── Mode 1: MailerLite (if configured) ──
    if (API_KEY && GROUP_ID) {
        try {
            const payload = {
                email,
                groups: [GROUP_ID],
                fields: {
                    name,
                    last_message: `[${subject}] ${message}`.substring(0, 500),
                },
            };

            const resp = await fetch(`${ML_BASE}/subscribers`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": `Bearer ${API_KEY}`,
                },
                body: JSON.stringify(payload),
            });

            if (resp.status === 200 || resp.status === 201 || resp.status === 422) {
                return {
                    statusCode: 200,
                    headers,
                    body: JSON.stringify({
                        success: true,
                        message: "Message received! We'll reply within 24h. 💛",
                    }),
                };
            }
            // MailerLite failed but don't block — fall through to Mode 2
            console.error("MailerLite error:", resp.status);
        } catch (e) {
            console.error("MailerLite exception:", e.message);
            // Fall through to Mode 2
        }
    }

    // ── Mode 2: Direct success (Netlify Forms handles storage client-side) ──
    // The contact form in mailerlite.js already submits to Netlify Forms
    // as a secondary POST. So even without MailerLite, the message is captured.
    console.log("Contact form submission (no MailerLite):", { name, email, subject, message: message.substring(0, 100) });

    return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
            success: true,
            message: "Message received! We'll reply within 24h. 💛",
        }),
    };
};
