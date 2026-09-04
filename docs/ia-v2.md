# Flo4Paws — information architecture v2

**Supersedes the seven-page proposal.** That one deleted the blog and the walks pages.
Search Console data shows those are the only parts of the site earning traffic, so the
proposal was wrong.

**Evidence:** GSC 31 May – 30 Aug 2026 (184 clicks, 11,378 impressions);
GA4 4 Jun – 1 Sep 2026 (472 sessions, 683 page views).
**Written:** 2 September 2026.

---

## 1. What the data changed

| I previously said | The data says |
|---|---|
| No blog content exists | Three posts exist. One earns **51% of all organic clicks** |
| Collapse Walkies into one page | Walk pages earn **37 clicks** — more than services and contact combined |
| Collapse the six Flo's Friends product pages | They rank **positions 9.8 to 23.9** with 714 impressions. They are not weak pages, they have weak titles |
| Build a new `/start-here` page | `/my-services` already does that job. Fix it, don't duplicate it |

### The cheapest win on the whole site

| Page | Position | Impressions | Clicks | CTR |
|---|---|---|---|---|
| `/pickpocket-foragers` | **9.8** | 169 | **0** | 0% |
| `/muzzle-movement` | 14.6 | 121 | **0** | 0% |
| `/pet-remedy` | 19.2 | 65 | **0** | 0% |
| `/green-and-wilds` | 23.9 | 63 | **0** | 0% |
| `/tug-e-nuff` | 21.1 | 296 | 1 | 0.34% |

`/pickpocket-foragers` sits at **position 9.8** — bottom of page one — and gets **zero
clicks from 169 impressions.** A page that ranks but is never clicked has a title and
description problem, not a ranking problem. These are already earning visibility. They
just look like nothing worth clicking.

Rewriting five titles and five meta descriptions is perhaps an hour's work and is the
highest return-per-minute action available.

---

## 2. The sitemap

```
/                                Home
/how-it-works/                   approach · four stages · packages · FAQ
/contact/                        the funnel → health & history form
/code-of-ethics/                 force-free commitments
/reviews/                        Trustpilot
/flos-friends/                   who and what Flo recommends (hub)
/guides/                         evergreen resource hub          ← replaces /blog
   /guides/tellington-ttouch-harness/
   /guides/is-your-dogs-behaviour-caused-by-pain/
   /guides/long-lines-and-decompression-walks/
   /guides/muzzle-training/
   /guides/calming-products-for-anxious-dogs/
   /guides/enrichment-and-freework/
   /guides/tug-toys-and-confidence/
   /guides/natural-chews/
/walks/                          walk hub
   /walks/gunthorpe-river-trent/
   /walks/houghton-on-the-hill/
   /walks/rufford-park-and-sherwood-forest/
/privacy-policy/  /terms-of-use/  /cookie-policy/
```

**Nav (6 items):** Home · How it works · Guides · Walks · Flo's Friends · **Contact us**
Ethics and Reviews link from the body and the footer, not the top nav.

---

## 3. Guides, not a blog

Flo is less interested in blogging, and the data agrees with her. The thing that works is
not a diary post. It is an **evergreen page answering one question or covering one piece
of equipment**, written once and left to earn.

The TTouch post is that, by accident. It has run for months and still pulls 94 clicks a
quarter without being touched. A blog needs feeding; a guide does not.

**So `/blog/` becomes `/guides/`**, and the six thin partner pages become proper guides
rather than link stubs.

### Guide priority, from measured impressions

| # | Guide | Why | Evidence |
|---|---|---|---|
| 1 | Tellington TTouch harness | Already the site's best asset | pos 8.5, 4,183 impr |
| 2 | **Is your dog's behaviour caused by pain?** | Flo's real differentiator. Nothing exists on it | new — the video + physio pathway |
| 3 | Enrichment and freework | Ranks page one already, zero clicks | pos 9.8, 169 impr |
| 4 | Muzzle training | Ranks, zero clicks | pos 14.6, 121 impr |
| 5 | Tug toys and confidence | 296 impressions, 1 click | pos 21.1 |
| 6 | Long lines and decompression walks | She recommends these in every plan | new |
| 7 | Calming products | pos 19.2 | 65 impr |
| 8 | Natural chews | pos 23.9 | 63 impr |

**Where guides 2 and 6 come from:** Flo's own consultation reports. Bunny-hopping,
shortened stride, gut trouble driving behaviour, ball launchers and joint strain, quiet
evening walks with no ball. That material is already written and is subject matter no
competitor is covering.

**Every guide links to `/contact/`.** The TTouch post currently brings 94 people a
quarter and invites them nowhere.

---

## 4. URL preservation — the part that must not be got wrong

⚠ **These carry all the site's earned authority. Rebuild the page, keep the path, or 301
precisely. Never delete.**

| Existing URL | Action | Why |
|---|---|---|
| `/post/how-the-tellington-ttouch-harness-transformed-my-nervous-dog-s-walks-a-pawsitively-groundbreaking` | **301 → `/guides/tellington-ttouch-harness/`** | 94 clicks. Highest-value URL on the site |
| `/gunthorpe-river-trent` | 301 → `/walks/gunthorpe-river-trent/` | 22 clicks |
| `/houghton-on-the-hill` | 301 → `/walks/houghton-on-the-hill/` | 14 clicks |
| `/tellington-touch` | 301 → `/guides/tellington-ttouch-harness/` | 13 clicks |
| `/rufford-park-and-sherwood-forest` | 301 → `/walks/rufford-park-and-sherwood-forest/` | 374 impr |
| `/pickpocket-foragers` | 301 → `/guides/enrichment-and-freework/` | pos 9.8 |
| `/muzzle-movement` | 301 → `/guides/muzzle-training/` | pos 14.6 |
| `/tug-e-nuff` | 301 → `/guides/tug-toys-and-confidence/` | 296 impr |
| `/pet-remedy` | 301 → `/guides/calming-products-for-anxious-dogs/` | pos 19.2 |
| `/green-and-wilds` | 301 → `/guides/natural-chews/` | pos 23.9 |
| `/my-services` | 301 → `/how-it-works/` | 89 impr |
| **`/my-servicesold`** | **301 → `/how-it-works/`** | ⚠ **currently 404s.** 34 users/quarter. Was the homepage's main CTA target |
| `/contact` | 301 → `/contact/` | |
| `/healthform` | keep live until the ClientFlex form is proven, then 301 → `/contact/` | live capture route |
| `/code-of-ethics` | 301 → `/code-of-ethics/` | |
| `/customer-testimonials` | 301 → `/reviews/` | |
| `/flos-friends` | 301 → `/flos-friends/` | |
| `/walkies` | 301 → `/walks/` | |
| `/blog`, `/blog/categories/walks` | 301 → `/guides/` | |
| `/post/diego-has-found-his-forever-home` | 301 → `/reviews/` | 5 impr |
| `/post/can-i-go-swimming-mum` | 301 → `/guides/` | |
| `/post/case-study-blanca` | 301 → `/reviews/` | |
| `/copy-of-contact-thank-you` | 301 → `/contact/` | stray Wix duplicate |
| `/contact-thank-you` | keep — conversion page | GA4 key event fires here |
| `/general-4` | 301 → `/` | stray Wix page |
| `/international-canine` | **ruling needed** | 136 impr, 2 clicks, 12 GA4 views |

⚠ Pull the full URL list from **GSC → Indexing → Pages** before finalising. Wix
accumulates URLs that were never linked — `/general-4` and `/copy-of-contact-thank-you`
are both proof of that.

---

## 5. Immediate fixes, before any rebuild

1. **301 `/my-servicesold` → `/my-services`.** It 404s today and was the homepage CTA
   target. Check where the homepage button points **now**.
2. **Rewrite five titles and meta descriptions** on the partner pages. Page-one rankings
   currently earning zero clicks.
3. **Fix the Ads conversion action** so phone-link clicks are not counted as leads.
4. ~~**Pause Display/PMax** — two thirds of £635 for 6.6-second sessions.~~ **Withdrawn (W1 §2.6, recorded W4):** PMax is £0.00 and paused, there is no Display campaign, and the one live campaign is healthy. Do not switch it off.
5. **Add GDPR consent wording to `/healthform`.** It collects more personal data than the
   contact form and carries no consent statement (measured S127, still open).

---

## 6. Baseline to beat

Recorded so the rebuild can be judged rather than assumed.

| Metric | 90 days to 1 Sep 2026 |
|---|---|
| Organic clicks | 184 |
| Organic impressions | 11,378 |
| Sessions (all channels) | 472 |
| Users reaching `/healthform` | 10 |
| Thank-you completions | 5 users / 8 events |
| Ads spend | £134.85 (W1 originally recorded £634.93 — a CSV summed with its own subtotal rows; corrected W1 §2.6, applied here W4. 198 clicks × £0.68 and 7 conversions × £19.26 both reconcile to this figure) |
| Cost per conversion | £19.26 (7 conversions; the earlier ~£79 followed from the wrong spend figure). Ads and GA4 broadly agree (7 vs 9 key events) |
