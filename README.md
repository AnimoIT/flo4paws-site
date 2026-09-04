# flo4paws-site

Static marketing site for www.flo4paws.co.uk (currently staging.flo4paws.co.uk).

- `build/`  — the served tree, committed. `/var/www/flo4paws-site/` must equal this directory.
- `deploy/` — nginx vhost and deploy notes.
- `src/`    — the source. `src/pages/<slug>.html` = JSON front-matter + body HTML;
              `src/static/` = css/js/images copied verbatim; `src/gen.py` renders `build/`.

## Workflow

    python3 src/gen.py            # render build/
    python3 src/gen.py --check    # CI gate: build/ must equal what src/ renders (exit 1 otherwise)

Edit `src/`, run `gen.py`, commit `src/` **and** `build/` together. Never edit `build/` by hand.

Tag `w2-live` = the tree as served on 2026-09-04, after the W2 mobile-nav session.
