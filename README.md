# flo4paws-site

Static marketing site for www.flo4paws.co.uk (currently staging.flo4paws.co.uk).

- `build/`  — the served tree, committed. `/var/www/flo4paws-site/` must equal this directory.
- `deploy/` — nginx vhost and deploy notes.
- `src/`    — generator (gen.py + content.py). Being reconstructed; until it regenerates
              `build/` byte-for-byte, `build/` is the source of truth.

Tag `w2-live` = the tree as served on 2026-09-04, after the W2 mobile-nav session.
