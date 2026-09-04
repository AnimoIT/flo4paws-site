#!/usr/bin/env python3
"""Flo4Paws static site generator.

  src/pages/<slug>.html   JSON front-matter between --- lines, then verbatim body HTML
  src/static/             copied into build/ unchanged
  build/                  output; committed; must equal /var/www/flo4paws-site/

  python3 src/gen.py            writes build/
  python3 src/gen.py --check    renders to a temp dir, diffs against build/, exit 1 on any difference
"""
import filecmp, hashlib, html, json, pathlib, shutil, sys, tempfile

SRC = pathlib.Path(__file__).resolve().parent
ROOT = SRC.parent
SITE = "https://www.flo4paws.co.uk"
NAV_ITEMS = [('/', 'Home'), ('/about/', 'About Flo'), ('/how-it-works/', 'How it works'), ('/guides/', 'Guides'), ('/walks/', 'Walks'), ('/flos-friends/', "Flo's Friends")]

HEAD = '<!DOCTYPE html>\n<html lang="en-GB">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>@@TITLE@@</title>\n<meta name="description" content="@@DESC@@">\n<link rel="canonical" href="https://www.flo4paws.co.uk@@PATH@@">\n<meta name="robots" content="@@ROBOTS@@">\n<meta name="theme-color" content="#50E3C2">\n<meta property="og:type" content="@@OGTYPE@@">\n<meta property="og:site_name" content="Flo 4 Paws">\n<meta property="og:locale" content="en_GB">\n<meta property="og:url" content="https://www.flo4paws.co.uk@@PATH@@">\n<meta property="og:title" content="@@TITLE@@">\n<meta property="og:description" content="@@DESC@@">\n<meta property="og:image" content="https://www.flo4paws.co.uk@@OGIMG@@">\n<meta name="twitter:card" content="summary_large_image">\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=Karla:wght@300;400;500;600;700&display=swap" rel="stylesheet">\n<link rel="stylesheet" href="/site.css?v=@@CSSV@@">\n<link rel="icon" href="/favicon.ico" sizes="32x32">\n<link rel="icon" type="image/png" sizes="16x16" href="/img/icon-16.png">\n<link rel="icon" type="image/png" sizes="32x32" href="/img/icon-32.png">\n<link rel="apple-touch-icon" sizes="180x180" href="/img/icon-180.png">\n<link rel="manifest" href="/site.webmanifest">\n'
HEAD_TAIL = '\n<script>\nwindow.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}\ngtag("consent","default",{"ad_storage":"denied","ad_user_data":"denied","ad_personalization":"denied","analytics_storage":"denied"});\ntry{if(localStorage.getItem("f4p-consent")==="granted"){gtag("consent","update",{"ad_storage":"granted","ad_user_data":"granted","ad_personalization":"granted","analytics_storage":"granted"});}}catch(e){}\ngtag("js",new Date());\nvar f4pCfg={"linker":{"domains":["flo4paws.co.uk","app.flo4paws.co.uk"]}};\nif(location.hostname==="staging.flo4paws.co.uk"){f4pCfg.debug_mode=true;}\ngtag("config","G-WZVF0MNWQF",f4pCfg);\n</script>\n<script async src="https://www.googletagmanager.com/gtag/js?id=G-WZVF0MNWQF"></script>\n<script src="/site.js?v=@@JSV@@" defer></script>\n</head>\n<body>\n<header class="site">\n  <div class="wrap bar">\n    <a class="logo" href="/" aria-label="Flo 4 Paws home">\n      <img src="/img/flo4paws-logo.png" alt="Flo 4 Paws — Helping Nervous Dogs and Owners"\n           width="380" height="96" fetchpriority="high">\n    </a>\n    @@NAV@@\n  </div>\n</header>'
FOOTER = '<footer class="site">\n  <div class="wrap cols">\n    <div>\n      <p class="fh">Flo 4 Paws</p>\n      <p>Nervous and anxious dog specialist based in Bingham, Nottingham NG13, covering\n      Nottinghamshire, Leicestershire and Rutland.</p>\n      <p style="font-size:.85rem">Saxondale &middot; Radcliffe on Trent &middot; Bottesford\n      &middot; Newark &middot; Grantham &middot; Melton Mowbray &middot; Oakham</p>\n    </div>\n    <div><p class="fh">Pages</p><ul>\n      <li><a href="/about/">About Flo</a></li>\n      <li><a href="/how-it-works/">How it works</a></li>\n      <li><a href="/guides/">Guides</a></li>\n      <li><a href="/walks/">Walks</a></li>\n      <li><a href="/flos-friends/">Flo\'s Friends</a></li>\n      <li><a href="/app/">The app</a></li>\n      <li><a href="/code-of-ethics/">Code of ethics</a></li>\n      <li><a href="/reviews/">Reviews</a></li>\n    </ul></div>\n    <div><p class="fh">Get in touch</p>\n      <p style="font-size:.88rem">The quickest way to reach me is the\n      <a href="/contact/">contact form</a>.</p>\n      <ul>\n        <li><a href="mailto:info@flo4paws.co.uk">info@flo4paws.co.uk</a></li>\n        <li><a href="tel:+447346142734">07346 142734</a></li>\n      </ul></div>\n  </div>\n  <div class="wrap legal">&copy;2026 Flo 4 Paws &middot;\n    <a href="/cookie-policy/">Cookie policy</a> &middot;\n    <a href="/terms-of-use/">Terms of use</a> &middot;\n    <a href="/privacy-policy/">Privacy policy</a> &middot; Built by AnimoIT Ltd</div>\n</footer>\n</body>\n</html>\n'


def esc(s):
    return html.escape(s, quote=True)


def load_pages():
    pages = []
    for p in sorted((SRC / "pages").glob("*.html")):
        raw = p.read_text(encoding="utf-8")
        assert raw.startswith("---\n"), p
        end = raw.index("\n---", 4)
        meta = json.loads(raw[4:end])
        meta["body"] = raw[end + len("\n---"):]
        meta["_file"] = p.name
        pages.append(meta)
    pages.sort(key=lambda m: (m["sitemap"] is None, m["sitemap"]["order"] if m["sitemap"] else 0))
    return pages


def render_nav(current):
    links = "".join(
        '<a href="%s"%s>%s</a>' % (href, ' aria-current="page"' if href == current else "", esc(label))
        for href, label in NAV_ITEMS)
    return ('<nav class="main"><button class="menu-btn" type="button" aria-expanded="false" '
            'aria-controls="nav-links">Menu</button><div class="links" id="nav-links">'
            + links + '</div><a class="cta" href="/contact/">Contact us</a></nav>')


def asset_version(name):
    """First 8 hex of the asset's sha256: changes when the file changes, so browsers refetch."""
    return hashlib.sha256((SRC / "static" / name).read_bytes()).hexdigest()[:8]


def render_page(m):
    head = (HEAD.replace("@@TITLE@@", esc(m["title"])).replace("@@DESC@@", esc(m["description"]))
            .replace("@@PATH@@", m["path"]).replace("@@OGTYPE@@", m["og_type"]).replace("@@OGIMG@@", m["og_image"])
            .replace("@@CSSV@@", asset_version("site.css"))
            .replace("@@ROBOTS@@", m.get("robots", "index,follow,max-image-preview:large")))
    ld = json.dumps(m["ld"], indent=2, ensure_ascii=False)
    return (head + '<script type="application/ld+json">' + ld + "</script>"
            + HEAD_TAIL.replace("@@NAV@@", render_nav(m["nav"])).replace("@@JSV@@", asset_version("site.js")) + m["body"] + FOOTER)


def render_sitemap(pages):
    rows = "".join(
        "  <url><loc>%s%s</loc><changefreq>%s</changefreq><priority>%s</priority></url>\n"
        % (SITE, m["path"], m["sitemap"]["changefreq"], m["sitemap"]["priority"]) for m in pages if m["sitemap"])
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + "</urlset>\n")


def build(out):
    out = pathlib.Path(out)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(SRC / "static", out)
    pages = load_pages()
    for m in pages:
        d = out / m["path"].strip("/")
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render_page(m), encoding="utf-8")
    (out / "sitemap.xml").write_text(render_sitemap(pages), encoding="utf-8")
    return len(pages)


def tree(d):
    d = pathlib.Path(d)
    return sorted(str(p.relative_to(d)) for p in d.rglob("*") if p.is_file())


def check():
    with tempfile.TemporaryDirectory() as tmp:
        n = build(tmp)
        a, b = tree(tmp), tree(ROOT / "build")
        bad = sorted(set(a) ^ set(b))
        bad += [rel for rel in sorted(set(a) & set(b))
                if not filecmp.cmp(pathlib.Path(tmp) / rel, ROOT / "build" / rel, shallow=False)]
        print("pages: %d  files: %d  differences: %d" % (n, len(a), len(bad)))
        for rel in bad:
            print("  DIFF", rel)
        return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(check() if "--check" in sys.argv else print("wrote build/: %d pages" % build(ROOT / "build")))
