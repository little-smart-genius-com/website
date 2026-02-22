// netlify/functions/contact.js
// Netlify serverless function — contact form handler
// Stores the contact message as a MailerLite subscriber with a tag

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

    // Add subscriber with the contact message stored in a custom field
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

    const result = await resp.json();

    if (resp.status === 200 || resp.status === 201 || resp.status === 422) {
        return { statusCode: 200, headers, body: JSON.stringify({ success: true, message: "Message received! We'll reply within 24h. 💛" }) };
    } else {
        console.error("MailerLite contact error:", resp.status, result);
        return { statusCode: 500, headers, body: JSON.stringify({ error: "Failed to send. Please try again." }) };
    }
};
