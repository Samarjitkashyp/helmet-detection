"""Builds the Axom AI research pages into website/research/dist (plain HTML, CSS and JS: no framework, no build step on the server).

Usage:  python -I website/research/build_site.py
Checks: titles and descriptions fit search results, one H1 per page, every image has alt text and size,
        all JSON-LD parses, all internal /research/ links point to a built page.
"""
import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pages_a  # noqa: E402
import pages_bot  # noqa: E402
import pages_browser  # noqa: E402
import pages_hd  # noqa: E402
from lib import BASE, GITHUB_APP, GITHUB_BACKEND, MODIFIED, page  # noqa: E402

DIST = HERE / "dist"
SITE_ROOT = DIST / "research"

PAGES = [pages_a.hub, pages_hd.overview, pages_bot.overview_bot, pages_browser.overview_browser]

KEY_FACTS = {
    "name": "Axom AI helmet detection",
    "publisher": "Axom AI (Axom AI Technologies), Guwahati, Assam, India",
    "author": "Samarjit Kashyap",
    "url": f"{BASE}/research/helmet-detection/",
    "updated": MODIFIED,
    "what_it_is": "Computer vision system that finds motorcycle riders in phone videos and CCTV streams, decides helmet or no helmet per person, and alerts on Telegram, a dashboard and an Android app.",
    "model": "Ultralytics YOLOv8s fine-tuned (classes: helmet, no_helmet); COCO YOLOv8s finds motorcycles; YOLOv8n-cls head-crop classifier",
    "runs_on": "CPU, no GPU needed (desktop Intel Core i3: about 1.4 analysed frames per second)",
    "measurements": [
        {"claim": "Recall on held-out CCTV frames before and after CCTV fine-tuning", "before": 0.617, "after": 0.791,
         "precision_after": 0.798, "map50_before": 0.547, "map50_after": 0.748, "frames": 500, "riders": 1114,
         "data": "HELMET dataset (Myanmar traffic cameras, CC BY 4.0), clips not used for training"},
        {"claim": "Share of bare-headed riders alerted by the live CCTV worker", "at_1_fps": 0.74, "at_2_fps": 0.90,
         "alerts_on_fully_helmeted_bikes": 0.01, "clips": 14, "bare_headed_riders": 170},
        {"claim": "Recall on night-style frames (model not yet trained on night images)", "daylight": 0.755, "night_style": 0.344, "frames": 200},
    ],
    "limits": ["Training data is daytime; night recall is 0.34 on night-style frames (night training not done yet)", "Turbans are not in the training data",
               "Test footage is from Myanmar traffic cameras; results differ per camera", "Screening tool: a person should review each alert"],
    "licences": {"code": "MIT", "base_model": "Ultralytics YOLOv8 (AGPL-3.0)", "data": "CC BY 4.0 and MIT datasets (HELMET dataset: CC BY 4.0)"},
    "source_code": [GITHUB_BACKEND, GITHUB_APP],
    "try_it": "https://helmet-detection.aiaxom.co.in/app",
    "who_source": "https://www.who.int/news/item/05-04-2023-new-who-guide-aims-to-boost-the-use-of-life-saving-helmets-for-motorcycle-riders",
}

LLMS = f"""# Axom AI

> Axom AI is Assam's first indigenous generative AI platform (Guwahati, Assam, India), with an Assamese AI assistant, AI tools and open research. Founder: Samarjit Kashyap.

## Research

- [Axom AI Research]({BASE}/research/): index of technical reports from Axom AI.
- [Helmet Detection]({BASE}/research/helmet-detection/): AI that checks every motorcycle rider for a helmet, from phone videos and CCTV cameras. YOLOv8, per-rider tracking, Telegram / dashboard / app alerts. Open source (MIT).
  The one page holds everything: how it works from A to Z (#how), results and benchmarks (#results), CCTV set-up (#cctv), honest limits (#limits), model card (#model), open source links (#open) and the FAQ (#faq).
- [Key facts as JSON]({BASE}/research/helmet-detection/key-facts.json)
- [Axom AI Crawler Bot]({BASE}/research/axom-ai-crawler-bot/): how a private tool turns websites and scanned Assamese, Hindi and English documents into clean passages with one AI-written question each for the Axom AI chat. Fetching (HTTP, headless browser, WordPress API), change detection with SHA-256, boilerplate cleaning with safety gates, document OCR with Gemini vision, admin approval, measured results and limits.
- [Axomai Browser]({BASE}/research/axomai-browser/): a free AI browser made in Assam for Windows and Android. Edge WebView2 pages with a Rust shell, a private chat proxy (key, prompt and model on the server, daily limits, chats not saved), a 202-domain ad and tracker shield, AES-256-GCM folder sync, SHA-256-checked updates, measured numbers and limits. Source: github.com/Samarjitkashyp/axomai-browser (MIT).

## Key facts (helmet detection, updated {MODIFIED})

- Recall on held-out CCTV frames: 0.62 before and 0.79 after CCTV fine-tuning (mAP@50 0.55 to 0.75; 500 frames, 1,114 riders; HELMET dataset, CC BY 4.0).
- Live CCTV worker: about 74% of bare-headed riders alerted at 1 analysed frame per second and about 90% at 2; about 1% of alerts on fully helmeted bikes (14 clips, 170 riders).
- Runs on a CPU without a GPU: about 1.4 analysed frames per second on an Intel Core i3.
- Limits: daytime training data; night recall 0.34 on night-style frames (night training not done yet); turbans not covered; a person should review each alert.
- Code: {GITHUB_BACKEND} and {GITHUB_APP} (MIT).

## Platform

- [Axom AI]({BASE}/): Assamese AI platform.
- [Axom AI Chat](https://chat.aiaxom.co.in/): chat in native Assamese.
- [AI Tools]({BASE}/tools): image, PDF, video and QR tools.
- [About]({BASE}/about)
- [Contact]({BASE}/contact)
"""


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.imgs, self.links, self.ld, self._in_ld, self.title, self._in_title = [], [], [], False, "", False
        self.desc = ""
        self.canonical = ""

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "h1":
            self.h1 += 1
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld = True
        elif tag == "title" and not self.title:      # the page title; SVG figures have their own <title>
            self._in_title = True
        elif tag == "meta" and a.get("name") == "description":
            self.desc = a.get("content", "")
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href", "")

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_ld = False
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_ld:
            self.ld.append(data)
        elif self._in_title:
            self.title += data


def main():
    if DIST.exists():
        # keep generated figures (made by make_figures.py), rebuild everything else
        keep = {}
        assets = SITE_ROOT / "assets"
        for f in (assets.glob("*.jpg") if assets.exists() else []):
            keep[f.name] = f.read_bytes()
        shutil.rmtree(DIST)
    else:
        keep = {}
    (SITE_ROOT / "assets").mkdir(parents=True)
    for name, data in keep.items():
        (SITE_ROOT / "assets" / name).write_bytes(data)
    shutil.copy(HERE / "src" / "research.css", SITE_ROOT / "assets" / "research.css")
    shutil.copy(HERE / "src" / "chrome" / "axom-site.css", SITE_ROOT / "assets" / "axom-site.css")   # the home page's own stylesheet
    shutil.copy(HERE / "src" / "research.js", SITE_ROOT / "assets" / "research.js")

    built = {}
    for make in PAGES:
        p, body = make()
        rel = p["path"].strip("/")
        out = DIST / rel / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        html = page(p, body)
        out.write_text(html, encoding="utf-8")
        built[p["path"]] = (p, html)

    # sitemap, llms.txt, key facts
    urls = list(built)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for u in urls:
        prio = "1.0" if u == "/research/helmet-detection/" else "0.9" if u in ("/research/", "/research/axom-ai-crawler-bot/", "/research/axomai-browser/") else "0.8"
        sm.append(f"<url><loc>{BASE}{u}</loc><lastmod>{MODIFIED}</lastmod><changefreq>monthly</changefreq><priority>{prio}</priority>"
                  + (f"<image:image><image:loc>{BASE}/research/assets/detection-junction.jpg</image:loc><image:caption>Helmet detection: each rider on a busy junction gets a red or green box (faces pixelated)</image:caption></image:image>"
                     if u in ("/research/", "/research/helmet-detection/") else "") + "</url>")
    sm.append("</urlset>")
    (SITE_ROOT / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")
    (DIST / "llms.txt").write_text(LLMS, encoding="utf-8")
    (SITE_ROOT / "helmet-detection" / "key-facts.json").write_text(json.dumps(KEY_FACTS, indent=2, ensure_ascii=False), encoding="utf-8")

    # checks
    problems = []
    canon = set()
    for path, (p, html) in built.items():
        s = Scan()
        s.feed(html)
        t, d = s.title.strip(), s.desc
        if len(t) > 62: problems.append(f"{path}: title is {len(t)} chars")
        if not 100 <= len(d) <= 165: problems.append(f"{path}: description is {len(d)} chars")
        if s.h1 != 1: problems.append(f"{path}: {s.h1} h1 tags")
        for im in s.imgs:
            if not im.get("alt") or not im.get("width") or not im.get("height"):
                problems.append(f"{path}: image without alt/size: {im.get('src')}")
        for blob in s.ld:
            try:
                json.loads(blob)
            except ValueError as ex:
                problems.append(f"{path}: bad JSON-LD ({ex})")
        for href in s.links:
            if href.startswith("/research/") and "#" not in href:
                target = href.split("?")[0]
                if target not in built and not (DIST / target.strip("/")).exists():
                    problems.append(f"{path}: broken link {href}")
        if s.canonical in canon: problems.append(f"{path}: duplicate canonical")
        canon.add(s.canonical)
        words = len(re.sub(r"<[^>]+>", " ", html).split())
        print(f"{path:48} title {len(t):2} desc {len(d):3} words {words}")
    for im in ("detection-street.jpg", "detection-junction.jpg", "og-helmet-detection.jpg"):
        if not (SITE_ROOT / "assets" / im).exists():
            problems.append(f"missing asset {im} (run make_figures.py)")
    print("PROBLEMS:" if problems else "all checks passed", *problems, sep="\n  ")


if __name__ == "__main__":
    main()

