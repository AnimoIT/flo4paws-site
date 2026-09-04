# W4 FINDINGS entries — 2026-09-04

Append to `animoit-infra/claude/FINDINGS.md`. Numbering continues from F-87 (W3).

---

### F-88 | W4 | MEASURED | a standing rule was in the brief and still not applied

The rule "never route multi-line content through an inline heredoc — the paste path strips blank lines" is in the memory summary and the S-series handovers. W4 wrote a commit message and a PR body through `cat <<'EOF'` anyway. Both lost their blank lines; git treated a five-line commit message as one subject. Harmless (squash-merge used the PR title), but the rule existed and was known.

★ Rules that live in prose are not applied under momentum. The fix that worked the same session: `printf '%s\n\n%s\n'`, which carries its own blank lines. Prefer constructs that make the rule unnecessary over remembering the rule.

---

### F-89 | W4 | MEASURED | a phrase grep nearly filed a false absence on the production estate

`grep '\.git' sites-enabled/*` → 0, so W4 predicted "no `.git` deny in any vhost" and prepared to treat a 200 on `/.git/HEAD` as an incident. The app vhost line 29 has `location ~ /\.(?!well-known)` — a generic dotfile deny that never mentions git. All four hosts 404.

★ F-86's corollary, applied to controls: a grep for a phrase proves something about the phrase. Before asserting an absence of a *behaviour*, test the behaviour (the `curl` did) and read the file for the *class* of rule, not the specific instance. The false-absence would have cost a wasted G-2 and an incident number.

---

### F-90 | W4 | MEASURED | three hand-counts in one session, all wrong by one or two

R7 cell 3 (+43/+41 bytes, actual +44/+40), R7 cell 6 (3 porcelain lines, actual 1 — `.candidate` gitignored), R12 cell 6 (26 live 301s, actual 25 — map is 24, not 25). None reached the bytes because each had an instrument beside it (`len()` assert, `git status`, `grep -c`).

★ Same F-01 shape as S101/S103/S111. The prediction discipline is doing its job — the miss is visible — but the *basis* column should refuse a number that was not derived. Rule: a predicted count must name the instrument that will produce it, and if the prediction was not produced by that instrument beforehand, write OPEN.

---

### F-91 | W4 | MEASURED | `gh pr merge --delete-branch` leaves the local branch when you checkout main first

R3 predicted the local branch would be gone. gh only deletes the local branch if it is the one checked out; switching to `main` first (done for safety) means it stays. Three PRs later the pattern was routine: `-D` gated on served-tree diff = 0.

★ Method note, not a defect: checkout-first + explicit `-D` after the downstream proof is the safer sequence, and costs one line.
