// ============================================================
// Cloudflare Worker — Admin API
// Replaces: netlify/functions/admin-api.js
//
// Environment variables (set in Cloudflare dashboard):
//   GITHUB_PAT       — GitHub Personal Access Token
//   GITHUB_REPO      — little-smart-genius-com/website
//   ADMIN_PASSWORD   — Dashboard admin password
//   SITE_URL         — https://littlesmartgenius.com
//   MAKECOM_WEBHOOK_URL — Make.com webhook URL
// ============================================================

// Global map to keep track of Pollinations keys that return 402/429.
// Maps key -> timestamp of when it was blacklisted.
// Keys are automatically recycled after KEY_COOLDOWN_MS (1 hour).
const deadPollinationsKeys = new Map();
const KEY_COOLDOWN_MS = 7 * 24 * 60 * 60 * 1000; // 1 week TTL

const GITHUB_API = "https://api.github.com";
const BRANCH = "main";

const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Content-Type": "application/json",
};

// ── GitHub API helpers ──────────────────────────────────────

async function ghFetch(path, opts = {}, env) {
    const PAT = env.GITHUB_PAT;
    const REPO = env.GITHUB_REPO || "little-smart-genius-com/website";
    const url = path.startsWith("http") ? path : `${GITHUB_API}/repos/${REPO}/${path}`;
    return fetch(url, {
        ...opts,
        headers: {
            Authorization: `Bearer ${PAT}`,
            Accept: "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "LittleSmartGenius-Admin",
            ...(opts.headers || {}),
        },
    });
}

async function ghJSON(path, env) {
    const res = await ghFetch(path, {}, env);
    if (!res.ok) throw new Error(`GitHub ${res.status}`);
    return res.json();
}

async function ghFileContent(path, env) {
    try {
        const data = await ghJSON(`contents/${path}?ref=${BRANCH}`, env);
        if (data.content) {
            return {
                content: atob(data.content.replace(/\n/g, "")),
                sha: data.sha,
                size: data.size,
            };
        }
        return { content: null, sha: null, size: 0 };
    } catch {
        return { content: null, sha: null, size: 0 };
    }
}

async function ghDeleteFile(path, sha, message, env) {
    return ghFetch(`contents/${path}`, {
        method: "DELETE",
        body: JSON.stringify({ message, sha, branch: BRANCH }),
    }, env);
}

async function ghListDir(path, env) {
    try {
        const data = await ghJSON(`contents/${path}?ref=${BRANCH}`, env);
        return Array.isArray(data) ? data : [];
    } catch {
        return [];
    }
}

async function ghUpdateFile(path, content, sha, message, env) {
    return ghFetch(`contents/${path}`, {
        method: "PUT",
        body: JSON.stringify({
            message,
            content: btoa(unescape(encodeURIComponent(content))),
            sha,
            branch: BRANCH,
        }),
    }, env);
}

// ── Auth check ──────────────────────────────────────────────

function checkAuth(request, env) {
    const auth = request.headers.get("Authorization") || "";
    const token = auth.replace("Bearer ", "");
    const ADMIN_PASS = env.ADMIN_PASSWORD || "";
    if (!ADMIN_PASS || token !== ADMIN_PASS) {
        return new Response(JSON.stringify({ error: "Unauthorized" }), {
            status: 401, headers: corsHeaders,
        });
    }
    return null;
}

// ═══════════════════════════════════════════════════════════
// GOOGLE ANALYTICS 4 (OAUTH JWT NATIVE IMPLEMENTATION)
// ═══════════════════════════════════════════════════════════

function str2ab(str) {
    const buf = new ArrayBuffer(str.length);
    const bufView = new Uint8Array(buf);
    for (let i = 0, strLen = str.length; i < strLen; i++) bufView[i] = str.charCodeAt(i);
    return buf;
}

function base64UrlEncode(str) {
    return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function arrayBufferToBase64Url(buffer) {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
    return base64UrlEncode(binary);
}

async function getGoogleAccessToken(env) {
    const clientEmail = env.GA_CLIENT_EMAIL;
    const privateKey = env.GA_PRIVATE_KEY;
    if (!clientEmail || !privateKey) return null;

    let pemContents = privateKey;
    pemContents = pemContents.replace(/\\n/g, '');
    pemContents = pemContents.replace(/-----BEGIN PRIVATE KEY-----/g, '');
    pemContents = pemContents.replace(/-----END PRIVATE KEY-----/g, '');
    pemContents = pemContents.replace(/-----BEGIN RSA PRIVATE KEY-----/g, '');
    pemContents = pemContents.replace(/-----END RSA PRIVATE KEY-----/g, '');
    pemContents = pemContents.replace(/\s/g, '');

    let binaryDer;
    try {
        binaryDer = atob(pemContents);
    } catch (e) {
        console.error("Failed to base64 decode private key:", e);
        return null;
    }

    const cryptoKey = await crypto.subtle.importKey(
        "pkcs8", str2ab(binaryDer),
        { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
        false, ["sign"]
    );

    const header = { alg: "RS256", typ: "JWT" };
    const now = Math.floor(Date.now() / 1000);
    const claim = {
        iss: clientEmail,
        scope: "https://www.googleapis.com/auth/analytics.readonly",
        aud: "https://oauth2.googleapis.com/token",
        exp: now + 3600,
        iat: now
    };

    const encodedHeader = base64UrlEncode(JSON.stringify(header));
    const encodedClaim = base64UrlEncode(JSON.stringify(claim));
    const signatureInput = `${encodedHeader}.${encodedClaim}`;

    const signature = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", cryptoKey, new TextEncoder().encode(signatureInput));
    const encodedSignature = arrayBufferToBase64Url(signature);
    const jwt = `${signatureInput}.${encodedSignature}`;

    const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}`
    });
    const tokenData = await tokenRes.json();
    return tokenData.access_token || null;
}

async function fetchGa4Metrics(env) {
    const propertyId = env.GA_PROPERTY_ID;
    if (!propertyId) return { error: "Missing GA_PROPERTY_ID" };

    try {
        const token = await getGoogleAccessToken(env);
        if (!token) return { error: "Failed to generate access token" };

        const payload = {
            dateRanges: [
                { name: "day", startDate: "today", endDate: "today" },
                { name: "week", startDate: "7daysAgo", endDate: "today" },
                { name: "month", startDate: "30daysAgo", endDate: "today" }
            ],
            dimensions: [{ name: "dateRange" }],
            metrics: [
                { name: "activeUsers" },
                { name: "screenPageViews" },
                { name: "averageSessionDuration" }
            ],
            keepEmptyRows: true
        };

        const res = await fetch(`https://analyticsdata.googleapis.com/v1beta/properties/${propertyId}:runReport`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errText = await res.text();
            throw new Error(`GA4 API Error: ${errText}`);
        }

        const data = await res.json();
        const result = {
            day: { visitors: 0, views: 0 },
            week: { visitors: 0, views: 0 },
            month: { visitors: 0, views: 0 },
            avgTime: 0
        };

        if (data.rows && data.rows.length > 0) {
            data.rows.forEach(row => {
                const rangeName = row.dimensionValues[0].value;
                const metrics = row.metricValues;
                if (result[rangeName]) {
                    result[rangeName].visitors = parseInt(metrics[0].value, 10);
                    result[rangeName].views = parseInt(metrics[1].value, 10);
                }
                if (rangeName === "month") {
                    result.avgTime = parseFloat(metrics[2].value);
                }
            });
            return result;
        }
        return result;
    } catch (e) {
        console.error("GA4 Fetch Error:", e);
        return { error: e.message };
    }
}

async function fetchGa4Realtime(env) {
    const propertyId = env.GA_PROPERTY_ID;
    if (!propertyId) return { activeUsers: 0 };

    try {
        const token = await getGoogleAccessToken(env);
        if (!token) return { activeUsers: 0 };

        // Query 1: Total active users
        const totalPayload = {
            metrics: [{ name: "activeUsers" }]
        };

        // Query 2: Active users by country + city (real-time geo)
        const geoPayload = {
            dimensions: [{ name: "country" }, { name: "city" }],
            metrics: [{ name: "activeUsers" }],
            orderBys: [{ metric: { metricName: "activeUsers" }, desc: true }],
            limit: 20
        };

        const [totalRes, geoRes] = await Promise.all([
            fetch(`https://analyticsdata.googleapis.com/v1beta/properties/${propertyId}:runRealtimeReport`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
                body: JSON.stringify(totalPayload)
            }),
            fetch(`https://analyticsdata.googleapis.com/v1beta/properties/${propertyId}:runRealtimeReport`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
                body: JSON.stringify(geoPayload)
            })
        ]);

        let activeUsers = 0;
        if (totalRes.ok) {
            const data = await totalRes.json();
            if (data.rows && data.rows.length > 0) {
                activeUsers = parseInt(data.rows[0].metricValues[0].value, 10);
            }
        }

        const liveVisitors = [];
        if (geoRes.ok) {
            const data = await geoRes.json();
            if (data.rows) {
                data.rows.forEach(row => {
                    const country = row.dimensionValues[0].value;
                    const city = row.dimensionValues[1].value;
                    const users = parseInt(row.metricValues[0].value, 10);
                    if (country && country !== '(not set)') {
                        liveVisitors.push({ country, city: city === '(not set)' ? '' : city, users });
                    }
                });
            }
        }

        return { activeUsers, liveVisitors };
    } catch (e) {
        console.error("GA4 Realtime Fetch Error:", e);
        return { activeUsers: 0, liveVisitors: [] };
    }
}

async function fetchGa4Geo(env) {
    const propertyId = env.GA_PROPERTY_ID;
    if (!propertyId) return { countries: [], cities: [] };

    try {
        const token = await getGoogleAccessToken(env);
        if (!token) return { countries: [], cities: [] };

        const countryPayload = {
            dateRanges: [{ startDate: "30daysAgo", endDate: "today" }],
            dimensions: [{ name: "country" }],
            metrics: [
                { name: "activeUsers" },
                { name: "screenPageViews" }
            ],
            orderBys: [{ metric: { metricName: "activeUsers" }, desc: true }],
            limit: 20
        };

        const cityPayload = {
            dateRanges: [{ startDate: "30daysAgo", endDate: "today" }],
            dimensions: [{ name: "city" }, { name: "country" }],
            metrics: [
                { name: "activeUsers" },
                { name: "screenPageViews" }
            ],
            orderBys: [{ metric: { metricName: "activeUsers" }, desc: true }],
            limit: 15
        };

        const [countryRes, cityRes] = await Promise.all([
            fetch(`https://analyticsdata.googleapis.com/v1beta/properties/${propertyId}:runReport`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
                body: JSON.stringify(countryPayload)
            }),
            fetch(`https://analyticsdata.googleapis.com/v1beta/properties/${propertyId}:runReport`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
                body: JSON.stringify(cityPayload)
            })
        ]);

        const countries = [];
        if (countryRes.ok) {
            const data = await countryRes.json();
            if (data.rows) {
                data.rows.forEach(row => {
                    countries.push({
                        country: row.dimensionValues[0].value,
                        users: parseInt(row.metricValues[0].value, 10),
                        views: parseInt(row.metricValues[1].value, 10)
                    });
                });
            }
        }

        const cities = [];
        if (cityRes.ok) {
            const data = await cityRes.json();
            if (data.rows) {
                data.rows.forEach(row => {
                    const city = row.dimensionValues[0].value;
                    if (city && city !== '(not set)') {
                        cities.push({
                            city,
                            country: row.dimensionValues[1].value,
                            users: parseInt(row.metricValues[0].value, 10),
                            views: parseInt(row.metricValues[1].value, 10)
                        });
                    }
                });
            }
        }

        return { countries, cities };
    } catch (e) {
        console.error("GA4 Geo Error:", e);
        return { countries: [], cities: [], error: e.message };
    }
}

// ═══════════════════════════════════════════════════════════
// LIST ARTICLES
// ═══════════════════════════════════════════════════════════

async function listArticles(env) {
    const SITE_URL = env.SITE_URL || "https://littlesmartgenius.com";
    const { content } = await ghFileContent("articles.json", env);
    if (!content) return { articles: [], total: 0 };

    const data = JSON.parse(content);
    let articles = data.articles || [];

    // ── Deduplicate by slug: keep the LAST (most recent) entry ──
    const slugMap = new Map();
    articles.forEach(a => { if (a.slug) slugMap.set(a.slug, a); });
    articles = Array.from(slugMap.values());

    const [htmlFiles, imgFiles, igFiles, postFiles] = await Promise.all([
        ghListDir("articles", env),
        ghListDir("images", env),
        ghListDir("instagram", env),
        ghListDir("posts", env),
    ]);

    const htmlSet = new Set(htmlFiles.map(f => f.name));
    const postSlugs = new Set(postFiles.map(f => {
        const m = f.name.match(/^(.+)-\d+\.json$/);
        return m ? m[1] : f.name.replace(".json", "");
    }));

    const enriched = articles.map(a => {
        const slug = a.slug || "";
        const hasHtml = htmlSet.has(`${slug}.html`);
        const hasPost = postSlugs.has(slug);

        // the 'image' field has the exact cover filename, e.g. 'images/long-seo-slug-cover-1234.webp'
        let imageSlug = slug;
        let imageTimestamp = "";
        if (a.image && a.image.includes('-cover')) {
            const coverName = a.image.replace('images/', '');
            imageSlug = coverName.split('-cover')[0];
            // Extract the timestamp from the cover filename (e.g. '-cover-1772737299.webp' → '1772737299')
            const tsMatch = coverName.match(/-cover-(\d+)/);
            if (tsMatch) imageTimestamp = tsMatch[1];
        }

        // Filter images: if we have a timestamp, only match files with THAT timestamp
        // This prevents showing stale images from previous regenerations
        let coverImgs, contentImgs;
        if (imageTimestamp) {
            coverImgs = imgFiles.filter(f => f.name.startsWith(imageSlug) && f.name.includes("-cover") && f.name.includes(imageTimestamp) && !f.name.includes("-thumb"));
            contentImgs = imgFiles.filter(f => f.name.startsWith(imageSlug) && f.name.includes("-img") && f.name.includes(imageTimestamp));
        } else {
            // Fallback: no timestamp found, use original broad matching
            coverImgs = imgFiles.filter(f => f.name.startsWith(imageSlug) && f.name.includes("-cover") && !f.name.includes("-thumb"));
            contentImgs = imgFiles.filter(f => f.name.startsWith(imageSlug) && f.name.includes("-img"));
        }

        // Sort content images by index (img1, img2, img3...)
        contentImgs.sort((a, b) => {
            const idxA = parseInt((a.name.match(/-img(\d+)/) || [0, 0])[1]);
            const idxB = parseInt((b.name.match(/-img(\d+)/) || [0, 0])[1]);
            return idxA - idxB;
        });
        const igPost = igFiles.filter(f => f.name.startsWith(slug));
        let health = "ok";
        if (!hasHtml) health = "error";
        else if (coverImgs.length === 0) health = "error";
        else if (!hasPost) health = "warning";
        return {
            ...a, hasHtml, hasPost,
            coverCount: coverImgs.length, contentImgCount: contentImgs.length,
            coverFiles: coverImgs.map(f => f.name),
            contentImgFiles: contentImgs.map(f => f.name),
            imageCount: coverImgs.length + contentImgs.length,
            hasInstagram: igPost.length > 0, igCount: igPost.length,
            health, viewUrl: `${SITE_URL}/articles/${slug}.html`,
        };
    });
    return { articles: enriched, total: enriched.length };
}

// ═══════════════════════════════════════════════════════════
// CASCADE DELETE
// ═══════════════════════════════════════════════════════════

async function cascadeDelete(slug, env) {
    if (!slug) throw new Error("Missing slug parameter");
    const deleted = [], errors = [];
    const [htmlFiles, postFiles, imgFiles, igFiles] = await Promise.all([
        ghListDir("articles", env), ghListDir("posts", env),
        ghListDir("images", env), ghListDir("instagram", env),
    ]);
    const toDelete = [];
    htmlFiles.filter(f => f.name === `${slug}.html`).forEach(f => toDelete.push({ path: `articles/${f.name}`, sha: f.sha }));
    postFiles.filter(f => f.name.startsWith(slug)).forEach(f => toDelete.push({ path: `posts/${f.name}`, sha: f.sha }));
    imgFiles.filter(f => f.name.startsWith(slug)).forEach(f => toDelete.push({ path: `images/${f.name}`, sha: f.sha }));
    igFiles.filter(f => f.name.startsWith(slug)).forEach(f => toDelete.push({ path: `instagram/${f.name}`, sha: f.sha }));

    for (const file of toDelete) {
        try { await ghDeleteFile(file.path, file.sha, `Dashboard: delete ${slug}`, env); deleted.push(file.path); }
        catch (e) { errors.push({ path: file.path, error: e.message }); }
    }

    try {
        const { content: ajContent, sha: ajSha } = await ghFileContent("articles.json", env);
        if (ajContent) {
            const ajData = JSON.parse(ajContent);
            ajData.articles = (ajData.articles || []).filter(a => a.slug !== slug);
            ajData.total_articles = ajData.articles.length;
            await ghUpdateFile("articles.json", JSON.stringify(ajData, null, 2), ajSha, `Dashboard: remove ${slug} from articles.json`, env);
            deleted.push("articles.json (entry removed)");
        }
    } catch (e) { errors.push({ path: "articles.json", error: e.message }); }

    try {
        const { content: siContent, sha: siSha } = await ghFileContent("search_index.json", env);
        if (siContent) {
            const siData = JSON.parse(siContent);
            siData.articles = (siData.articles || []).filter(a => a.slug !== slug);
            siData.total_articles = siData.articles.length;
            await ghUpdateFile("search_index.json", JSON.stringify(siData, null, 2), siSha, `Dashboard: remove ${slug} from search_index.json`, env);
            deleted.push("search_index.json (entry removed)");
        }
    } catch (e) { errors.push({ path: "search_index.json", error: e.message }); }

    try {
        const { content: smContent, sha: smSha } = await ghFileContent("sitemap.xml", env);
        if (smContent) {
            const urlPattern = new RegExp(`\\s*<url>\\s*<loc>[^<]*${slug}[^<]*</loc>[\\s\\S]*?</url>`, "g");
            const newSitemap = smContent.replace(urlPattern, "");
            if (newSitemap !== smContent) {
                await ghUpdateFile("sitemap.xml", newSitemap, smSha, `Dashboard: remove ${slug} from sitemap.xml`, env);
                deleted.push("sitemap.xml (URL removed)");
            }
        }
    } catch (e) { errors.push({ path: "sitemap.xml", error: e.message }); }

    return { slug, deleted, errors, totalDeleted: deleted.length };
}

// ═══════════════════════════════════════════════════════════
// HEALTH CHECK
// ═══════════════════════════════════════════════════════════

async function healthCheck(env) {
    const issues = [];
    let score = 100;
    const [htmlFiles, postFiles, imgFiles, igFiles] = await Promise.all([
        ghListDir("articles", env), ghListDir("posts", env),
        ghListDir("images", env), ghListDir("instagram", env),
    ]);
    const { content: ajContent } = await ghFileContent("articles.json", env);
    const ajData = ajContent ? JSON.parse(ajContent) : { articles: [] };
    const indexSlugs = new Set((ajData.articles || []).map(a => a.slug));
    const htmlSlugs = new Set(htmlFiles.map(f => f.name.replace(".html", "")));
    const postSlugs = new Set(postFiles.map(f => {
        const m = f.name.match(/^(.+)-\d+\.json$/);
        return m ? m[1] : f.name.replace(".json", "");
    }));

    htmlSlugs.forEach(slug => { if (!postSlugs.has(slug)) { issues.push({ type: "warning", cat: "orphan", msg: `HTML sans JSON: ${slug}` }); score -= 2; } });
    postSlugs.forEach(slug => { if (!htmlSlugs.has(slug)) { issues.push({ type: "error", cat: "build", msg: `JSON sans HTML (build needed): ${slug}` }); score -= 3; } });
    htmlSlugs.forEach(slug => { if (!indexSlugs.has(slug)) { issues.push({ type: "warning", cat: "index", msg: `Absent de articles.json: ${slug}` }); score -= 2; } });
    indexSlugs.forEach(slug => { if (!htmlSlugs.has(slug)) { issues.push({ type: "error", cat: "index", msg: `Dans index mais pas de HTML: ${slug}` }); score -= 3; } });
    htmlSlugs.forEach(slug => {
        const hasCover = imgFiles.some(f => f.name.startsWith(slug) && (f.name.includes("-cover") || f.name.includes("cover")));
        if (!hasCover) { issues.push({ type: "error", cat: "image", msg: `Image cover manquante: ${slug}` }); score -= 5; }
        const contentImgs = imgFiles.filter(f => f.name.startsWith(slug) && f.name.includes("-img"));
        if (contentImgs.length < 4) { issues.push({ type: "warning", cat: "image", msg: `Images contenu: ${contentImgs.length}/4 pour ${slug}` }); score -= 1; }
    });
    const { content: smContent } = await ghFileContent("sitemap.xml", env);
    if (smContent) { htmlSlugs.forEach(slug => { if (!smContent.includes(slug)) { issues.push({ type: "warning", cat: "sitemap", msg: `Absent du sitemap: ${slug}` }); score -= 1; } }); }
    htmlSlugs.forEach(slug => { if (!igFiles.some(f => f.name.startsWith(slug))) { issues.push({ type: "info", cat: "instagram", msg: `Pas d'Instagram: ${slug}` }); } });

    return {
        score: Math.max(0, score), totalArticles: htmlSlugs.size, totalPosts: postSlugs.size,
        totalImages: imgFiles.length, totalInstagram: igFiles.filter(f => f.name.endsWith(".jpg") || f.name.endsWith(".png")).length,
        issues, issueCount: issues.length,
    };
}

// ═══════════════════════════════════════════════════════════
// DEEP SCAN
// ═══════════════════════════════════════════════════════════

async function deepScan(targetSlug, env) {
    const SITE_URL = env.SITE_URL || "https://littlesmartgenius.com";
    const [htmlFiles, imgFiles] = await Promise.all([ghListDir("articles", env), ghListDir("images", env)]);
    const imgSet = new Set(imgFiles.map(f => f.name));
    const filesToScan = targetSlug
        ? htmlFiles.filter(f => f.name === `${targetSlug}.html`)
        : htmlFiles.filter(f => f.name.endsWith(".html"));
    const results = [];

    for (const file of filesToScan) {
        const slug = file.name.replace(".html", "");
        try {
            const { content: html } = await ghFileContent(`articles/${file.name}`, env);
            if (!html) { results.push({ slug, error: "Could not fetch HTML" }); continue; }

            const imgRegex = /<img[^>]+src=["']([^"']+)["']/gi;
            const altRegex = /<img(?![^>]*\balt=)[^>]*>/gi;
            let m;
            const imgs = [];
            while ((m = imgRegex.exec(html)) !== null) imgs.push(m[1]);
            const imgResults = imgs.map(src => {
                const fname = src.split("/").pop().split("?")[0];
                const isExternal = src.startsWith("http");
                const isDataUri = src.startsWith("data:");
                const exists = isExternal || isDataUri || imgSet.has(fname) || src.startsWith("/images/") && imgSet.has(src.replace("/images/", ""));
                return { src: src.substring(0, 120), filename: fname, exists, external: isExternal };
            });

            const titleMatch = html.match(/<title>([^<]*)<\/title>/i);
            const metaDescMatch = html.match(/<meta\s+name=["']description["']\s+content=["']([^"']*)["']/i);
            const ogTitleMatch = html.match(/<meta\s+property=["']og:title["']\s+content=["']([^"']*)["']/i);
            const ogDescMatch = html.match(/<meta\s+property=["']og:description["']\s+content=["']([^"']*)["']/i);
            const ogImgMatch = html.match(/<meta\s+property=["']og:image["']\s+content=["']([^"']*)["']/i);
            const canonicalMatch = html.match(/<link\s+rel=["']canonical["']\s+href=["']([^"']*)["']/i);
            const h1Matches = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/gi) || [];
            const h2Matches = html.match(/<h2[^>]*>/gi) || [];
            const altMissing = (html.match(altRegex) || []).length;
            const textContent = html.replace(/<script[\s\S]*?<\/script>/gi, "").replace(/<style[\s\S]*?<\/style>/gi, "").replace(/<[^>]*>/g, " ");
            const wordCount = textContent.split(/\s+/).filter(w => w.length > 1).length;

            let seoScore = 100;
            const seoIssues = [];
            if (!titleMatch) { seoScore -= 15; seoIssues.push("Pas de balise <title>"); }
            else { const tLen = titleMatch[1].length; if (tLen < 30) { seoScore -= 5; seoIssues.push(`Title trop court (${tLen} cars)`); } if (tLen > 65) { seoScore -= 5; seoIssues.push(`Title trop long (${tLen} cars)`); } }
            if (!metaDescMatch) { seoScore -= 15; seoIssues.push("Pas de meta description"); }
            else { const dLen = metaDescMatch[1].length; if (dLen < 110) { seoScore -= 5; seoIssues.push(`Meta desc trop courte (${dLen} cars)`); } if (dLen > 165) { seoScore -= 5; seoIssues.push(`Meta desc trop longue (${dLen} cars)`); } }
            if (h1Matches.length === 0) { seoScore -= 15; seoIssues.push("Pas de H1"); }
            if (h1Matches.length > 1) { seoScore -= 5; seoIssues.push(`${h1Matches.length} H1 (1 seul recommande)`); }
            if (h2Matches.length === 0) { seoScore -= 5; seoIssues.push("Pas de H2"); }
            if (!ogTitleMatch) { seoScore -= 3; seoIssues.push("Pas de og:title"); }
            if (!ogDescMatch) { seoScore -= 3; seoIssues.push("Pas de og:description"); }
            if (!ogImgMatch) { seoScore -= 3; seoIssues.push("Pas de og:image"); }
            if (!canonicalMatch) { seoScore -= 3; seoIssues.push("Pas de canonical URL"); }
            if (imgs.length === 0) { seoScore -= 10; seoIssues.push("Aucune image"); }
            if (altMissing > 0) { seoScore -= Math.min(10, altMissing * 2); seoIssues.push(`${altMissing} images sans alt`); }
            if (wordCount < 500) { seoScore -= 10; seoIssues.push(`Contenu court (${wordCount} mots)`); }
            if (wordCount < 300) { seoScore -= 5; seoIssues.push("Contenu tres court"); }

            const missingImgs = imgResults.filter(i => !i.exists && !i.external);
            if (missingImgs.length > 0) { seoScore -= missingImgs.length * 5; seoIssues.push(`${missingImgs.length} images manquantes`); }

            const linkRegex = /<a[^>]+href=["']([^"'#][^"']*)["']/gi;
            const internalLinks = [];
            while ((m = linkRegex.exec(html)) !== null) {
                const href = m[1];
                if (!href.startsWith("http") && !href.startsWith("mailto:") && !href.startsWith("javascript:")) internalLinks.push(href);
            }

            results.push({
                slug,
                images: { total: imgs.length, missing: missingImgs, missingCount: missingImgs.length, details: imgResults },
                seo: {
                    score: Math.max(0, seoScore), title: titleMatch ? titleMatch[1] : null,
                    titleLength: titleMatch ? titleMatch[1].length : 0,
                    metaDescription: metaDescMatch ? metaDescMatch[1].substring(0, 160) : null,
                    metaDescLength: metaDescMatch ? metaDescMatch[1].length : 0,
                    h1Count: h1Matches.length, h2Count: h2Matches.length,
                    hasOgTags: !!(ogTitleMatch && ogDescMatch && ogImgMatch),
                    hasCanonical: !!canonicalMatch, imgCount: imgs.length, altMissing, wordCount, issues: seoIssues,
                },
                links: { internal: internalLinks.length, details: internalLinks.slice(0, 20) },
                viewUrl: `${SITE_URL}/articles/${slug}.html`,
            });
        } catch (e) { results.push({ slug, error: e.message }); }
    }

    const validResults = results.filter(r => !r.error);
    const avgSeo = validResults.length ? Math.round(validResults.reduce((sum, r) => sum + r.seo.score, 0) / validResults.length) : 0;
    const totalMissing = validResults.reduce((sum, r) => sum + r.images.missingCount, 0);
    return { scanned: filesToScan.length, totalAvailable: filesToScan.length, avgSeoScore: avgSeo, totalMissingImages: totalMissing, articlesWithNoImages: validResults.filter(r => r.images.total === 0).length, articles: results };
}

// ═══════════════════════════════════════════════════════════
// STATS
// ═══════════════════════════════════════════════════════════

async function getStats(env) {
    const [htmlFiles, postFiles, imgFiles, igFiles, ga4Metrics, ga4Realtime, ga4Geo] = await Promise.all([
        ghListDir("articles", env), ghListDir("posts", env),
        ghListDir("images", env), ghListDir("instagram", env),
        fetchGa4Metrics(env),
        fetchGa4Realtime(env),
        fetchGa4Geo(env)
    ]);
    const { content: ajContent } = await ghFileContent("articles.json", env);
    const ajData = ajContent ? JSON.parse(ajContent) : { articles: [] };
    const categories = {};
    (ajData.articles || []).forEach(a => { const cat = a.category || "Uncategorized"; categories[cat] = (categories[cat] || 0) + 1; });
    const { content: topicsContent } = await ghFileContent("data/used_topics.json", env);
    const topics = topicsContent ? JSON.parse(topicsContent) : {};
    const { content: kwContent } = await ghFileContent("data/keywords.txt", env);
    const totalKeywords = kwContent ? kwContent.split("\n").filter(l => l.trim() && !l.startsWith("#")).length : 0;
    const rootFiles = await ghListDir("", env);
    const blogPages = rootFiles.filter(f => f.name.match(/^blog(-\d+)?\.html$/)).map(f => f.name);
    const launchDate = new Date("2026-02-22");
    const now = new Date();
    const weekNum = Math.max(1, Math.floor((now - launchDate) / (7 * 24 * 60 * 60 * 1000)) + 1);
    let articlesPerDay = 3;
    if (weekNum >= 10) articlesPerDay = 6;
    else if (weekNum >= 7) articlesPerDay = 5;
    else if (weekNum >= 4) articlesPerDay = 4;
    return {
        articles: htmlFiles.length, posts: postFiles.filter(f => f.name.endsWith(".json")).length,
        images: imgFiles.length, instagram: igFiles.filter(f => f.name.endsWith(".jpg") || f.name.endsWith(".png")).length,
        categories, blogPages, topics: { keyword: { used: (topics.keyword || []).length, total: totalKeywords }, product: { used: (topics.product || []).length }, freebie: { used: (topics.freebie || []).length } },
        schedule: { week: weekNum, articlesPerDay, launchDate: "2026-02-22" },
        analytics: ga4Metrics,
        realtime: ga4Realtime,
        geo: ga4Geo
    };
}

// ═══════════════════════════════════════════════════════════
// TOPICS
// ═══════════════════════════════════════════════════════════

async function getTopics(env) {
    const [topicsRes, kwRes, productsRes, freebiesRes] = await Promise.all([
        ghFileContent("data/used_topics.json", env), ghFileContent("data/keywords.txt", env),
        ghFileContent("products_tpt.js", env), ghFileContent("download_links.js", env),
    ]);
    const topics = topicsRes.content ? JSON.parse(topicsRes.content) : {};
    const allKeywords = kwRes.content ? kwRes.content.split("\n").filter(l => l.trim() && !l.startsWith("#")).map(l => l.trim()) : [];
    const usedKeywords = new Set(topics.keyword || []);
    const remainingKeywords = allKeywords.filter(k => !usedKeywords.has(k));
    let allProducts = [];
    if (productsRes.content) { try { const match = productsRes.content.match(/window\.tptProducts\s*=\s*(\[.+?\]);/s); if (match) { const arr = JSON.parse(match[1]); allProducts = arr.map(p => p[0]); } } catch (e) { } }
    let allFreebies = [];
    if (freebiesRes.content) { try { const nameMatches = freebiesRes.content.match(/"([^"]+)"\s*:/g); if (nameMatches) { allFreebies = nameMatches.map(m => m.replace(/"/g, '').replace(/:$/, '').trim()); } } catch (e) { } }
    const usedProducts = new Set(topics.product || []);
    const usedFreebies = new Set(topics.freebie || []);
    return {
        used: topics, remaining: { keyword: remainingKeywords, keywordCount: remainingKeywords.length },
        allKeywords, keywordsRaw: kwRes.content || "", allProducts, allFreebies,
        remainingProducts: allProducts.filter(p => !usedProducts.has(p)), remainingFreebies: allFreebies.filter(f => !usedFreebies.has(f)),
    };
}

async function saveKeywords(content, env) {
    const REPO = env.GITHUB_REPO || "little-smart-genius-com/website";
    const { sha } = await ghFileContent("data/keywords.txt", env);
    await ghFetch(`/repos/${REPO}/contents/data/keywords.txt`, {
        method: "PUT",
        body: JSON.stringify({ message: "Update keywords from admin dashboard", content: btoa(unescape(encodeURIComponent(content))), sha: sha || undefined }),
    }, env);
    const lines = content.split("\n").filter(l => l.trim() && !l.startsWith("#"));
    return { saved: lines.length, message: `${lines.length} keywords saved` };
}

// ═══════════════════════════════════════════════════════════
// FIX SEO
// ═══════════════════════════════════════════════════════════

async function fixSeo(slug, env) {
    if (!slug) throw new Error("slug required");
    const path = `articles/${slug}.html`;
    const { content: html, sha } = await ghFileContent(path, env);
    if (!html) throw new Error(`Article not found: ${slug}`);
    let fixed = html;
    const fixes = [];

    const titleMatch = fixed.match(/<title>([^<]*)<\/title>/i);
    if (titleMatch && titleMatch[1].length > 65) {
        const oldTitle = titleMatch[1];
        let newTitle = oldTitle.replace(/\s*\|\s*Little Smart Genius$/i, '');
        if (newTitle.length > 60) newTitle = newTitle.substring(0, 57) + '...';
        newTitle += ' | Little Smart Genius';
        if (newTitle.length <= 65) { fixed = fixed.replace(`<title>${oldTitle}</title>`, `<title>${newTitle}</title>`); fixes.push(`Title: ${oldTitle.length} → ${newTitle.length} chars`); }
    }

    const metaDescMatch = fixed.match(/<meta\s+name=["']description["']\s+content=["']([^"']*)["']/i);
    if (metaDescMatch && metaDescMatch[1].length < 110) {
        const pMatch = fixed.match(/<p[^>]*>([^<]{100,})<\/p>/i);
        if (pMatch) {
            let newDesc = pMatch[1].replace(/\s+/g, ' ').trim();
            if (newDesc.length > 155) newDesc = newDesc.substring(0, 152) + '...';
            fixed = fixed.replace(metaDescMatch[0], `<meta name="description" content="${newDesc.replace(/"/g, '&quot;')}"`);
            fixes.push(`Meta desc: ${metaDescMatch[1].length} → ${newDesc.length} chars`);
        }
    }

    let h1Count = 0;
    fixed = fixed.replace(/<h1([^>]*)>([\s\S]*?)<\/h1>/gi, (match, attrs, content) => {
        h1Count++;
        if (h1Count > 1) { fixes.push(`H1 #${h1Count} → H2: ${content.substring(0, 40)}...`); return `<h2${attrs}>${content}</h2>`; }
        return match;
    });

    if (fixes.length === 0) return { slug, fixed: 0, message: "No SEO issues to fix" };

    await ghFetch(`contents/${path}`, {
        method: "PUT",
        body: JSON.stringify({ message: `SEO fix: ${slug} (${fixes.length} corrections)`, content: btoa(unescape(encodeURIComponent(fixed))), sha }),
    }, env);
    return { slug, fixed: fixes.length, fixes, message: `${fixes.length} SEO issues fixed` };
}

// ═══════════════════════════════════════════════════════════
// INSTAGRAM PUSH
// ═══════════════════════════════════════════════════════════

async function pushInstagram(slug, env) {
    const SITE_URL = env.SITE_URL || "https://littlesmartgenius.com";
    const REPO = env.GITHUB_REPO || "little-smart-genius-com/website";
    if (!slug) throw new Error("slug required");
    const igFiles = await ghListDir("instagram", env);
    const slugFiles = igFiles.filter(f => f.name.startsWith(slug));
    if (slugFiles.length === 0) throw new Error(`No Instagram files found for: ${slug}`);
    const imgFile = slugFiles.find(f => /\.(jpg|png|webp)$/i.test(f.name));
    const captionFile = slugFiles.find(f => /\.txt$/i.test(f.name));
    let imageUrl = '', caption = '';
    if (imgFile) imageUrl = `https://raw.githubusercontent.com/${REPO}/${BRANCH}/instagram/${imgFile.name}`;
    if (captionFile) { const { content } = await ghFileContent(`instagram/${captionFile.name}`, env); caption = content || ''; }
    if (!imageUrl) throw new Error(`No image found for Instagram post: ${slug}`);
    const webhookUrl = env.MAKECOM_WEBHOOK_URL;
    if (!webhookUrl) return { slug, imageUrl, caption: caption.substring(0, 200), message: "No MAKECOM_WEBHOOK_URL configured.", sent: false };
    const webhookRes = await fetch(webhookUrl, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "instagram-post", slug, imageUrl, caption, siteUrl: `${SITE_URL}/articles/${slug}.html` }),
    });
    return { slug, imageUrl, caption: caption.substring(0, 200), webhookStatus: webhookRes.status, sent: webhookRes.ok, message: webhookRes.ok ? "Instagram post sent to Make!" : `Webhook error: ${webhookRes.status}` };
}

// ═══════════════════════════════════════════════════════════
// WORKFLOW TRIGGER
// ═══════════════════════════════════════════════════════════

async function triggerWorkflow(action, slug, env) {
    const validActions = ["generate-batch", "generate-keyword", "generate-product", "generate-freebie", "build-site", "full-rebuild", "fix-images", "maintenance-scan", "regenerate-article", "comprehensive-repair", "humanize", "regen-all-images", "instagram-batch"];
    if (!validActions.includes(action)) throw new Error(`Invalid action: ${action}`);
    const inputs = { action };
    if (slug) inputs.slug = slug;
    const res = await ghFetch("actions/workflows/autoblog.yml/dispatches", {
        method: "POST", body: JSON.stringify({ ref: BRANCH, inputs }),
    }, env);
    if (!res.ok && res.status !== 204) { const text = await res.text(); throw new Error(`GitHub ${res.status}: ${text.substring(0, 200)}`); }
    return { triggered: true, action, slug, message: `Workflow triggered: ${action}${slug ? ` for ${slug}` : ''}` };
}

async function getWorkflowRuns(env) {
    try {
        const data = await ghJSON(`actions/runs?per_page=10&branch=${BRANCH}`, env);
        return { runs: (data.workflow_runs || []).map(r => ({ id: r.id, name: r.name, status: r.status, conclusion: r.conclusion, created_at: r.created_at, updated_at: r.updated_at, html_url: r.html_url, run_number: r.run_number })) };
    } catch { return { runs: [] }; }
}

// ═══════════════════════════════════════════════════════════
// SNAPSHOTS
// ═══════════════════════════════════════════════════════════

async function listSnapshots(env) {
    const res = await ghFetch("releases", { method: "GET" }, env);
    if (!res.ok) throw new Error(`GitHub releases: ${res.status}`);
    const releases = await res.json();
    const snapshots = releases.filter(r => r.tag_name.startsWith("snapshot-")).map(r => {
        let meta = {};
        try { meta = JSON.parse(r.body || "{}"); } catch (e) { }
        return { id: r.id, tag: r.tag_name, name: r.name || r.tag_name, date: r.created_at, commit: meta.commit || "unknown", articles: meta.articles || 0, images: meta.images || 0, posts: meta.posts || 0, downloadUrl: r.zipball_url };
    });
    return { snapshots, total: snapshots.length };
}

async function createSnapshot(name, env) {
    if (!name) name = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const tag = `snapshot-${name.toLowerCase().replace(/[^a-z0-9-]/g, "-").slice(0, 40)}`;
    const refRes = await ghFetch(`git/ref/heads/${BRANCH}`, { method: "GET" }, env);
    if (!refRes.ok) throw new Error(`Could not get HEAD: ${refRes.status}`);
    const refData = await refRes.json();
    const commitSha = refData.object.sha;
    let articleCount = 0, imageCount = 0, postCount = 0;
    try {
        const [arts, imgs, posts] = await Promise.all([ghListDir("articles", env), ghListDir("images", env), ghListDir("posts", env)]);
        articleCount = arts.filter(f => f.name.endsWith(".html")).length;
        imageCount = imgs.length; postCount = posts.filter(f => f.name.endsWith(".json")).length;
    } catch (e) { }
    const metadata = { commit: commitSha.substring(0, 8), articles: articleCount, images: imageCount, posts: postCount, createdAt: new Date().toISOString() };
    const tagRes = await ghFetch("git/refs", { method: "POST", body: JSON.stringify({ ref: `refs/tags/${tag}`, sha: commitSha }) }, env);
    if (!tagRes.ok && tagRes.status !== 422) { const txt = await tagRes.text(); throw new Error(`Create tag failed: ${tagRes.status} ${txt.substring(0, 200)}`); }
    const relRes = await ghFetch("releases", { method: "POST", body: JSON.stringify({ tag_name: tag, name: `📸 ${name}`, body: JSON.stringify(metadata), draft: false, prerelease: false }) }, env);
    if (!relRes.ok) { const txt = await relRes.text(); throw new Error(`Create release failed: ${relRes.status} ${txt.substring(0, 200)}`); }
    return { tag, name, commit: metadata.commit, articles: articleCount, images: imageCount, message: `Snapshot "${name}" created (${articleCount} articles, ${imageCount} images)` };
}

async function restoreSnapshot(tag, env) {
    if (!tag) throw new Error("tag required");
    const tagRes = await ghFetch(`git/ref/tags/${tag}`, { method: "GET" }, env);
    if (!tagRes.ok) throw new Error(`Tag not found: ${tag}`);
    const tagData = await tagRes.json(); const targetSha = tagData.object.sha;
    const safetyTag = `pre-restore-${Date.now()}`;
    const headRes = await ghFetch(`git/ref/heads/${BRANCH}`, { method: "GET" }, env);
    if (headRes.ok) { const headData = await headRes.json(); await ghFetch("git/refs", { method: "POST", body: JSON.stringify({ ref: `refs/tags/${safetyTag}`, sha: headData.object.sha }) }, env); }
    const updateRes = await ghFetch(`git/refs/heads/${BRANCH}`, { method: "PATCH", body: JSON.stringify({ sha: targetSha, force: true }) }, env);
    if (!updateRes.ok) { const txt = await updateRes.text(); throw new Error(`Restore failed: ${updateRes.status} ${txt.substring(0, 200)}`); }
    return { restored: true, tag, commit: targetSha.substring(0, 8), safetyTag, message: `Restored to "${tag}". Safety backup: ${safetyTag}` };
}

async function deleteSnapshot(tag, env) {
    if (!tag) throw new Error("tag required");
    const relRes = await ghFetch(`releases/tags/${tag}`, { method: "GET" }, env);
    if (relRes.ok) { const rel = await relRes.json(); await ghFetch(`releases/${rel.id}`, { method: "DELETE" }, env); }
    await ghFetch(`git/refs/tags/${tag}`, { method: "DELETE" }, env);
    return { deleted: true, tag, message: `Snapshot "${tag}" deleted` };
}

async function scanTpt(env) {
    const res = await ghFetch("actions/workflows/scrape-tpt.yml/dispatches", { method: "POST", body: JSON.stringify({ ref: BRANCH }) }, env);
    if (!res.ok && res.status !== 204) throw new Error(`Failed to trigger TPT scan: ${res.status}`);
    return { success: true, message: "TPT scan workflow triggered! Check GitHub Actions for progress." };
}

// ═══════════════════════════════════════════════════════════
// DIRECT IMAGE REGENERATION (Pollinations + GitHub commit)
// ═══════════════════════════════════════════════════════════

// V8 Master Prompt templates (exact copy from scripts/master_prompt.py)
const MASTER_PROMPTS = [
    // Cover (idx 0): Intense Golden Hour
    `A feature-film quality 3D CGI render in the distinct modern Pixar/Disney animation style, featuring [SUJET]. The scene utilizes dramatic golden hour cinematography with intense, warm backlighting creating prominent rim lights on subjects and volumetric sun rays. The atmosphere is glowing and highly textured with a shallow depth of field. 8K resolution masterpiece with photorealistic rendering engine details; the entire image is rendered explicitly without containing any text, letters, words, numbers, watermarks, signatures, deformed anatomy, distorted faces, ugly features, poorly drawn hands, missing limbs, extra fingers, mutated shapes, blurry artifacts, low resolution areas, bad proportions, crossed eyes, creepy expressions, or floating objects.`,
    // img1 (idx 1): Bright & Airy Morning
    `A pristine 3D CGI animated render in the modern Pixar/Disney style, featuring [SUJET], focused on clean geometry and soft, inviting textures. The lighting setup is high-key and airy, simulating clean morning daylight with balanced exposure, soft diffused shadows, and a fresh, cheerful color grading. The background is smoothly blurred. 8K resolution, highly detailed render; the entire image is rendered explicitly without containing any text, letters, words, numbers, watermarks, signatures, deformed anatomy, distorted faces, ugly features, poorly drawn hands, missing limbs, extra fingers, mutated shapes, blurry artifacts, low resolution areas, bad proportions, crossed eyes, creepy expressions, or floating objects.`,
    // img2 (idx 2): Cozy Evening Intimacy
    `A highly detailed 3D animated render in the modern Pixar production style, featuring [SUJET]. The lighting is a low-key interior setup, characterized by deep, warm tones from practical light sources creating an intimate and tranquil mood. Emphasis on rich texture details, warm highlights, and significant bokeh depth of field. 8K masterpiece render; the entire image is rendered explicitly without containing any text, letters, words, numbers, watermarks, signatures, deformed anatomy, distorted faces, ugly features, poorly drawn hands, missing limbs, extra fingers, mutated shapes, blurry artifacts, low resolution areas, bad proportions, crossed eyes, creepy expressions, or floating objects.`,
    // img3 (idx 3): Soft Dappled Natural Light
    `A high-quality 3D CGI render displaying modern Disney/Pixar animation aesthetics, featuring [SUJET] with gentle, rounded character designs. The lighting is naturalistic and tranquil, utilizing a dappled sunlight effect through off-camera foliage to create soft, organic light and shadow patterns across the scene. 8K resolution, photorealistic texture rendering; the entire image is rendered explicitly without containing any text, letters, words, numbers, watermarks, signatures, deformed anatomy, distorted faces, ugly features, poorly drawn hands, missing limbs, extra fingers, mutated shapes, blurry artifacts, low resolution areas, bad proportions, crossed eyes, creepy expressions, or floating objects.`,
    // img4 (idx 4): Vibrant & Joyful Daytime
    `A vibrant 3D animated CGI render in the professional style of modern Pixar, featuring [SUJET]. The art direction emphasizes a highly saturated color palette, soft expressive textures, and clean forms. The illumination is bright, even daytime lighting, optimizing color pop and creating an energetic atmosphere with a clean focus fall-off in the background. 8K masterpiece quality; the entire image is rendered explicitly without containing any text, letters, words, numbers, watermarks, signatures, deformed anatomy, distorted faces, ugly features, poorly drawn hands, missing limbs, extra fingers, mutated shapes, blurry artifacts, low resolution areas, bad proportions, crossed eyes, creepy expressions, or floating objects.`,
    // img5 (idx 5): Soft Overcast Diffused Light
    `A high-fidelity 3D animated CGI render in the modern Pixar/Disney animation style, featuring [SUJET]. The lighting scenario is soft, diffused daylight typical of an overcast sky, resulting in ultra-soft, nearly invisible shadows and a peaceful, comforting interior ambiance. Emphasis on tactile material textures and a warmly blurred background with shallow depth of field. 8K resolution masterpiece; the entire image is rendered explicitly without containing any text, letters, words, numbers, watermarks, signatures, deformed anatomy, distorted faces, ugly features, poorly drawn hands, missing limbs, extra fingers, mutated shapes, blurry artifacts, low resolution areas, bad proportions, crossed eyes, creepy expressions, or floating objects.`,
];

const NO_TEXT_SUFFIX = ", ABSOLUTELY NO text, letters, words, numbers, titles, captions, labels, watermarks, or UI overlays in the image, pure visual storytelling only";

function buildArtDirectorSubject(title, concept, imageIndex) {
    if (imageIndex === 0) {
        return `a group of joyful, diverse children and a smiling teacher engaged in ${concept} activities together, carefully placing pieces and smiling, in a warm cozy classroom with sunlight streaming in`;
    } else if (imageIndex === 1) {
        return `an overhead flat-lay view of small hands carefully working on colorful worksheets about ${concept}, with colored pencils, stickers, and a magnifying glass scattered around on a warm wooden table in soft morning light`;
    } else if (imageIndex === 2) {
        return `multiple children's hands reaching across a large shared activity page about ${concept}, collaborating together, with markers, glue sticks, and craft materials, on a bright classroom table with sunlight streaming through windows`;
    } else if (imageIndex === 3) {
        return `a detail shot of beautifully designed educational materials about ${concept}, surrounded by colorful art supplies like scissors, colored pencils, glitter glue, and stickers on a neat desk with a plant in the background`;
    } else if (imageIndex === 4) {
        return `a close-up of a child's small hands joyfully interacting with a puzzle piece related to ${concept}, with a parent's hands gently guiding nearby, in a cozy home setting with warm natural light`;
    } else {
        return `a wide shot of a warm, inviting learning environment where children and a teacher sit around a table covered with worksheets about ${concept}, all smiling and engaged, with educational posters on the walls and sunlight through large windows`;
    }
}

function buildFullPrompt(subject, imageIndex) {
    const template = MASTER_PROMPTS[Math.min(imageIndex, MASTER_PROMPTS.length - 1)];
    return template.replace("[SUJET]", subject);
}

function getImageIndex(imageType) {
    if (imageType === "cover") return 0;
    const m = imageType.match(/img(\d+)/);
    return m ? parseInt(m[1]) : 0;
}

async function regenImageFetch(slug, imageType, env) {
    if (!slug) throw new Error("slug required");
    if (!imageType) throw new Error("imageType required (cover, img1, img2, img3, img4, img5)");

    const imageIndex = getImageIndex(imageType);

    // 1. Find the post JSON
    let postContent = null;
    let postFilename = "";

    // First try the active posts/ directory
    const postFiles = await ghListDir("posts", env);
    const postFile = postFiles.find(f => f.name.startsWith(slug) && f.name.endsWith(".json"));

    if (postFile) {
        const { content } = await ghFileContent(`posts/${postFile.name}`, env);
        postContent = content;
        postFilename = postFile.name;
    } else {
        // Fallback: check the archive directory
        try {
            const archiveFiles = await ghListDir("data/archive_posts", env);
            const archiveFile = archiveFiles.find(f => f.name.startsWith(slug) && f.name.endsWith(".json"));
            if (archiveFile) {
                const { content } = await ghFileContent(`data/archive_posts/${archiveFile.name}`, env);
                postContent = content;
                postFilename = archiveFile.name;
            }
        } catch (e) {
            // Archive folder might not exist or be empty on GitHub yet
        }
    }

    if (!postContent) throw new Error(`Post JSON not found for slug: ${slug} (checked posts/ and data/archive_posts/)`);
    const postData = JSON.parse(postContent);

    const title = postData.title || slug.replace(/-/g, " ");
    const concept = title.replace(/-/g, " ");

    // 2. Find existing filenames
    let existingFilename = "";
    if (imageType === "cover") {
        existingFilename = (postData.image || "").replace("images/", "");
    } else {
        const content = postData.content || "";
        const imgPattern = new RegExp(`(\\S*-${imageType}-\\d+\\.webp)`, "i");
        const match = content.match(imgPattern);
        if (match) {
            existingFilename = match[1].replace(/^.*\//, "");
        }
    }

    if (!existingFilename) {
        throw new Error(`Image filename not found in post JSON for ${imageType}.`);
    }

    // 3. Get existing SHAs
    const imgFiles = await ghListDir("images", env);
    const existingFile = imgFiles.find(f => f.name === existingFilename);
    const existingSha = existingFile ? existingFile.sha : null;

    let thumbFilename = null;
    let thumbSha = null;
    if (imageType === "cover") {
        thumbFilename = existingFilename.replace(".webp", "-thumb.webp");
        const thumbFile = imgFiles.find(f => f.name === thumbFilename);
        thumbSha = thumbFile ? thumbFile.sha : null;
    }

    // 4. Build Prompts
    const subject = buildArtDirectorSubject(title, concept, imageIndex);
    const fullPrompt = buildFullPrompt(subject, imageIndex);
    const cleanPrompt = (fullPrompt + NO_TEXT_SUFFIX).replace(/[^a-zA-Z0-9 ,.\-]/g, "");
    const encodedPrompt = encodeURIComponent(cleanPrompt);
    const seed = Math.floor(Date.now() / 1000) + imageIndex * 100;

    // 5. Call Pollinations
    const modelName = env.POLLINATIONS_MODEL_NAME || "klein-large";
    const allKeys = env.POLLINATIONS_KEYS_LIST ? env.POLLINATIONS_KEYS_LIST.split(",") : [];

    // Filter out dead keys (skip keys blacklisted less than 1 hour ago)
    const now = Date.now();
    const apiKeys = allKeys.filter(k => {
        const blockedAt = deadPollinationsKeys.get(k);
        if (!blockedAt) return true; // not blacklisted
        if (now - blockedAt > KEY_COOLDOWN_MS) {
            deadPollinationsKeys.delete(k); // TTL expired, recycle the key
            return true;
        }
        return false; // still in cooldown
    });

    // If all keys are in cooldown, clear all and retry everything
    if (apiKeys.length === 0 && allKeys.length > 0) {
        deadPollinationsKeys.clear();
        apiKeys.push(...allKeys);
    }

    const baseUrl = `https://gen.pollinations.ai/image/${encodedPrompt}`;

    let imageData = null;
    let lastError = null;
    const WALL_CLOCK_BUDGET = 28000; // 28s total max to stay under CF limits
    const PER_REQUEST_TIMEOUT = 20000; // 20s per request (image gen needs time!)
    const startTime = Date.now();
    const maxAttempts = Math.max(3, apiKeys.length + 2);
    const triedKeys = new Set();

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        // Check wall-clock budget
        const elapsed = Date.now() - startTime;
        if (elapsed > WALL_CLOCK_BUDGET - 3000) break; // stop 3s before limit

        const seedValue = seed + attempt;
        let currentKey = "";
        if (apiKeys.length > 0) {
            const keyIndex = attempt % apiKeys.length;
            currentKey = apiKeys[keyIndex];
            // Skip keys already blacklisted during this run
            if (triedKeys.has(currentKey)) continue;
        }

        const pollinationsUrl = `${baseUrl}?width=1200&height=675&seed=${seedValue}&model=${modelName}&nologo=true&enhance=true`;

        try {
            const headers = { "User-Agent": "Mozilla/5.0 (LittleSmartGenius-Admin)" };
            if (currentKey) headers["Authorization"] = `Bearer ${currentKey}`;

            // Timeout = remaining budget or per-request limit, whichever is smaller
            const remaining = WALL_CLOCK_BUDGET - (Date.now() - startTime) - 1000;
            const timeoutMs = Math.min(PER_REQUEST_TIMEOUT, remaining);
            if (timeoutMs < 3000) break; // not enough time left

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

            const imgRes = await fetch(pollinationsUrl, {
                headers,
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (imgRes.ok) {
                const arrayBuf = await imgRes.arrayBuffer();
                if (arrayBuf.byteLength > 1024) {
                    imageData = arrayBuf;
                    break;
                } else {
                    lastError = `Image too small: ${arrayBuf.byteLength} bytes`;
                }
            } else if (imgRes.status === 402 || imgRes.status === 429) {
                if (currentKey) {
                    deadPollinationsKeys.set(currentKey, Date.now());
                    triedKeys.add(currentKey);
                }
                lastError = `HTTP ${imgRes.status} (clé bloquée, rotation...)`;
                continue; // instant skip, no sleep
            } else {
                lastError = `HTTP ${imgRes.status} ${imgRes.statusText}`;
            }
        } catch (e) {
            lastError = e.name === 'AbortError' ? `Timeout (${Math.round((Date.now() - startTime) / 1000)}s)` : e.message;
        }

        // Small sleep between real attempts (not 402 skips)
        const remainingAfter = WALL_CLOCK_BUDGET - (Date.now() - startTime);
        if (remainingAfter > 4000) {
            await new Promise(r => setTimeout(r, 500));
        }
    }

    if (!imageData) {
        throw new Error(`Échec après ${Math.round((Date.now() - startTime) / 1000)}s. Dernière erreur: ${lastError}`);
    }

    // 6. Convert to base64 to send to browser for WEBP compression
    const bytes = new Uint8Array(imageData);
    let binary = "";
    for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
    const rawBase64 = btoa(binary);

    return {
        success: true,
        slug,
        imageType,
        filename: existingFilename,
        existingSha,
        thumbFilename,
        thumbSha,
        rawBase64
    };
}

async function regenImageCommitMain(params, env) {
    const { slug, imageType, filename, existingSha, base64Webp } = params;

    const putBody = {
        message: `Dashboard: regen ${imageType} for ${slug} (WebP optimized)`,
        content: base64Webp,
        branch: BRANCH,
    };
    if (existingSha) putBody.sha = existingSha;

    const putRes = await ghFetch(`contents/images/${filename}`, {
        method: "PUT",
        body: JSON.stringify(putBody),
    }, env);

    if (!putRes.ok) {
        const errText = await putRes.text();
        throw new Error(`GitHub upload failed (${putRes.status}): ${errText.substring(0, 200)}`);
    }

    return {
        success: true,
        message: `✅ Image ${imageType} principale sauvegardée sur GitHub !`,
    };
}

async function regenImageCommitThumb(params, env) {
    const { slug, thumbFilename, thumbSha, base64ThumbWebp } = params;

    if (!thumbFilename || !base64ThumbWebp) {
        return { success: true, message: "No thumbnail to commit." };
    }

    const thumbBody = {
        message: `Dashboard: regen cover thumb for ${slug} (WebP optimized)`,
        content: base64ThumbWebp,
        branch: BRANCH,
    };
    if (thumbSha) thumbBody.sha = thumbSha;

    const putRes = await ghFetch(`contents/images/${thumbFilename}`, {
        method: "PUT",
        body: JSON.stringify(thumbBody),
    }, env);

    if (!putRes.ok) {
        const errText = await putRes.text();
        throw new Error(`GitHub thumb upload failed (${putRes.status}): ${errText.substring(0, 200)}`);
    }

    return {
        success: true,
        message: `✅ Thumbnail sauvegardé sur GitHub !`,
    };
}

// ═══════════════════════════════════════════════════════════
// CLEANUP INSTAGRAM (delete files > 24h old)
// ═══════════════════════════════════════════════════════════

async function cleanupInstagram(env) {
    const igFiles = await ghListDir("instagram", env);
    if (igFiles.length === 0) return { deleted: [], skipped: 0, message: "Instagram folder is empty" };

    const now = Date.now();
    const TWENTY_FOUR_HOURS = 24 * 60 * 60 * 1000;
    const deleted = [];
    const errors = [];
    let skipped = 0;

    // Group files by their timestamp suffix (e.g. "-ig-1771634214")
    const filesByTimestamp = {};
    for (const f of igFiles) {
        const match = f.name.match(/-ig-(\d+)\.(jpg|png|txt)$/i);
        if (match) {
            const ts = match[1];
            if (!filesByTimestamp[ts]) filesByTimestamp[ts] = [];
            filesByTimestamp[ts].push(f);
        }
    }

    for (const [tsStr, files] of Object.entries(filesByTimestamp)) {
        const timestamp = parseInt(tsStr, 10);
        // The timestamp in filenames is Unix seconds
        const fileAge = now - (timestamp * 1000);

        if (fileAge > TWENTY_FOUR_HOURS) {
            // Delete all files in this group
            for (const f of files) {
                try {
                    await ghDeleteFile(`instagram/${f.name}`, f.sha, `Auto-cleanup: Instagram file > 24h`, env);
                    deleted.push(f.name);
                } catch (e) {
                    errors.push({ file: f.name, error: e.message });
                }
            }
        } else {
            skipped += files.length;
        }
    }

    return {
        deleted,
        deletedCount: deleted.length,
        skipped,
        errors,
        message: deleted.length > 0
            ? `Cleaned up ${deleted.length} Instagram files older than 24h`
            : `No files older than 24h found (${skipped} files are recent)`,
    };
}

// ═══════════════════════════════════════════════════════════
// MAIN HANDLER (Cloudflare Workers format)
// ═══════════════════════════════════════════════════════════

export default {
    async fetch(request, env) {
        if (request.method === "OPTIONS") {
            return new Response(null, { status: 204, headers: corsHeaders });
        }

        const authErr = checkAuth(request, env);
        if (authErr) return authErr;

        const url = new URL(request.url);
        let params = Object.fromEntries(url.searchParams.entries());

        if (request.method !== "GET" && request.method !== "OPTIONS") {
            try {
                const bodyJson = await request.json();
                params = { ...params, ...bodyJson };
            } catch (e) {
                // Ignore parsing errors for empty bodies
            }
        }

        const action = params.action || "";

        try {
            let result;
            switch (action) {
                case "articles": result = await listArticles(env); break;
                case "delete":
                    if (request.method !== "DELETE" && request.method !== "POST")
                        return new Response(JSON.stringify({ error: "Use DELETE or POST" }), { status: 405, headers: corsHeaders });
                    result = await cascadeDelete(params.slug, env); break;
                case "health": result = await healthCheck(env); break;
                case "deep-scan": result = await deepScan(params.slug || null, env); break;
                case "stats": result = await getStats(env); break;
                case "topics": result = await getTopics(env); break;
                case "save-keywords":
                    if (request.method !== "POST") return new Response(JSON.stringify({ error: "Use POST" }), { status: 405, headers: corsHeaders });
                    result = await saveKeywords(decodeURIComponent(params.content || ""), env); break;
                case "fix-seo": result = await fixSeo(params.slug, env); break;
                case "push-instagram": result = await pushInstagram(params.slug, env); break;
                case "snapshots": result = await listSnapshots(env); break;
                case "create-snapshot": result = await createSnapshot(params.name || null, env); break;
                case "restore-snapshot":
                    if (!params.tag) return new Response(JSON.stringify({ error: "tag required" }), { status: 400, headers: corsHeaders });
                    result = await restoreSnapshot(params.tag, env); break;
                case "delete-snapshot":
                    if (!params.tag) return new Response(JSON.stringify({ error: "tag required" }), { status: 400, headers: corsHeaders });
                    result = await deleteSnapshot(params.tag, env); break;
                case "generate": result = await triggerWorkflow(params.type || "generate-batch", params.slug || null, env); break;
                case "runs": result = await getWorkflowRuns(env); break;
                case "scan-tpt": result = await scanTpt(env); break;
                case "cleanup-instagram": result = await cleanupInstagram(env); break;
                case "regen-image-fetch":
                    result = await regenImageFetch(params.slug, params.imageType, env);
                    break;
                case "regen-image-commit-main":
                    result = await regenImageCommitMain(params, env);
                    break;
                case "regen-image-commit-thumb":
                    result = await regenImageCommitThumb(params, env);
                    break;
                default:
                    return new Response(JSON.stringify({
                        error: "Unknown action",
                        available: ["articles", "delete", "health", "deep-scan", "stats", "topics", "save-keywords", "fix-seo", "push-instagram", "snapshots", "create-snapshot", "restore-snapshot", "delete-snapshot", "generate", "runs", "scan-tpt", "cleanup-instagram", "regen-image-fetch", "regen-image-commit-main", "regen-image-commit-thumb"],
                    }), { status: 400, headers: corsHeaders });
            }
            return new Response(JSON.stringify(result), { status: 200, headers: corsHeaders });
        } catch (e) {
            console.error("Admin API error:", e);
            return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: corsHeaders });
        }
    },
};
