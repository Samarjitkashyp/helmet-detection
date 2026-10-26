"""Hub page, helmet-detection overview and the A-to-Z "how it works" page."""
from lib import (APP_PAGE, BASE, GITHUB_APP, GITHUB_BACKEND, MODIFIED, WHO_URL, article_schema, e, faq_schema,
                 meta_line, related)

HD = "/research/helmet-detection/"
WHO_TEXT = ("WHO reports that head trauma is the leading cause of death for motorcycle riders, and that safe, quality helmets "
            "reduce the risk of death by more than six times and the risk of brain injury by up to 74%.")

OVERVIEW_FAQ = [
    ("What is helmet detection?",
     "Helmet detection is a computer vision task: a model looks at a photo, video or camera stream, finds each motorcycle rider and decides whether that person is wearing a helmet. Axom AI's system also saves a photo for every rider without a helmet."),
    ("How accurate is Axom AI helmet detection?",
     "On held-out traffic-camera footage the live system caught about 74% of bare-headed riders when it analysed one frame per second and about 90% at two frames per second, with roughly 1% of alerts landing on fully helmeted bikes. After CCTV fine-tuning, recall on held-out frames rose from 0.62 to 0.79."),
    ("Does it work on CCTV cameras?",
     "Yes. A worker program reads the camera's RTSP stream, tracks every rider separately and sends a photo alert to Telegram, the admin dashboard and the Axom AI Android app for each rider without a helmet."),
    ("Does it need a GPU?",
     "No. The whole pipeline runs on a desktop CPU (an Intel Core i3) at about 1.4 analysed frames per second. A faster CPU or a GPU analyses more frames per second, which catches more riders."),
    ("Is the helmet detection code open source?",
     "Yes. The backend and the Android app are published on GitHub under the MIT licence. The model builds on Ultralytics YOLOv8 (AGPL-3.0) and public datasets released under CC BY 4.0 and MIT, so check those terms before commercial use."),
]


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
<section class="hero wrap">
<span class="eyebrow">Axom AI Research</span>
<h1>Practical AI built in Assam, <span class="grad">published with real numbers</span></h1>
<p class="lead">What we built, how we measured it, what worked, what failed and what we still cannot do. Every report links to its code, its data and its limits.</p>
{meta_line()}
</section>
<div class="wrap"><div class="read" style="margin:0">
<div class="answer"><h2>What is Axom AI Research?</h2>
<p>Axom AI Research is the home of technical reports from Axom AI, Assam's first indigenous generative AI platform. Each report explains a system we built, the data and tools behind it, the results we measured on data the model had never seen, and the places where it still fails.</p></div></div></div>

<section class="wrap"><h2>Featured report</h2>
<a class="card" href="{HD}" style="padding:0;overflow:hidden">
<img src="/research/assets/detection-junction.jpg" width="1280" height="720" alt="Traffic junction where an AI model marks each rider with a red box for no helmet or a green box for helmet; faces are pixelated" style="width:100%;border-radius:0;border:0" loading="eager" fetchpriority="high">
<div style="padding:20px 22px 24px"><span class="tag">Computer vision &middot; Road safety</span>
<h3 style="margin-top:0;font-size:1.5rem">Helmet Detection: every rider checked, from a phone video or a CCTV camera</h3>
<p>An end-to-end system: YOLOv8 detection, per-rider tracking, an Android app, an admin dashboard and live CCTV alerts. Recall on held-out CCTV frames rose from 0.62 to 0.79 after fine-tuning; the live worker caught about 90% of bare-headed riders at two analysed frames per second.</p>
<p style="margin:0"><strong class="grad">Read the report &rarr;</strong></p></div></a>
</section>

<section class="wrap"><h2>How we publish</h2>
<div class="cards">
<div class="card"><h3>Numbers you can check</h3><p>Results come from clips the model never trained on, and we say how they were measured.</p></div>
<div class="card"><h3>Limits next to results</h3><p>Night, distance, speed and bias are written beside the good news, not hidden at the end.</p></div>
<div class="card"><h3>Credit where it is due</h3><p>Every dataset, model and tool is named with its licence.</p></div>
<div class="card"><h3>Open code</h3><p>Our code is on GitHub so others can repeat and improve the work.</p></div>
<div class="card"><h3>Updated, never erased</h3><p>Corrections and new results go in with a date. Wrong early findings stay visible, marked as wrong.</p></div>
</div></section>

<section class="wrap"><h2>Where this work runs today</h2>
<div class="cards">
<a class="card" href="{HD}"><span class="tag">Research</span><h3>Helmet detection</h3><p>Phone videos and CCTV streams, with alerts on Telegram and in the app.</p></a>
<a class="card" href="https://chat.aiaxom.co.in/"><span class="tag amber">Platform</span><h3>Axom AI Chat</h3><p>Chat in native Assamese with the Axom AI assistant.</p></a>
<a class="card" href="/tools"><span class="tag amber">Platform</span><h3>Axom AI Tools</h3><p>Image, PDF, video and QR tools, free to use.</p></a>
</div>
<p>More reports will be added to this page as they are published. For collaboration or questions, use the <a href="/contact">contact page</a>.</p>
</section>'''
    return p, body


def overview():
    url = HD
    p = dict(path=url, title="Helmet Detection AI for CCTV & Mobile | Axom AI Research",
             og_title="Helmet Detection AI: every rider checked, from a phone or a CCTV camera",
             description="Axom AI helmet detection finds riders without helmets in phone videos and CCTV. YOLOv8, per-rider tracking, instant alerts, measured results and open source.",
             keywords=["helmet detection", "AI helmet detection", "helmet detection using YOLOv8", "no helmet detection", "CCTV helmet detection",
                       "artificial intelligence", "computer vision", "road safety AI", "Axom AI"],
             crumbs=[("Home", "/"), ("Research", "/research/"), ("Helmet detection", url)], article=True)
    p["schemas"] = [
        article_schema(url, "Helmet Detection AI: every rider checked, from a phone video or a CCTV camera", p["description"],
                       keywords=p["keywords"], about=["Helmet detection", "Computer vision", "Road safety", "YOLO", "Closed-circuit television"],
                       cites=[("WHO: new guide to boost the use of life-saving helmets for motorcycle riders", WHO_URL),
                              ("HELMET dataset (Myanmar traffic cameras, CC BY 4.0)", "https://osf.io/4pwj8/"),
                              ("Ultralytics YOLOv8", "https://github.com/ultralytics/ultralytics")]),
        {"@context": "https://schema.org", "@type": "SoftwareSourceCode", "name": "helmet-detection (backend, CCTV worker, training tools)",
         "codeRepository": GITHUB_BACKEND, "programmingLanguage": "Python", "license": "https://opensource.org/licenses/MIT",
         "author": {"@type": "Person", "name": "Samarjit Kashyap"}, "runtimePlatform": "Python 3.11+"},
        {"@context": "https://schema.org", "@type": "SoftwareSourceCode", "name": "helmet-detection-mobile-app (Flutter, Android)",
         "codeRepository": GITHUB_APP, "programmingLanguage": "Dart", "license": "https://opensource.org/licenses/MIT",
         "author": {"@type": "Person", "name": "Samarjit Kashyap"}},
        faq_schema(OVERVIEW_FAQ)]
    faq_html = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in OVERVIEW_FAQ)
    body = f'''
<article>
<header class="hero wrap">
<span class="eyebrow">Research &middot; Computer vision &middot; Road safety</span>
<h1>Helmet Detection AI: <span class="grad">every rider checked,</span> from a phone video or a CCTV camera</h1>
<p class="lead">An end-to-end system from Axom AI that finds each motorcycle rider, decides helmet or no helmet, and sends a photo alert for every rider without one.</p>
{meta_line()}
<div class="cta"><a class="btn primary" href="{url}results/">See the results</a><a class="btn" href="{GITHUB_BACKEND}">View code on GitHub</a><a class="btn" href="{APP_PAGE}">Try the Android app</a></div>
</header>

<div class="wrap"><div class="read" style="margin:0">
<div class="answer"><h2>Quick answer</h2>
<p><strong>Helmet detection is computer vision that finds motorcycle riders and decides, person by person, whether a helmet is worn.</strong> Axom AI's system does this on uploaded videos and on live CCTV streams. On traffic-camera footage it had never seen, it caught about 74% of bare-headed riders when analysing one frame per second and about 90% at two frames per second, with about 1% of alerts on fully helmeted bikes. It runs on a normal CPU, with no GPU.</p></div>

<div class="stats" role="list">
<div class="stat" role="listitem"><b>0.79</b><span>recall on held-out CCTV frames after fine-tuning (was 0.62)</span></div>
<div class="stat" role="listitem"><b>~90%</b><span>of bare-headed riders alerted at 2 analysed frames per second</span></div>
<div class="stat" role="listitem"><b>~1%</b><span>of alerts on fully helmeted bikes (false alarms)</span></div>
<div class="stat" role="listitem"><b>1.4 fps</b><span>analysed on a desktop Intel Core i3 CPU, no GPU</span></div>
</div>

<nav class="toc" aria-label="On this page"><b>On this page</b><ol>
<li><a href="#why">Why helmet detection matters</a></li><li><a href="#built">What Axom AI built</a></li>
<li><a href="#see">See it work</a></li><li><a href="#steps">How it works in eight steps</a></li>
<li><a href="#used">What we used</a></li><li><a href="#results">How well it works</a></li>
<li><a href="#limits">Honest limits</a></li><li><a href="#open">Open source and links</a></li>
<li><a href="#cite">Cite this work</a></li><li><a href="#faq">FAQ</a></li></ol></nav>

<h2 id="why">Why helmet detection matters</h2>
<p>{e(WHO_TEXT)} (<a href="{WHO_URL}" rel="noopener">World Health Organization, 2023</a>). A helmet only helps when it is worn, and no team can watch every road.</p>
<p>Cameras already watch many junctions and highways. An AI model can read those streams all day, point at the riders without a helmet, and hand a human a photo to review. That is the idea behind this work: <strong>use the cameras that exist, and let people spend their time on the cases that matter.</strong></p>

<h2 id="built">What Axom AI built</h2>
<ul>
<li><strong>Video analysis.</strong> Record or upload a clip in the Android app. The server finds every person, gives each one a single verdict and returns a photo with the time it was seen.</li>
<li><strong>Live CCTV monitoring.</strong> A worker reads a camera's RTSP stream, tracks every rider separately and raises one alert per person without a helmet. See <a href="{url}cctv-monitoring/">CCTV monitoring</a>.</li>
<li><strong>Admin dashboard.</strong> Statistics, violation review, false-positive marking, camera management and a CCTV events page.</li>
<li><strong>Alerts where people already look.</strong> Telegram, the dashboard and an Alerts tab in the app, plus a warning when the monitor itself stops.</li>
<li><strong>A retraining loop.</strong> Reviewers flag wrong detections; those frames become training data for the next version.</li>
</ul>

<h2 id="see">See it work</h2>
<figure><img src="/research/assets/detection-street.jpg" width="1280" height="720" alt="Street scene where an AI model marks three motorcycle riders without helmets with red boxes; faces are pixelated" loading="lazy">
<figcaption>Held-out frame from the public HELMET dataset (Myanmar traffic cameras, CC BY 4.0). Red = no helmet, green = helmet. Faces are pixelated here; the live system saves the original frame as evidence for the administrator only.</figcaption></figure>
<figure><img src="/research/assets/detection-junction.jpg" width="1280" height="720" alt="Busy junction where each rider on several motorcycles gets their own red or green box; faces are pixelated" loading="lazy">
<figcaption>A busy junction: every rider gets their own verdict, so a bike with two people gives two results, not one.</figcaption></figure>

<h2 id="steps">How it works in eight steps</h2>
<ol class="flow">
<li><b>Take the picture.</b> A phone video, or frames from a camera's RTSP stream.</li>
<li><b>Find motorcycles.</b> A general-purpose YOLOv8s model (trained on COCO) marks every motorcycle and bicycle.</li>
<li><b>Find heads.</b> Our fine-tuned YOLOv8s looks at the whole frame and, regularly, at an enlarged crop around each motorcycle, where small, far-away heads become big enough to judge.</li>
<li><b>Decide helmet or no helmet.</b> The detector gives a verdict; a small classifier looks at the head crop and can overrule it when it is very sure. Caps, hats and scarves count as no helmet.</li>
<li><b>Keep only riders.</b> A head must sit on a motorcycle and be a believable size. Pedestrians and cyclists have no helmet rule here, so they are ignored.</li>
<li><b>Track every rider.</b> Each head gets its own track, so one frame with many riders gives many verdicts.</li>
<li><b>Confirm.</b> A rider is flagged after one very sure sighting, or two sightings, without a helmet.</li>
<li><b>Alert once.</b> One photo with every rider boxed, a Telegram message, a dashboard event and an app alert; repeats of the same person are suppressed.</li>
</ol>
<p>The full explanation, with the reasons behind each choice, is on <a href="{url}how-it-works/">How helmet detection works, from A to Z</a>.</p>

<h2 id="used">What we used</h2>
<ul class="chips">
<li>Ultralytics YOLOv8s</li><li>COCO-pretrained YOLOv8s</li><li>YOLOv8n-cls (crop classifier)</li><li>ByteTrack, then a custom tracker</li><li>OpenCV</li><li>PyTorch</li>
<li>FastAPI</li><li>PostgreSQL</li><li>Flutter and Dart</li><li>ONNX Runtime</li><li>Telegram Bot API</li><li>MediaMTX and FFmpeg (test camera)</li>
<li>Google Colab (T4 GPU)</li><li>nginx and Cloudflare</li><li>AWS Lightsail</li><li>HELMET dataset (CC BY 4.0)</li><li>Seven public Roboflow datasets</li>
</ul>

<h2 id="results">How well it works</h2>
<div class="table-wrap"><table><caption>Held-out CCTV frames: 500 frames, 1,114 riders, clips never used for training</caption>
<thead><tr><th>Model</th><th class="num">Precision</th><th class="num">Recall</th><th class="num">mAP@50</th></tr></thead>
<tbody><tr><td>Before CCTV fine-tuning</td><td class="num">0.777</td><td class="num">0.617</td><td class="num">0.547</td></tr>
<tr><td><strong>After CCTV fine-tuning</strong></td><td class="num good">0.798</td><td class="num good">0.791</td><td class="num good">0.748</td></tr></tbody></table></div>
<p>The live worker adds tracking and alert logic on top of the model. All numbers, how they were measured and what went wrong along the way are on the <a href="{url}results/">results page</a>.</p>

<h2 id="limits">Honest limits</h2>
<ul>
<li><strong>Night.</strong> The training data is daytime. On the same frames made to look like night, recall fell from 0.76 to 0.34. Night-style training images are prepared but the model has not been trained on them yet, and real night footage is still needed.</li>
<li><strong>Distance.</strong> Heads that are only a few pixels wide are missed. Enlarged crops help; they cost speed.</li>
<li><strong>Speed decides recall.</strong> The more frames analysed per second, the more riders are caught. A desktop CPU manages about 1.4.</li>
<li><strong>Your camera is not ours.</strong> Our test footage is from Myanmar traffic cameras. Angle, light and clothing at your site will differ, and results will too.</li>
<li><strong>A screening tool, not a judge.</strong> A person should review an alert before any action is taken against anyone.</li>
</ul>

<h2 id="open">Open source and links</h2>
<ul>
<li>Backend, CCTV worker and training tools: <a href="{GITHUB_BACKEND}">github.com/Samarjitkashyp/helmet-detection</a> (MIT)</li>
<li>Android app (Flutter): <a href="{GITHUB_APP}">github.com/Samarjitkashyp/helmet-detection-mobile-app</a> (MIT)</li>
<li>Download the Android app: <a href="{APP_PAGE}">helmet-detection.aiaxom.co.in/app</a></li>
<li>Details of the model: <a href="{url}model-card/">model card</a></li>
</ul>

<h2 id="cite">Cite this work</h2>
<pre><code>@techreport{{axomai2026helmet,
  title  = {{Helmet Detection: every rider checked, from a phone video or a CCTV camera}},
  author = {{Kashyap, Samarjit}},
  institution = {{Axom AI}},
  year   = {{2026}},
  url    = {{{BASE}{url}}}
}}</code></pre>

<h2 id="faq">Frequently asked questions</h2>
{faq_html}
<p><a href="{url}faq/">More questions and answers &rarr;</a></p>

<h2>Keep reading</h2>
{related([
    ("How it works, A to Z", url + "how-it-works/", "Explained", "Every step, every tool, and why we chose it."),
    ("Results and benchmarks", url + "results/", "Numbers", "Accuracy, speed, night tests and what went wrong."),
    ("CCTV monitoring", url + "cctv-monitoring/", "Live", "Connect a camera and get alerts on Telegram and in the app."),
    ("Model card", url + "model-card/", "Reference", "Intended use, data, limits and licences."),
])}
</div></div>
</article>'''
    return p, body


def how_it_works():
    url = HD + "how-it-works/"
    p = dict(path=url, title="How AI Helmet Detection Works: YOLOv8, Tracking, CCTV",
             description="A to Z of Axom AI's helmet detection: YOLOv8 detection, head crops, a crop classifier, per-rider tracking, alerts, training data and infrastructure.",
             keywords=["how helmet detection works", "helmet detection YOLOv8", "helmet detection using deep learning", "object tracking",
                       "YOLOv8 helmet detection tutorial", "CCTV AI pipeline", "Axom AI"],
             crumbs=[("Home", "/"), ("Research", "/research/"), ("Helmet detection", HD), ("How it works", url)], article=True)
    p["schemas"] = [article_schema(url, "How AI helmet detection works, from A to Z", p["description"], keywords=p["keywords"],
                                   about=["Helmet detection", "YOLO", "Object tracking", "Computer vision"],
                                   cites=[("Ultralytics YOLOv8", "https://github.com/ultralytics/ultralytics"),
                                          ("ByteTrack: multi-object tracking by associating every detection box", "https://arxiv.org/abs/2110.06864"),
                                          ("COCO dataset", "https://cocodataset.org/")])]
    svg = '''<svg viewBox="0 0 920 250" role="img" aria-labelledby="flowT flowD" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">
<title id="flowT">Helmet detection pipeline</title><desc id="flowD">A camera or phone sends frames to a worker that finds motorcycles, heads and helmet verdicts, tracks each rider, and sends alerts to the server, which notifies Telegram, the dashboard and the app.</desc>
<defs><marker id="ar" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#34d399"/></marker></defs>
<g font-family="Plus Jakarta Sans, system-ui, sans-serif" font-size="15" fill="#e5e7eb" text-anchor="middle">
<rect x="10" y="85" width="140" height="70" rx="14" fill="#10b9811f" stroke="#34d399"/><text x="80" y="115" font-weight="700">Camera</text><text x="80" y="136" fill="#a3b2c7" font-size="13">or phone video</text>
<rect x="200" y="30" width="250" height="190" rx="14" fill="#ffffff0d" stroke="#ffffff30"/><text x="325" y="56" font-weight="700" fill="#34d399">Worker (PC or server)</text>
<text x="325" y="88">1. find motorcycles</text><text x="325" y="114">2. find heads (frame + crops)</text><text x="325" y="140">3. helmet / no helmet</text><text x="325" y="166">4. track every rider</text><text x="325" y="192">5. confirm once</text>
<rect x="500" y="85" width="150" height="70" rx="14" fill="#10b9811f" stroke="#34d399"/><text x="575" y="115" font-weight="700">Server</text><text x="575" y="136" fill="#a3b2c7" font-size="13">API + database</text>
<rect x="710" y="10" width="200" height="56" rx="14" fill="#ffffff0d" stroke="#ffffff30"/><text x="810" y="44">Telegram message</text>
<rect x="710" y="97" width="200" height="56" rx="14" fill="#ffffff0d" stroke="#ffffff30"/><text x="810" y="131">Admin dashboard</text>
<rect x="710" y="184" width="200" height="56" rx="14" fill="#ffffff0d" stroke="#ffffff30"/><text x="810" y="218">Android app Alerts</text>
</g><g stroke="#34d399" stroke-width="2.4" fill="none" marker-end="url(#ar)"><path d="M150 120 H196"/><path d="M450 120 H496"/><path d="M650 120 C680 120 680 38 706 38"/><path d="M650 125 H706"/><path d="M650 130 C680 130 680 212 706 212"/></g></svg>'''
    body = f'''
<article>
<header class="hero wrap">
<span class="eyebrow">Technical deep dive</span>
<h1>How helmet detection works, <span class="grad">from A to Z</span></h1>
<p class="lead">Every stage of Axom AI's system, the tools behind it, and the reasons we chose them, including the choices that did not work.</p>
{meta_line()}
</header>
<div class="wrap"><div class="read" style="margin:0">
<div class="answer"><h2>Quick answer</h2>
<p>The system finds motorcycles with a general YOLOv8s model, finds heads with a helmet-trained YOLOv8s (on the whole frame and on enlarged crops), double-checks each head with a small classifier, keeps only heads that sit on a motorcycle, tracks every rider separately and raises one alert per rider without a helmet. It runs on a CPU.</p></div>

<figure>{svg}<figcaption>The live CCTV pipeline. Phone videos follow the same detection steps on the server, with tracking over every frame.</figcaption></figure>

<nav class="toc" aria-label="On this page"><b>On this page</b><ol>
<li><a href="#input">Input</a></li><li><a href="#motor">Find motorcycles</a></li><li><a href="#heads">Find heads</a></li><li><a href="#verdict">Helmet or no helmet</a></li>
<li><a href="#riders">Keep only riders</a></li><li><a href="#track">Track every rider</a></li><li><a href="#confirm">Confirm and alert</a></li><li><a href="#video">Video mode</a></li>
<li><a href="#training">Training</a></li><li><a href="#infra">Servers and apps</a></li><li><a href="#stack">Technology table</a></li></ol></nav>

<h2 id="input">1. Input: a phone video or a camera stream</h2>
<p>Two kinds of input feed the same detector. <strong>Videos</strong> come from the Android app (recorded in HD or picked from the gallery, up to two minutes) and are uploaded in small resumable pieces, so a weak mobile connection does not lose the upload. <strong>Live cameras</strong> are read over RTSP; the worker always keeps only the newest frame, so it never falls behind the stream.</p>

<h2 id="motor">2. Find motorcycles</h2>
<p>A COCO-pretrained YOLOv8s (run at 640 px) marks motorcycles and bicycles. It answers two questions: <em>where should we look more closely?</em> and <em>is this head on a motorcycle at all?</em> Without it, every pedestrian without a hat would be a violation.</p>

<h2 id="heads">3. Find heads, close up and far away</h2>
<p>Our detector is a YOLOv8s fine-tuned to find heads and label them <code>helmet</code> or <code>no_helmet</code>. On a CCTV frame the heads are small, sometimes only 20 pixels wide. So the model looks twice:</p>
<ul><li>at the <strong>whole frame</strong> (768 px) on every analysed frame, which is cheap;</li>
<li>at an <strong>enlarged crop around each motorcycle</strong> (512 px) on every fifth frame, where a distant head becomes large enough to judge.</li></ul>
<p>On early tests (9 clips, 42 motorcycles) the crops raised the share of bare-headed motorcycles caught from 0.67 to 0.76. They are also the slowest step, so the worker runs them regularly rather than constantly. See the speed trade-off on the <a href="{HD}results/">results page</a>.</p>

<h2 id="verdict">4. Helmet or no helmet</h2>
<p>The detector gives each head a verdict and a confidence. Two design choices matter more than any other:</p>
<ul><li><strong>Caps, hats, hijabs and scarves count as no helmet.</strong> A cap is not protection. Adding head-covering data raised recall on caps and hats from 0.21 to 0.88 in the first model.</li>
<li><strong>A second opinion.</strong> A small YOLOv8n-cls classifier, trained on head crops cut from CCTV footage, looks at each head. If it is at least 85% sure the detector is wrong, it overrules it. On 299 test motorcycles this lifted recall from 0.71 to about 0.74 and precision from 0.89 to about 0.91.</li></ul>

<h2 id="riders">5. Keep only riders</h2>
<p>A head counts only if it sits on a motorcycle (above the bike, within its width) and has a believable size. The size check came from a mistake: enlarged crops of far-away bikes sometimes made the model draw one giant box around a whole rider and bike. Rejecting boxes that are too large for their motorcycle cut these stray detections from 158 to 6 on our early test set (9 clips).</p>

<h2 id="track">6. Track every rider separately</h2>
<p>A frame with five riders must give five verdicts. Each head gets its own track, so the system can remember what it has seen of each person and alert only once.</p>
<div class="note bad"><p><strong>What went wrong first.</strong> We started with ByteTrack, a strong tracker built for video at 25 to 30 frames per second. A CPU analyses about one frame per second, and by the next frame a fast rider has moved several head-widths. ByteTrack keeps a new head hidden until it matches it a second time, so most riders were never reported: in the first test, four of five crowded clips produced no alert at all.</p></div>
<p>The fix was a tracker designed for few frames per second. It reports a head the moment it is seen and links it to the same person by distance measured in head-widths, using the person's last speed. Crowded clips then gave alerts for most bare-headed riders.</p>

<h2 id="confirm">7. Confirm, then alert once</h2>
<ul><li>A rider is flagged after <strong>one sighting without a helmet at 55% confidence or more</strong>, or after <strong>two sightings</strong>, as long as the no-helmet evidence outweighs the helmet evidence.</li>
<li>One photo is saved per frame, with every rider boxed (red or green) and a caption: how many are new, and how many riders are in view.</li>
<li>A <strong>repeat filter</strong> stops the same person from being alerted again when the tracker loses and re-finds them. We tuned it carefully: a strict version removed repeats but also hid real, different riders, so the final setting is mild.</li></ul>
<p>Alerts go to Telegram, the dashboard and the app. The worker also sends a heartbeat every minute, so the server can warn when the PC or the camera stream stops. Alerts that cannot be uploaded wait in a local outbox and are sent later.</p>

<h2 id="video">Video mode (phone uploads)</h2>
<p>For a recorded video the server runs the helmet model with ByteTrack at the video's full frame rate, adds each head's evidence over time and gives each person <strong>one verdict</strong>: the confidences of every sighting are summed per class, so a long clear view beats a single blurry frame. The best frame of each person is saved as the photo. People seen too few times, or too small, are ignored.</p>

<h2 id="training">Training: data and method</h2>
<ol>
<li><strong>Base model.</strong> YOLOv8s fine-tuned on about 11.7 thousand images from seven public Roboflow datasets, merged into two classes: helmet and no helmet, including caps, hats, hijabs and scarves.</li>
<li><strong>CCTV fine-tune.</strong> The HELMET dataset (Myanmar traffic cameras, 910 clips of 100 frames, 1080p, CC BY 4.0) labels every motorcycle with the helmet state of each person on it. We turned that into head labels by running our detector inside each motorcycle's box and giving each head the bike's label whenever every person on the bike agreed. Mixed bikes were left out.</li>
<li><strong>Training.</strong> Fine-tuned on a free Google Colab T4 GPU at 960 px for up to 30 epochs, together with a replay set of the old data so the model does not forget.</li>
<li><strong>Honest testing.</strong> The dataset ships its own split into training, validation and test clips. We never trained on the test clips, and our results are measured on them.</li>
<li><strong>Phone model.</strong> An ONNX build at 416 px runs on the phone with ONNX Runtime to draw live boxes while framing a shot; the server distributes it, so a new model reaches phones without an app release.</li></ol>

<h2 id="infra">Servers and apps</h2>
<p>The backend is FastAPI with PostgreSQL behind nginx and Cloudflare on an AWS Lightsail server. It has JWT sign-in, role-based access, rate limiting, an optional admin IP allow-list, and resumable uploads. The heavy CCTV analysis runs on a PC next to the camera and only sends photos and heartbeats to the server, so a small shared server is enough. The Android app is written in Flutter.</p>

<h2 id="stack">Technology table</h2>
<div class="table-wrap"><table><caption>What we used and why</caption>
<thead><tr><th>Part</th><th>Tool</th><th>Why</th></tr></thead><tbody>
<tr><td>Head detector</td><td>Ultralytics YOLOv8s</td><td>Accurate and fast enough on a CPU; easy to fine-tune.</td></tr>
<tr><td>Motorcycle finder</td><td>YOLOv8s (COCO)</td><td>Already knows motorcycles and bicycles; no training needed.</td></tr>
<tr><td>Crop classifier</td><td>YOLOv8n-cls</td><td>Tiny and quick; learns what CCTV helmets, caps and bare heads look like.</td></tr>
<tr><td>Tracking, video</td><td>ByteTrack</td><td>Strong at full video frame rate.</td></tr>
<tr><td>Tracking, CCTV</td><td>Custom distance tracker</td><td>Works at one or two analysed frames per second.</td></tr>
<tr><td>Image work</td><td>OpenCV, NumPy, PyTorch</td><td>Decoding, cropping, drawing, inference.</td></tr>
<tr><td>Backend</td><td>FastAPI, SQLAlchemy, PostgreSQL</td><td>Simple, fast, easy to deploy on a small server.</td></tr>
<tr><td>Phone app</td><td>Flutter, ONNX Runtime</td><td>One codebase; the model runs on the phone for live boxes.</td></tr>
<tr><td>Alerts</td><td>Telegram Bot API; optional Firebase push</td><td>Messages people already read.</td></tr>
<tr><td>Camera test bench</td><td>MediaMTX, FFmpeg</td><td>Plays a recorded clip as a fake RTSP camera for testing.</td></tr>
<tr><td>Training</td><td>Google Colab (T4)</td><td>Free GPU for fine-tuning.</td></tr>
<tr><td>Hosting</td><td>nginx, Cloudflare, AWS Lightsail</td><td>Low cost, HTTPS, protection from direct internet traffic.</td></tr>
</tbody></table></div>

<h2>Keep reading</h2>
{related([
    ("Results and benchmarks", HD + "results/", "Numbers", "Every measurement and what went wrong."),
    ("CCTV monitoring", HD + "cctv-monitoring/", "Live", "Connect a camera and run the worker."),
    ("Helmet detection overview", HD, "Start", "The short version."),
])}
</div></div>
</article>'''
    return p, body

