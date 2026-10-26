"""Copy the Axom AI home page's own header (<nav>), footer and stylesheet, so the research pages use the real thing.

Run again whenever the home page header or footer changes:   python -I website/research/sync_chrome.py
Writes website/research/src/chrome/{header.html, footer.html, axom-site.css}. build_site.py puts them into every page.

Changes made to the copy (the home page's header and footer are React components; these parts need JavaScript there):
 - the "Sign in" button becomes a link (the home page opens a Google sign-in pop-up that a static page cannot open);
 - the hamburger button gets an id so research.js can open a menu panel;
 - the "Cookie Settings" button (it opens a pop-up of the React app) becomes a link to the cookie policy page.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent / "src" / "chrome"
SIGN_IN_URL = "https://chat.aiaxom.co.in/"


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read()


def element_at(html, start):
    tag = re.match(r"<([a-zA-Z0-9]+)", html[start:]).group(1).lower()
    depth = 0
    for m in re.finditer(r"<(/?)([a-zA-Z0-9]+)([^>]*?)(/?)>", html[start:]):
        if m.group(2).lower() != tag:
            continue
        if m.group(1):
            depth -= 1
            if depth == 0:
                return html[start:start + m.end()]
        elif not m.group(4):
            depth += 1
    raise ValueError("unbalanced <%s>" % tag)


html = get("https://aiaxom.co.in/").decode("utf-8", "replace")
body = html[html.find("<body"):]
nav = element_at(body, body.find("<nav"))
foot = element_at(body, body.find("<footer"))

# 1) Sign in: <button ...><span>Sign in</span>...</button>  ->  <a href=...>...</a>
m = re.search(r'<button type="button"( class="[^"]*")>(<span>Sign in</span>.*?)</button>', nav, re.S)
assert m, "Sign in button not found: the home page header changed, adapt sync_chrome.py"
nav = nav.replace(m.group(0), f'<a href="{SIGN_IN_URL}"{m.group(1).replace("class=\"", "class=\"no-underline ", 1)}>{m.group(2)}</a>')
# 2) hamburger
assert 'aria-label="Open menu"' in nav
nav = nav.replace('<button aria-label="Open menu"', '<button id="menu-open" aria-expanded="false" aria-controls="m-drawer" aria-label="Open menu"', 1)
# 3) cookie settings
foot, n = re.subn(r'<button type="button"( class="[^"]*")>Cookie Settings</button>', r'<a href="/cookie-policy"\1>Cookie Settings</a>', foot)
assert n == 1, "Cookie Settings button not found"

css_href = re.search(r'href="(/_next/static/css/[^"]+\.css)"', html).group(1)
css = get("https://aiaxom.co.in" + css_href)

# the tools listed in the AI Tools menu, for the phone menu panel
tools = []
for a in re.findall(r"<a [^>]*mega-item[^>]*>.*?</a>", nav, re.S):
    href = re.search(r'href="([^"]+)"', a).group(1)
    title = re.search(r'<div class="text-sm font-bold[^"]*">([^<]+)</div>', a).group(1)
    tools.append([title, href])
assert len(tools) >= 5, "tool list not found in the header"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "tools.json").write_text(json.dumps(tools, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "header.html").write_text(nav, encoding="utf-8")
(OUT / "footer.html").write_text(foot, encoding="utf-8")
(OUT / "axom-site.css").write_bytes(css)
links = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>(?:<span>)?([^<]+)', nav)
print("header", len(nav), "footer", len(foot), "css", len(css), css_href)
print("header links:", [(h, t.strip()) for h, t in links if t.strip()][:24])
