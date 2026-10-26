"""The research hub (/research/). The helmet-detection report itself is in pages_hd.py."""
from lib import BASE, MODIFIED, feature_card, hero, story_card
from pages_bot import BOT, MINUTES as BOT_MINUTES
from pages_browser import BROWSER, MINUTES as BROWSER_MINUTES
from pages_hd import HD


def hub():
    p = dict(path="/research/", title="Axom AI Research: AI Research from Assam, India",
             description="Research from Axom AI, Assam's indigenous AI platform: measured results, open source code and honest limits. Start with helmet detection for road safety.",
             keywords=["Axom AI research", "AI research Assam", "Indian AI research", "helmet detection", "computer vision India"],
             crumbs=[("Home", "/"), ("Research", "/research/")], image_alt="Axom AI research: helmet detection")
    p["schemas"] = [{
        "@context": "https://schema.org", "@type": "CollectionPage", "@id": BASE + "/research/#page", "url": BASE + "/research/",
        "name": "Axom AI Research", "inLanguage": "en-IN", "isPartOf": {"@id": "https://aiaxom.co.in/#organization"},
        "description": p["description"], "dateModified": MODIFIED,
        "mainEntity": {"@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "url": BASE + HD, "name": "Helmet Detection: AI that checks every rider, from a phone video or a CCTV camera"},
            {"@type": "ListItem", "position": 2, "url": BASE + BOT, "name": "Axom AI Crawler Bot: websites and documents turned into answers"},
            {"@type": "ListItem", "position": 3, "url": BASE + BROWSER, "name": "Axomai Browser: a free AI browser made in Assam"}]}}]
    body = f'''
{hero("Official Axom AI Research",
      'Practical AI built in Assam, <span class="grad">published with real numbers</span>',
      "What we built, how we measured it, what worked, what failed and what we still cannot do. Every report links to its code, its data and its limits.",
      chips=[("camera", "Computer vision"), ("shield", "Road safety"), ("chart", "Measured results"), ("code", "Open source code"), ("moon", "Honest limits")])}
<div class="wrap"><div class="prose" style="margin-inline:auto">
<div class="answer"><h2>What is Axom AI Research?</h2>
<p>Axom AI Research is the home of technical reports from Axom AI, Assam's first indigenous generative AI platform. Each report explains a system we built, the data and tools behind it, the results we measured on data the model had never seen, and the places where it still fails.</p></div></div></div>

<section class="wrap">
{feature_card(HD, "Computer vision · Road safety", "Helmet Detection: every rider checked, from a phone video or a CCTV camera",
              "An end-to-end system: YOLOv8 detection, per-rider tracking, an Android app, an admin dashboard and live CCTV alerts. Recall on held-out CCTV frames rose from 0.62 to 0.79 after fine-tuning; the live worker caught about 90% of bare-headed riders at two analysed frames per second.",
              "/research/assets/detection-junction.jpg", "Traffic junction where an AI model marks each rider with a red box for no helmet or a green box for helmet; faces are pixelated",
              MINUTES, "Oct 26, 2026")}
<p class="section-label">More research</p>
<div class="s-grid">
{story_card(BOT, "AI · Knowledge for chat", "Axom AI Crawler Bot: websites and documents turned into answers",
            "How a private tool reads websites and scanned Assamese, Hindi and English documents, cleans the text and writes a question for every passage, so the Axom AI chat can answer from them.",
            "/research/assets/card-crawler-bot.jpg", "Crawler bot pipeline: website, clean text, questions, Axom AI chat",
            BOT_MINUTES, "Oct 26, 2026")}
{story_card(BROWSER, "Product · AI browser", "Axomai Browser: a free AI browser made in Assam",
            "How a Windows and Android browser puts Axom AI next to the page you read: a Rust shell on Edge WebView2, a private chat proxy, an ad and tracker shield, encrypted folder sync and checked updates.",
            "/research/assets/card-browser.jpg", "Axomai Browser window with the Axom AI chat panel beside a page about Assam tea",
            BROWSER_MINUTES, "Oct 26, 2026")}
</div>
</section>'''
    return p, body


MINUTES = 30
