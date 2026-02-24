# ============================================================
# Cloudflare Workers — Configuration (wrangler.toml)
# ============================================================
# These are TEMPLATE configurations.
# Replace <YOUR_ACCOUNT_ID> with your actual Cloudflare account ID.
# Deploy each worker separately using:
#   cd workers/<worker-name>
#   npx wrangler deploy
# ============================================================

# ── CONTACT WORKER ──────────────────────────────────────────
# File: workers/contact/wrangler.toml
# Route: https://contact.littlesmartgenius.com/*
# Secrets to set:
#   npx wrangler secret put MAILERLITE_API_KEY
#   npx wrangler secret put MAILERLITE_GROUP_ID
#   npx wrangler secret put ADMIN_EMAIL
#   npx wrangler secret put SITE_URL

# ── SUBSCRIBE WORKER ────────────────────────────────────────
# File: workers/subscribe/wrangler.toml
# Route: https://subscribe.littlesmartgenius.com/*
# Secrets to set:
#   npx wrangler secret put MAILERLITE_API_KEY
#   npx wrangler secret put MAILERLITE_GROUP_ID

# ── ADMIN-API WORKER ────────────────────────────────────────
# File: workers/admin-api/wrangler.toml
# Route: https://admin-api.littlesmartgenius.com/*
# Secrets to set:
#   npx wrangler secret put GITHUB_PAT
#   npx wrangler secret put GITHUB_REPO        (little-smart-genius-com/website)
#   npx wrangler secret put ADMIN_PASSWORD
#   npx wrangler secret put SITE_URL
#   npx wrangler secret put MAKECOM_WEBHOOK_URL

# ── FREEBIE-EMAIL WORKER ────────────────────────────────────
# File: workers/freebie-email/wrangler.toml
# Route: https://freebie-email.littlesmartgenius.com/*
# Secrets to set:
#   npx wrangler secret put MAILERLITE_API_KEY
#   npx wrangler secret put MAILERLITE_GROUP_ID
#   npx wrangler secret put SITE_URL
