// ═══════════════════════════════════════════════════════════
// ADMIN API V2 — Little Smart Genius Full-Control Backend
// Netlify Serverless Function — Complete project control
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
// ACTION: LIST ARTICLES
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
        const coverImgs = imgFiles.filter(f => f.name.startsWith(slug) && f.name.includes("-cover-"));
        const contentImgs = imgFiles.filter(f => f.name.startsWith(slug) && f.name.includes("-img"));
        const igPost = igFiles.filter(f => f.name.startsWith(slug));

        let health = "ok";
        if (!hasHtml) health = "error";
        else if (coverImgs.length === 0) health = "warning";
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

    const [htmlFiles, postFiles, imgFiles, igFiles] = await Promise.all([
        ghListDir("articles"),
        ghListDir("posts"),
        ghListDir("images"),
        ghListDir("instagram"),
    ]);

    const toDelete = [];

    htmlFiles.filter(f => f.name === `${slug}.html`).forEach(f => {
        toDelete.push({ path: `articles/${f.name}`, sha: f.sha });
    });
    postFiles.filter(f => f.name.startsWith(slug)).forEach(f => {
        toDelete.push({ path: `posts/${f.name}`, sha: f.sha });
    });
    imgFiles.filter(f => f.name.startsWith(slug)).forEach(f => {
        toDelete.push({ path: `images/${f.name}`, sha: f.sha });
    });
    igFiles.filter(f => f.name.startsWith(slug)).forEach(f => {
        toDelete.push({ path: `instagram/${f.name}`, sha: f.sha });
    });

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

    // HTML without JSON
    htmlSlugs.forEach(slug => {
        if (!postSlugs.has(slug)) {
            issues.push({ type: "warning", category: "orphan", message: `Article HTML sans JSON: ${slug}` });
            score -= 2;
        }
    });

    // JSON without HTML
    postSlugs.forEach(slug => {
        if (!htmlSlugs.has(slug)) {
            issues.push({ type: "error", category: "orphan", message: `Post JSON sans HTML: ${slug}` });
            score -= 3;
        }
    });

    // Missing from index
    htmlSlugs.forEach(slug => {
        if (!indexSlugs.has(slug)) {
            issues.push({ type: "warning", category: "index", message: `Article absent de articles.json: ${slug}` });
            score -= 2;
        }
    });

    // Index without HTML
    indexSlugs.forEach(slug => {
        if (!htmlSlugs.has(slug)) {
            issues.push({ type: "error", category: "index", message: `Entree index sans HTML: ${slug}` });
            score -= 3;
        }
    });

    // Missing cover images
    htmlSlugs.forEach(slug => {
        const hasCover = imgFiles.some(f => f.name.startsWith(slug) && f.name.includes("-cover-"));
        if (!hasCover) {
            issues.push({ type: "error", category: "image", message: `Image cover manquante: ${slug}` });
            score -= 5;
        }
    });

    // Missing content images
    htmlSlugs.forEach(slug => {
        const contentImgs = imgFiles.filter(f => f.name.startsWith(slug) && f.name.includes("-img"));
        if (contentImgs.length < 4) {
            issues.push({ type: "warning", category: "image", message: `Images contenu (${contentImgs.length}/4): ${slug}` });
            score -= 1;
        }
    });

    // Sitemap check
    const { content: smContent } = await ghFileContent("sitemap.xml");
    if (smContent) {
        htmlSlugs.forEach(slug => {
            if (!smContent.includes(slug)) {
                issues.push({ type: "warning", category: "sitemap", message: `Article absent du sitemap: ${slug}` });
                score -= 1;
            }
        });
    }

    // Instagram check
    htmlSlugs.forEach(slug => {
        const hasIg = igFiles.some(f => f.name.startsWith(slug));
        if (!hasIg) {
            issues.push({ type: "info", category: "instagram", message: `Pas de post Instagram: ${slug}` });
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

    const categories = {};
    (ajData.articles || []).forEach(a => {
        const cat = a.category || "Uncategorized";
        categories[cat] = (categories[cat] || 0) + 1;
    });

    const { content: topicsContent } = await ghFileContent("data/used_topics.json");
    const topics = topicsContent ? JSON.parse(topicsContent) : {};

    const { content: kwContent } = await ghFileContent("data/keywords.txt");
    const totalKeywords = kwContent ? kwContent.split("\n").filter(l => l.trim() && !l.startsWith("#")).length : 0;

    // Calculate schedule info
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
        topics: {
            keyword: { used: (topics.keyword || []).length, total: totalKeywords },
            product: { used: (topics.product || []).length },
            freebie: { used: (topics.freebie || []).length },
        },
        schedule: {
            week: weekNum,
            articlesPerDay,
            launchDate: "2026-02-22",
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
        remaining: { keyword: remainingKeywords, keywordCount: remainingKeywords.length },
        allKeywords,
    };
}

// ═══════════════════════════════════════════════════════════
// ACTION: TRIGGER WORKFLOW
// ═══════════════════════════════════════════════════════════

async function triggerWorkflow(action) {
    const validActions = [
        "generate-batch", "generate-keyword", "generate-product", "generate-freebie",
        "build-site", "full-rebuild", "maintenance-scan",
    ];
    if (!validActions.includes(action)) throw new Error(`Invalid action: ${action}`);

    const res = await ghFetch(`actions/workflows/autoblog.yml/dispatches`, {
        method: "POST",
        body: JSON.stringify({
            ref: BRANCH,
            inputs: { action },
        }),
    });

    if (!res.ok && res.status !== 204) {
        const text = await res.text();
        throw new Error(`GitHub ${res.status}: ${text.substring(0, 200)}`);
    }

    return { triggered: true, action, message: `Workflow triggered: ${action}` };
}

// ═══════════════════════════════════════════════════════════
// ACTION: WORKFLOW RUNS
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
                result = await triggerWorkflow(params.type || "generate-batch");
                break;
            case "runs":
                result = await getWorkflowRuns();
                break;
            default:
                return {
                    statusCode: 400, headers,
                    body: JSON.stringify({
                        error: "Unknown action",
                        available: ["articles", "delete", "health", "stats", "topics", "generate", "runs"],
                    }),
                };
        }

        return { statusCode: 200, headers, body: JSON.stringify(result) };
    } catch (e) {
        console.error("Admin API error:", e);
        return { statusCode: 500, headers, body: JSON.stringify({ error: e.message }) };
    }
};
