// ============================================================
// Cloudflare Worker — Freebie Email Sender
// ============================================================

const ML_BASE = "https://connect.mailerlite.com/api";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Content-Type": "application/json",
};

// ── Database of Download Links (SECURED IN WORKER) ──────────
const productData = {
  // LOGIC
  "Tic Tac Toe": {
    link: "https://drive.google.com/uc?export=download&id=1sLEHa4hVNhslv_fMlBpwJglPqjTr7Ml-",
    desc: "A classic strategy game that helps children develop critical thinking and sportsmanship skills."
  },
  "Tic Tac Logic": {
    link: "https://drive.google.com/uc?export=download&id=1q5IV1sr6boFx-qncyx-2zUGZCzXqJcdf",
    desc: "A step up from the classic! This puzzle challenges spatial reasoning and logic planning."
  },
  "Nurikabe": {
    link: "https://drive.google.com/uc?export=download&id=1yA6hqRGsqXviBHtNMdBZkgmXgdVXgoUQ",
    desc: "A Japanese logic puzzle forming islands. Excellent for developing concentration and patience."
  },
  "Hitori": {
    link: "https://drive.google.com/uc?export=download&id=14_Y0LCX51aDYUZIybjSORMZIIudmikWj",
    desc: "Eliminate duplicate numbers in this engaging grid puzzle. Perfect for math logic practice."
  },
  "Kakurasu": {
    link: "https://drive.google.com/uc?export=download&id=1V1MtGt_gOCP58OS_rGIhlq68xRerYVfm",
    desc: "Combine logic and addition sums in this unique puzzle. Great for strengthening mental math."
  },
  "Shikaku": {
    link: "https://drive.google.com/uc?export=download&id=1JfjM0sOj6fK30fmzFRtCKy3hZGidOWVx",
    desc: "Divide the grid into rectangles. A fantastic visual-spatial geometry exercise for kids."
  },
  "Four In A Row": {
    link: "https://drive.google.com/uc?export=download&id=1KgY8T7Y45zUCa0PQy1h0gKDKgnPO85Pb",
    desc: "Connect four pieces to win. Builds strategic forward-thinking and pattern recognition."
  },
  "Skyscraper": {
    link: "https://drive.google.com/uc?export=download&id=1Si2HCW7TI46ALGZ00iPnp0bn28bbNdG1",
    desc: "Build a city skyline using logic. A fun twist on Sudoku that kids love."
  },
  "Mine Finder": {
    link: "https://drive.google.com/uc?export=download&id=1Aa3v8jSlt1zZCQX996KMT874KtuQrx4E",
    desc: "Clear the grid without detonating mines. Teaches risk assessment and deductive reasoning."
  },
  "Warships": {
    link: "https://drive.google.com/uc?export=download&id=1eoLfCNkbrpNkUn1yLpwAc6UC1nwHd90f",
    desc: "Locate the hidden fleet. A classic game of deduction and coordinate tracking."
  },
  "Logic Puzzle (Adult)": {
    link: "https://drive.google.com/uc?export=download&id=1RqBwqNktyLq4LpGdzWYV7mkX6jvA5Wou",
    desc: "Advanced logic grids for older students and adults to keep the mind sharp."
  },

  // WORDS
  "ABC Path": {
    link: "https://drive.google.com/uc?export=download&id=1fP3wwtHPJHeUa4SQbf_PJqUJACsONVYx",
    desc: "Trace the alphabet through the grid. Reinforces letter sequencing and pathfinding."
  },
  "Hangman": {
    link: "https://drive.google.com/uc?export=download&id=1qvvb77Gxp6iUtcKtmTu365MpuZAvg2tU",
    desc: "Guess the word before it's too late! Expands vocabulary and spelling skills."
  },
  "Word Search": {
    link: "https://drive.google.com/uc?export=download&id=1jkLi6Wpv3fq7KZbQTBIV_-1U2Yge3LMl",
    desc: "Find hidden words in the grid. Improves pattern recognition and vocabulary."
  },
  "Crossword": {
    link: "https://drive.google.com/uc?export=download&id=1VyLYHAPtmvoGGnw0Ts-E7KKl2qw1HM72",
    desc: "Solve clues to fill the grid. The ultimate test of general knowledge and spelling."
  },
  "Missing Vowels": {
    link: "https://drive.google.com/uc?export=download&id=1qKWXAuCpczgeI3Qkqn5XU2zmnL2RuixW",
    desc: "Fill in the missing vowels to complete words. Great for phonics and reading fluency."
  },
  "Word Scramble": {
    link: "https://drive.google.com/uc?export=download&id=1qwX7X0Fih8EnNbvDVV0WpVqMKqcNBhmF",
    desc: "Unscramble the letters to reveal words. Boosts spelling and cognitive flexibility."
  },
  "Cryptogram": {
    link: "https://drive.google.com/uc?export=download&id=1I-oUCstYz-0tcRFAtEyZcLd64xrcMHCw",
    desc: "Decode the secret message. A fun introduction to codes and ciphers."
  },
  "Complete the Word": {
    link: "https://drive.google.com/uc?export=download&id=1O_-kEScVVgl41EIiPZN2pILqsFL7EXAU",
    desc: "Finish the partial words. Helps with vocabulary recall and spelling confidence."
  },
  "Spot Correct Spelling": {
    link: "https://drive.google.com/uc?export=download&id=18svQ97GBrcdCx82RORGu982EJzTajhx8",
    desc: "Identify the correctly spelled word. Essential practice for standardized tests."
  },
  "Bi-Lingual Matching": {
    link: "https://drive.google.com/uc?export=download&id=1IJxeHu1bAadhFZa9qR-lZAmqsiIyM9ku",
    desc: "Match words across two languages. Perfect for ESL students and language learners."
  },

  // MATH
  "Sudoku": {
    link: "https://drive.google.com/uc?export=download&id=1kMsX9yB_YhSkC_isuQoo_8Lg8JZfwgld",
    desc: "The classic number placement puzzle. Builds pure logic and deductive skills."
  },
  "CalcuDoku": {
    link: "https://drive.google.com/uc?export=download&id=17bIZJ3tBbh3u_NvVVABsRut57H5dohzA",
    desc: "Sudoku meets math operations. Fun way to practice addition, subtraction, multiplication, and division."
  },
  "Kids Math Equations": {
    link: "https://drive.google.com/uc?export=download&id=1PjoEBsMxS_eSW-H4Uql_wKv9IrOJfQUD",
    desc: "Solve the equations to clear the board. Direct practice for arithmetic fluency."
  },
  "Counting Numbers": {
    link: "https://drive.google.com/uc?export=download&id=1hodAjxXzxzrjuijnsphu7jIowu2lN46t",
    desc: "Fun counting exercises for early learners to build number sense."
  },
  "Range Puzzle": {
    link: "https://drive.google.com/uc?export=download&id=1jUnHqtq-y5roFYBSb4y5hw40FjF_QMfM",
    desc: "Determine the range and placement of numbers. Advanced logical thinking for math."
  },
  "One Hundred Puzzle": {
    link: "https://drive.google.com/uc?export=download&id=1BKcqK7IOmrWZd4nZRbBShba0Mduhb_8-",
    desc: "Work with the 100-chart to find patterns. Essential for understanding number relationships."
  },

  // CREATIVE
  "Stickers Pack": {
    link: "https://drive.google.com/uc?export=download&id=1xqBtCb6QPID7MmTzfcJBiGmyXalMECNk",
    desc: "Printable stickers for rewards and decoration. Adds fun to any notebook!"
  },
  "Clip Art Set": {
    link: "https://drive.google.com/uc?export=download&id=1hCOsB-cX81kqsD1BMxHAoANBhhjiSzLk",
    desc: "High-quality clipart for student projects and classroom decorations."
  },
  "Coloring Page (Kids)": {
    link: "https://drive.google.com/uc?export=download&id=1WuFF1fYLt6ah2Xgcd_Y-wOMprrunC473",
    desc: "Engaging illustrations to color. Improves fine motor skills and creativity."
  },
  "Coloring Page (Adult)": {
    link: "https://drive.google.com/uc?export=download&id=12UpsVEr0vrbGMkd5bS156F_zyVM36M3b",
    desc: "Intricate designs for relaxation and mindfulness. Take a break and create art."
  },
  "Cookbook for Kids": {
    link: "https://drive.google.com/uc?export=download&id=1iCIyaTwdiOCZi5ZyWuSQsH_bRrbjg-kR",
    desc: "Simple, safe recipes for young chefs. Teaches following instructions and measurements."
  },
  "Joke Book for Kids": {
    link: "https://drive.google.com/uc?export=download&id=1Isik52YmevUpuueZJobQKkylU9TIOY0n",
    desc: "Clean, funny jokes to keep the classroom laughing. Great for reading practice."
  },
  "Activity Book": {
    link: "https://drive.google.com/uc?export=download&id=1CvIBdbWc9rn4wa65i5N5yvxBCgLxNeB8",
    desc: "A mixed collection of puzzles and games. Perfect for road trips or rainy days."
  },
  "Spot the Difference": {
    link: "https://drive.google.com/uc?export=download&id=1mJatCxHXsG_LbVAUyHcvuGbhpNTuuPLJ",
    desc: "Find the subtle differences between images. Sharps observation and attention to detail."
  },
  "Shadow Matching": {
    link: "https://drive.google.com/uc?export=download&id=12920MbVWqFsKN7PQbtRJlnQ2N2aStW2z",
    desc: "Match the object to its shadow. A critical pre-reading visual discrimination skill."
  },
  "Maze for Kids": {
    link: "https://drive.google.com/uc?export=download&id=16TVMRA-ynjzluisizspL2Gy7mWNCxwPU",
    desc: "Navigate the labyrinth to the exit. Develops problem-solving and pen control."
  },

  // PACKS
  "Full Freebie Pack": {
    link: "https://drive.google.com/uc?export=download&id=1Gdvmp2gBTbj_194tN5SXHN68IKhODZgu",
    desc: "The complete collection of all our current free resources in one click."
  },
  "Creative Pack": {
    link: "https://drive.google.com/uc?export=download&id=1dTue-BzNZ08s9ndIVT59QQhCXwPz-GM9",
    desc: "A bundle of all art, coloring, and creative activities."
  },
  "Logic Pack": {
    link: "https://drive.google.com/uc?export=download&id=17GU3eZUUvpPoDbJnSaNavoRfUWUBWWbX",
    desc: "A bundle of all logic grids and strategy puzzles."
  },
  "Math Pack": {
    link: "https://drive.google.com/uc?export=download&id=1FnMwDNyxKiwkHak7aqAiIW_-Jmz9bqsh",
    desc: "A bundle of all numerical and arithmetic puzzles."
  },
  "Word Pack": {
    link: "https://drive.google.com/uc?export=download&id=1zIROJhLpbo3iNQ_MlkccV_RmadtwnMTo",
    desc: "A bundle of all vocabulary and spelling games."
  }
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

    let body;
    try {
      body = await request.json();
    } catch {
      return new Response(JSON.stringify({ error: "Invalid JSON" }), {
        status: 400, headers: corsHeaders,
      });
    }

    const email = (body.email || "").trim();
    const productName = (body.productName || "").trim();

    if (!email || !productName) {
      return new Response(JSON.stringify({ error: "email and productName are required" }), {
        status: 400, headers: corsHeaders,
      });
    }

    // Validate email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return new Response(JSON.stringify({ error: "Invalid email" }), {
        status: 400, headers: corsHeaders,
      });
    }

    // Get product data from database
    const info = productData[productName];
    if (!info) {
      return new Response(JSON.stringify({ error: "Product not found" }), {
        status: 404, headers: corsHeaders,
      });
    }

    const downloadLink = info.link;
    const productDesc = info.desc;

    // ── Send email via MailChannels ──
    const siteUrl = env.SITE_URL || "https://littlesmartgenius.com";
    const emailHtml = buildFreebieEmail({ productName, productDesc, downloadLink, siteUrl });

    let emailSent = false;
    let error = null;

    try {
      await sendEmail({
        to: email,
        from: "freebies@littlesmartgenius.com",
        fromName: "Little Smart Genius",
        subject: `🎁 Your Free Download: ${productName}`,
        html: emailHtml,
        apiKey: env.RESEND_API_KEY,
      });
      emailSent = true;
    } catch (e) {
      console.error("Email error:", e.message);
      error = e.message;
    }

    // ── Add/Update MailerLite ──
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
      success: emailSent,
      message: emailSent
        ? `📧 Email sent to ${email}!`
        : `Error sending email: ${error}`,
      downloadLink: downloadLink // Still returned as fallback
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

// ── Resend Email Sender ──
async function sendEmail({ to, from, fromName, subject, html, apiKey }) {
  if (!apiKey) {
    throw new Error("RESEND_API_KEY is missing from environment variables.");
  }

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      from: `${fromName} <${from}>`,
      to: [to],
      subject: subject,
      html: html,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    console.error("Resend raw error:", text);
    throw new Error(`Resend ${res.status}: ${text}`);
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
