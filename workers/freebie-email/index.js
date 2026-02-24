// ============================================================
// Cloudflare Worker — Freebie Email Sender (NEW)
// Sends the actual Drive download link to the user's email
//
// Environment variables (set in Cloudflare dashboard):
//   MAILERLITE_API_KEY  — MailerLite API key
//   MAILERLITE_GROUP_ID — MailerLite group ID
//   SITE_URL            — https://littlesmartgenius.com
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
        const productName = (data.productName || "").trim();
        const downloadLink = (data.downloadLink || "").trim();
        const productDesc = (data.productDesc || "").trim();

        if (!email || !productName || !downloadLink) {
            return new Response(JSON.stringify({ error: "email, productName and downloadLink are required" }), {
                status: 400, headers: corsHeaders,
            });
        }

        // Validate email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return new Response(JSON.stringify({ error: "Invalid email address" }), {
                status: 400, headers: corsHeaders,
            });
        }

        // ── Send freebie email via MailChannels ──
        const siteUrl = env.SITE_URL || "https://littlesmartgenius.com";
        const emailHtml = buildFreebieEmail({ productName, productDesc, downloadLink, siteUrl });

        let emailSent = false;
        try {
            await sendEmail({
                to: email,
                from: "freebies@littlesmartgenius.com",
                fromName: "Little Smart Genius",
                subject: `🎁 Your Free Download: ${productName}`,
                html: emailHtml,
            });
            emailSent = true;
        } catch (e) {
            console.error("Freebie email send error:", e.message);
        }

        // ── Add subscriber to MailerLite ──
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
                        fields: { last_freebie_downloaded: productName },
                    }),
                });
            } catch (e) {
                console.error("MailerLite error:", e.message);
            }
        }

        return new Response(JSON.stringify({
            success: true,
            emailSent,
            message: emailSent
                ? `📧 Email sent to ${email}! Check your inbox.`
                : `Download link: ${downloadLink}`,
            downloadLink,
        }), { status: 200, headers: corsHeaders });
    },
};

// ── Email builder ──
function buildFreebieEmail({ productName, productDesc, downloadLink, siteUrl }) {
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Free Download — Little Smart Genius</title>
</head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="580" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
          
          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#F48C06,#fbbf24);padding:32px;text-align:center;">
              <p style="color:#fff;font-size:32px;margin:0;font-weight:900;">🎓 Little Smart Genius</p>
              <p style="color:rgba(255,255,255,0.9);font-size:14px;margin:8px 0 0;">Your #1 resource for educational printables</p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:36px 40px;">
              <h1 style="color:#1e293b;font-size:22px;margin:0 0 8px;">🎁 Your freebie is ready!</h1>
              <p style="color:#64748b;font-size:15px;margin:0 0 24px;">Thank you for downloading from Little Smart Genius. Here's your free resource:</p>
              
              <!-- Product Card -->
              <table width="100%" cellpadding="0" cellspacing="0" style="background:#fef3c7;border-radius:12px;margin-bottom:28px;">
                <tr>
                  <td style="padding:20px 24px;">
                    <p style="color:#92400e;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin:0 0 6px;">FREE DOWNLOAD</p>
                    <p style="color:#1e293b;font-size:18px;font-weight:800;margin:0 0 6px;">${escapeHtml(productName)}</p>
                    ${productDesc ? `<p style="color:#64748b;font-size:13px;margin:0;">${escapeHtml(productDesc)}</p>` : ''}
                  </td>
                </tr>
              </table>

              <!-- Download Button -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center">
                    <a href="${downloadLink}" target="_blank" style="display:inline-block;background:linear-gradient(135deg,#F48C06,#ea580c);color:#ffffff;text-decoration:none;font-weight:800;font-size:16px;padding:16px 40px;border-radius:12px;letter-spacing:0.02em;">
                      📥 Download Your Freebie
                    </a>
                  </td>
                </tr>
              </table>

              <p style="color:#94a3b8;font-size:12px;text-align:center;margin:16px 0 0;">
                Link not working? Copy and paste this in your browser:<br>
                <span style="color:#F48C06;word-break:break-all;">${downloadLink}</span>
              </p>

              <hr style="border:none;border-top:1px solid #e2e8f0;margin:32px 0;">

              <p style="color:#64748b;font-size:14px;margin:0 0 16px;">
                Want more free educational resources for kids? Check out our full freebies library at <a href="${siteUrl}/freebies.html" style="color:#F48C06;font-weight:600;">littlesmartgenius.com</a>!
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f1f5f9;padding:20px 40px;text-align:center;">
              <p style="color:#94a3b8;font-size:11px;margin:0;">
                © 2026 Little Smart Genius. All rights reserved.<br>
                You received this email because you downloaded a free resource from our site.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;
}

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
        throw new Error(`MailChannels ${res.status}: ${text.substring(0, 200)}`);
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
