import codecs
import re

with codecs.open('old_admin.html', 'r', 'utf-8') as f:
    html = f.read()

# 1. Update CSS Theme
css_injection = """        /* ═══════════════════════════ PREMIUM GLASSMORPHISM THEME ═══════════════════════════ */
        :root {
            --bg: #09090b;
            --bg2: rgba(24, 24, 27, 0.65);
            --card: rgba(39, 39, 42, 0.4);
            --card-hover: rgba(39, 39, 42, 0.8);
            --border: rgba(255, 255, 255, 0.1);
            --text: #f8fafc;
            --text-dim: #94a3b8;
            --brand: #f59e0b;
            --brand-dark: #fbbf24;
            --green: #10b981;
            --red: #ef4444;
            --blue: #3b82f6;
            --purple: #8b5cf6;
            --cyan: #06b6d4;
            --pink: #ec4899;
            --radius: 16px;
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            --glass-blur: blur(16px);
        }

        [data-theme="light"] {
            --bg: #f8fafc;
            --bg2: rgba(255, 255, 255, 0.7);
            --card: rgba(255, 255, 255, 0.5);
            --card-hover: rgba(255, 255, 255, 0.8);
            --border: rgba(0, 0, 0, 0.08);
            --text: #0f172a;
            --text-dim: #64748b;
            --shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }

        /* Ambient Orbs */
        .ambient-orb { position: fixed; border-radius: 50%; filter: var(--glass-blur); z-index: 0; opacity: 0.15; pointer-events: none; filter: blur(120px); }
        .orb-1 { top: -10%; left: -5%; width: 500px; height: 500px; background: var(--brand); }
        .orb-2 { bottom: -10%; right: -5%; width: 600px; height: 600px; background: var(--purple); }

        /* Glassmorphism applications */
        .top-bar { backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur); background: var(--bg2); }
        .tabs { background: transparent; }
        .tab { background: var(--card); backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur); }
        .tab.active { background: var(--card-hover); border-color: var(--brand); }
        
        .stat-card, .action-card, .scan-card, .topic-section, .guide-section, .kw-editor, .login-box, .modal {
            background: var(--card);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            border: 1px solid var(--border);
        }
        
        .tbl-wrap { background: var(--card); backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur); }
        #app { position: relative; z-index: 10; }
        
        /* Fix login input */
        .login-box input { background: rgba(0,0,0,0.2) !important; color: white !important; }
        [data-theme="light"] .login-box input { background: rgba(255,255,255,0.5) !important; color: black !important; }

        /* API Keys styles */
        .api-key-row { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
        .api-key-input { flex: 1; padding: 12px 16px; background: rgba(0,0,0,0.2); border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-family: monospace; }
        [data-theme="light"] .api-key-input { background: rgba(255,255,255,0.5); }
        .api-status { width: 120px; text-align: center; padding: 8px; border-radius: 8px; font-weight: 700; font-size: 0.85rem; }
        .status-idle { background: var(--card); color: var(--text-dim); }
        .status-ok { background: rgba(16, 185, 129, 0.15); color: var(--green); }
        .status-fail { background: rgba(239, 68, 68, 0.15); color: var(--red); }
        .status-testing { background: rgba(59, 130, 246, 0.15); color: var(--blue); }
"""

# Replace root up to exactly "* {"
html = re.sub(r':root\s*\{.*?(?=\* \{)', css_injection, html, flags=re.DOTALL)

# Add Orbs
html = html.replace('<body>', '<body>\n    <div class="ambient-orb orb-1"></div>\n    <div class="ambient-orb orb-2"></div>')

# 2. Add API Keys Tab
tab_html = """            <div class="tab" data-tab="runs" data-tip="Historique des exécutions GitHub Actions">📋 Runs</div>
            <div class="tab" data-tab="apikeys" data-tip="Gérer et tester les clés API Pollinations">🔑 API Keys</div>"""
html = html.replace('<div class="tab" data-tab="runs" data-tip="Historique des exécutions GitHub Actions">📋 Runs</div>', tab_html)

# 3. Add API Keys Panel
api_panel = """
        <!-- ═══════ API KEYS MANAGER ═══════ -->
        <div class="panel" id="panel-apikeys">
            <div class="panel-header">
                <h2>🔑 API Keys Manager</h2>
            </div>
            
            <div class="topic-section">
                <h3 style="margin-bottom: 8px;">Pollinations.ai Keys Tester</h3>
                <p style="color:var(--text-dim); font-size:0.85rem; margin-bottom: 24px; line-height:1.6">
                    Testez vos clés API Pollinations gratuitement ici. Si une génération échoue, une clé a pu expirer (erreur 429).<br>
                    <strong>Note:</strong> Mettez à jour les clés dans vos Secrets GitHub (POLLINATIONS_API_KEY_1 à 5).
                </p>
                <div id="apiKeysList"></div>
                <button class="btn btn-brand" style="margin-top: 16px;" onclick="testAllKeys()" id="testKeysBtn">🧪 Tester les 5 Clés</button>
            </div>
        </div>
"""
html = html.replace('<!-- ═══════ GUIDE ═══════ -->', api_panel + '\n        <!-- ═══════ GUIDE ═══════ -->')

# 4. Add Bulk Fix Button in Blog Tab
deepscan_btn = '<button class="btn btn-brand" id="deepScanBtn" onclick="runDeepScan()" data-tip="Analyse SEO complète : title, meta, H1, images, liens internes">🔍 Lancer le Scan Complet</button>'
deepscan_repl = deepscan_btn + '\n                    <button class="btn btn-purple" id="bulkFixBtn" onclick="bulkFixSeo()" style="display:none" data-tip="Répare automatiquement tous les problèmes SEO (Title, Meta, H1) !">✨ Bulk Fix All SEO</button>'
html = html.replace(deepscan_btn, deepscan_repl)

# 5. Inject API Key & Bulk Fix JS
js_addons = """
        // ═══════ NEW: API KEYS MANAGER & SEO BULK FIX ═══════
        function getSavedKeys() { try { return JSON.parse(localStorage.getItem('lsg_api_keys') || '["","","","",""]') } catch { return ["","","","",""] } }
        function renderApiKeysManager() {
            const keys = getSavedKeys(); let h = "";
            for(let i=0; i<5; i++) {
                h += `<div class="api-key-row">
                    <span style="font-weight:700; color:var(--text-dim); width: 24px;">#${i+1}</span>
                    <input type="text" class="api-key-input" id="apiKeyIn_${i}" value="${esc(keys[i])}" placeholder="Clé pollinations ${i+1}..." onchange="saveApiKeysLocally()">
                    <div class="api-status status-idle" id="apiStatus_${i}">Idle</div>
                </div>`;
            }
            document.getElementById("apiKeysList").innerHTML = h;
        }
        function saveApiKeysLocally() {
            const arr = []; for(let i=0; i<5; i++) arr.push(document.getElementById(`apiKeyIn_${i}`).value.trim());
            localStorage.setItem('lsg_api_keys', JSON.stringify(arr));
        }
        async function testAllKeys() {
            saveApiKeysLocally(); const keys = getSavedKeys(); const btn = document.getElementById("testKeysBtn");
            btn.innerHTML = '<div class="spinner"></div> Testing...'; btn.disabled = true;
            for(let i=0; i<5; i++) {
                const key = keys[i]; const statEl = document.getElementById(`apiStatus_${i}`);
                if(!key) { statEl.className = "api-status status-idle"; statEl.innerText = "Empty"; continue; }
                statEl.className = "api-status status-testing"; statEl.innerText = "Testing...";
                try {
                    const res = await fetch(`https://image.pollinations.ai/prompt/test?width=10&height=10&nologo=true`, {
                        headers: { 'Authorization': `Bearer ${key}` }
                    });
                    if(res.ok) { statEl.className = "api-status status-ok"; statEl.innerText = "✅ Active"; }
                    else if(res.status === 429) { statEl.className = "api-status status-fail"; statEl.innerText = "❌ 429 Limit"; }
                    else { statEl.className = "api-status status-fail"; statEl.innerText = `❌ Err ${res.status}`; }
                } catch(e) { statEl.className = "api-status status-fail"; statEl.innerText = "❌ Network Err"; }
            }
            btn.innerHTML = '🧪 Tester les 5 Clés'; btn.disabled = false;
        }

        let globalSeoList = [];
        async function bulkFixSeo() {
            const fixable = globalSeoList.filter(a => (a.seo && a.seo.issues && a.seo.issues.length > 0));
            if(!confirm(`Corriger automatiquement ${fixable.length} articles ?`)) return;
            toast("Bulk fixing started... please wait.", "info");
            document.getElementById("bulkFixBtn").innerHTML = '<div class="spinner"></div>';
            let fixedCount = 0;
            for(let a of fixable) {
                try { await api("fix-seo", { slug: a.slug }); fixedCount++; } catch(e) { console.error(e); }
            }
            toast(`✅ Bulk fix terminé ! ${fixedCount} réparés.`, "success");
            runDeepScan();
        }
"""
html = html.replace('// ═══════ UTILS ═══════', js_addons + '\n        // ═══════ UTILS ═══════')

# Handle tabs JS
old_loads = 'const loads = { articles: loadArticles, health: loadHealth, topics: () => { loadTopics(); loadKeywordsEditor() }, backups: loadSnapshots, runs: loadRuns };'
new_loads = 'const loads = { articles: loadArticles, health: loadHealth, topics: () => { loadTopics(); loadKeywordsEditor() }, backups: loadSnapshots, runs: loadRuns, apikeys: renderApiKeysManager };'
html = html.replace(old_loads, new_loads)

# Capture globalSeoList in Deep Scan
search_deep_scan = 'const d = await api("deep-scan");'
replace_deep_scan = search_deep_scan + ' globalSeoList = d.articles;'
html = html.replace(search_deep_scan, replace_deep_scan)

# Toggle Bulk fix visibility
search_sort = '// Sort: issues first'
replace_sort = """const fixable = globalSeoList.filter(a => a.seo && a.seo.issues && a.seo.issues.length > 0);
                if (fixable.length > 0) {
                    document.getElementById("bulkFixBtn").style.display = "inline-flex";
                    document.getElementById("bulkFixBtn").innerText = `✨ Bulk Fix All SEO (${fixable.length})`;
                } else {
                    document.getElementById("bulkFixBtn").style.display = "none";
                }
                // Sort: issues first"""
html = html.replace(search_sort, replace_sort)

with codecs.open('admin.html', 'w', 'utf-8') as f:
    f.write(html)
print("Merge script completed successfully!")
