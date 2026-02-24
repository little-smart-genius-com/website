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
// LIST ARTICLES
// ═══════════════════════════════════════════════════════════

async function listArticles(env) {
    const SITE_URL = env.SITE_URL || "https://littlesmartgenius.com";
    const { content } = await ghFileContent("articles.json", env);
    if (!content) return { articles: [], total: 0 };

    const data = JSON.parse(content);
    const articles = data.articles || [];

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
        const coverImgs = imgFiles.filter(f => f.name.startsWith(slug) && f.name.includes("-cover"));
        const contentImgs = imgFiles.filter(f => f.name.startsWith(slug) && f.name.includes("-img"));
        const igPost = igFiles.filter(f => f.name.startsWith(slug));
        let health = "ok";
        if (!hasHtml) health = "error";
        else if (coverImgs.length === 0) health = "error";
        else if (!hasPost) health = "warning";
        return {
            ...a, hasHtml, hasPost,
            coverCount: coverImgs.length, contentImgCount: contentImgs.length,
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
    const [htmlFiles, postFiles, imgFiles, igFiles] = await Promise.all([
        ghListDir("articles", env), ghListDir("posts", env),
        ghListDir("images", env), ghListDir("instagram", env),
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
    const validActions = ["generate-batch", "generate-keyword", "generate-product", "generate-freebie", "build-site", "full-rebuild", "fix-images", "maintenance-scan", "regenerate-article"];
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
        const params = Object.fromEntries(url.searchParams.entries());
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
                default:
                    return new Response(JSON.stringify({
                        error: "Unknown action",
                        available: ["articles", "delete", "health", "deep-scan", "stats", "topics", "save-keywords", "fix-seo", "push-instagram", "snapshots", "create-snapshot", "restore-snapshot", "delete-snapshot", "generate", "runs", "scan-tpt"],
                    }), { status: 400, headers: corsHeaders });
            }
            return new Response(JSON.stringify(result), { status: 200, headers: corsHeaders });
        } catch (e) {
            console.error("Admin API error:", e);
            return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: corsHeaders });
        }
    },
};
