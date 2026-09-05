# W3 FINDINGS entries — 2026-09-04

W-series register entry (ruling A, W6b, 5 Sep 2026: W register lives in `flo4paws-site/docs/`, not `animoit-infra`). Numbering continues from F-81 (S216) under the WF- prefix.

---

### WF-82 | W3 | MEASURED | a constructed hostname is a claim, not a control

R1 cell 18: the Lily control used `app.lilyvetphysiotherapy.co.uk`, built from a truncated line in the W1 handover. `curl` returned `000` — the host does not exist. The real host (`.com`) came from `grep server_name` on the enabled vhosts. Same shape later in the session: a page title typed from memory ("Muzzle training for nervous dogs, done kindly") failed an `assert count==1` against the real title.

★ Any name a control depends on — host, path, title, key — must be read off the artefact in the same block or an earlier one, never supplied by Claude. A control with a guessed input cannot fail for the right reason. F-01 instance; sibling of F-73 (inputs resolved by the wrong step).

---

### WF-83 | W3 | MEASURED | an unrun check became a recorded finding

W2 recorded "`Cache-Control: max-age=604800` on all assets including HTML — must fix before cutover" and issued a read-only block to confirm it. The block was never run. W3 measured: HTML has **no** Cache-Control; the 7d header is on `site.css`. The claim survived a session boundary as a blocker.

★ A finding whose confirming block did not run is a hypothesis and must be recorded as OPEN/UNTESTED, not as a finding. Handovers must carry the "not yet run" state explicitly. Stale-claim class: the box never said it; a document did.

---

### WF-84 | W3 | MEASURED | `grep -c` has no stopping power, then had the wrong stopping power

Three instances in one session, all `grep -c` used as a gate:
1. R9 step 0: secret-shaped grep printed `1` (expected 0). `set -e` does not act on a printed count; the tree was pushed public before the hit was identified. (It was "password hashing" prose — harmless — but the control did not gate.)
2. R13: `gh pr checks 2 … --watch | grep -E '^(✓|X|✗)'` filtered out the status line; merge proceeded with CI unread.
3. R14: `gh pr checks 3 … | grep -c '✓'` printed `0`, which is exit status 1; under `set -e` that terminated the shell — which was Ian's SSH session. The deploy half of the block never ran.

★ A count is not a gate. Gate with an explicit comparison that exits: `n=$(…| grep -c …); [ "$n" -eq 0 ] || { echo FAIL; exit 1; }`. Never put a bare `grep`/`grep -c` on the last line of a pipeline under `set -e`. And never `set -e` in a block Ian pastes into an interactive shell — a false exit kills the session; use `|| exit` per step or a subshell. Sibling of F-75 (a control that cannot distinguish the states it claims to) and F-80 (status grep anchored on the wrong thing).

---

### WF-85 | W3 | MEASURED | generated artefacts shipped without their generator in git

W1 produced 23 pages from `gen.py` + `content.py` in the sandbox, tarred `build/`, and shipped the tar. The generator was never presented as a download, never committed anywhere, and was gone when the session ended. W2 then edited the output by hand — the only rational move given no source — and the served tree became the sole copy. Recovery cost a session of reverse-engineering plus a byte-identity proof.

★ Anything Claude generates in the sandbox that will be deployed must leave the sandbox as **source + a reproducibility check**, in git, before the deploy step — not as output alone. The frontend git-drift lesson (S201) applied to a new estate and was not carried across. Rule: no estate deploys from a tree that is not in a repo with a CI check that source reproduces it.

---

### WF-86 | W3 | MEASURED | a screenshot audit infers absence from the nav

ChatGPT's audit marked eight items 🔴 "lost". Six existed on the box — pages not in the primary nav (Code of Ethics, Reviews, walks, guides), a redirect map that is invisible to a browser, and a guide whose body does not contain its own search phrase. The two real hits (thin credentials, no About) were the ones Ian had already spotted.

★ An audit made from rendered screenshots can only see what the nav exposes. Score every "missing" claim against the file tree and the vhost before acting on it. Corollary for our own greps: `grep -l 'International Canine'` → 0 while `/guides/international-canine/` exists — a phrase grep proves something about the phrase.

---

### WF-87 | W3 | MEASURED | the pipeline's exit status is `tail`'s, not the check's

`python3 src/gen.py --check | tail -1; echo "exit=$?"` printed `exit=0` after a deliberate one-byte break, because `$?` was `tail`'s. The DIFF line above it was the actual evidence. Same for `| grep -c` (WF-84 #3) and W2's changed-line count vs replacement count.

★ When proving a check can fail, capture the check's own status: run it unpiped, or `set -o pipefail`, or read its stdout for the assertion rather than `$?`. A falsification test whose exit code is someone else's has not falsified anything.
