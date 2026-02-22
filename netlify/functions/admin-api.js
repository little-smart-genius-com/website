// ═══════════════════════════════════════════════════════════
// ADMIN API — Little Smart Genius Dashboard Backend
// Netlify Serverless Function — Full project control
// ═══════════════════════════════════════════════════════════

const GITHUB_API = "https://api.github.com";
const PAT = process.env.GITHUB_PAT;
const REPO = process.env.GITHUB_REPO || "little-smart-genius-com/website";
const ADMIN_PASS = process.env.ADMIN_PASSWORD || "";
const BRANCH = "main";

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
    if (!res.ok && opts.okStatuses && !opts.okStatuses.includes(res.status)) {
        const text = await res.text();
        throw new Error(`GitHub ${res.status}: ${text.substring(0, 200)}`);
    }
    return res;
}

async function ghJSON(path) {
    const res = await ghFetch(path);
    return res.json();
}

async function ghFileContent(path) {
    try {
        const data = await ghJSON(`contents/${path}?ref=${BRANCH}`);
        if (data.content) {
            return { content: Buffer.from(data.content, "base64").toString("utf-8"), sha: data.sha };
        }
        return { content: null, sha: null };
    } catch {
        return { content: null, sha: null };
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
// ACTION: LIST ARTICLES
// ═══════════════════════════════════════════════════════════

async function listArticles() {
    const { content } = await ghFileContent("articles.json");
    if (!content) return { articles: [], total: 0 };

    const data = JSON.parse(content);
    const articles = data.articles || [];

    // Check which files actually exist
    const [htmlFiles, imgFiles, igFiles] = await Promise.all([
        ghListDir("articles"),
        ghListDir("images"),
        ghListDir("instagram"),
    ]);

    const htmlSet = new Set(htmlFiles.map(f => f.name));
    const imgSet = new Set(imgFiles.map(f => f.name));
    const igSet = new Set(igFiles.map(f => f.name));

    const enriched = articles.map(a => {
        const slug = a.slug || "";
        const hasHtml = htmlSet.has(`${slug}.html`);
        const coverImgs = imgFiles.filter(f => f.name.startsWith(slug) && f.name.includes("-cover-"));
        const contentImgs = imgFiles.filter(f => f.name.startsWith(slug) && f.name.includes("-img"));
        const igPost = igFiles.filter(f => f.name.startsWith(slug));

        return {
            ...a,
            hasHtml,
            imageCount: coverImgs.length + contentImgs.length,
            hasInstagram: igPost.length > 0,
            health: hasHtml && coverImgs.length > 0 ? "ok" : "warning",
        };
    });

    return { articles: enriched, total: enriched.length };
}

// ═══════════════════════════════════════════════════════════
// ACTION: CASCADE DELETE
// ═══════════════════════════════════════════════════════════

async function cascadeDelete(slug) {
    if (!slug) throw new Error("Missing slug parameter");

    const deleted = [];
    const errors = [];

    // 1. Find all files matching this slug
    const [htmlFiles, postFiles, imgFiles, igFiles] = await Promise.all([
        ghListDir("articles"),
        ghListDir("posts"),
        ghListDir("images"),
        ghListDir("instagram"),
    ]);

    const toDelete = [];

    // articles/{slug}.html
    const html = htmlFiles.find(f => f.name === `${slug}.html`);
    if (html) toDelete.push({ path: `articles/${html.name}`, sha: html.sha });

    // posts/{slug}-*.json
    postFiles.filter(f => f.name.startsWith(slug)).forEach(f => {
        toDelete.push({ path: `posts/${f.name}`, sha: f.sha });
    });

    // images/{slug}-*.webp
    imgFiles.filter(f => f.name.startsWith(slug)).forEach(f => {
        toDelete.push({ path: `images/${f.name}`, sha: f.sha });
    });

    // instagram/{slug}-*.jpg/.txt
    igFiles.filter(f => f.name.startsWith(slug)).forEach(f => {
        toDelete.push({ path: `instagram/${f.name}`, sha: f.sha });
    });

    // Delete files sequentially (GitHub API rate limit)
    for (const file of toDelete) {
        try {
            await ghDeleteFile(file.path, file.sha, `Dashboard: delete ${slug}`);
            deleted.push(file.path);
        } catch (e) {
            errors.push({ path: file.path, error: e.message });
        }
    }

    // 2. Update articles.json (remove entry)
    try {
        const { content: ajContent, sha: ajSha } = await ghFileContent("articles.json");
        if (ajContent) {
            const ajData = JSON.parse(ajContent);
            ajData.articles = (ajData.articles || []).filter(a => a.slug !== slug);
            ajData.total_articles = ajData.articles.length;
            await ghFetch(`contents/articles.json`, {
                method: "PUT",
                body: JSON.stringify({
                    message: `Dashboard: remove ${slug} from articles.json`,
                    content: Buffer.from(JSON.stringify(ajData, null, 2)).toString("base64"),
                    sha: ajSha,
                    branch: BRANCH,
                }),
            });
            deleted.push("articles.json (entry removed)");
        }
    } catch (e) { errors.push({ path: "articles.json", error: e.message }); }

    // 3. Update search_index.json (remove entry)
    try {
        const { content: siContent, sha: siSha } = await ghFileContent("search_index.json");
        if (siContent) {
            const siData = JSON.parse(siContent);
            siData.articles = (siData.articles || []).filter(a => a.slug !== slug);
            siData.total_articles = siData.articles.length;
            await ghFetch(`contents/search_index.json`, {
                method: "PUT",
                body: JSON.stringify({
                    message: `Dashboard: remove ${slug} from search_index.json`,
                    content: Buffer.from(JSON.stringify(siData, null, 2)).toString("base64"),
                    sha: siSha,
                    branch: BRANCH,
                }),
            });
            deleted.push("search_index.json (entry removed)");
        }
    } catch (e) { errors.push({ path: "search_index.json", error: e.message }); }

    // 4. Update sitemap.xml (remove URL)
    try {
        const { content: smContent, sha: smSha } = await ghFileContent("sitemap.xml");
        if (smContent) {
            const urlPattern = new RegExp(
                `\\s*<url>\\s*<loc>[^<]*${slug}[^<]*</loc>[\\s\\S]*?</url>`, "g"
            );
            const newSitemap = smContent.replace(urlPattern, "");
            if (newSitemap !== smContent) {
                await ghFetch(`contents/sitemap.xml`, {
                    method: "PUT",
                    body: JSON.stringify({
                        message: `Dashboard: remove ${slug} from sitemap.xml`,
                        content: Buffer.from(newSitemap).toString("base64"),
                        sha: smSha,
                        branch: BRANCH,
                    }),
                });
                deleted.push("sitemap.xml (URL removed)");
            }
        }
    } catch (e) { errors.push({ path: "sitemap.xml", error: e.message }); }

    return { slug, deleted, errors, totalDeleted: deleted.length };
}

// ═══════════════════════════════════════════════════════════
// ACTION: HEALTH CHECK
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

    // Check: HTML without JSON
    htmlSlugs.forEach(slug => {
        if (!postSlugs.has(slug)) {
            issues.push({ type: "warning", category: "orphan", message: `Article HTML sans JSON: ${slug}` });
            score -= 2;
        }
    });

    // Check: JSON without HTML
    postSlugs.forEach(slug => {
        if (!htmlSlugs.has(slug)) {
            issues.push({ type: "error", category: "orphan", message: `Post JSON sans HTML: ${slug}` });
            score -= 3;
        }
    });

    // Check: Articles missing from index
    htmlSlugs.forEach(slug => {
        if (!indexSlugs.has(slug)) {
            issues.push({ type: "warning", category: "index", message: `Article absent de articles.json: ${slug}` });
            score -= 2;
        }
    });

    // Check: Index entries without HTML
    indexSlugs.forEach(slug => {
        if (!htmlSlugs.has(slug)) {
            issues.push({ type: "error", category: "index", message: `Entrée index sans HTML: ${slug}` });
            score -= 3;
        }
    });

    // Check: Missing cover images
    htmlSlugs.forEach(slug => {
        const hasCover = imgFiles.some(f => f.name.startsWith(slug) && f.name.includes("-cover-"));
        if (!hasCover) {
            issues.push({ type: "error", category: "image", message: `Image cover manquante: ${slug}` });
            score -= 5;
        }
    });

    // Check: Sitemap
    const { content: smContent } = await ghFileContent("sitemap.xml");
    if (smContent) {
        htmlSlugs.forEach(slug => {
            if (!smContent.includes(slug)) {
                issues.push({ type: "warning", category: "sitemap", message: `Article absent du sitemap: ${slug}` });
                score -= 1;
            }
        });
    }

    return {
        score: Math.max(0, score),
        totalArticles: htmlSlugs.size,
        totalPosts: postSlugs.size,
        totalImages: imgFiles.length,
        totalInstagram: igFiles.filter(f => f.name.endsWith(".jpg")).length,
        issues,
        issueCount: issues.length,
    };
}

// ═══════════════════════════════════════════════════════════
// ACTION: STATS
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

    // Categories breakdown
    const categories = {};
    (ajData.articles || []).forEach(a => {
        const cat = a.category || "Uncategorized";
        categories[cat] = (categories[cat] || 0) + 1;
    });

    // Topics
    const { content: topicsContent } = await ghFileContent("data/used_topics.json");
    const topics = topicsContent ? JSON.parse(topicsContent) : {};

    const { content: kwContent } = await ghFileContent("data/keywords.txt");
    const totalKeywords = kwContent ? kwContent.split("\n").filter(l => l.trim() && !l.startsWith("#")).length : 0;

    return {
        articles: htmlFiles.length,
        posts: postFiles.filter(f => f.name.endsWith(".json")).length,
        images: imgFiles.length,
        instagram: igFiles.filter(f => f.name.endsWith(".jpg")).length,
        categories,
        topics: {
            keyword: { used: (topics.keyword || []).length, total: totalKeywords },
            product: { used: (topics.product || []).length },
            freebie: { used: (topics.freebie || []).length },
        },
    };
}

// ═══════════════════════════════════════════════════════════
// ACTION: TOPICS
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
        remaining: {
            keyword: remainingKeywords,
            keywordCount: remainingKeywords.length,
        },
        allKeywords,
    };
}

// ═══════════════════════════════════════════════════════════
// ACTION: TRIGGER WORKFLOW
// ═══════════════════════════════════════════════════════════

async function triggerWorkflow(slot) {
    const validSlots = ["keyword", "product", "freebie", "batch", "build-only"];
    if (!validSlots.includes(slot)) throw new Error(`Invalid slot: ${slot}`);

    await ghFetch(`actions/workflows/autoblog.yml/dispatches`, {
        method: "POST",
        body: JSON.stringify({
            ref: BRANCH,
            inputs: { slot },
        }),
    });

    return { triggered: true, slot, message: `Workflow triggered for slot: ${slot}` };
}

// ═══════════════════════════════════════════════════════════
// MAIN HANDLER
// ═══════════════════════════════════════════════════════════

exports.handler = async (event) => {
    // CORS preflight
    if (event.httpMethod === "OPTIONS") {
        return { statusCode: 204, headers, body: "" };
    }

    // Auth
    const authErr = checkAuth(event);
    if (authErr) return authErr;

    const params = event.queryStringParameters || {};
    const action = params.action || "";

    try {
        let result;

        switch (action) {
            case "articles":
                result = await listArticles();
                break;
            case "delete":
                if (event.httpMethod !== "DELETE" && event.httpMethod !== "POST") {
                    return { statusCode: 405, headers, body: JSON.stringify({ error: "Use DELETE or POST" }) };
                }
                result = await cascadeDelete(params.slug);
                break;
            case "health":
                result = await healthCheck();
                break;
            case "stats":
                result = await getStats();
                break;
            case "topics":
                result = await getTopics();
                break;
            case "generate":
                result = await triggerWorkflow(params.slot || "batch");
                break;
            default:
                return {
                    statusCode: 400, headers,
                    body: JSON.stringify({
                        error: "Unknown action",
                        available: ["articles", "delete", "health", "stats", "topics", "generate"],
                    }),
                };
        }

        return { statusCode: 200, headers, body: JSON.stringify(result) };
    } catch (e) {
        console.error("Admin API error:", e);
        return { statusCode: 500, headers, body: JSON.stringify({ error: e.message }) };
    }
};
