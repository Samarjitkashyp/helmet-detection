"""Results, CCTV monitoring, model card and FAQ pages."""
from lib import (APP_PAGE, BASE, GITHUB_APP, GITHUB_BACKEND, article_schema, e, faq_schema, meta_line, related)

HD = "/research/helmet-detection/"

FAQ = [
    ("What is helmet detection?",
     "Helmet detection is a computer vision task: a model looks at a photo, video or camera stream, finds each motorcycle rider and decides whether that person is wearing a helmet. Axom AI's system also saves a photo for every rider without a helmet."),
    ("How does AI helmet detection work?",
     "The system finds motorcycles, finds heads on the whole frame and on enlarged crops, labels each head helmet or no helmet, keeps only heads that sit on a motorcycle, tracks every rider separately and raises one alert per rider without a helmet."),
    ("How accurate is Axom AI helmet detection?",
     "On traffic-camera clips never used for training, the live system caught about 74% of bare-headed riders at one analysed frame per second and about 90% at two, with about 1% of alerts on fully helmeted bikes. On held-out CCTV frames the model's recall is 0.79 and mAP@50 is 0.75. Results on your own camera will differ."),
    ("Which AI model does it use?",
     "A YOLOv8s model from Ultralytics, fine-tuned on public helmet datasets and then on CCTV frames, plus a COCO-pretrained YOLOv8s to find motorcycles and a small YOLOv8n-cls classifier as a second opinion on each head."),
    ("Can it detect helmets on CCTV cameras?",
     "Yes. A worker reads the camera's RTSP stream, analyses frames, tracks every rider and sends a photo alert to Telegram, the admin dashboard and the Android app."),
    ("Does it work at night?",
     "Not yet reliably. The training data is daytime. On the same frames made to look like night, recall fell from 0.76 to 0.34. Night-style training images are prepared, but the model has not been trained on them yet. Real night footage from your own cameras is needed for good night accuracy."),
    ("Are caps, hats and turbans counted as helmets?",
     "No. Caps, hats, hijabs and scarves are labelled no helmet. Turbans are not covered by the training data yet, so they may be judged wrongly."),
    ("Does it need a GPU?",
     "No. It runs on a desktop CPU (an Intel Core i3) at about 1.4 analysed frames per second. A faster CPU or a GPU analyses more frames per second, which catches more riders."),
    ("Can it follow several riders in one frame?",
     "Yes. Every head is tracked on its own, so a frame with several helmeted and bare-headed riders gives one verdict per person. On a busy junction the system tracked up to 11 riders in one frame."),
    ("How do I get alerts?",
     "Alerts arrive on Telegram, in the admin dashboard (CCTV events page) and in the Alerts tab of the Android app for admin accounts. The server also warns on Telegram if the monitoring PC or the camera stream stops."),
    ("Is it open source?",
     "The backend, CCTV worker, training tools and the Android app are on GitHub under the MIT licence. The model builds on Ultralytics YOLOv8 (AGPL-3.0) and on datasets released under CC BY 4.0 and MIT, so read those terms before commercial use."),
    ("Can it be used to issue fines?",
     "It is a screening tool. A person should review each alert, and the law and rules that apply in your area decide what can be done. We do not recommend automatic penalties from an AI alert alone."),
    ("What about privacy?",
     "Alert photos are saved on the server and are visible only to administrators. Camera passwords are never shown in the dashboard. Faces in this report's figures are pixelated. Check the privacy and data-protection rules that apply to your cameras before you deploy."),
    ("What data was it trained on?",
     "Seven public Roboflow datasets (about 11.7 thousand images, CC BY 4.0 and MIT) for the first model, then the HELMET dataset of Myanmar traffic-camera clips (CC BY 4.0) for the CCTV fine-tune."),
    ("Can I try it?",
     "Yes. Download the Android app from helmet-detection.aiaxom.co.in/app, create an account, record or upload a video and read the verdict for every person. The code is on GitHub if you want to run your own copy."),
    ("How do I connect my own camera?",
     "Add the camera's RTSP address on the dashboard's Cameras page, put the shared key and the server address in the worker's settings on a PC near the camera, and start the worker. The CCTV monitoring page lists every step."),
]


def faq_html(items):
    return "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in items)


def bar(label, pct, warn=False, note=""):
    cls = "bar-fill warn" if warn else "bar-fill"
    return (f'<div class="bar-row"><span>{e(label)}</span><div class="bar-track" role="img" aria-label="{e(label)}: {pct}%">'
            f'<div class="{cls}" style="width:{pct}%"></div></div><b>{pct}%</b></div>')


def results():
    url = HD + "results/"
    p = dict(path=url, title="Helmet Detection Accuracy & Benchmarks: Real Results",
             description="Measured accuracy of Axom AI helmet detection: precision, recall and mAP on held-out CCTV frames, live results at 1 and 2 fps, CPU speed, night tests and mistakes.",
             keywords=["helmet detection accuracy", "helmet detection benchmark", "YOLOv8 helmet detection results", "mAP", "precision recall helmet",
                       "CCTV helmet detection results", "Axom AI"],
             crumbs=[("Home", "/"), ("Research", "/research/"), ("Helmet detection", HD), ("Results", url)], article=True)
    p["schemas"] = [article_schema(url, "Helmet detection results and benchmarks", p["description"], keywords=p["keywords"],
                                   about=["Helmet detection", "Benchmark", "Precision and recall", "YOLO"],
                                   cites=[("HELMET dataset (Myanmar traffic cameras, CC BY 4.0)", "https://osf.io/4pwj8/")])]
    body = f'''
<article>
<header class="hero wrap"><span class="eyebrow">Results &amp; benchmarks</span>
<h1>Helmet detection results: <span class="grad">what we measured</span></h1>
<p class="lead">Accuracy, speed, night behaviour and the mistakes we made on the way. Every number says what it was measured on.</p>{meta_line()}</header>
<div class="wrap"><div class="read" style="margin:0">
<div class="answer"><h2>Quick answer</h2>
<p>After fine-tuning on CCTV frames, recall on held-out frames rose from 0.62 to 0.79 and mAP@50 from 0.55 to 0.75. In the live CCTV worker, about 74% of bare-headed riders were alerted when one frame per second was analysed and about 90% at two frames per second, with about 1% of alerts on fully helmeted bikes. On night-like frames recall is only 0.34, and night training is still to be done.</p></div>

<h2>How we measured</h2>
<ul>
<li><strong>Data.</strong> The HELMET dataset: 910 clips (100 frames each, 1080p, 10 fps) from traffic cameras in Myanmar, CC BY 4.0. It labels every motorcycle with the helmet state of each person on it.</li>
<li><strong>Honest split.</strong> We use the dataset's own split. Training used only the training clips; the numbers below come from validation or test clips the model never saw.</li>
<li><strong>"Riders caught".</strong> For each clip, alerts are compared with the number of bare-headed people in the ground truth; an alert on a bike with a bare-headed rider counts as correct, an alert on a bike where everyone wears a helmet counts as a false alarm. Counts are approximate because the labels name bikes, not individual heads.</li>
<li><strong>Limits of the test.</strong> One country, daytime, a few hundred riders. Treat the figures as a guide, not a promise for your camera.</li></ul>

<h2>1. The model on held-out CCTV frames</h2>
<div class="table-wrap"><table><caption>500 validation frames, 1,114 riders, from clips not used for training (confidence 0.5, image size 960)</caption>
<thead><tr><th>Model</th><th class="num">Precision</th><th class="num">Recall</th><th class="num">mAP@50</th></tr></thead>
<tbody><tr><td>First model (public Roboflow data only)</td><td class="num">0.777</td><td class="num">0.617</td><td class="num">0.547</td></tr>
<tr><td><strong>After CCTV fine-tuning</strong></td><td class="num good">0.798</td><td class="num good">0.791</td><td class="num good">0.748</td></tr></tbody></table></div>
<p>Fine-tuning on a few thousand real CCTV frames matters more than anything else we tried: recall rose by 17 points.</p>

<h2>2. The first model on public test sets</h2>
<div class="table-wrap"><table><caption>Test splits of the public datasets (confidence 0.4, 640 px)</caption>
<thead><tr><th>Test set</th><th>Class</th><th class="num">Precision</th><th class="num">Recall</th></tr></thead><tbody>
<tr><td rowspan="2">Riders and people (300 images)</td><td>helmet</td><td class="num">0.93</td><td class="num">0.93</td></tr><tr><td>no helmet</td><td class="num">0.95</td><td class="num">0.84</td></tr>
<tr><td rowspan="2">Caps, hats, hijabs (87 images)</td><td>helmet</td><td class="num">0.94</td><td class="num">0.85</td></tr><tr><td>no helmet</td><td class="num">0.87</td><td class="num">0.88</td></tr></tbody></table></div>
<p>mAP@50 was 0.92 on riders and people and 0.91 on head coverings. Adding head-covering data lifted no-helmet recall on caps and hats from 0.21 to 0.88 without hurting the original set. These sets are easier than real CCTV, which is why the CCTV test above matters.</p>

<h2>3. The live CCTV worker at different speeds</h2>
<p>The worker analyses as many frames per second as the computer allows. How many riders get an alert depends strongly on that rate. Test: 14 of the busiest held-out clips with 170 bare-headed riders.</p>
<div role="group" aria-label="Share of bare-headed riders alerted">
{bar("1 frame / second", 74)}{bar("2 frames / second", 90)}</div>
<div class="table-wrap"><table><caption>Same clips, same settings</caption>
<thead><tr><th>Analysed frames per second</th><th class="num">Riders alerted</th><th class="num">Extra alerts for the same people</th><th class="num">Alerts on fully helmeted bikes</th></tr></thead><tbody>
<tr><td>1</td><td class="num">about 74%</td><td class="num">2</td><td class="num">1 (about 1%)</td></tr>
<tr><td>2</td><td class="num good">about 90%</td><td class="num">44</td><td class="num">1 (about 1%)</td></tr></tbody></table></div>
<p>Faster analysis catches more riders but also alerts the same person more than once. A repeat filter keeps this in check; a stricter filter removed the repeats but also hid real riders, so we kept it mild.</p>

<h2>4. What each part of the pipeline adds</h2>
<div class="table-wrap"><table><caption>299 motorcycles in 52 test clips, before CCTV fine-tuning</caption>
<thead><tr><th>Setup</th><th class="num">Bare-headed bikes caught</th><th class="num">Recall</th><th class="num">False alarms on helmeted bikes</th><th class="num">Precision</th></tr></thead><tbody>
<tr><td>Detector alone</td><td class="num">213 / 299</td><td class="num">0.71</td><td class="num">25 / 164</td><td class="num">0.89</td></tr>
<tr><td>Detector + crop classifier</td><td class="num">219 / 299</td><td class="num">0.73</td><td class="num">22 / 164</td><td class="num">0.91</td></tr></tbody></table></div>
<div class="table-wrap"><table><caption>Early exploration: 9 clips, 42 motorcycles</caption>
<thead><tr><th>Setup</th><th class="num">Recall</th><th>What we learned</th></tr></thead><tbody>
<tr><td>Whole frame only</td><td class="num">0.69</td><td>Many pedestrians and cyclists without helmets also fired.</td></tr>
<tr><td>Only heads on motorcycles</td><td class="num">0.67</td><td>Stray detections fell from 117 to 6; precision rose to 0.97.</td></tr>
<tr><td>Plus enlarged crops (first try)</td><td class="num">0.86</td><td>Too good: giant boxes around a whole rider and bike inflated it.</td></tr>
<tr><td>Crops plus size check</td><td class="num good">0.76</td><td>The honest gain from crops.</td></tr></tbody></table></div>

<h2>5. Speed on a CPU, and the trade-off</h2>
<p>Test machine: desktop Intel Core i3-10100F, no GPU.</p>
<div class="table-wrap"><table><caption>Time per analysed frame and riders caught when frames are 0.5 s apart</caption>
<thead><tr><th>Enlarged crops around motorcycles</th><th class="num">Riders alerted</th><th>Speed</th></tr></thead><tbody>
<tr><td>Never</td><td class="num">81%</td><td>about 0.3 s per frame</td></tr>
<tr><td>Every 6th frame</td><td class="num">84%</td><td>fast</td></tr>
<tr><td>Every 3rd frame</td><td class="num">85%</td><td>medium</td></tr>
<tr><td>Every frame</td><td class="num">90%</td><td>about 1.3 s per frame</td></tr></tbody></table></div>
<p>Crops help, but they cost time, and time means fewer frames per second. We run crops on every 5th frame and reach about 1.4 analysed frames per second on this CPU. A GPU or a faster CPU would let us analyse more frames and catch more riders.</p>

<h2>6. Night</h2>
<div class="table-wrap"><table><caption>The same 200 validation frames in daylight and made to look like night (darkened, infrared-style, dusk)</caption>
<thead><tr><th>Lighting</th><th class="num">Precision</th><th class="num">Recall</th><th class="num">mAP@50</th></tr></thead><tbody>
<tr><td>Daylight</td><td class="num">0.80</td><td class="num">0.76</td><td class="num">0.72</td></tr>
<tr><td>Made to look like night</td><td class="num">0.78</td><td class="num warn">0.34</td><td class="num">0.31</td></tr></tbody></table></div>
<div class="note"><p>This was measured <em>before</em> the model saw any night-style images. We have prepared night-style training data, but it is a stand-in; real night footage from your own cameras will help far more.</p></div>

<h2>What went wrong, and what it taught us</h2>
<ul>
<li><strong>A result that was too good.</strong> Enlarged crops first showed recall 0.86. Looking at the pictures showed giant boxes covering a whole rider and bike. A size check brought recall to 0.76. <em>Always look at the pictures.</em></li>
<li><strong>A tracker built for the wrong frame rate.</strong> ByteTrack hid new riders until a second match. At one frame per second most riders never got one, and four of five crowded clips gave no alert. A tracker made for low frame rates fixed it.</li>
<li><strong>A filter that was too strict.</strong> The first repeat filter removed duplicate alerts but also hid real riders: coverage fell from about 89% to 70%. We relaxed it.</li>
<li><strong>A slow training run.</strong> Using all mined crops made classifier training take far too long on a CPU. Capping and balancing the data made it practical with no loss in accuracy.</li></ul>

<h2>Keep reading</h2>
{related([("How it works, A to Z", HD + "how-it-works/", "Explained", "The pipeline and the reasons behind each step."),
          ("Model card", HD + "model-card/", "Reference", "Intended use, data, limits and licences."),
          ("Helmet detection FAQ", HD + "faq/", "Answers", "Short answers to common questions.")])}
</div></div></article>'''
    return p, body


def cctv():
    url = HD + "cctv-monitoring/"
    p = dict(path=url, title="CCTV Helmet Detection: No-Helmet Alerts on Telegram & App",
             description="Connect an RTSP camera to Axom AI helmet detection. Per-rider tracking, photo alerts on Telegram, dashboard and Android app, offline warnings and Windows auto-start.",
             keywords=["CCTV helmet detection", "RTSP helmet detection", "no helmet alert Telegram", "traffic camera AI", "helmet violation detection CCTV",
                       "Axom AI"],
             crumbs=[("Home", "/"), ("Research", "/research/"), ("Helmet detection", HD), ("CCTV monitoring", url)], article=True)
    p["schemas"] = [article_schema(url, "CCTV helmet detection: setup, alerts and tuning", p["description"], keywords=p["keywords"],
                                   about=["CCTV", "RTSP", "Helmet detection", "Telegram Bot API"])]
    body = f'''
<article>
<header class="hero wrap"><span class="eyebrow">Live monitoring</span>
<h1>CCTV helmet detection: <span class="grad">alerts within seconds</span></h1>
<p class="lead">Connect an IP camera, and get a photo of every rider without a helmet on Telegram, in the dashboard and in the app.</p>{meta_line()}</header>
<div class="wrap"><div class="read" style="margin:0">
<div class="answer"><h2>Quick answer</h2>
<p>A worker program runs on a PC near the camera. It reads the camera's RTSP stream, finds and tracks every rider, and uploads a photo for each rider without a helmet to the Axom AI server, which sends a Telegram message and shows the event in the dashboard and the Android app. A heartbeat every minute lets the server warn you if the PC or the stream stops.</p></div>

<h2>How it is built</h2>
<ul><li><strong>Worker (PC).</strong> Does the heavy AI work. Needs Python 3.11+ and the model files; no GPU.</li>
<li><strong>Server.</strong> Stores events and photos, sends Telegram messages, serves the dashboard and the app. A small shared server is enough, because the server does no AI work for CCTV.</li>
<li><strong>Safety.</strong> The worker and the server share a secret key. Camera passwords stay on the server and are never shown in full in the dashboard.</li></ul>

<h2>Set it up</h2>
<ol class="flow">
<li><b>Add the camera.</b> Dashboard &rarr; Cameras &rarr; name and RTSP address, for example <code>rtsp://user:password@192.168.1.10:554/stream1</code>.</li>
<li><b>Set the keys on the server.</b> A long random <code>CCTV_WORKER_KEY</code>, plus <code>TELEGRAM_BOT_TOKEN</code> and <code>TELEGRAM_CHAT_ID</code> from your own Telegram bot.</li>
<li><b>Configure the PC.</b> In the worker's <code>.env</code> put the same <code>CCTV_WORKER_KEY</code> and <code>CCTV_SERVER_URL</code>.</li>
<li><b>Start the worker.</b> <code>python -m services.cctv_worker --camera-id 1</code>, or install the Windows auto-start so it runs at every login and restarts if it stops.</li>
<li><b>Check.</b> The dashboard's CCTV events page and the app's Alerts tab show new alerts; the worker status card shows it is running.</li></ol>
<pre><code>.\\deploy\\pc\\install_autostart.ps1 -CameraId 1
# several cameras: -CameraId 1,2,3   (one worker each; every worker uses CPU)</code></pre>

<h2>What an alert contains</h2>
<ul><li>A photo with <strong>every rider boxed</strong>: red for no helmet, green for helmet. New people have a thicker box.</li>
<li>A line on the photo: how many are new and how many riders are in view.</li>
<li>The camera name, the time and the confidence.</li>
<li>Admins can mark an alert as a mistake in the dashboard or in the app; those frames can be exported for retraining.</li></ul>
<figure><img src="/research/assets/detection-street.jpg" width="1280" height="720" alt="Example of an alert photo: motorcycle riders on a street boxed in red for no helmet; faces are pixelated here" loading="lazy">
<figcaption>An alert photo from the public HELMET dataset, faces pixelated for this page.</figcaption></figure>

<h2>Tuning</h2>
<div class="table-wrap"><table><caption>Main options of the worker</caption><thead><tr><th>Option</th><th>Default</th><th>What it does</th></tr></thead><tbody>
<tr><td><code>--imgsz</code></td><td>768</td><td>Whole-frame size. Larger sees smaller heads, slower.</td></tr>
<tr><td><code>--crop-every</code></td><td>5</td><td>Enlarged crops around motorcycles on every Nth frame. 1 = most accurate, slowest.</td></tr>
<tr><td><code>--single-conf</code></td><td>0.55</td><td>One sighting at this confidence is enough to alert.</td></tr>
<tr><td><code>--min-hits</code></td><td>2</td><td>Sightings needed when confidence is lower.</td></tr>
<tr><td><code>--max-fps</code></td><td>3</td><td>Upper limit of analysed frames per second.</td></tr>
<tr><td><code>--all-heads</code></td><td>off</td><td>Alert for any bare head, not only motorcycle riders.</td></tr></tbody></table></div>

<h2>How many riders will it catch?</h2>
<p>That depends on how many frames per second your computer can analyse: about 74% at one frame per second and about 90% at two in our tests (see <a href="{HD}results/">results</a>). Plan for a faster CPU or a GPU if the camera sees fast traffic or distant riders.</p>
<div class="note"><p><strong>Use it responsibly.</strong> This is a screening tool. Have a person review alerts before any action against anyone, and follow the privacy and data-protection rules for cameras in your area.</p></div>

<h2>Keep reading</h2>
{related([("How it works, A to Z", HD + "how-it-works/", "Explained", "The pipeline in detail."),
          ("Results", HD + "results/", "Numbers", "Accuracy and speed."),
          ("Code on GitHub", GITHUB_BACKEND, "Open source", "Worker, server and training tools (MIT).")])}
</div></div></article>'''
    return p, body


def model_card():
    url = HD + "model-card/"
    p = dict(path=url, title="Helmet Detection Model Card (YOLOv8s): Data, Limits, Use",
             description="Model card for Axom AI's helmet detector: architecture, training data, metrics, intended use, limitations, bias, licences and how to run it.",
             keywords=["helmet detection model card", "YOLOv8s helmet", "helmet detection dataset", "model card", "AI model limitations", "Axom AI"],
             crumbs=[("Home", "/"), ("Research", "/research/"), ("Helmet detection", HD), ("Model card", url)], article=True)
    p["schemas"] = [article_schema(url, "Helmet detection model card", p["description"], keywords=p["keywords"],
                                   about=["Model card", "Helmet detection", "YOLO", "Responsible AI"])]
    body = f'''
<article>
<header class="hero wrap"><span class="eyebrow">Reference</span>
<h1>Helmet detection <span class="grad">model card</span></h1>
<p class="lead">What the model is, what it was trained on, what it should and should not be used for.</p>{meta_line()}</header>
<div class="wrap"><div class="read" style="margin:0">
<div class="answer"><h2>Quick answer</h2>
<p>A YOLOv8s object detector with two classes, <code>helmet</code> and <code>no_helmet</code>, fine-tuned on public helmet datasets and on CCTV frames from Myanmar traffic cameras. It is meant to screen road footage for riders without helmets, with a person reviewing each alert.</p></div>

<div class="table-wrap"><table><caption>Model details</caption><tbody>
<tr><th scope="row">Name</th><td>Axom AI helmet detector, CCTV fine-tune (October 2026)</td></tr>
<tr><th scope="row">Architecture</th><td>Ultralytics YOLOv8s (about 11.1 million parameters)</td></tr>
<tr><th scope="row">Task</th><td>Object detection of heads with two classes: <code>helmet</code> (0), <code>no_helmet</code> (1)</td></tr>
<tr><th scope="row">Input</th><td>RGB image; 960 px used for training and 768 px for live CCTV; a 416 px ONNX build runs on phones</td></tr>
<tr><th scope="row">Companion models</th><td>COCO-pretrained YOLOv8s (finds motorcycles); YOLOv8n-cls head-crop classifier (second opinion)</td></tr>
<tr><th scope="row">Developer</th><td>Axom AI (Samarjit Kashyap), Guwahati, Assam, India</td></tr>
<tr><th scope="row">Code licence</th><td>MIT. The weights are derived from Ultralytics YOLOv8 (AGPL-3.0) and datasets under CC BY 4.0 and MIT.</td></tr>
<tr><th scope="row">Repository</th><td><a href="{GITHUB_BACKEND}">github.com/Samarjitkashyp/helmet-detection</a></td></tr></tbody></table></div>

<h2>Intended use</h2>
<ul><li>Screening traffic-camera footage and uploaded videos for motorcycle riders without a helmet, with <strong>human review</strong> of each alert.</li>
<li>Road-safety studies and awareness campaigns.</li>
<li>Research and education on object detection and tracking.</li></ul>
<h2>Out-of-scope use</h2>
<ul><li>Automatic fines or penalties without human review.</li>
<li>Identifying people. The system does not recognise faces or read plates, and should not be extended to.</li>
<li>Safety-critical decisions where a miss or a false alarm could cause harm.</li>
<li>Night scenes, heavy rain or very distant riders, until validated on your own footage.</li></ul>

<h2>Training data</h2>
<div class="table-wrap"><table><thead><tr><th>Source</th><th>Used for</th><th>Licence</th></tr></thead><tbody>
<tr><td>Seven public Roboflow Universe datasets (about 11.7 thousand training images; helmets, riders, caps, hats, hijabs, head accessories)</td><td>First model</td><td>CC BY 4.0, one MIT</td></tr>
<tr><td><a href="https://osf.io/4pwj8/">HELMET dataset</a>: 910 traffic-camera clips from Myanmar, 100 frames each, 1080p</td><td>CCTV fine-tune and all CCTV tests</td><td>CC BY 4.0</td></tr></tbody></table></div>
<p>Labels for the CCTV fine-tune were derived from the dataset's per-motorcycle ground truth: our detector found heads inside each motorcycle and each head received the bike's label when every person on it agreed. Caps, hats, hijabs and scarves are labelled <code>no_helmet</code>.</p>

<h2>Evaluation</h2>
<div class="table-wrap"><table><thead><tr><th>Set</th><th class="num">Precision</th><th class="num">Recall</th><th class="num">mAP@50</th></tr></thead><tbody>
<tr><td>Held-out CCTV frames (500 frames, 1,114 riders)</td><td class="num">0.798</td><td class="num">0.791</td><td class="num">0.748</td></tr></tbody></table></div>
<p>Live-worker results at one and two analysed frames per second, speed and night tests are on the <a href="{HD}results/">results page</a>.</p>

<h2>Limitations and bias</h2>
<ul><li><strong>Geography and setting.</strong> The CCTV data is from Myanmar. Clothing, helmet styles, road layouts and camera angles differ in other places.</li>
<li><strong>Light.</strong> Training data is daytime. Night recall is 0.34 on night-style test frames; night training has not been done yet.</li>
<li><strong>Size and distance.</strong> Heads a few pixels wide are missed.</li>
<li><strong>Head coverings.</strong> Turbans are not in the training data and may be judged wrongly.</li>
<li><strong>Frame rate.</strong> Fewer analysed frames per second means fewer riders caught.</li>
<li><strong>Helmet quality.</strong> The model checks whether a helmet is present, not whether it is certified or fastened correctly.</li></ul>

<h2>Ethical considerations</h2>
<ul><li>Alert photos can show faces. Keep them access-controlled (administrators only here), keep them only as long as needed, and follow local privacy law.</li>
<li>False alarms and misses happen. Design the process so that a person checks before anyone is affected.</li>
<li>Be open with the public when cameras run AI analysis, where the law or good practice requires it.</li></ul>

<h2>How to run it</h2>
<pre><code>git clone {GITHUB_BACKEND}
cd helmet-detection/backend
pip install -r requirements.txt
python -m services.cctv_worker --url rtsp://... --name Gate --local</code></pre>
<p>The Android app is at <a href="{GITHUB_APP}">github.com/Samarjitkashyp/helmet-detection-mobile-app</a>; install the published build from <a href="{APP_PAGE}">helmet-detection.aiaxom.co.in/app</a>.</p>

<h2>Version history</h2>
<ul><li><strong>26 Oct 2026.</strong> CCTV fine-tune: recall on held-out CCTV frames 0.62 &rarr; 0.79. Per-rider tracker for low frame rates, crop classifier, size check, speed profile.</li>
<li><strong>Earlier.</strong> First model: seven public datasets, caps and hats as no helmet.</li></ul>
<p>Questions or corrections: <a href="/contact">contact Axom AI</a>.</p>
</div></div></article>'''
    return p, body


def faq_page():
    url = HD + "faq/"
    p = dict(path=url, title="Helmet Detection FAQ: Accuracy, Night, Cost, Privacy",
             description="Short answers about AI helmet detection: how it works, accuracy, CCTV, night, GPU, caps and turbans, privacy, open source and how to try it.",
             keywords=["helmet detection FAQ", "what is helmet detection", "how accurate is helmet detection", "helmet detection at night",
                       "helmet detection open source", "Axom AI"],
             crumbs=[("Home", "/"), ("Research", "/research/"), ("Helmet detection", HD), ("FAQ", url)], article=False)
    p["schemas"] = [faq_schema(FAQ), {"@context": "https://schema.org", "@type": "WebPage", "@id": BASE + url + "#page", "url": BASE + url,
                                      "name": "Helmet detection FAQ", "inLanguage": "en-IN", "isPartOf": {"@id": "https://aiaxom.co.in/#organization"},
                                      "dateModified": "2026-10-26", "speakable": {"@type": "SpeakableSpecification", "cssSelector": ["h1", "details p"]}}]
    body = f'''
<article>
<header class="hero wrap"><span class="eyebrow">FAQ</span>
<h1>Helmet detection: <span class="grad">questions and answers</span></h1>
<p class="lead">Short, direct answers about how Axom AI's helmet detection works and what it can and cannot do.</p>{meta_line()}</header>
<div class="wrap"><div class="read" style="margin:0">
{"".join(f'<details open><summary>{e(q)}</summary><p>{e(a)}</p></details>' if i < 3 else f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for i, (q, a) in enumerate(FAQ))}
<h2>Keep reading</h2>
{related([("Helmet detection overview", HD, "Start", "The short version."),
          ("Results", HD + "results/", "Numbers", "All measurements."),
          ("Model card", HD + "model-card/", "Reference", "Data, limits and licences.")])}
</div></div></article>'''
    return p, body

