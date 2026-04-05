# Little Smart Genius - Product Requirements Document (PRD)

## 1. Product Overview and Goals

**Little Smart Genius** is a fully automated, AI-driven educational blog platform. The engine is a "Multi-Agent Generation Pipeline" that autonomously conducts research, writes educational articles, generates visuals, completely handles Search Engine Optimization (SEO), and syndicates content. The front-end serves as a blazing-fast static HTML website. 

**Core Goals:**
1. Maintain an autonomous pipeline capable of creating, validating, and formatting full blog posts with zero human intervention.
2. Deliver a static architecture providing top-tier Lighthouse performance and fault-intolerant SEO metadata structure.
3. Manage audience growth securely via Cloudflare Worker-backed endpoints for newsletter subscriptions and digital freebies.
4. Facilitate project administration via a secure, serverless dashboard that interacts with the GitHub API for code-level management directly from the browser.

## 2. Target Users and Main Use Cases

* **Readers (Parents, Educators, Children)**:
  * Browse the blog with an interactive, local search and filter experience.
  * Subscribe to email newsletters.
  * Claim and download educational digital freebies.
  * Contact the development team.
* **System Administrator (Site Owner)**:
  * Access a secure dashboard (`admin.html`).
  * Quickly delete or adjust generated articles that fail QA.
  * Monitor real-time Google Analytics (GA4) traffic and geographic data directly from the bespoke interface.
* **Search Engine Crawlers**:
  * Traverse a consistently updated `sitemap.xml`.
  * Validate robust, error-free canonical links, breadcrumbs, and OpenGraph structures.

## 3. Feature List with User Stories

### 3.1 Client-Side Blog Search & Filtering Engine
**User Story:** As a reader, I want to search for specific topics and filter by categories dynamically so I don't have to navigate through manual pagination links.

### 3.2 Secure API Cloudflare Integrations (Subscriptions & Freebies)
**User Story:** As a reader, I want to sign up for the newsletter safely, and securely receive digital content directly to my inbox in response.

### 3.3 Serverless Admin Dashboard
**User Story:** As an admin, I want a secure dashboard interface where I can trigger new AI builds, remove badly generated posts, and review site metrics without touching terminal code deployment.

### 3.4 Multi-Agent Article Pipeline
**User Story:** As the automation schedule, I want to synthesize new articles using LLMs into statically hosted HTML to continually grow the website organic reach.

## 4. Acceptance Criteria

### 4.1 Client-Side Blog Search
* **AC1:** Upon loading `/blog.html`, the system must attempt to load `search_index.json` via fetch. If fetch fails, the system must fallback gracefully to DOM-level parsing.
* **AC2:** When characters are typed into the `blog-search-input`, the default static grid must hide, and a filtered set of article chips must immediately render.
* **AC3:** Sorting dropdowns (A-Z, Oldest, Newest) must correctly arrange matching objects.
* **AC4:** Empty queries or cleared search filters should restore the static UI layout to avoid an empty state.

### 4.2 Secure Subscriptions
* **AC5:** A POST payload directed to `/workers/subscribe` must contain a rigidly formatted email string.
* **AC6:** The Worker environment must securely validate the email against third-party providers (e.g., MailerLite) without exposing the platform API key.
* **AC7:** Returns HTTP 200 and redirects to `/signup-success.html` on a valid success.

### 4.3 Admin Dashboard Functions
* **AC8:** The Dashboard UI must reject access if the local `ADMIN_PASSWORD` Bearer Token does not equal the Cloudflare Worker environment secret.
* **AC9:** Firing a `Delete` command against an article slug via Admin API must trigger multiple GitHub REST deletions (JSON file, HTML file, WebP Assets, IG assets).
* **AC10:** Admin deletions must synchronously update `articles.json` and `sitemap.xml` to strip references to the removed core slug.

### 4.4 Automated SEO Compilation (Static Builders)
* **AC11:** Execution of `build_articles.py` must convert a valid JSON from `/posts/` to a completely valid HTML document.
* **AC12:** The output HTML must have exactly one `<h1>`, `<title>` between 30-65 chars, and `<meta name="description">` between 110-155 characters.
* **AC13:** All image `<img>` elements ingested must output absolute paths normalized to `.webp` files.
* **AC14:** Breadcrumbs metadata script (JSON-LD) must always refer to canonical roots (e.g., `https://littlesmartgenius.com/`) and never local index paths (`index.html`).

## 5. Edge Cases and Invariants

* **Fallback Search Integrity:** If `search_index.json` corruption occurs, the frontend must intercept the error and silently extract data objects exclusively from the natively rendered HTML DOM elements to permit continuous filtering execution.
* **Missing AI Visuals**: If Pollinations AI times out and a cover image is completely missing in `images/`, the backend script must default the OpenGraph output to a generic fallback `og_image` to prevent Twitter/Facebook card crashing.
* **GitHub API Throttling**: Operations executed from the Admin UI may run into GitHub API rate limits. The Worker must respond gracefully with an informative error rather than breaking dashboard rendering.
* **Duplicate Slugs**: Article creation must enforce timestamp bounding on conflicting file generation preventing file-overwrites if the V6 pipeline attempts executing the exact same keyword.

## 6. Non-Functional Requirements

* **Performance Budget**: Initial load parameters for the landing `/index.html` must pass 95+ Mobile Lighthouse scoring.
* **Security & Secrets**: Strictly 0 API keys parameterizing GitHub, DeepSeek, GoogleAnalytics, MailerLite, or Webhooks can exist inside the `scripts/` or `src/` UI files. All execution bounds remain on local ENV or Cloudflare.
* **Cross-Browser Compatibility**: Core JavaScript interactions (`exit-intent.js`, `blog-search.js`) map down fully to ES6 standards conforming for Chrome, Safari, and Firefox.
* **Localization**: The platform strictly defaults to English (US) parameterization.

## 7. Open Questions (For QA / TestSprite Implementations)

1. **Mocking External APIs**: Specifically for integration tests, should we implement a fast, native Mocking schema for DeepSeek / GitHub to decouple TestSprite workflow runs from exhausting paid remote credits or repository quotas?
2. **Worker Execution Frameworks**: Which proxy or emulation (e.g., Miniflare / Wrangler dev) will TestSprite attach over to execute E2E testing against Cloudflare backend routes securely locally before CI environments?
3. **Database Generation Tests:** Specifically regarding file generation verification, should the end to end tests generate temporary `.json` payloads and trigger pipeline tests, ensuring it asserts removal hooks correctly?
