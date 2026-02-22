/**
 * BLOG SEARCH & FILTER ENGINE — V4.0
 * Client-side search, category filters, sort, and IntersectionObserver infinite scroll.
 * Loads search_index.json once, then filters/sorts/renders in-memory.
 * 
 * Behaviour:
 * - Default: static pagination (server-rendered cards visible)
 * - User types in search / picks category / changes sort → dynamic mode:
 *   hides static cards + pagination, shows dynamic results
 * - Clearing all filters → back to static pagination
 */

(function () {
    'use strict';

    // ─── CONFIG ────────────────────────────────────────
    const BATCH_SIZE = 12;
    const INDEX_URL = 'search_index.json';

    // ─── STATE ─────────────────────────────────────────
    let allArticles = [];
    let filteredArticles = [];
    let displayedCount = 0;
    let isDynamicMode = false;

    // ─── DOM REFS ──────────────────────────────────────
    const searchInput = document.getElementById('blog-search-input');
    const categorySelect = document.getElementById('blog-category-select');
    const sortSelect = document.getElementById('blog-sort-select');
    const staticGrid = document.getElementById('blog-static-grid');
    const dynamicGrid = document.getElementById('blog-dynamic-grid');
    const sentinel = document.getElementById('blog-scroll-sentinel');
    const paginationNav = document.getElementById('blog-pagination-nav');
    const resultCount = document.getElementById('blog-result-count');
    const clearBtn = document.getElementById('blog-clear-filters');
    const toolbar = document.getElementById('blog-toolbar');

    if (!searchInput || !staticGrid || !dynamicGrid) return; // Not on blog page

    // ─── LOAD INDEX ────────────────────────────────────
    async function loadIndex() {
        // Strategy 0: Check if data was embedded inline via <script> tag
        if (window.__SEARCH_INDEX__ && window.__SEARCH_INDEX__.articles) {
            allArticles = window.__SEARCH_INDEX__.articles;
            populateCategories();
            console.log('Blog search: loaded', allArticles.length, 'articles from inline data');
            return;
        }

        // Strategy 1: Try fetch (works on HTTP/HTTPS)
        try {
            const res = await fetch(INDEX_URL);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            allArticles = data.articles || [];
            populateCategories();
            console.log('Blog search: loaded', allArticles.length, 'articles via fetch');
            return;
        } catch (err) {
            console.warn('Blog search: fetch failed, trying XHR fallback...', err.message);
        }

        // Strategy 2: XMLHttpRequest fallback (works on file:// protocol)
        try {
            const data = await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();
                xhr.open('GET', INDEX_URL, true);
                xhr.onload = function () {
                    if (xhr.status === 200 || xhr.status === 0) { // status 0 = file://
                        try {
                            resolve(JSON.parse(xhr.responseText));
                        } catch (e) {
                            reject(e);
                        }
                    } else {
                        reject(new Error(`XHR status ${xhr.status}`));
                    }
                };
                xhr.onerror = function () { reject(new Error('XHR network error')); };
                xhr.send();
            });
            allArticles = data.articles || [];
            populateCategories();
            console.log('Blog search: loaded', allArticles.length, 'articles via XHR');
            return;
        } catch (err) {
            console.warn('Blog search: XHR also failed', err.message);
        }

        // Strategy 3: Parse articles from the static grid DOM as last resort
        try {
            const cards = staticGrid.querySelectorAll('article');
            cards.forEach(card => {
                const link = card.querySelector('a');
                const img = card.querySelector('img');
                const h3 = card.querySelector('h3');
                const cat = card.querySelector('.text-brand.bg-orange-50, .text-brand.bg-slate-800');
                const excerpt = card.querySelector('.line-clamp-3');
                const date = card.querySelector('.text-slate-500:last-child');
                const readTime = card.querySelector('.text-xs.text-slate-500');

                if (h3 && link) {
                    allArticles.push({
                        title: h3.textContent.trim(),
                        url: link.getAttribute('href') || '',
                        image: img ? img.getAttribute('src') : '',
                        category: cat ? cat.textContent.trim() : '',
                        excerpt: excerpt ? excerpt.textContent.trim() : '',
                        date: date ? date.textContent.trim() : '',
                        reading_time: readTime ? parseInt(readTime.textContent) || 5 : 5,
                        keywords: (h3.textContent + ' ' + (excerpt ? excerpt.textContent : '')).toLowerCase().split(/\s+/)
                    });
                }
            });
            // Also try to load from other pagination pages (blog-2, blog-3...)
            populateCategories();
            console.log('Blog search: loaded', allArticles.length, 'articles from DOM fallback');
        } catch (err) {
            console.warn('Blog search: all loading strategies failed', err);
        }
    }

    function populateCategories() {
        const cats = new Set();
        allArticles.forEach(a => {
            if (a.category) cats.add(a.category);
        });
        const sorted = [...cats].sort();
        sorted.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            categorySelect.appendChild(opt);
        });
    }

    // ─── FILTER / SORT ─────────────────────────────────
    function applyFilters() {
        const query = searchInput.value.trim().toLowerCase();
        const category = categorySelect.value;
        const sortBy = sortSelect.value;

        // Determine if we should be in dynamic mode
        const shouldBeDynamic = query.length > 0 || category !== '';

        if (!shouldBeDynamic && sortBy === 'newest') {
            // Back to static pagination
            exitDynamicMode();
            return;
        }

        enterDynamicMode();

        // Filter
        filteredArticles = allArticles.filter(a => {
            // Category filter
            if (category && a.category !== category) return false;
            // Search filter
            if (query) {
                const haystack = [
                    a.title || '',
                    a.excerpt || '',
                    a.category || '',
                    ...(a.keywords || [])
                ].join(' ').toLowerCase();
                return haystack.includes(query);
            }
            return true;
        });

        // Sort
        switch (sortBy) {
            case 'oldest':
                filteredArticles.sort((a, b) => (a.iso_date || '').localeCompare(b.iso_date || ''));
                break;
            case 'az':
                filteredArticles.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
                break;
            case 'za':
                filteredArticles.sort((a, b) => (b.title || '').localeCompare(a.title || ''));
                break;
            case 'newest':
            default:
                filteredArticles.sort((a, b) => (b.iso_date || '').localeCompare(a.iso_date || ''));
                break;
        }

        // Reset display
        displayedCount = 0;
        dynamicGrid.innerHTML = '';
        loadNextBatch();

        // Update count
        updateResultCount();
    }

    function updateResultCount() {
        if (resultCount) {
            const query = searchInput.value.trim();
            if (query || categorySelect.value) {
                resultCount.textContent = `${filteredArticles.length} result${filteredArticles.length !== 1 ? 's' : ''} found`;
                resultCount.classList.remove('hidden');
            } else {
                resultCount.classList.add('hidden');
            }
        }
    }

    // ─── RENDER ────────────────────────────────────────
    function createCard(article) {
        const categoryBadge = article.category
            ? `<span class="text-xs font-bold uppercase tracking-wider text-brand bg-orange-50 dark:bg-slate-800 px-2 py-1 rounded-full">${escHtml(article.category)}</span>`
            : '';

        return `
        <article class="rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 border animate-fadeIn" style="background: var(--card); border-color: var(--bord);">
            <a href="${escHtml(article.url)}" class="block">
                <div class="aspect-video overflow-hidden">
                    <img src="${escHtml(article.image)}" alt="${escHtml(article.title)}" class="w-full h-full object-cover hover:scale-105 transition-transform duration-300" loading="lazy">
                </div>
                <div class="p-6">
                    <div class="flex items-center gap-2 mb-3">
                        ${categoryBadge}
                        <span class="text-xs text-slate-500">📖 ${article.reading_time || 5} min</span>
                    </div>
                    <h3 class="text-xl font-extrabold mb-3 hover:text-brand transition" style="color: var(--text);">
                        ${escHtml(article.title)}
                    </h3>
                    <p class="text-sm text-slate-600 dark:text-slate-400 mb-4 line-clamp-3">
                        ${escHtml((article.excerpt || '').substring(0, 150))}...
                    </p>
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-slate-500">${escHtml(article.date)}</span>
                        <span class="text-brand font-bold text-sm">Read More →</span>
                    </div>
                </div>
            </a>
        </article>`;
    }

    function loadNextBatch() {
        const batch = filteredArticles.slice(displayedCount, displayedCount + BATCH_SIZE);
        if (batch.length === 0) {
            sentinel.classList.add('hidden');
            if (displayedCount === 0) {
                dynamicGrid.innerHTML = `
                    <div class="col-span-full text-center py-16">
                        <div class="text-5xl mb-4">🔍</div>
                        <h3 class="text-xl font-bold mb-2" style="color: var(--text);">No articles found</h3>
                        <p class="text-slate-500">Try a different search term or category.</p>
                    </div>`;
            }
            return;
        }

        batch.forEach(article => {
            dynamicGrid.insertAdjacentHTML('beforeend', createCard(article));
        });
        displayedCount += batch.length;

        // Show/hide sentinel
        if (displayedCount < filteredArticles.length) {
            sentinel.classList.remove('hidden');
        } else {
            sentinel.classList.add('hidden');
        }
    }

    // ─── MODE TOGGLE ───────────────────────────────────
    function enterDynamicMode() {
        if (!isDynamicMode) {
            isDynamicMode = true;
            staticGrid.classList.add('hidden');
            dynamicGrid.classList.remove('hidden');
            if (paginationNav) paginationNav.classList.add('hidden');
            clearBtn.classList.remove('hidden');
        }
    }

    function exitDynamicMode() {
        isDynamicMode = false;
        staticGrid.classList.remove('hidden');
        dynamicGrid.classList.add('hidden');
        dynamicGrid.innerHTML = '';
        if (paginationNav) paginationNav.classList.remove('hidden');
        if (resultCount) resultCount.classList.add('hidden');
        clearBtn.classList.add('hidden');
        displayedCount = 0;
    }

    function clearAllFilters() {
        searchInput.value = '';
        categorySelect.value = '';
        sortSelect.value = 'newest';
        exitDynamicMode();
    }

    // ─── INTERSECTION OBSERVER ─────────────────────────
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && isDynamicMode) {
                loadNextBatch();
            }
        });
    }, { rootMargin: '200px' });

    if (sentinel) observer.observe(sentinel);

    // ─── EVENT LISTENERS ───────────────────────────────
    let debounceTimer;
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(applyFilters, 250);
    });

    categorySelect.addEventListener('change', applyFilters);
    sortSelect.addEventListener('change', applyFilters);
    clearBtn.addEventListener('click', clearAllFilters);

    // ─── UTILITIES ─────────────────────────────────────
    function escHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    // ─── INIT ──────────────────────────────────────────
    loadIndex();

})();
