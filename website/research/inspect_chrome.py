"""Look at the home page's server-rendered header (<nav>) and footer: python inspect_chrome.py > file"""
import re
import sys
import urllib.request
from html.parser import HTMLParser

sys.stdout.reconfigure(encoding="utf-8")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr", "path", "circle", "rect", "line", "polyline", "polygon", "ellipse"}


def element_at(html, start):
    """Outer HTML of the element whose start tag begins at `start` (balanced tags)."""
    tag = re.match(r"<([a-zA-Z0-9]+)", html[start:]).group(1).lower()
    depth, pos = 0, start
    for m in re.finditer(r"<(/?)([a-zA-Z0-9]+)([^>]*?)(/?)>", html[start:]):
        t = m.group(2).lower()
        if t != tag:
            continue
        if m.group(1):
            depth -= 1
            if depth == 0:
                return html[start:start + m.end()]
        elif not m.group(4):
            depth += 1
    raise ValueError("unbalanced " + tag)


req = urllib.request.Request("https://aiaxom.co.in/", headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
body = html[html.find("<body"):]
nav = element_at(body, body.find("<nav"))
foot = element_at(body, body.find("<footer"))
print("NAV LEN", len(nav), "FOOTER LEN", len(foot))
print("=== NAV (tail, svg shortened) ===")
tail = nav[-(int(sys.argv[1]) if len(sys.argv) > 1 else 5000):]
print(re.sub(r'<svg.*?</svg>', '<svg/>', tail, flags=re.S))
print("=== FOOTER (end) ===")
print(re.sub(r'<svg.*?</svg>', '<svg/>', foot[-2600:], flags=re.S))
