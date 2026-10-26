"""The research hub (/research/). The helmet-detection report itself is in pages_hd.py."""
from lib import BASE, MODIFIED, feature_card, hero
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
            {"@type": "ListItem", "position": 1, "url": BASE + HD, "name": "Helmet Detection: AI that checks every rider, from a phone video or a CCTV camera"}]}}]
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
</section>'''
    return p, body


MINUTES = 30
