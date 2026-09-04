# W4 BACKLOG entries — 2026-09-04

Append to `animoit-infra/claude/BACKLOG.md`. Numbering continues from BL-654 (W3). Census instrument: `grep -c '^### BL-'`.

## Closures (edit existing rows)

- **BL-644 → DONE (W4).** PR #3 squash-merged `49fbe88`. `/about/` live on staging; CI read unfiltered before merge. Flo's read-through still owed (content, not a blocker).
- **BL-645 → DONE (W4).** `location /` carries `Cache-Control: no-cache` (PR #5, `75ab537`). MEASURED: `curl -sI staging/` → `Cache-Control: no-cache`.
- **BL-646 → DONE-PARTIAL (W4).** Marketing half shipped: `/app/` page, PR #4 `395f711`. Not in primary nav; footer + home links. Help half → BL-655.
- **BL-650 → DONE (W4).** `docs/` in repo, PR #6 `d1f4967`. `ia-v2.md` corrected in three cells (spend, cost per conversion, withdrawn PMax recommendation). W2/W3 handovers and the ChatGPT audit not yet in `docs/` (README names the gap).
- **BL-652 → PARTIAL (W4).** Second login identified: four sessions from Ian's IP, one `flo4paws` pts from 2 Sep. Not a third party. `r2dev.env`, `/tmp` tarballs, and beerscope-in-controls still open (beerscope was used as a control in W4 — 200 before/after reload — but not yet written into any control list).

---

### BL-655 | OPEN | W4 | RULED | MEDIUM | Help / user guides served by the tenant frontend at `/help/`

state:    Ian wants in-app guides. Ruling W4: served from `flo4paws-frontend` at `/help/` on every tenant host, branded via `/api/tenant/config` (name, colours, noun), linked from the website `/app/` and the app menu. Audiences ruled: Client; Practitioner (behaviourist and physio-owner are one document with noun substitution); Physio reviewer (`physio-gate` role). Ian's proposal was four; Claude's counter is three — ruling owed.
remedy:   Own session series (H1…). Draft from `clientflexuserguidev2.pdf` + handovers; every step verified against a live screen by Ian/Flo/Lily before linking; screenshots from a real phone. Practitioner guide first (the reviewers need it to check the client one). Deploy path: frontend repo → `deploy.sh` line-37 chmod list and `pr-checks.yml` validator list must include the new file (S164 finding).
Claim evidence: RULED — Ian, W4.

---

### BL-656 | OPEN | W4 | MEASURED | SMALL | Images emit two `Cache-Control` headers

state:    `curl -sI staging/img/flo4paws-logo.png` → `Cache-Control: max-age=2592000` (from `expires 30d`) **and** `Cache-Control: public, immutable` (from `add_header`). Pre-existing; W4 made it visible. Browsers merge them; untidy, not wrong.
remedy:   Drop `expires`; `add_header Cache-Control "public, max-age=2592000, immutable" always;`. Same for `site.css` (7d → consider `immutable` now that `?v=` busts it). One `deploy/` PR + reload with controls.
Claim evidence: MEASURED.

---

### BL-657 | OPEN | W4 | MEASURED | SMALL | `/app/` copy claims recorded VERBAL; screenshots owed

state:    Two lines in `src/pages/app.html` assert product behaviour — "your plan and forms" visible in the client app; one diary per dog under one account. Ian confirmed by running the commit block after being asked; no screen was read. Page ships with store badges only; no screenshots.
remedy:   Flo's read-through of `/app/`; 2–3 real-phone screenshots as a follow-on PR; strike either line if the walk-through disproves it.
Claim evidence: VERBAL — Ian, W4.

---

### BL-658 | OPEN | W4 | INHERITED | SMALL | `docs/` gaps — W2, W3, W4 handovers and the ChatGPT audit

state:    `docs/README.md` names them missing. W4 handover written but delivered to the Claude project, not the repo.
remedy:   Add on the next docs PR. Consider making "handover into `docs/` in the same session" the rule for the W series.
Claim evidence: INHERITED.

---

### BL-659 | OPEN | W4 | MEASURED | SMALL | `ia-v2` Ads figure — W1 gives two "corrected" values

state:    W1 §2.6 says £134.85 (twice, with clicks/CPC/conversions/CPA that reconcile to it); W1 §8 error table says £143.90 (once, reconciles to nothing). W4 used £134.85 and said why in the file.
remedy:   Ian glances at the Ads screenshot; if £134.85, close; if not, one-cell PR.
Claim evidence: MEASURED (arithmetic) — not yet read off the Ads account.
