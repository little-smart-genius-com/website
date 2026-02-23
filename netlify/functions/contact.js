// netlify/functions/contact.js
// Contact form handler:
//   1. Always submits to Netlify Forms SERVER-SIDE (reliable email notifications)
//   2. If MAILERLITE_API_KEY is set → also stores in MailerLite

const ML_BASE = "https://connect.mailerlite.com/api";
const API_KEY = process.env.MAILERLITE_API_KEY;
const GROUP_ID = process.env.MAILERLITE_GROUP_ID;
const SITE_URL = process.env.URL || "https://littlesmartgenius.com";

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

    // ── ALWAYS: Submit to Netlify Forms server-side ──
    // This ensures the submission appears in Netlify dashboard and triggers email notifications
    try {
        const formData = new URLSearchParams();
        formData.append("form-name", "contact");
        formData.append("name", name);
        formData.append("email", email);
        formData.append("subject", subject);
        formData.append("message", message);

        const nfRes = await fetch(`${SITE_URL}/contact.html`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData.toString(),
        });
        console.log("Netlify Forms server-side submit:", nfRes.status);
    } catch (e) {
        console.error("Netlify Forms submit error:", e.message);
        // Don't block — continue to return success
    }

    // ── OPTIONAL: MailerLite (if configured) ──
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

            await fetch(`${ML_BASE}/subscribers`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": `Bearer ${API_KEY}`,
                },
                body: JSON.stringify(payload),
            });
        } catch (e) {
            console.error("MailerLite exception:", e.message);
        }
    }

    console.log("Contact form processed:", { name, email, subject: subject.substring(0, 50) });

    return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
            success: true,
            message: "Message received! We'll reply within 24h. 💛",
        }),
    };
};
