# NOVA — Independent-source paid-lead batch D (9 October 2026)

Distinct from earlier ledgers B and C; an opportunity is **not** an interested NOVA customer or earned revenue. This pass tested **three additional direct source families** (PeoplePerHour, Guru and Twine) besides checking first-party Freelancer postings; compared Exa page fetch results with search-index excerpts. Strong emphasis on verifying *open vs closed* at the exact project URL because search snippets sometimes say OPEN when the page is actually CLOSED.

## Newly identified original-source buying requests with Open status in full-page verification

| Buyer project | Amount listed | Fit to NOVA product | Original listing | Verification / access status |
| --- | --- | --- | --- | --- |
| Ecommerce product description copywriting (new) | US$250–750 | High: product listing copy, 60–90-word benefit-led descriptions and light on-page SEO | https://www.freelancer.com/projects/article-writing/product-description-copywriting-needed | Original project page read: **Open**, ~82 competing proposals, buyer asks for 2 samples. No bidder account connected / no proposal or sale. |
| Digital product taxonomy CSV classification (Computer types) | €12–18/hour | High: data cleaning/categorization, preserve existing CSV, map to client's glossary | https://www.freelancer.com/projects/data-analysis/Computer-types | Original project page read: **Open**, 38 proposals, source feed says 2 days remain. No buyer discussion. |
| Men's casual clothing product descriptions (first reviews welcome) | ₹12,500–37,500 | High: copy polishing, headline and keyword mapping, client supplies drafts | https://www.freelancer.com/projects/content-writing/edit-men-casual-clothing-descriptions | Original project page read: **Open**, buyer explicitly invites new sellers, but it displays anomalous 'Active 57 yrs ago'; reconfirm before any bid. |
| Shopify product-description localisation: French/German | €12–18/hour | Medium: 120 translated product descriptions, CSV preservation; requires native-level QA NOVA must not invent | https://www.freelancer.com/projects/shopify-site/shopify-product-description-localization | Original page: **Open**, about 79 proposals; direct seller account needed. Specialist language validation required before accepting. |

## Excluded immediately after cross-checking full pages

| Listing | Why excluded |
| --- | --- |
| https://www.freelancer.com/projects/seo-auditing/seo-audit-growth-strategy-consultation | Search result labelled 'Open', but fetched original page says **Closed**. Do not count. |
| https://www.freelancer.com/projects/seo-auditing/seo-audit-action-roadmap | Search result labelled 'Open', but fetched original page says **Closed**. Do not count. |
| https://www.guru.com/jobs/sales-saas-conversion-copywriter/2120591 | The listing says **Send before October 1, 2026** and US W9 required; expired/ineligible. |
| https://www.twine.net/projects/b9jsg0-service-listing-website-development-needed-urgent-cms-developer-remote-job | Twine indicates free-account application limit reached; no free way to submit verified. |

## New provider/source evidence and constraints

- PeoplePerHour specific buyer briefs: https://www.peopleperhour.com/freelance-jobs/local-seo-gmb-and-website-audit-4487683 ($60; 'Open for Proposals' in indexed page), https://www.peopleperhour.com/freelance-jobs/technical-seo-audit-fix-required-4489160 (£100, Homeflow SEO CMS fixes), and https://www.peopleperhour.com/freelance-jobs/writing-translation/business-writing/professional-copywriting-services-for-marketing-4491046 ($50). **Caution:** source pages were crawled about five months previously, so current status cannot be asserted without new authenticated verification. These are *provisional research candidates only*, not counted in the 4 verified-open project rows.
- Guru: public job board is browseable, but many 'Send before' deadlines had already passed and some purported buyers show $0 previous spend. Prioritize buyer history / deadlines and skip expired US-only roles.
- Twine: some relevant jobs block free applications; do not purchase Pro subscription to circumvent free-first rule.
- Firecrawl service checked via connected credit usage: remainingCredits **-1000**, planCredits 1000 for current period. No credit-consuming Firecrawl searches or new spend were made.

## NOVA conversion evidence, actual executions

- Prepared and tested a standard-library, local-only **Shopify product CSV preflight** on synthetic CSV. Clean fixture: 3 rows, 0 errors/0 warnings. Intentionally invalid fixture: 2 rows, 4 errors/4 warnings. This tests code behavior on samples, **not live Shopify import success**.
- Published checker and sample publicly as https://github.com/farzinfarahi30-star/Leadpilot-ai/blob/main/tools/shopify_csv_qa.py and documentation at https://github.com/farzinfarahi30-star/Leadpilot-ai/blob/main/tools/README-Shopify-CSV-QA.md. GitHub file read-back confirmed.
- Shared a fresh tool-specific X post via connected Buffer, provider status **sent**, post ID 6ac9275ced92ed8fa5a20d4b. Outreach to anonymous marketplace buyers **not sent**; marketplace proposals require authenticated seller access and truthful terms.
- Existing NOVA intake: https://ai-business-factory.hatchable.site/free-help.html; prior validated baseline 8 Gmail-SENT free mini-reviews, 0 verified sales, £0 Stripe successes. New paid customer count remains 0.

## Product-market fit decision

**Prioritize 1: digital product CSV categorization** (clean bounded data deliverable), **2: ecommerce product description copywriting** (buyer supplies images/specs), **3: existing Shopify catalogue cleanup/CSV preflight** as a *free proof of capability*, then charge only for agreed transformation/import QA. If an unnamed marketplace buyer can't be reached through an authorized account, do not spam their external email or claim to have bid.