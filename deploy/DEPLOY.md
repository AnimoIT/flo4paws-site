# Flo4Paws site — staging deploy

**Nothing here touches www. This puts the site on a staging hostname only.**

## What this bundle is
20 pages, one HTML file each, real URLs, per-page title/description/canonical/OG,
JSON-LD on every page, breadcrumbs, sitemap.xml, robots.txt, images as files.

## Preconditions
1. DNS: add an A record `staging.flo4paws.co.uk` → the box. **Do not touch www or MX.**
2. Confirm with Flo before any nginx reload — the same nginx serves her production API.

## Steps
```
# 1. copy the bundle up (from your machine)
scp -r build/ user@204.168.132.118:/tmp/flo4paws-site

# 2. on the box — place it
sudo mkdir -p /var/www/flo4paws-site
sudo rsync -a --delete /tmp/flo4paws-site/ /var/www/flo4paws-site/
sudo rm -f /var/www/flo4paws-site/nginx-flo4paws.conf /var/www/flo4paws-site/DEPLOY.md

# 3. install the vhost
sudo cp /tmp/flo4paws-site/nginx-flo4paws.conf /etc/nginx/sites-available/flo4paws-site
sudo ln -sf /etc/nginx/sites-available/flo4paws-site /etc/nginx/sites-enabled/

# 4. GATE — must pass before reload
sudo nginx -t

# 5. only if step 4 passed
sudo systemctl reload nginx

# 6. certificate
sudo certbot --nginx -d staging.flo4paws.co.uk
```

## Falsifiers — run these, do not assume
```
curl -sI http://staging.flo4paws.co.uk/ | head -1                  # expect 200
curl -sI http://staging.flo4paws.co.uk/guides/ | head -1           # expect 200
curl -sI http://staging.flo4paws.co.uk/my-servicesold | head -1    # expect 301
curl -s  http://staging.flo4paws.co.uk/ | grep -c '<h1'            # expect 1
curl -sI http://staging.flo4paws.co.uk/ | grep -i x-robots-tag     # expect noindex
curl -sI http://app.flo4paws.co.uk/ | head -1                      # CONTROL: app still up
```
The last one matters most. If the app is not still serving, roll back immediately:
`sudo rm /etc/nginx/sites-enabled/flo4paws-site && sudo nginx -t && sudo systemctl reload nginx`

## Not done yet
- GA4 tag + Consent Mode v2 (placeholder comment in every `<head>`)
- favicon.ico
- 9 guide bodies and 3 walk bodies — stubs with a note
- Newgrange / K9 Corner / Maddy's Mutts logos and one-liners
- Verbatim Trustpilot reviews or the widget


---

## ⚠ PRE-CUTOVER GATE — the intake form

The contact CTA now points at `https://app.flo4paws.co.uk/intake-form/flo4paws/`.
That form is published and serves 200, but it has **not taken a real client submission**.
The 9 rows on prod are test data.

**All four must be true before `www` moves to this box:**

1. **BL-576 / BL-491 — validation.** Ian hit a validation error on this form that
   listed problems he could not navigate to, caused by hidden conditional children
   being validated. A real client hitting that abandons silently and Flo never knows.
   Reproduce, fix, or prove absent.
2. **BL-566 / BL-572 — claim link.** No resend, no delete in the admin panel, and
   claim emails are indistinguishable from one another. Spent links dead-end.
3. **One real submission, end to end.** Form → `pending_intake` → claim email →
   account created → Flo sees the answers. Deployed is not real-actor-proven.
4. **Cross-domain analytics.** GA4 must list both `flo4paws.co.uk` and
   `app.flo4paws.co.uk` under Configure your domains, and a conversion event must
   fire on the form's success state. Otherwise every enquiry attributes to a
   referral and Ads reports zero conversions.

**Then, in the same change:** uncomment the `/healthform` redirect in the vhost, and
take the Wix form down. Not before — until then `/healthform` is the live route and
a redirect would break it.
