"""The Axom AI home page's own header and footer (copied by sync_chrome.py), plus the small menu panel for phones."""
import json
from pathlib import Path

CHROME = Path(__file__).resolve().parent / "src" / "chrome"

# What the home page's React menu shows on a phone (the desktop header holds the same links)
PAGE_LINKS = [("Use Cases", "/use-cases"), ("Pricing", "/pricing"), ("Blog &amp; Insights", "/blog"), ("FAQ", "/faq"),
              ("About Us", "/about"), ("Contact Us", "/contact")]


def header(asset_v):
    nav = (CHROME / "header.html").read_text(encoding="utf-8")
    tools = json.loads((CHROME / "tools.json").read_text(encoding="utf-8"))
    parts = ['<a href="/tools">AI Tools</a>']
    parts += [f'<a class="sub" href="{href}">{title}</a>' for title, href in tools]
    parts += [f'<a href="{href}">{title}</a>' for title, href in PAGE_LINKS]
    parts.append('<a class="m-cta" href="https://chat.aiaxom.co.in/">Sign in &rarr;</a>')
    drawer = f'<div id="m-drawer" class="m-drawer" hidden><nav aria-label="Menu">{"".join(parts)}</nav></div>'
    return ('<body class="research-page">\n<a class="skip" href="#main">Skip to content</a>\n<div class="progress" aria-hidden="true"></div>\n'
            + nav + "\n" + drawer)


def footer(asset_v):
    return ((CHROME / "footer.html").read_text(encoding="utf-8")
            + f'\n<script src="/research/assets/research.js?v={asset_v}" defer></script>\n</body></html>')
