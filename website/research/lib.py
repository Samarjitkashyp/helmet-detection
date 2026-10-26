"""Page shell for the Axom AI research pages: head (SEO / social / structured data), header, footer.

Mirrors aiaxom.co.in: Plus Jakarta Sans, dark navy (#0b1220), emerald and amber, the same navigation and footer wording.
"""
import json
from html import escape

BASE = "https://aiaxom.co.in"
PUBLISHED = "2026-10-26"
MODIFIED = "2026-10-26"
ASSET_V = "20261026"
SITE = "Axom AI"
ORG_ID = f"{BASE}/#organization"       # the Organization the main site already declares
AUTHOR = {"@type": "Person", "name": "Samarjit Kashyap", "url": "https://github.com/Samarjitkashyp",
          "jobTitle": "Founder, Axom AI", "worksFor": {"@id": ORG_ID}}
GITHUB_BACKEND = "https://github.com/Samarjitkashyp/helmet-detection"
GITHUB_APP = "https://github.com/Samarjitkashyp/helmet-detection-mobile-app"
APP_PAGE = "https://helmet-detection.aiaxom.co.in/app"
WHO_URL = "https://www.who.int/news/item/05-04-2023-new-who-guide-aims-to-boost-the-use-of-life-saving-helmets-for-motorcycle-riders"
OG_IMAGE = f"{BASE}/research/assets/og-helmet-detection.jpg"

NAV = [("AI Tools", "/tools"), ("Axom AI Chat", "https://chat.aiaxom.co.in/"), ("Research", "/research/"),
       ("Use Cases", "/use-cases"), ("Pricing", "/pricing"), ("Blog", "/blog"), ("FAQ", "/faq"),
       ("About", "/about"), ("Contact", "/contact")]


def e(s):
    return escape(s, quote=True)


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>"


def breadcrumb_schema(crumbs):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + u}
                                for i, (n, u) in enumerate(crumbs)]}


def faq_schema(items):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}


def article_schema(url, headline, description, image=OG_IMAGE, keywords=(), about=(), cites=(), extra=None):
    d = {"@context": "https://schema.org", "@type": "TechArticle", "@id": BASE + url + "#article",
         "headline": headline, "description": description, "image": [image], "inLanguage": "en-IN",
         "datePublished": PUBLISHED, "dateModified": MODIFIED, "author": AUTHOR,
         "publisher": {"@id": ORG_ID}, "mainEntityOfPage": BASE + url, "url": BASE + url,
         "isAccessibleForFree": True, "keywords": ", ".join(keywords),
         "about": [{"@type": "Thing", "name": n} for n in about],
         "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".answer", "h1"]}}
    if cites:
        d["citation"] = [{"@type": "CreativeWork", "name": n, "url": u} for n, u in cites]
    if extra:
        d.update(extra)
    return d


def head(p):
    url = BASE + p["path"]
    og_image = p.get("image", OG_IMAGE)
    typ = "article" if p.get("article") else "website"
    schemas = [breadcrumb_schema(p["crumbs"])] + p.get("schemas", [])
    out = [
        '<!doctype html>', '<html lang="en-IN">', '<head>', '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f'<title>{e(p["title"])}</title>',
        f'<meta name="description" content="{e(p["description"])}">',
        f'<link rel="canonical" href="{url}">',
        '<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large,max-video-preview:-1">',
        '<meta name="author" content="Samarjit Kashyap, Axom AI">',
        f'<meta name="keywords" content="{e(", ".join(p.get("keywords", [])))}">',
        f'<link rel="alternate" hreflang="en-IN" href="{url}">',
        f'<link rel="alternate" hreflang="x-default" href="{url}">',
        '<meta name="theme-color" media="(prefers-color-scheme: light)" content="#f0fdf4">',
        '<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#0b1220">',
        f'<meta property="og:type" content="{typ}">', f'<meta property="og:site_name" content="{SITE}">',
        '<meta property="og:locale" content="en_IN">', f'<meta property="og:url" content="{url}">',
        f'<meta property="og:title" content="{e(p["og_title"] if "og_title" in p else p["title"])}">',
        f'<meta property="og:description" content="{e(p["description"])}">',
        f'<meta property="og:image" content="{og_image}">', '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:image:alt" content="{e(p.get("image_alt", "Helmet detection results on traffic camera footage, riders shown with verdict boxes"))}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{e(p["og_title"] if "og_title" in p else p["title"])}">',
        f'<meta name="twitter:description" content="{e(p["description"])}">', f'<meta name="twitter:image" content="{og_image}">',
    ]
    if p.get("article"):
        out += [f'<meta property="article:published_time" content="{PUBLISHED}">',
                f'<meta property="article:modified_time" content="{MODIFIED}">',
                '<meta property="article:author" content="Samarjit Kashyap">', '<meta property="article:section" content="Research">']
        out += [f'<meta property="article:tag" content="{e(k)}">' for k in p.get("keywords", [])[:6]]
    out += [
        '<link rel="icon" href="/favicon.ico" sizes="any">', '<link rel="icon" href="/favicon-32x32.png" sizes="32x32" type="image/png">',
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180">',
        '<link rel="sitemap" type="application/xml" href="/research/sitemap.xml">',
        '<link rel="preconnect" href="https://fonts.googleapis.com">', '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">',
        f'<link rel="stylesheet" href="/research/assets/research.css?v={ASSET_V}">',
    ]
    out += [jsonld(s) for s in schemas]
    out.append("</head>")
    return "\n".join(out)


def header(current):
    links = []
    for name, href in NAV:
        cur = ' aria-current="page"' if (href == "/research/" and current == "research") else ""
        links.append(f'<a href="{href}"{cur}>{name}</a>')
    return f'''<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap bar">
<a class="brand" href="/"><img src="/axom-browser-logo.png" width="40" height="40" alt="Axom AI logo"><span><b>Axom AI</b><small>SMART &bull; ASSAMESE &bull; AI FOR ALL</small></span></a>
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Open menu">&#9776;</button>
<nav class="nav" id="site-nav" aria-label="Main">{"".join(links)}</nav>
</div></header>'''


def crumbs_html(crumbs):
    items = []
    for i, (n, u) in enumerate(crumbs):
        last = i == len(crumbs) - 1
        items.append(f'<li>{e(n)}</li>' if last else f'<li><a href="{u}">{e(n)}</a></li>')
    return f'<nav class="crumbs wrap" aria-label="Breadcrumb"><ol>{"".join(items)}</ol></nav>'


FOOTER = '''<footer class="site-footer"><div class="wrap">
<div class="foot-grid">
<div><a class="brand" href="/"><img src="/axom-browser-logo.png" width="40" height="40" alt="Axom AI logo" loading="lazy"><span><b>Axom AI</b><small>SMART &bull; ASSAMESE &bull; AI FOR ALL</small></span></a>
<p style="margin-top:14px;max-width:420px">Axom AI is Assam's first indigenous generative artificial intelligence platform, engineered to bridge the linguistic divide for 15 million Assamese speakers with native conversational models, multimodal creative suites, and regional computing infrastructure.</p></div>
<div><h4>Product</h4><ul><li><a href="/tools">AI Tools</a></li><li><a href="/pricing">Pricing</a></li><li><a href="/blog">What's New</a></li><li><a href="/use-cases">Use Cases</a></li></ul></div>
<div><h4>Research</h4><ul><li><a href="/research/">All research</a></li><li><a href="/research/helmet-detection/">Helmet detection</a></li><li><a href="/research/helmet-detection/results/">Results</a></li><li><a href="/research/helmet-detection/model-card/">Model card</a></li></ul></div>
<div><h4>Resources</h4><ul><li><a href="/blog">Blog &amp; Insights</a></li><li><a href="/faq">Frequently Asked Questions</a></li><li><a href="https://user.aiaxom.co.in/support/">Help &amp; Support</a></li><li><a href="https://chat.aiaxom.co.in/tools">AI Tools Directory</a></li></ul></div>
<div><h4>Company</h4><ul><li><a href="/about">About Axom AI</a></li><li><a href="/privacy">Privacy Policy</a></li><li><a href="/terms">Terms of Service</a></li><li><a href="/contact">Contact Us</a></li></ul></div>
</div>
<div class="foot-bottom"><span>&copy; 2026 Axom AI. All rights reserved.</span><span><a href="/privacy">Privacy Policy</a> &middot; <a href="/terms">Terms of Service</a> &middot; <a href="/cookie-policy">Cookie Policy</a></span><span>Made with &hearts; in Assam, India</span></div>
</div></footer>
<script src="/research/assets/research.js?v=''' + ASSET_V + '''" defer></script>
</body></html>'''


def page(p, body):
    """p: dict(path, title, description, crumbs, ...)  body: html placed inside <main>"""
    return "\n".join([head(p), header("research"), crumbs_html(p["crumbs"]), f'<main id="main">{body}</main>', FOOTER])


def related(links):
    return '<div class="related">' + "".join(
        f'<a class="card" href="{u}"><span class="tag">{e(t)}</span><h3>{e(n)}</h3><p>{e(d)}</p></a>' for n, u, t, d in links) + "</div>"


def meta_line(updated=MODIFIED, extra=""):
    return (f'<p class="meta"><span>By <strong><a href="https://github.com/Samarjitkashyp">Samarjit Kashyap</a></strong>, Axom AI</span>'
            f'<span>Published <strong><time datetime="{PUBLISHED}">26 Oct 2026</time></strong></span>'
            f'<span>Updated <strong><time datetime="{updated}">26 Oct 2026</time></strong></span>{extra}</p>')
