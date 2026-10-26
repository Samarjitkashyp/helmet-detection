"""How is the home page's stylesheet organised? (dark mode switch, reset rules, class names that could clash with ours)"""
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
css = urllib.request.urlopen(urllib.request.Request("https://aiaxom.co.in/_next/static/css/c1fb9c7150b7dfa6.css", headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read().decode()
print("size", len(css))
print("dark selectors:", len(re.findall(r"\.dark\s", css)), "| media dark:", len(re.findall(r"prefers-color-scheme:\s*dark", css)))
print("sample dark rule:", re.findall(r"[^{}]{0,60}\.dark[^{}]{0,80}\{[^}]{0,80}\}", css)[:2])
print("html/body rules:", re.findall(r"(?:^|\})(html[^{]*\{[^}]*\}|body[^{]*\{[^}]*\})", css)[:6])
print("preflight present:", "box-sizing:border-box" in css[:3000], "| list reset:", bool(re.search(r"ol,ul,menu\{[^}]*list-style:none", css)))
mine = ["wrap", "bar", "brand", "nav", "menu-btn", "progress", "site-header", "site-footer", "hero", "hero-c", "badge", "lead", "cta", "btn", "meta", "who", "avatar", "layout", "prose", "side",
        "toc", "answer", "stats", "stat", "cards", "card", "tag", "note", "table-wrap", "good", "warn", "bar-row", "bar-track", "bar-fill", "flow", "chips", "related", "diagram", "social", "foot-grid",
        "foot-bottom", "crumbs", "grad", "skip", "f-card", "f-meta", "f-title", "f-excerpt", "f-foot", "f-read", "f-img", "s-grid", "s-card", "section-label", "hero-chips", "chip-on-img", "feature", "dd",
        "dd-panel", "dd-toggle", "pill", "num", "ico", "more", "r", "l", "t", "i", "a", "b"]
classes = set(re.findall(r"\.([a-zA-Z_][\w-]*)", css))
print("clashing class names:", sorted(c for c in mine if c in classes))
print("element rules that could clash:", [m for m in ["h1", "h2", "ul", "ol", "table", "details", "summary", "code", "pre", "figure", "blockquote"] if re.search(r"(^|[,}])" + m + r"[,{]", css)])
print("non-tailwind component classes (mega-menu etc.):", [c for c in ["mega-menu", "nav-item", "mega-item", "brand"] if c in classes])
print(re.findall(r"\.nav-item[^{]*\{[^}]*\}", css)[:4])
print(re.findall(r"\.mega-menu[^{]*\{[^}]*\}", css)[:4])
