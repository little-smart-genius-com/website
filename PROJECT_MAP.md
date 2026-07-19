# PROJECT_MAP.md

## [TECH_STACK]
- **Frontend Core**: HTML5, Vanilla JavaScript, Tailwind CSS (via static CSS files).
- **Static Generation Engine**: Python 3.x (custom build scripts).
- **Data Structure**: JSON (Acts as a NoSQL source of truth for articles).
- **Media**: WEBP format enforced for optimized delivery.
- **Search Engine**: Client-side in-memory search (`search_index.json` loaded via `blog-search.js`).

## [SYSTEM_FLOW]
1. **Data Ingestion**: Raw article data is stored as JSON in `posts/`.
2. **Build Process** (`build_articles.py`):
   - Reads JSON from `posts/`.
   - Parses into HTML using `ARTICLE_TEMPLATE`.
   - Generates output in `articles/`.
   - Builds `search_index.json` and `articles.json` for client-side functionality.
   - Triggers `generate_sitemap.py` to rebuild XML sitemaps.
   - *Crucial Step*: Archives processed JSON to `data/archive_posts/`.
3. **Client-Side Navigation**: User loads `blog/index.html`. `blog-search.js` hijacks rendering for dynamic filtering/searching over `search_index.json`. Static pagination (`blog/page-X.html`) serves as fallback and crawler entry-points.

## [ARCHITECTURE]
- **Simplicity First**: No complex frontend frameworks (React/Vue). Direct DOM manipulation via Vanilla JS.
- **Shared/Core Abstraction**: Python scripts share constants (e.g. `PROJECT_ROOT`, `POSTS_DIR`, `ARCHIVE_DIR`). `build_articles.py` is the monolithic compiler. 
- **Decoupled Data**: Content is strictly separated from presentation (JSON vs HTML template).
- **Safe Logging**: Python scripts use basic `print` stdout; client JS uses `console.log`. A more robust async logging system is pending.

## [ORPHANS & PENDING]
- **[BUG-01] Script Path Desync**: `comprehensive_repair.py`, `blog_check.py` and image generation scripts skip existing articles because they only query `posts/` instead of `data/archive_posts/` for the JSON source of truth.
- **[BUG-02] Missing Images Generation**: Several recent articles lack generated `.webp` images because the generation scripts failed to locate the moved JSON data.
- **[BUG-03] Indexing/SEO Bottleneck**: `blog_check.py` crashes on Windows environments due to `cp1252` encoding of the `\u2705` (✅) character, masking potential pipeline errors. `sitemap.xml` was temporarily out of sync, hindering Google Console indexing.
- **[PENDING] Safe Logging System**: Need to establish a non-blocking logging approach for Python build scripts.
