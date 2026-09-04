# Session Handover — 2026-09-02 — WEBSITE (Flo4Paws marketing site rebuild)

**Session ID:** not numbered. Ran in parallel with **S213** in a separate window on the
same box. See §9 — that parallelism is itself a finding.
**Box:** `ubuntu-4gb-hel1-1` / `204.168.132.118`
**Scope:** Flo's consultation report template, then the Flo4Paws marketing website —
audit, rebuild, and deployment to a staging hostname.
**Posture:** LIVE-SOFT. Flo's production API and Lily's tenant share the nginx that was
modified. Controls run on both, before and after every config change.

---

## 1. WHAT SHIPPED

### 1.1 Consultation report template — DONE, in use

Three Word artefacts produced and accepted by Flo:

| File | State |
|---|---|
| `Flo4Paws_First_Consult_Template_v2.docx` | blank template, 12 sections |
| `Bonnie_First_Consult_22_08_2026.docx` | worked example |
| `Buddy_First_Consult_25_08_2026.docx` | worked example |

**Structure:** stage banner (4 stages) × workstreams (parallel threads). "Workstreams"
is Flo's own word, taken from the bottom of her existing drafts. Sections split
first-hand observation (§2) from owner report (§4), which she previously merged.

**★ Flo returned both case documents edited. Diffing her edits against what was issued
exposed two defects in the template:**

1. **She deleted the "not a diagnosis" disclaimer from both.** It was set in grey italic,
   which the template teaches means *delete this guidance*. Her own Code of Ethics opens
   with "I cannot diagnose medical conditions", so this is the one line that must survive.
   **Fix: black body text, not grey.** NOT YET APPLIED.
2. **She deleted the stage caption from both**, same cause. The banner now floats without
   explanation, removing most of the journey framing. **Same fix.** NOT YET APPLIED.
3. She deleted §10 "What you told me you want" entirely and renumbered. That is a ruling,
   not an error — but `owner_goals` may already exist in the intake register, which would
   make the section free to fill.
4. She **added** warmth ("Buddy jumped on my chair and gave me kisses, an affectionate
   boy"). The template has nowhere for that. §2 should invite it.
5. Follow-ups are **Zoom**, not telephone — she pasted real Zoom links into both. The
   website said "telephone calls". Corrected on the new site.

### 1.2 Marketing website — BUILT AND DEPLOYED TO STAGING

**`https://staging.flo4paws.co.uk`** — live, certificate to 2026-12-01, auto-renew set.

- 23 pages, one HTML file each, real URLs
- 13,692 words (was ~4,400 in the single-file prototype)
- Per-page title / description / canonical / Open Graph
- JSON-LD: LocalBusiness, Person with credentials, priced Services, FAQPage (8 Q),
  WebSite, BreadcrumbList on every subpage
- `sitemap.xml`, `robots.txt`, `site.webmanifest`, full favicon set
- Real logo cropped from `Transparent.png`; brand colours sampled, not guessed:
  **mint `#50E3C2`, forest `#194702`, grey `#575757`**
- Type: Cormorant Garamond (echoes the logo wordmark) + Karla for interface
- `X-Robots-Tag: noindex` on staging

**On the box:**

| Path | What |
|---|---|
| `/var/www/flo4paws-site/` | the site, 1.1 MB, `www-data`, 755/644 |
| `/etc/nginx/sites-available/flo4paws-site` | vhost + 24-entry 301 map |
| `/root/incoming/flo4paws-site-meta/` | `nginx-flo4paws.conf`, `DEPLOY.md` |

**Final bundle:** `flo4paws-site-build-v7.tar.gz`
sha256 `0bb80c99b5b569a1859913256957e46a709fee49400f135290cd2c5ff21f5517`

---

## 2. ★★ THE MEASUREMENT WORK — THIS CHANGED THE STRATEGY

Search Console (92 days to 2026-08-30) and GA4 (4 Jun – 1 Sep) were pulled and analysed.
**The data overturned two of my own recommendations.**

### 2.1 The site is accidentally a harness review site

| | clicks | share |
|---|---|---|
| TTouch harness blog post | 94 | **51% of all organic clicks** |
| All TTouch/harness queries | 63 of 67 | **94% of query-level clicks** |
| **144 behaviour-service queries** | **1** | positions 30–90 |

She ranks **page one** for "t touch harness for dogs" (pos 8.6) and is **invisible** for
everything she sells. `nottingham dog training` pos 45. `dog behaviour nottingham` pos 32.
Homepage pos 46.2 on 4,395 impressions.

### 2.2 Two corrections to my own audit

- I wrote **"no blog content exists."** Wrong. Three posts, one carrying half the traffic.
- My first IA proposal **deleted the walks pages and folded away the blog.** That would
  have destroyed the only working organic asset. `/gunthorpe-river-trent` earns 22 clicks —
  more than `/my-services` (4) and `/contact` (3) combined.

### 2.3 The cheapest win available, still not done

Partner pages rank but are never clicked — a **title and description** problem, not a
ranking one:

| page | position | impressions | clicks |
|---|---|---|---|
| `/pickpocket-foragers` | **9.8** | 169 | **0** |
| `/muzzle-movement` | 14.6 | 121 | **0** |
| `/pet-remedy` | 19.2 | 65 | **0** |
| `/green-and-wilds` | 23.9 | 63 | **0** |
| `/tug-e-nuff` | 21.1 | 296 | 1 |

≈1 hour of work on the **live Wix site**, independent of cutover.

### 2.4 Google does not know where Flo is

Appearing for `dog behaviourist darlington`, `newton aycliffe`, `grimsby`,
`separation anxiety specialist county durham`, `dog behaviour alcester`. Hundreds of
miles away. No confident location signal. The site's own geography contradicts itself —
intro says Lincolnshire, footer says Nottinghamshire/Leicestershire/Rutland then lists
Grantham, which is in Lincolnshire. **Ruling still outstanding.**

### 2.5 The live funnel, measured

Home 174 users → `/my-services` 81 → `/my-servicesold` **34** → `/contact` 35 →
`/healthform` **10** → thank-you **5**.

**`/my-servicesold` took 30% of services traffic** while pricing a follow-up call at £25
against £50. It has since started **404ing** — worse, not better, because it was the
homepage CTA target. **Needs a 301, not a deletion. Still outstanding.**

### 2.6 ⛔ MY OWN ERROR — Google Ads, stated and corrected

I reported **£634.93 spend, £79 per enquiry, two-thirds wasted on Display/PMax, pause it.**
**All of it wrong.**

The keyword CSV contains its own subtotal rows with blank keyword names. I filtered on
`len(row) >= len(header)`, which every row passes, and summed keywords *and* their
subtotals *and* the campaign total.

**Truth:** one live campaign, **£134.85**, 198 clicks at £0.68, 3.4% CTR, **7 conversions
at £19.26**. Performance Max total is **£0.00 and paused**. There is no Display campaign.

Ads and GA4 broadly agree (7 vs 9 key events). **The account is healthy.** Recommendation
reversed: do not switch it off.

The correct figure was visible in a screenshot Ian had already sent, and I read past it.

**Still worth doing:** check whether the "Contacts" goal counts phone-link clicks. Bidding
is Maximize Conversions, so it optimises toward whatever it is told is a conversion.

---

## 3. DEFECTS FOUND ON THE LIVE WIX SITE — ALL STILL OPEN

| # | Defect | Severity |
|---|---|---|
| 1 | **An AI editing prompt is published in the Code of Ethics page**, offering to reformat the content into a values block | ★★ embarrassing, on the credibility page |
| 2 | `/my-servicesold` **404s** and was the homepage's primary CTA target | ★★ live conversion loss |
| 3 | `/healthform` collects more personal data than the contact form and carries **no GDPR consent wording** (S127, still open) | ★★ compliance |
| 4 | Muzzle Movement description is the **Pet Remedy description verbatim** | ★ |
| 5 | Five partner-page titles/metas — page-one rankings, zero clicks | ★★ cheapest win |
| 6 | Geography contradicts itself in three places | ★ ranking signal |
| 7 | Discovery call is 30 min on home, 20–30 on both services pages | ○ |
| 8 | Typos: "inital consultations", "Prefferred Contact Method", "Notinghamshire" ×4 alt text | ○ |
| 9 | Unedited "Elaine and Bonnie" testimonial including "ts very true Flo" | ○ |
| 10 | Cookie policy states no analytics cookies while GA + Ads run | ★★ PECR |
| 11 | App footer says ©2025, site says ©2026 | ○ |

---

## 4. ⚠ PRE-CUTOVER GATE — DO NOT MOVE `www` UNTIL ALL FOUR

The contact CTA now points at `https://app.flo4paws.co.uk/intake-form/flo4paws/`.
It serves 200. **It has never taken a real client submission** — the 9 prod rows are test
data. Deployed ≠ real-actor-proven.

1. **BL-576 / BL-491 — validation.** Ian personally hit a validation error listing
   problems he could not navigate to (hidden conditional children being validated). He
   knew the system and still could not pass it. A client abandons silently. **Fix or prove
   absent.**
2. **BL-566 / BL-572 — claim link.** No resend, no delete; claim emails indistinguishable;
   spent links dead-end.
3. **One real submission end to end** — form → `pending_intake` → claim email → account →
   Flo reads the answers.
4. **Cross-domain analytics.** GA4 must list both `flo4paws.co.uk` and
   `app.flo4paws.co.uk`; a conversion event must fire on the success state. The tag has to
   go in the **`publish.js` generator template**, not the artefact, or the next republish
   wipes it. ⚠ That puts Google's tag on a page carrying medical history — record *that* a
   submission happened, never field content. Needs an explicit decision.

**Then, in the same change:** uncomment `location = /healthform { return 301 /contact/; }`
in the vhost and take the Wix form down. **Not before** — until then `/healthform` is the
live capture route.

---

## 5. CUTOVER — WHAT IS AND IS NOT RISKY

**★ MX is at Fastmail (`messagingengine.com`), not Wix.** Email is fully independent of
web hosting. Cutover is **one A record** for `www`, MX/SPF/apex untouched. This removes
the risk I had been treating as most serious.

- DNS zone is managed **at Wix**. If the Wix account is ever closed, DNS goes with it —
  either keep a plan alive for DNS or transfer the zone.
- `www.flo4paws.co.uk` currently CNAMEs to `cdn3.wixdns.net`. Nothing on the box claims it.
- Keep Wix paid 30 days after cutover for one-DNS-change rollback.
- Re-verify Search Console by **DNS TXT**, not a meta tag, so it survives.
- **Add a GSC Domain property** for `flo4paws.co.uk` — the current property is URL-prefix
  `https://www.` only and cannot see `app.`.

**Baseline to beat** (90 days to 2026-09-01): 184 organic clicks · 11,378 impressions ·
472 sessions · 10 users reached `/healthform` · 5 thank-you completions · £134.85 Ads
spend · 7 conversions at £19.26.

---

## 6. STILL OUTSTANDING ON THE NEW SITE

| Item | Note |
|---|---|
| **"Newgrange Vets — One line to be confirmed"** | renders as client-facing text on Flo's Friends |
| GA4 + Consent Mode v2 | placeholder comment in every `<head>` |
| Trustpilot reviews | currently shortened/reworded summaries — paste verbatim or embed the widget |
| Review schema | do **not** hand-author; Google penalises self-serving markup. Use the widget. |
| K9 Corner / Maddy's Mutts / Newgrange logos | not supplied |
| BCCS, IMDT, Galen, Chirag Stewart badges | not supplied |
| App Store / Play badge URLs | placeholders |
| Affiliate check | Tug-E-Nuff link and Pet Remedy code **GTSBY25** — still current? |
| Flo to read all 12 new pages | written in her first person |
| Lincolnshire ruling | in or out |
| Intake form page title | "Client intake" — generic, and every enquiry lands there |

---

## 7. ★ WHAT THE PROJECT RECORD GOT WRONG

Two long-held claims were falsified by reading the artefact:

1. **"Staging pull + `pm2 delete/start` is not in `deploy.sh`."** It is — lines 254–284.
   S213 confirmed by execution (`clientflex-staging` 164 → 166 at `↺ 0`). *This was carried
   as an open gap in this session too, and comes off the list.*
2. **The favicon set in project files (`favicon16/32/48`, `icon192/512`, `appletouchicon`)
   is a horse and a dog — that is Lily's branding, not Flo's.** Also mis-sized: `favicon16`
   is 28×28, `favicon32` and `favicon48` are both 56×56, `icon512` is 532×532. **Do not use
   on Flo's site.**

Both are BL-222 shape: a claim about an artefact, believed across sessions, falsified by
reading the file.

---

## 8. ⛔ ERROR LOG — MINE, THIS SESSION

Four, all the same class (**F-01**): asserting a property of an instrument or artefact
without consulting it.

| # | Error | Cost |
|---|---|---|
| 1 | **Ads CSV summed with subtotal rows included** → £634.93 vs true £143.90 | Three confident recommendations, all wrong. Corrected figure was in a screenshot already supplied. |
| 2 | `grep -r` on symlinked vhosts (should be `-R`) | Both controls returned 0; instrument could not distinguish pass from fail. **The gotcha was in my own notes.** |
| 3 | Predicted 34 tar entries, actual 57 | Counted files, forgot directories are entries |
| 4 | **CSS written with unasserted `h.replace()`** — anchor did not match, failed silently, I reported success | Ian saw a broken hero. Every replacement since is assertion-guarded. |

Also: wrote `expect 200/302` for an app control that correctly returns **301** on port 80,
causing an unnecessary rollback. Controls must compare against a captured baseline, not a
guessed value.

**A fifth, of a different class:** I said "no blog content exists" without checking, then
built an IA that deleted the site's best-performing pages.

---

## 9. ★ PARALLEL-SESSION HAZARD

**Two Claude sessions were operating on `ubuntu-4gb-hel1-1` simultaneously** — S213 in
`animoit-infra`, this one on the website. Discovered only because Ian pasted the tail of
S213's output into this window.

Nothing collided: S213 worked in `animoit-infra`, this session touched only
`/var/www/flo4paws-site` and one new vhost. **But S213 ran `deploy.sh` (PM2 recycle) while
this session installed an nginx vhost and ran certbot.** Wrong ordering, or a reload
during certbot, would have been very hard to diagnose.

**Mitigation:** any session touching nginx or PM2 declares it in the other, or a boundary
is agreed up front. **This session should have opened by asking whether it was the only one
on the box. It did not.**

---

## 10. NEXT SESSION — SUGGESTED ORDER

**Off-box, no deploy, highest value first:**

1. 301 `/my-servicesold` → `/my-services` on Wix. It 404s and was the homepage CTA.
2. Rewrite five partner-page titles/metas. Page-one rankings earning zero clicks.
3. Add GDPR consent wording to `/healthform`. It is the only live capture route.
4. Delete the AI prompt from the Code of Ethics page.
5. Check the Ads "Contacts" conversion action for phone-link clicks.

**Then, to unblock cutover:**

6. Reproduce and fix the intake-form validation defect (BL-576 / BL-491).
7. Build resend-claim-link (BL-566 / BL-572).
8. One real submission end to end.
9. GA4 + Consent Mode, including the `publish.js` template decision.

**Then cutover:** drop TTL 48h ahead → move the `www` A record → uncomment the
`/healthform` redirect → take the Wix form down → resubmit sitemap → keep Wix 30 days.

**Template fixes** (§1.1) are independent of all of the above and take minutes.

---

## 11. FILES PRODUCED

| File | Purpose |
|---|---|
| `Flo4Paws_First_Consult_Template_v2.docx` | blank consult template |
| `Bonnie_First_Consult_22_08_2026.docx` | worked example |
| `Buddy_First_Consult_25_08_2026.docx` | worked example |
| `seo-audit.md` | technical audit + analytics migration plan |
| `ia-v2.md` | evidence-based IA, 25-entry redirect map, guide priority |
| `flo4paws-site-build-v7.tar.gz` | the site — 23 pages, images, sitemap, vhost, DEPLOY.md |

⚠ `homepage.md`, `journey.md`, `homepage_v2.md`, `journey_v2.md` and the
`flo4paws-site-v*.html` prototypes are **superseded** by the v7 bundle. Do not carry them
forward.
