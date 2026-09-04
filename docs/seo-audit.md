# Flo4Paws — SEO audit and analytics plan

**Audit target:** the prototype (`flo4paws-site-v7.html`) and the migration off Wix.
**Date:** 2 September 2026.

---

## 1. The finding that matters most

**The prototype is one HTML file with six pages hidden behind `display:none`, switched by
JavaScript. For search, that is one page, not six.**

Measured before fixes:

| Check | Result |
|---|---|
| `<h1>` elements | **0** |
| `rel="canonical"` | 0 |
| Open Graph / Twitter tags | 0 |
| Structured data | 0 |
| Navigation as crawlable `<a href>` | 0 — all 13 nav items were `<button onclick>` |
| Distinct URLs | 1 |
| Document size | 1,001 KB with 11 base64 images inline |

Six pages of good content sharing one title, one description and one URL means five of
them cannot rank for anything. The nav being buttons means there is no internal link
graph at all.

**This is a prototype artefact, not a design decision.** It was built as one file so it
could be reviewed in a chat window. The real build must be six separate documents.

### Fixed in v7

- Six real `<h1>` elements, one per page, carrying the hero line
- Canonical, Open Graph, Twitter card, robots, theme-colour
- JSON-LD `@graph`: LocalBusiness/ProfessionalService, Person (Flo, with credentials),
  two Service nodes with prices — validated as parsing
- `loading="lazy"` and `decoding="async"` on all but the hero image, which gets
  `fetchpriority="high"`
- Title rewritten from the placeholder

### Must be fixed at build, cannot be fixed in a single file

- Split into six documents at real paths
- Nav rebuilt as `<a href>` — the `go()` function goes away entirely
- Per-page title, description and canonical (table in §3)
- Images as separate optimised files, not base64
- `sitemap.xml` and `robots.txt`

---

## 2. Competitive position — this changes the keyword strategy

**Pawsitive Dog Behaviour (Nottinghamshire)** is positioned on the same differentiator:
complex cases, particularly where pain or health issues contribute to behaviour, and
where previous approaches have not worked. Backed by 19 years, a BSc, and IAABC
accreditation with a Vet Relations Committee seat.

**FairlyDunn (Nottingham)** already offers three months of post-visit WhatsApp, Zoom,
email and phone support.

**Consequence.** "Pain-aware behaviourist" is contested locally by someone with heavier
credentials, and the three-month support window is table stakes. Competing head-on for
*dog behaviourist Nottingham* against nineteen years and a BSc is a poor use of the
budget.

**What is actually unique to Flo, and is not claimed by any competitor found:**

> Video captured at the consultation, reviewed by a canine physiotherapist, written up as
> clinical findings for your vet — with Flo attending the vet appointment at no charge.

Target that. Long-tail, low competition, high intent:

- `dog behaviourist gait assessment` / `is my dog's behaviour caused by pain`
- `dog bunny hopping back legs behaviour` — appears in all three of Flo's own cases
- `dog behaviourist who works with vet`
- `dog behaviourist Bingham` / `Radcliffe on Trent` / `Bottesford` / `Melton Mowbray`
- `nervous dog behaviourist Rutland`

The local-town terms are where a small practice can actually win.

---

## 3. Per-page metadata for the build

| Path | Title (≤60 where possible) | Meta description |
|---|---|---|
| `/` | Dog Behaviourist for Nervous Dogs \| Bingham, Nottinghamshire | Force-free behaviour support for nervous, anxious and reactive dogs. Video gait assessment reviewed by a canine physiotherapist, findings sent to your vet. |
| `/how-it-works/` | How It Works — Stages, Packages & Prices \| Flo 4 Paws | Six steps from first contact to your first consultation, four stages of behaviour work, and what each support package costs. |
| `/code-of-ethics/` | Code of Ethics — Force-Free Practice \| Flo 4 Paws | No shock, prong or choke. Seven commitments covering diagnosis, multi-disciplinary work, consent and realistic expectations. |
| `/reviews/` | Client Reviews \| Flo 4 Paws Dog Behaviourist | Verified Trustpilot reviews from owners of nervous, anxious and reactive dogs in Nottinghamshire and Leicestershire. |
| `/flos-friends/` | Recommended Partners & Products \| Flo 4 Paws | The vets, physiotherapists, groomers and products Flo works with and recommends for nervous and anxious dogs. |
| `/contact/` | Contact — Start With the Health & History Form \| Flo 4 Paws | Every dog starts the same way. Fill in the health and history form and Flo will be in touch to arrange your free discovery call. |

Each page needs its own `canonical`, `og:url` and `og:title`.

---

## 4. Redirect map — author before cutover

301 permanent, all of them. Missing these loses whatever authority the Wix site holds.

| From | To |
|---|---|
| `/my-services` | `/how-it-works/` |
| `/my-servicesold` | `/how-it-works/` |
| `/healthform` | `/contact/` |
| `/contact` | `/contact/` |
| `/code-of-ethics` | `/code-of-ethics/` |
| `/customer-testimonials` | `/reviews/` |
| `/flos-friends` | `/flos-friends/` |
| `/flos-friends/*` (6 product pages) | `/flos-friends/` |
| `/walkies` + 3 walk pages | ruling needed — keep or redirect to `/` |
| `/international-canine` | ruling needed |
| `/privacy-policy`, `/terms-of-use`, `/cookie-policy` | same paths, keep |

⚠ Pull the full URL list from Google Search Console before writing this, not from the
nav. Wix sites accumulate URLs that were never linked.

---

## 5. Analytics and Ads migration

### 5.1 Retrieve the IDs first

They are in Wix under **Marketing & SEO → Marketing Integrations**. You need:

- GA4 Measurement ID — `G-XXXXXXXXXX`
- Google Ads Conversion ID — `AW-XXXXXXXXX`
- Any conversion labels already configured
- Google Search Console verification method (likely a Wix meta tag — will break on cutover)

**Also check whether Google Tag Manager is in use.** If so, everything moves as one
container and the work is much smaller.

### 5.2 ⚠ The cross-domain problem — this is new, and it is caused by the funnel ruling

Every conversion now happens at **`app.flo4paws.co.uk/intake-form/flo4paws/`**, a
different hostname from `www.flo4paws.co.uk`.

Without configuration, GA4 treats that hop as the user leaving the site and a brand new
session arriving from a referral. The result:

- Every enquiry is attributed to `www.flo4paws.co.uk` as a referrer, not to Google Ads
- Ads conversion tracking reports **zero conversions**, so the campaign cannot optimise
- Sessions are double-counted and bounce rate is meaningless

**Three things are required:**

1. **Cross-domain measurement.** In GA4 Admin → Data Streams → Configure tag settings →
   Configure your domains, list both `flo4paws.co.uk` and `app.flo4paws.co.uk`.
2. **The tag must also load on the intake form page.** That page is generated by
   `publish.js` from the question register — the tag has to go into the generator
   template, not be pasted into the artefact, or the next republish wipes it.
3. **A conversion event on submission.** GA4 has no idea the form succeeded unless the
   success state fires an event. Simplest is a `?submitted=1` redirect or a
   `gtag('event','generate_lead')` call on the success screen.

Item 2 has a cost worth stating plainly: it puts Google's tag on a page where clients
enter their dog's medical history. Analytics should record **that** a submission
happened, never any field content. Worth an explicit decision rather than a default.

### 5.3 ⚠ The cookie policy currently contradicts running analytics

The live cookie policy states that Flo4Paws does not use advertising or marketing
cookies, third-party tracking cookies, analytics cookies, or social media cookies.

The website runs Google Analytics and Google Ads. Both set cookies in all four of those
categories.

The policy is scoped to the *platform* at `app.flo4paws.co.uk`, so it is arguably
accurate about the app — but it is linked from the footer of every marketing page, where
a reader will take it to describe the page they are on.

**Under PECR, analytics and advertising cookies require prior consent in the UK.** Three
things follow:

1. A consent banner is needed on the marketing site. Wix may be providing one today —
   verify before cutover, because it will not come with you.
2. **Google Consent Mode v2** is mandatory for Ads personalisation in the UK and EEA.
   Tags must set `ad_storage`, `ad_user_data`, `ad_personalization` and `analytics_storage`
   to `denied` by default and update on consent.
3. The cookie policy must be rewritten to cover the website separately from the platform.

This is the one item on the list with a regulator attached.

### 5.4 Also worth doing at cutover

- Re-verify Google Search Console by DNS TXT rather than a meta tag, so it survives
- Submit the new `sitemap.xml`
- Use the GSC **Change of Address** tool only if the domain changes — it does not here,
  so no action
- Claim/refresh the Google Business Profile: category *Dog Trainer*, service area
  Nottinghamshire, Leicestershire, Rutland, and link to `/contact/`
- Keep Wix live for 30 days after cutover for rollback

---

## 6. Content gaps that cost rankings

- **No blog or article content anywhere.** The competitors rank partly on volume. Flo's
  own consult reports are full of searchable subject matter — bunny hopping, gut trouble
  driving behaviour, decompression walks, ball launchers and joint strain. One article a
  month on those topics would outperform any amount of tag tuning.
- **Reviews shortened and reworded in the prototype** so they can be reviewed. Verbatim
  reviews carry the language real people search with, so paste the full text before
  publishing, or embed the Trustpilot widget.
- **No `Review` or `AggregateRating` structured data.** Do not hand-author it — Google
  penalises self-serving review markup. Use the Trustpilot widget, which carries its own.
- **Geography still contradicts itself** (Lincolnshire in the intro, absent from the
  footer, while Grantham is listed). Search engines read the inconsistency too.
  Ruling still outstanding.

---

## 7. Priority order

1. Split into six pages with real URLs and per-page metadata — nothing else matters until this is done
2. Author the 301 map from the Search Console URL list
3. Retrieve the GA4 and Ads IDs from Wix before touching DNS
4. Consent banner + Consent Mode v2, and rewrite the cookie policy for the website
5. Cross-domain measurement, and the tag in the `publish.js` template
6. Sitemap, robots, GSC verification by DNS
7. Google Business Profile
8. Start writing articles on the pain-and-behaviour topics
