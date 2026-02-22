// ═══════════════════════════════════════════════════════════
// ADMIN API V3 — Full Control + Deep Scan
// ═══════════════════════════════════════════════════════════

const GITHUB_API = "https://api.github.com";
const PAT = process.env.GITHUB_PAT;
const REPO = process.env.GITHUB_REPO || "little-smart-genius-com/website";
const ADMIN_PASS = process.env.ADMIN_PASSWORD || "";
const BRANCH = "main";
const SITE_URL = process.env.SITE_URL || "https://littlesmartgenius.com";

const headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Content-Type": "application/json",
};

// ── GitHub API helpers ──────────────────────────────────

async function ghFetch(path, opts = {}) {
    const url = path.startsWith("http") ? path : `${GITHUB_API}/repos/${REPO}/${path}`;
    const res = await fetch(url, {
        ...opts,
        headers: {
            Authorization: `Bearer ${PAT}`,
            Accept: "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            ...(opts.headers || {}),
        },
    });
    return res;
}

async function ghJSON(path) {
    const res = await ghFetch(path);
    if (!res.ok) throw new Error(`GitHub ${res.status}`);
    return res.json();
}

async function ghFileContent(path) {
    try {
        const data = await ghJSON(`contents/${path}?ref=${BRANCH}`);
        if (data.content) {
            return { content: Buffer.from(data.content, "base64").toString("utf-8"), sha: data.sha, size: data.size };
        }
        return { content: null, sha: null, size: 0 };
    } catch {
        return { content: null, sha: null, size: 0 };
    }
}

async function ghDeleteFile(path, sha, message) {
    return ghFetch(`contents/${path}`, {
        method: "DELETE",
        body: JSON.stringify({ message, sha, branch: BRANCH }),
    });
}

async function ghListDir(path) {
    try {
        const data = await ghJSON(`contents/${path}?ref=${BRANCH}`);
        return Array.isArray(data) ? data : [];
    } catch {
        return [];
    }
}

async function ghUpdateFile(path, content, sha, message) {
    return ghFetch(`contents/${path}`, {
        method: "PUT",
        body: JSON.stringify({
            message,
            content: Buffer.from(content).toString("base64"),
            sha,
            branch: BRANCH,
        }),
    });
}

// ── Auth check ──────────────────────────────────────────

function checkAuth(event) {
    const auth = event.headers.authorization || "";
    const token = auth.replace("Bearer ", "");
    if (!ADMIN_PASS || token !== ADMIN_PASS) {
        return { statusCode: 401, headers, body: JSON.stringify({ error: "Unauthorized" }) };
    }
    return null;
}

// ═══════════════════════════════════════════════════════════
// LIST ARTICLES (enriched)
// ═══════════════════════════════════════════════════════════

async function listArticles() {
    const { content } = await ghFileContent("articles.json");
    if (!content) return { articles: [], total: 0 };

    const data = JSON.parse(content);
    const articles = data.articles || [];

    const [htmlFiles, imgFiles, igFiles, postFiles] = await Promise.all([
        ghListDir("articles"),
        ghListDir("images"),
        ghListDir("instagram"),
        ghListDir("posts"),
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
            ...a,
            hasHtml,
            hasPost,
            coverCount: coverImgs.length,
            contentImgCount: contentImgs.length,
            imageCount: coverImgs.length + contentImgs.length,
            hasInstagram: igPost.length > 0,
            igCount: igPost.length,
            health,
            viewUrl: `${SITE_URL}/articles/${slug}.html`,
        };
    });

    return { articles: enriched, total: enriched.length };
}

// ═══════════════════════════════════════════════════════════
// CASCADE DELETE
// ═══════════════════════════════════════════════════════════

async function cascadeDelete(slug) {
    if (!slug) throw new Error("Missing slug parameter");

    const deleted = [];
    const errors = [];

    const [htmlFiles, postFiles, imgFiles, igFiles] = await Promise.all([
        ghListDir("articles"),
        ghListDir("posts"),
        ghListDir("images"),
        ghListDir("instagram"),
    ]);

    const toDelete = [];
    htmlFiles.filter(f => f.name === `${slug}.html`).forEach(f => toDelete.push({ path: `articles/${f.name}`, sha: f.sha }));
    postFiles.filter(f => f.name.startsWith(slug)).forEach(f => toDelete.push({ path: `posts/${f.name}`, sha: f.sha }));
    imgFiles.filter(f => f.name.startsWith(slug)).forEach(f => toDelete.push({ path: `images/${f.name}`, sha: f.sha }));
    igFiles.filter(f => f.name.startsWith(slug)).forEach(f => toDelete.push({ path: `instagram/${f.name}`, sha: f.sha }));

    for (const file of toDelete) {
        try {
            await ghDeleteFile(file.path, file.sha, `Dashboard: delete ${slug}`);
            deleted.push(file.path);
        } catch (e) {
            errors.push({ path: file.path, error: e.message });
        }
    }

    // Update articles.json
    try {
        const { content: ajContent, sha: ajSha } = await ghFileContent("articles.json");
        if (ajContent) {
            const ajData = JSON.parse(ajContent);
            ajData.articles = (ajData.articles || []).filter(a => a.slug !== slug);
            ajData.total_articles = ajData.articles.length;
            await ghUpdateFile("articles.json", JSON.stringify(ajData, null, 2), ajSha, `Dashboard: remove ${slug} from articles.json`);
            deleted.push("articles.json (entry removed)");
        }
    } catch (e) { errors.push({ path: "articles.json", error: e.message }); }

    // Update search_index.json
    try {
        const { content: siContent, sha: siSha } = await ghFileContent("search_index.json");
        if (siContent) {
            const siData = JSON.parse(siContent);
            siData.articles = (siData.articles || []).filter(a => a.slug !== slug);
            siData.total_articles = siData.articles.length;
            await ghUpdateFile("search_index.json", JSON.stringify(siData, null, 2), siSha, `Dashboard: remove ${slug} from search_index.json`);
            deleted.push("search_index.json (entry removed)");
        }
    } catch (e) { errors.push({ path: "search_index.json", error: e.message }); }

    // Update sitemap.xml
    try {
        const { content: smContent, sha: smSha } = await ghFileContent("sitemap.xml");
        if (smContent) {
            const urlPattern = new RegExp(`\\s*<url>\\s*<loc>[^<]*${slug}[^<]*</loc>[\\s\\S]*?</url>`, "g");
            const newSitemap = smContent.replace(urlPattern, "");
            if (newSitemap !== smContent) {
                await ghUpdateFile("sitemap.xml", newSitemap, smSha, `Dashboard: remove ${slug} from sitemap.xml`);
                deleted.push("sitemap.xml (URL removed)");
            }
        }
    } catch (e) { errors.push({ path: "sitemap.xml", error: e.message }); }

    return { slug, deleted, errors, totalDeleted: deleted.length };
}

// ═══════════════════════════════════════════════════════════
// HEALTH CHECK (light — directory-based)
// ═══════════════════════════════════════════════════════════

async function healthCheck() {
    const issues = [];
    let score = 100;

    const [htmlFiles, postFiles, imgFiles, igFiles] = await Promise.all([
        ghListDir("articles"),
        ghListDir("posts"),
        ghListDir("images"),
        ghListDir("instagram"),
    ]);

    const { content: ajContent } = await ghFileContent("articles.json");
    const ajData = ajContent ? JSON.parse(ajContent) : { articles: [] };
    const indexSlugs = new Set((ajData.articles || []).map(a => a.slug));

    const htmlSlugs = new Set(htmlFiles.map(f => f.name.replace(".html", "")));
    const postSlugs = new Set(postFiles.map(f => {
        const m = f.name.match(/^(.+)-\d+\.json$/);
        return m ? m[1] : f.name.replace(".json", "");
    }));

    htmlSlugs.forEach(slug => {
        if (!postSlugs.has(slug)) {
            issues.push({ type: "warning", cat: "orphan", msg: `HTML sans JSON: ${slug}` });
            score -= 2;
        }
    });
    postSlugs.forEach(slug => {
        if (!htmlSlugs.has(slug)) {
            issues.push({ type: "error", cat: "build", msg: `JSON sans HTML (build needed): ${slug}` });
            score -= 3;
        }
    });
    htmlSlugs.forEach(slug => {
        if (!indexSlugs.has(slug)) {
            issues.push({ type: "warning", cat: "index", msg: `Absent de articles.json: ${slug}` });
            score -= 2;
        }
    });
    indexSlugs.forEach(slug => {
        if (!htmlSlugs.has(slug)) {
            issues.push({ type: "error", cat: "index", msg: `Dans index mais pas de HTML: ${slug}` });
            score -= 3;
        }
    });
    htmlSlugs.forEach(slug => {
        const hasCover = imgFiles.some(f => f.name.startsWith(slug) && (f.name.includes("-cover") || f.name.includes("cover")));
        if (!hasCover) {
            issues.push({ type: "error", cat: "image", msg: `Image cover manquante: ${slug}` });
            score -= 5;
        }
        const contentImgs = imgFiles.filter(f => f.name.startsWith(slug) && f.name.includes("-img"));
        if (contentImgs.length < 4) {
            issues.push({ type: "warning", cat: "image", msg: `Images contenu: ${contentImgs.length}/4 pour ${slug}` });
            score -= 1;
        }
    });

    const { content: smContent } = await ghFileContent("sitemap.xml");
    if (smContent) {
        htmlSlugs.forEach(slug => {
            if (!smContent.includes(slug)) {
                issues.push({ type: "warning", cat: "sitemap", msg: `Absent du sitemap: ${slug}` });
                score -= 1;
            }
        });
    }

    htmlSlugs.forEach(slug => {
        const hasIg = igFiles.some(f => f.name.startsWith(slug));
        if (!hasIg) {
            issues.push({ type: "info", cat: "instagram", msg: `Pas d'Instagram: ${slug}` });
        }
    });

    return {
        score: Math.max(0, score),
        totalArticles: htmlSlugs.size,
        totalPosts: postSlugs.size,
        totalImages: imgFiles.length,
        totalInstagram: igFiles.filter(f => f.name.endsWith(".jpg") || f.name.endsWith(".png")).length,
        issues,
        issueCount: issues.length,
    };
}

// ═══════════════════════════════════════════════════════════
// DEEP SCAN — Fetch article HTML and analyze content
// ═══════════════════════════════════════════════════════════

async function deepScan(targetSlug) {
    const [htmlFiles, imgFiles] = await Promise.all([
        ghListDir("articles"),
        ghListDir("images"),
    ]);

    const imgSet = new Set(imgFiles.map(f => f.name));
    const filesToScan = targetSlug
        ? htmlFiles.filter(f => f.name === `${targetSlug}.html`)
        : htmlFiles.filter(f => f.name.endsWith(".html"));

    // Limit to 15 articles per scan to stay within timeout
    const batch = filesToScan.slice(0, 15);
    const results = [];

    for (const file of batch) {
        const slug = file.name.replace(".html", "");
        try {
            const { content: html } = await ghFileContent(`articles/${file.name}`);
            if (!html) { results.push({ slug, error: "Could not fetch HTML" }); continue; }

            // ── Extract images ──
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

            // ── SEO analysis ──
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

            // ── Internal links ──
            const linkRegex = /<a[^>]+href=["']([^"'#][^"']*)["']/gi;
            const internalLinks = [];
            while ((m = linkRegex.exec(html)) !== null) {
                const href = m[1];
                if (!href.startsWith("http") && !href.startsWith("mailto:") && !href.startsWith("javascript:")) {
                    internalLinks.push(href);
                }
            }

            // ── SEO Score ──
            let seoScore = 100;
            const seoIssues = [];

            if (!titleMatch) { seoScore -= 15; seoIssues.push("Pas de balise <title>"); }
            else {
                const tLen = titleMatch[1].length;
                if (tLen < 30) { seoScore -= 5; seoIssues.push(`Title trop court (${tLen} cars)`); }
                if (tLen > 65) { seoScore -= 5; seoIssues.push(`Title trop long (${tLen} cars)`); }
            }

            if (!metaDescMatch) { seoScore -= 15; seoIssues.push("Pas de meta description"); }
            else {
                const dLen = metaDescMatch[1].length;
                if (dLen < 110) { seoScore -= 5; seoIssues.push(`Meta desc trop courte (${dLen} cars)`); }
                if (dLen > 165) { seoScore -= 5; seoIssues.push(`Meta desc trop longue (${dLen} cars)`); }
            }

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

            results.push({
                slug,
                images: {
                    total: imgs.length,
                    missing: missingImgs,
                    missingCount: missingImgs.length,
                    details: imgResults,
                },
                seo: {
                    score: Math.max(0, seoScore),
                    title: titleMatch ? titleMatch[1] : null,
                    titleLength: titleMatch ? titleMatch[1].length : 0,
                    metaDescription: metaDescMatch ? metaDescMatch[1].substring(0, 160) : null,
                    metaDescLength: metaDescMatch ? metaDescMatch[1].length : 0,
                    h1Count: h1Matches.length,
                    h2Count: h2Matches.length,
                    hasOgTags: !!(ogTitleMatch && ogDescMatch && ogImgMatch),
                    hasCanonical: !!canonicalMatch,
                    imgCount: imgs.length,
                    altMissing,
                    wordCount,
                    issues: seoIssues,
                },
                links: {
                    internal: internalLinks.length,
                    details: internalLinks.slice(0, 20),
                },
                viewUrl: `${SITE_URL}/articles/${slug}.html`,
            });
        } catch (e) {
            results.push({ slug, error: e.message });
        }
    }

    // Calculate averages
    const validResults = results.filter(r => !r.error);
    const avgSeo = validResults.length
        ? Math.round(validResults.reduce((sum, r) => sum + r.seo.score, 0) / validResults.length)
        : 0;
    const totalMissing = validResults.reduce((sum, r) => sum + r.images.missingCount, 0);
    const articlesWithNoImages = validResults.filter(r => r.images.total === 0);

    return {
        scanned: batch.length,
        totalAvailable: filesToScan.length,
        avgSeoScore: avgSeo,
        totalMissingImages: totalMissing,
        articlesWithNoImages: articlesWithNoImages.length,
        articles: results,
    };
}

// ═══════════════════════════════════════════════════════════
// STATS
// ═══════════════════════════════════════════════════════════

async function getStats() {
    const [htmlFiles, postFiles, imgFiles, igFiles] = await Promise.all([
        ghListDir("articles"),
        ghListDir("posts"),
        ghListDir("images"),
        ghListDir("instagram"),
    ]);

    const { content: ajContent } = await ghFileContent("articles.json");
    const ajData = ajContent ? JSON.parse(ajContent) : { articles: [] };

    const categories = {};
    (ajData.articles || []).forEach(a => {
        const cat = a.category || "Uncategorized";
        categories[cat] = (categories[cat] || 0) + 1;
    });

    const { content: topicsContent } = await ghFileContent("data/used_topics.json");
    const topics = topicsContent ? JSON.parse(topicsContent) : {};

    const { content: kwContent } = await ghFileContent("data/keywords.txt");
    const totalKeywords = kwContent ? kwContent.split("\n").filter(l => l.trim() && !l.startsWith("#")).length : 0;

    // Blog pages
    const blogPages = [];
    const rootFiles = await ghListDir("");
    rootFiles.filter(f => f.name.match(/^blog(-\d+)?\.html$/)).forEach(f => blogPages.push(f.name));

    const launchDate = new Date("2026-02-22");
    const now = new Date();
    const weekNum = Math.max(1, Math.floor((now - launchDate) / (7 * 24 * 60 * 60 * 1000)) + 1);
    let articlesPerDay = 3;
    if (weekNum >= 10) articlesPerDay = 6;
    else if (weekNum >= 7) articlesPerDay = 5;
    else if (weekNum >= 4) articlesPerDay = 4;

    return {
        articles: htmlFiles.length,
        posts: postFiles.filter(f => f.name.endsWith(".json")).length,
        images: imgFiles.length,
        instagram: igFiles.filter(f => f.name.endsWith(".jpg") || f.name.endsWith(".png")).length,
        categories,
        blogPages,
        topics: {
            keyword: { used: (topics.keyword || []).length, total: totalKeywords },
            product: { used: (topics.product || []).length },
            freebie: { used: (topics.freebie || []).length },
        },
        schedule: { week: weekNum, articlesPerDay, launchDate: "2026-02-22" },
    };
}

// ═══════════════════════════════════════════════════════════
// TOPICS
// ═══════════════════════════════════════════════════════════

async function getTopics() {
    const { content: topicsContent } = await ghFileContent("data/used_topics.json");
    const topics = topicsContent ? JSON.parse(topicsContent) : {};

    const { content: kwContent } = await ghFileContent("data/keywords.txt");
    const allKeywords = kwContent
        ? kwContent.split("\n").filter(l => l.trim() && !l.startsWith("#")).map(l => l.trim())
        : [];

    const usedKeywords = new Set(topics.keyword || []);
    const remainingKeywords = allKeywords.filter(k => !usedKeywords.has(k));

    return {
        used: topics,
        remaining: { keyword: remainingKeywords, keywordCount: remainingKeywords.length },
        allKeywords,
    };
}

// ═══════════════════════════════════════════════════════════
// TRIGGER WORKFLOW
// ═══════════════════════════════════════════════════════════

async function triggerWorkflow(action) {
    const validActions = [
        "generate-batch", "generate-keyword", "generate-product", "generate-freebie",
        "build-site", "full-rebuild", "maintenance-scan",
    ];
    if (!validActions.includes(action)) throw new Error(`Invalid action: ${action}`);

    const res = await ghFetch(`actions/workflows/autoblog.yml/dispatches`, {
        method: "POST",
        body: JSON.stringify({ ref: BRANCH, inputs: { action } }),
    });

    if (!res.ok && res.status !== 204) {
        const text = await res.text();
        throw new Error(`GitHub ${res.status}: ${text.substring(0, 200)}`);
    }

    return { triggered: true, action, message: `Workflow triggered: ${action}` };
}

// ═══════════════════════════════════════════════════════════
// WORKFLOW RUNS
// ═══════════════════════════════════════════════════════════

async function getWorkflowRuns() {
    try {
        const data = await ghJSON(`actions/runs?per_page=10&branch=${BRANCH}`);
        const runs = (data.workflow_runs || []).map(r => ({
            id: r.id,
            name: r.name,
            status: r.status,
            conclusion: r.conclusion,
            created_at: r.created_at,
            updated_at: r.updated_at,
            html_url: r.html_url,
            run_number: r.run_number,
        }));
        return { runs };
    } catch {
        return { runs: [] };
    }
}

// ═══════════════════════════════════════════════════════════
// MAIN HANDLER
// ═══════════════════════════════════════════════════════════

exports.handler = async (event) => {
    if (event.httpMethod === "OPTIONS") {
        return { statusCode: 204, headers, body: "" };
    }

    const authErr = checkAuth(event);
    if (authErr) return authErr;

    const params = event.queryStringParameters || {};
    const action = params.action || "";

    try {
        let result;
        switch (action) {
            case "articles": result = await listArticles(); break;
            case "delete":
                if (event.httpMethod !== "DELETE" && event.httpMethod !== "POST")
                    return { statusCode: 405, headers, body: JSON.stringify({ error: "Use DELETE or POST" }) };
                result = await cascadeDelete(params.slug);
                break;
            case "health": result = await healthCheck(); break;
            case "deep-scan": result = await deepScan(params.slug || null); break;
            case "stats": result = await getStats(); break;
            case "topics": result = await getTopics(); break;
            case "generate": result = await triggerWorkflow(params.type || "generate-batch"); break;
            case "runs": result = await getWorkflowRuns(); break;
            default:
                return {
                    statusCode: 400, headers, body: JSON.stringify({
                        error: "Unknown action",
                        available: ["articles", "delete", "health", "deep-scan", "stats", "topics", "generate", "runs"],
                    })
                };
        }
        return { statusCode: 200, headers, body: JSON.stringify(result) };
    } catch (e) {
        console.error("Admin API error:", e);
        return { statusCode: 500, headers, body: JSON.stringify({ error: e.message }) };
    }
};
