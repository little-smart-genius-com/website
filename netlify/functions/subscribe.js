// netlify/functions/subscribe.js
// Netlify serverless function — newsletter signup
// Environment variable MAILERLITE_API_KEY and MAILERLITE_GROUP_ID
// must be set in Netlify dashboard → Site settings → Environment variables

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
    if (!email || !email.includes("@")) {
        return { statusCode: 400, headers, body: JSON.stringify({ error: "Valid email required" }) };
    }

    const payload = {
        email,
        groups: [GROUP_ID],
        ...(data.name && { fields: { name: data.name } }),
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

    if (resp.status === 200 || resp.status === 201) {
        return { statusCode: 200, headers, body: JSON.stringify({ success: true, message: "You're subscribed! 🎉" }) };
    } else if (resp.status === 422) {
        return { statusCode: 200, headers, body: JSON.stringify({ success: true, message: "You're already subscribed!" }) };
    } else {
        console.error("MailerLite error:", resp.status, result);
        return { statusCode: 500, headers, body: JSON.stringify({ error: "Subscription failed. Please try again." }) };
    }
};
