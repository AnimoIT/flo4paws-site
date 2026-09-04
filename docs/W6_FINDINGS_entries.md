# W6 FINDINGS entries — PROVISIONAL numbering (W6-Fn); assign F-numbers at the register merge (W6-BL1)

### W6-F1 | W6 | MEASURED | close-set invariant recorded as MEASURED before the last write to the file

W5's handover: "deploy/ == /etc/nginx/ (7c8100ed) MEASURED at close 18:10". The vhost was zeroed at 18:07:20; the `diff … && echo "deploy/ == live vhost"` in history ran before that. Found at W6 open as `e3b0c442…` (sha256 of nothing). Running nginx still had the 18:05 config, so every control passed; the next reload would have taken www/staging/apex down, and `nginx -t` would have said "successful" on the way.

★ A close-set invariant is re-run as the **last** block of the session, after the last write, or it is INHERITED. And an `nginx -t` gate needs a byte-count/sha guard beside it for every file the reload depends on (→ W6-BL2).

---

### W6-F2 | W6 | MEASURED | four counts derived from my own edit, mislabelled, in one evening

Snippet `add_header` "4 MEASURED from W5's header list" (3 — Cache-Control is in the vhost locations); rate lines "2" after seeing 3 in `contact.html` (3); `a animal physiotherapist` "4" (3 + one capital `A`); `Telephone consultation` "3" (1 — two are "Extra **t**elephone", grep case-sensitive, `-c` counts lines). Each caught by an `assert count==n` or the instrument; none reached the bytes.

★ F-93's rule, restated one level down: a count of *my own edit* is not derived until a script prints it. Write the assert first, predict from the assert's output, not from the diff I remember reading.

---

### W6-F3 | W6 | MEASURED | `journalctl -u nginx` is not a reload instrument

Empty for W5's 18:05 reload, empty for certbot's dry-run challenge reloads, one "Reloaded" line for W6's `systemctl reload nginx`. `nginx -s reload` signals the master directly; systemd never sees it. Used twice tonight as if it were complete (recon 5c; certbot prediction "2 Reloaded").

★ For "did nginx reload", the instrument is the master's worker start times (`ps -o lstart` on the worker PIDs) or behaviour on the wire — not the unit's journal, unless every reload goes through `systemctl`. Preference: make `systemctl reload nginx` the only reload path in `deploy.sh` and the W-series so the journal becomes true.

---

### W6-F4 | W6 | MEASURED | recon instrument faults (mine): `rev-parse --short` with two revisions; `gen.py` path asserted, not read

`git rev-parse --short HEAD origin/main` → "Needed a single revision" (cell 2 unscored). `python3 gen.py --check` at repo root → no such file; it is `src/gen.py` (cell 3 unscored). Both had a `find`/`ls` available in the same block.

★ F-01 again. A path or a flag is a property of an instrument; read it before the block that depends on it, or put the discovery in the same block ahead of the use.

---

### W6-F5 | W6 | MEASURED | W-series register debt: numbers allocated from the infra sequence, never landed, now colliding

Details in the handover §4 and W6-BL1. The failure is process, not a slip: three sessions closed with entries "authored as files" that never reached the register the numbers came from, while another series kept allocating from the same `NEXT_ID`.

★ An entry is registered when `grep -c '^### BL-nnn'` on the register prints 1, not when the file exists. Close-set is not complete until that grep has run on the box.
