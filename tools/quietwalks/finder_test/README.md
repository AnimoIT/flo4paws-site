# Finder identity test (S373)

Proves a change to `src/static/walks/finder/finder.js` leaves the UK finder unchanged.
The harness loads the UK page in jsdom with a stub map and synthetic data, scripts 15 visitor
steps (search, sliders, quiet-only, list, path popup, bad/unknown/uncovered postcodes, location)
and prints a record of everything the page shows. The record must not change.

    cd tools/quietwalks/finder_test
    npm install jsdom@24                      # once, outside the repo is fine
    python3 make_uk_fixture.py /tmp/uk_fx.json
    node harness.js ../../../build/walks/quiet-walk-finder/index.html ../../../build/walks/finder/finder.js /tmp/uk_fx.json > /tmp/rec.json
    sha256sum /tmp/rec.json                   # must equal UK_RECORD_SHA256 below

UK_RECORD_SHA256 is the record of the pre-S373 finder.js (391fd1c lineage), which the
S373 shared core reproduces byte for byte.
UK_RECORD_SHA256: f777b246c1430235def54c2df47afe7ec6d0339625b6188bd775a41930a2db5e
