# NOVA Global — website redesign strategy and conversion audit
**Independent sample on an NOVA-controlled site, not paid client work**  
**Audited website:** https://nova-global-first-sale.vercel.app/  
**Public-page evidence captured:** 12 October 2026, HTTP 200, readable HTML; no private analytics, Google Search Console access, user interviews or client sales.  
**Prepared by:** NOVA / Azin Ahi (AI-assisted; evidence-checked where stated)

## 1. Executive diagnosis

**The problem is not a missing page; it is a diffuse first decision.** The first-screen H1 is *“Practical AI, automation, data and QA work — worldwide.”* This says what the provider can do, but not which painful problem a buyer can solve immediately. The page offers two starter services (£9, £14.90), a free checklist, and eight higher-priced services further below. All are legitimate options, but the page forces an unfamiliar buyer to choose the category rather than identify one problem first.

**Recommendation:** lead with the smallest credible buyer outcome and one primary next step: *“Get a focused technical review of one public webpage for £9.”* Make the sample report visible before checkout; place the other services behind a secondary catalog route.

This is a **qualitative UX/CRO hypothesis** grounded in the audited page content, **not measured lost conversion**. No change in revenue, click-through, sales or rankings has been established.

## 2. Observable facts vs hypotheses

| Public observation (12 Oct 2026) | Implication to test, not a proven fact |
|---|---|
| One H1 names broad categories: AI, automation, data and QA. | New visitors may not know which specific problem the service addresses. |
| Main navigation labels are **Services**, **Worldwide**, **Contact**. | Buyers looking for price, proof and delivery may not spot them immediately. |
| First-screen actions include **Free 30-point website QA checklist** and **Professional audit from £9**. | One prominent primary action would reduce decision conflict. |
| Ten offered services; starters at **£9** and **£14.90**, larger offers include **£79**, **£99**, **£129**, **£149** and **£249**. | Broad scope can weaken the relevance of the page to a first-time audit buyer. |
| Audit description promises observable technical signals and prioritized fixes, expressly **not** a pentest or guaranteed rankings. | That honest scope can become a trust-building comparison table. |
| The page links to a **synthetic** CSV example and a separate security/SEO case on NOVA's own site; no customer testimonial is presented. | Put the genuine internal case near checkout and avoid implying it is a customer success. |
| Paid actions lead to Stripe; contact actions open an email composer. | Verify a buyer can understand fulfillment, timing, revision policy and refund rules *before* Stripe. |
| An 8-service catalog uses **Book service** calls to action while starters say **Buy**. | Harmonize these verb choices or make the scope difference explicit. |

Evidence: GET of the current public home page, inspection of the H1/H2/H3 hierarchy, anchor text and destinations; refer to [first-party technical case study](../NOVA_SITE_HARDENING_2026-10-12.md) for header and indexing reproduction.

## 3. Recommended positioning

**Audience:** Owner-operators and small teams with a public website who suspect they have an indexability, clarity, metadata or basic implementation issue but do not need a full SEO agency commitment.

**Job to be done:** “Tell me, with publicly reproducible evidence, what is wrong with this page and what to fix first.”

**Promise:** One URL, one clearly scoped technical diagnostic, practical fixes. Not: guaranteed rankings, traffic, sales, penetration testing, or access to the customer's private analytics.

### Proposed first screen

**Eyebrow:** `ONE PAGE • PUBLIC DATA ONLY • £9 FIXED SCOPE`

**H1:** `Know what to fix on your website — starting with one page.`

**Subheading:** `An AI-assisted technical review of one public URL. We check visible indexability signals, page structure and selected security headers, then deliver an evidence-backed priority list. No login required.`

**Primary CTA:** `Get my £9 page audit` (existing Stripe checkout)

**Secondary CTA:** `See a real example` (NOVA's own live noindex case with raw before/after evidence)

**Expectation text immediately below:** `Public signals only. Not a full SEO audit, penetration test or ranking guarantee. Confirm scope and delivery method before purchase.`

This proposal does not claim a turnaround time because it has not been independently capacity-tested.

## 4. Information architecture

For an audit-focused landing page, use this sequence instead of opening with all ten offers:

1. **Who this is for:** A 2–3 sentence buyer problem description.
2. **What you get:** One URL, findings with evidence, ranked fixes, limitations.
3. **Example:** Before/after of the actual NOVA `X-Robots-Tag: noindex` deployment-address issue.
4. **Process:** Submit URL at secure checkout → run read-only checks → deliver report to checkout email; state genuine turnaround only after verified.
5. **FAQ:** What is inspected? Do I need access? Does it guarantee indexing? How are refunds/revisions handled? What data is retained?
6. **Price and CTA:** One £9 primary action; optional question-by-email.
7. **Other services:** Secondary link to full catalog for visitors who need something else.

Mobile wireframe sketch:

```text
[ NOVA / Website Audit ]        [FAQ]
-------------------------------------
 ONE PAGE · PUBLIC URL · £9
 Know what to fix on your website
 [one-sentence outcome and limits]
 [ GET MY £9 AUDIT ]  <-- primary
 [ See real example ] <-- secondary
-------------------------------------
 [What you get: 3 evidence deliverables]
 [Actual internal case: noindex -> fix]
 [How it works / scope]
 [FAQ / guarantees / privacy]
 [£9 / CTA]
 [Other NOVA services]
```

## 5. Buyer journeys and friction

**Journey A — high intent.** Visitor has a specific webpage problem → reads deliverables + internal case → opens Stripe → supplies required public URL → paid checkout → receives scoped report. **Need to instrument:** page view, audit CTA click, successful checkout, report delivery, revision requested. A click is not an order.

**Journey B — uncertain visitor.** Visitor opens free 30-point checklist → self-evaluates concerns → sees clearly optional paid report → can email a single question or buy. Keep checklist local-first; never force signup or collect answers through hidden analytics.

**Journey C — agency partner.** Agency wants 5+ pages or a strategic redesign → *do not mis-sell the £9 single-page audit as a strategy workshop.* Route to a written scope request with objective inputs and quote; no invented testimonials or enterprise commitments.

## 6. Competitor/alternative framing (not a live external competitor audit)

The relevant alternatives are: **DIY checklist** (free, user's time, not independent report), **NOVA one-page audit** (£9, bounded public technical evidence), **full agency strategy/rebuild** (broader UX research, competitor audits and implementation; variable higher scope and fees). The site should distinguish these rather than suggest they are interchangeable.

This section deliberately contains **no invented competitor traffic, pricing, performance comparisons or market-share claims**. External competitor benchmarking would require a named current rival and an equally controlled live-page audit.

## 7. Reusable design handoff: prioritized work

| Priority | Concrete change | Rationale | Acceptance test |
|---|---|---|---|
| P0 | Create focused /website-audit landing page; make £9 audit hero offer. | One clear first decision for one audience. | H1 addresses buyer need, price and primary button visible on mobile. |
| P0 | Show *one* first-party example next to the CTA and label it an internal case. | Credible proof without invented client results. | Case identifies inspected URL, date, raw header evidence and limitations. |
| P0 | Add precise service inclusions/exclusions, true delivery commitment and refund/revision terms. | Reduce checkout uncertainty. | Buyer can answer “what will I receive, when, and what if it's wrong?” before paying. |
| P1 | Move eight unrelated services to a catalog page. | Preserve breadth without overloading first conversion step. | Main audit page has one dominant paid CTA. |
| P1 | Use identical naming from marketing to Stripe receipt. | Reduce confusion and mistaken orders. | Product name, £9 price, requested input and follow-up email match. |
| P1 | Add a clean two-CTA mobile hierarchy and keyboard-focus states. | Accessibility and clear choice. | 320px layout has no cropped CTA; keyboard users reach both controls. |
| P2 | Set up consent-compliant non-sensitive purchase funnel measurement. | Prioritize based on observed behavior, not conjecture. | Event definitions written; no customer URLs, emails or private checklist text in analytics. |
| P2 | Test first-screen offer wording on qualified visitors. | Determine whether specificity outperforms broad provider pitch. | Pre-registered primary metric: paid audit purchases per qualified visit; small samples labelled inconclusive. |

**Important commercial infrastructure caveat:** The sampled Vercel hosting account is on Hobby; commercial use must be moved to a hosting arrangement that permits this business activity or properly upgraded **before distributing the storefront as a commercial URL**. The existing externally hosted Stripe payment link can remain the secure payment mechanism. No future host migration is claimed complete.

## 8. Visual system guidance for a designer

- Use one dominant accent for the pay CTA and a clearly secondary style for “See example.”
- Keep offer title, scope summary, trust proof and CTA within the first two mobile scrolls; test rather than assume that this layout converts better.
- Use short factual captions under diagrams/screenshots: *signal → why it matters → evidence → fix*.
- Avoid decorative badges suggesting certifications or client outcomes NOVA does not possess.
- Preserve the existing readable, dark technical visual identity if usability testing supports it; this assignment is **structure first, not a logo redesign**.
- Create component states for primary/secondary CTA, service inclusion rows, FAQ disclosures, an evidence card and a small “not included” warning.

## 9. Test plan and next decision

**Baseline absent:** We have not obtained qualified visit counts, real prospective-buyer interviews, screen recordings or customer order completion rates. We cannot infer a percentage lift.

Before claiming improvement, check: mobile 320/375/430px layouts; actual Stripe checkout completion with normal, non-fabricated buyer activity; link/CTA semantics; keyboard navigation; canonical/robots; cookie/analytics consent; and whether reports can be fulfilled under the advertised scope.

Success is not “more audits found.” Success is *a real paid order fulfilled to the buyer's satisfaction*, followed by independently sourced repeat orders.

---
**Portfolio use:** This is a public **self-audit/design strategy sample**, prepared on a first-party NOVA page and suitable to demonstrate the *process* used for website/UX/CRO diagnosis. It is NOT client work, a completed agency commission, a measured CRO outcome, or evidence that we have prior clients. No third-party website was tested, and no credentials, private analytics or customer information were accessed.
