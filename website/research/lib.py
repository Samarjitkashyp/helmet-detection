"""Page shell for the Axom AI research pages: head (SEO / social / structured data), header, footer.

Mirrors aiaxom.co.in: Plus Jakarta Sans, dark navy (#0b1220), emerald and amber, the same navigation and footer wording.
"""
import json
import re
from html import escape

BASE = "https://aiaxom.co.in"
PUBLISHED = "2026-10-26"
MODIFIED = "2026-10-26"
ASSET_V = "20261026c"
SITE = "Axom AI"
ORG_ID = f"{BASE}/#organization"       # the Organization the main site already declares
AUTHOR = {"@type": "Person", "name": "Samarjit Kashyap", "url": "https://github.com/Samarjitkashyp",
          "jobTitle": "Founder, Axom AI", "worksFor": {"@id": ORG_ID}}
GITHUB_BACKEND = "https://github.com/Samarjitkashyp/helmet-detection"
GITHUB_APP = "https://github.com/Samarjitkashyp/helmet-detection-mobile-app"
APP_PAGE = "https://helmet-detection.aiaxom.co.in/app"
WHO_URL = "https://www.who.int/news/item/05-04-2023-new-who-guide-aims-to-boost-the-use-of-life-saving-helmets-for-motorcycle-riders"
OG_IMAGE = f"{BASE}/research/assets/og-helmet-detection.jpg"

NAV = [("AI Tools", "/tools"), ("Use Cases", "/use-cases"), ("Pricing", "/pricing"), ("Blog &amp; Insights", "/blog"),
       ("FAQ", "/faq"), ("About Us", "/about"), ("Contact Us", "/contact")]    # Research is linked from the footer

_S = '<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{p}</svg>'
SMALL = {
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "sparkle":'<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 17l.7 1.8L21.5 19.5l-1.8.7L19 22l-.7-1.8-1.8-.7 1.8-.7z"/>',
    "camera": '<path d="M23 7l-7 5 7 5V7z"/><rect x="1" y="5" width="15" height="14" rx="2"/>',
    "phone": '<rect x="5" y="2" width="14" height="20" rx="3"/><path d="M12 18h.01"/>',
    "code": '<path d="m16 18 6-6-6-6M8 6l-6 6 6 6"/>',
    "chart": '<path d="M3 3v18h18"/><path d="M7 15l4-5 3 3 5-7"/>',
    "moon": '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 19.5V22h16"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "bolt": '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>',
    "cpu": '<rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v4M15 1v4M9 19v4M15 19v4M1 9h4M1 15h4M19 9h4M19 15h4"/>',
    "lock": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>',
    "star": '<path d="M12 2l3 6.9 7.5.7-5.7 5 1.7 7.4L12 18l-6.5 4 1.7-7.4-5.7-5 7.5-.7z" fill="currentColor"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
}


def small(name, size=16):
    return _S.format(s=size, p=SMALL[name])


def hero(badge, h1, lead, chips=(), cta="", meta=True, badge_icon="sparkle"):
    """Centred hero as on the Use Cases page: badge pill, big heading with a gradient, sub-title, row of pills."""
    chips_html = ""
    if chips:
        chips_html = '<ul class="hero-chips">' + "".join(f'<li>{small(i)}{e(t)}</li>' for i, t in chips) + "</ul>"
    return (f'<header class="hero-c wrap"><span class="badge">{small(badge_icon, 15)}{e(badge)}</span>'
            f'<h1>{h1}</h1><p class="lead">{lead}</p>{chips_html}{meta_line() if meta else ""}'
            + (f'<div class="cta">{cta}</div>' if cta else "") + "</header>")


def read_minutes(words):
    return max(1, round(words / 200))


def feature_card(url, category, title, excerpt, image, alt, minutes, date_text, author="Samarjit Kashyap", initials="SK"):
    """The blog's 'Featured insight' card."""
    return (f'<p class="section-label feat">{small("star", 14)} Featured research</p>'
            f'<a class="f-card" href="{url}"><div><div class="f-meta"><span class="pill">{e(category)}</span>'
            f'<span class="i">{small("clock", 14)}{minutes} min read</span><span class="i">{small("calendar", 14)}{e(date_text)}</span></div>'
            f'<h2 class="f-title" style="padding:0;margin-top:0">{e(title)}</h2><p class="f-excerpt">{e(excerpt)}</p>'
            f'<div class="f-foot"><span class="who"><span class="avatar" aria-hidden="true">{initials}</span>By {e(author)}</span>'
            f'<span class="f-read">Read full report &rarr;</span></div></div>'
            f'<div class="f-img"><img src="{image}" width="960" height="540" alt="{e(alt)}" loading="eager" fetchpriority="high">'
            f'<span class="chip-on-img l">{e(category)}</span><span class="chip-on-img r">{small("clock", 12)} {minutes} min read</span></div></a>')


def story_card(url, category, title, excerpt, image, alt, minutes, date_text, author="Samarjit Kashyap", initials="SK"):
    """One of the blog's 'Latest stories' cards."""
    return (f'<a class="s-card" href="{url}"><div class="s-img"><img src="{image}" width="960" height="540" alt="{e(alt)}" loading="lazy">'
            f'<span class="chip-on-img l">{e(category)}</span></div><div class="s-body"><div class="s-meta"><span>{e(date_text)}</span>'
            f'<span class="t">{small("clock", 12)} {minutes} min read</span></div><h3 class="s-title">{e(title)}</h3>'
            f'<p class="s-excerpt">{e(excerpt)}</p></div><div class="s-foot"><span class="who"><span class="avatar" aria-hidden="true">{initials}</span>{e(author)}</span>'
            f'<span class="r">Read &rarr;</span></div></a>')
ICONS = {
    "target": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/></svg>',
    "users": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/></svg>',
    "shield": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>',
    "bolt": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13 2 3 14h9l-1 8 10-12h-9z"/></svg>',
}


def stat(icon, value, text):
    return f'<div class="stat" role="listitem"><div class="ico">{ICONS[icon]}</div><b>{value}</b><span>{text}</span></div>'


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
<div class="progress" aria-hidden="true"></div>
<header class="site-header"><div class="wrap bar">
<a class="brand" href="/"><img src="/axom-browser-logo.png" width="40" height="40" alt="Axom AI logo"><span><b>Axom AI</b><small>SMART &bull; ASSAMESE &bull; AI FOR ALL</small></span></a>
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Open menu">&#9776;</button>
<nav class="nav" id="site-nav" aria-label="Main">{"".join(links)}<a class="cta-pill" href="https://chat.aiaxom.co.in/">Try Axom AI &rarr;</a></nav>
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


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", text).lower()).strip("-")[:48]


def page(p, body):
    """p: dict(path, title, description, crumbs, ...)  body: html placed inside <main>

    Gives every H2 an id, builds the contents list when a page has none, puts it in a sticky side column on wide screens
    and turns the article column into the shared `prose` layout."""
    heads = []

    def add_id(m):
        title = m.group(1)
        sid = _slug(title)
        heads.append((sid, re.sub(r"<[^>]+>", "", title)))
        return f'<h2 id="{sid}">{title}</h2>'

    body = re.sub(r'(?<!<div class="answer">)<h2>(.*?)</h2>', add_id, body)
    body = body.replace('<span class="eyebrow">', '<span class="badge">')
    toc = re.search(r'<nav class="toc".*?</nav>', body, re.S)
    if not toc and len(heads) >= 4 and '<div class="read"' in body:
        items = "".join(f'<li><a href="#{i}">{e(re.sub(r"^\d+\.\s*", "", t))}</a></li>' for i, t in heads)
        toc_html = f'<nav class="toc" aria-label="On this page"><b>On this page</b><ol>{items}</ol></nav>'
        body = body.replace('<div class="read" style="margin:0">', '<div class="read" style="margin:0">' + toc_html, 1)
        toc = re.search(r'<nav class="toc".*?</nav>', body, re.S)
    side = f'<aside class="side" aria-label="Contents">{toc.group(0)}</aside>' if toc else ""
    body = body.replace('<div class="wrap"><div class="read" style="margin:0">',
                        f'<div class="wrap layout{" has-side" if toc else ""}">{side}<div class="prose">', 1)
    return "\n".join([head(p), header("research"), crumbs_html(p["crumbs"]), f'<main id="main">{body}</main>', FOOTER])


def related(links):
    return '<div class="related">' + "".join(
        f'<a class="card" href="{u}"><span class="tag">{e(t)}</span><h3>{e(n)}</h3><p>{e(d)}</p></a>' for n, u, t, d in links) + "</div>"


def meta_line(updated=MODIFIED, extra=""):
    return (f'<p class="meta"><span class="who"><span class="avatar" aria-hidden="true">S</span><span>By <strong><a href="https://github.com/Samarjitkashyp">Samarjit Kashyap</a></strong>, Axom AI</span></span>'
            f'<span>Published <strong><time datetime="{PUBLISHED}">26 Oct 2026</time></strong></span>'
            f'<span>Updated <strong><time datetime="{updated}">26 Oct 2026</time></strong></span>{extra}</p>')
