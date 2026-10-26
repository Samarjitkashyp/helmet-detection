"""The helmet-detection research report: everything on ONE page (how it works, results, CCTV set-up, model card, FAQ).

One long page instead of five thin ones: all the evidence about this topic sits on a single URL, which is what search engines
and AI answer engines prefer, and readers get one place with a contents list on the side.
"""
from diagram import PIPELINE_SVG
from lib import (APP_PAGE, BASE, GITHUB_APP, GITHUB_BACKEND, MODIFIED, WHO_URL, article_schema, e, faq_schema, hero, small, stat)

HD = "/research/helmet-detection/"

WHO_TEXT = ("WHO reports that head trauma is the leading cause of death for motorcycle riders, and that safe, quality helmets "
            "reduce the risk of death by more than six times and the risk of brain injury by up to 74%.")

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

def icon_cards(items, cls="cards"):
    """Grid of cards with a round icon: items = (icon, title, html text)."""
    return f'<div class="{cls}">' + "".join(
        f'<div class="card ic"><span class="ic-ico">{small(i, 22)}</span><h3>{t}</h3><p>{d}</p></div>' for i, t, d in items) + "</div>"


def cmp_bar(label, pct, value, before):
    return (f'<div class="cmp-row"><span>{label}</span><div class="bar-track"><div class="bar-fill{" warn" if before else ""}" style="width:{pct}%"></div></div>'
            f'<b>{value}</b></div>')


def link_cards(items):
    """Grid of link cards: items = (icon, title, text, href, link label)."""
    return '<div class="cards">' + "".join(
        f'<a class="card ic lk" href="{h}"><span class="ic-ico">{small(i, 22)}</span><h3>{t}</h3><p>{d}</p><span class="go">{l} &rarr;</span></a>'
        for i, t, d, h, l in items) + "</div>"


def faq_html(items):
    return "".join(f'<details{" open" if i < 3 else ""}><summary>{e(q)}</summary><p>{e(a)}</p></details>' for i, (q, a) in enumerate(items))


def bar(label, pct, warn=False, note=""):
    cls = "bar-fill warn" if warn else "bar-fill"
    return (f'<div class="bar-row"><span>{e(label)}</span><div class="bar-track" role="img" aria-label="{e(label)}: {pct}%">'
            f'<div class="{cls}" style="width:{pct}%"></div></div><b>{pct}%</b></div>')


def how_html(svg):
    return f'''
<figure>{svg}<figcaption>The live CCTV pipeline. Phone videos follow the same detection steps on the server, with tracking over every frame.</figcaption></figure>

<h3 id="input">1. Input: a phone video or a camera stream</h3>
<p>Two kinds of input feed the same detector. <strong>Videos</strong> come from the Android app (recorded in HD or picked from the gallery, up to two minutes) and are uploaded in small resumable pieces, so a weak mobile connection does not lose the upload. <strong>Live cameras</strong> are read over RTSP; the worker always keeps only the newest frame, so it never falls behind the stream.</p>

<h3 id="motor">2. Find motorcycles</h3>
<p>A COCO-pretrained YOLOv8s (run at 640 px) marks motorcycles and bicycles. It answers two questions: <em>where should we look more closely?</em> and <em>is this head on a motorcycle at all?</em> Without it, every pedestrian without a hat would be a violation.</p>

<h3 id="heads">3. Find heads, close up and far away</h3>
<p>Our detector is a YOLOv8s fine-tuned to find heads and label them <code>helmet</code> or <code>no_helmet</code>. On a CCTV frame the heads are small, sometimes only 20 pixels wide. So the model looks twice:</p>
<ul><li>at the <strong>whole frame</strong> (768 px) on every analysed frame, which is cheap;</li>
<li>at an <strong>enlarged crop around each motorcycle</strong> (512 px) on every fifth frame, where a distant head becomes large enough to judge.</li></ul>
<p>On early tests (9 clips, 42 motorcycles) the crops raised the share of bare-headed motorcycles caught from 0.67 to 0.76. They are also the slowest step, so the worker runs them regularly rather than constantly. See the speed trade-off on the <a href="#results">results page</a>.</p>

<h3 id="verdict">4. Helmet or no helmet</h3>
<p>The detector gives each head a verdict and a confidence. Two design choices matter more than any other:</p>
<ul><li><strong>Caps, hats, hijabs and scarves count as no helmet.</strong> A cap is not protection. Adding head-covering data raised recall on caps and hats from 0.21 to 0.88 in the first model.</li>
<li><strong>A second opinion.</strong> A small YOLOv8n-cls classifier, trained on head crops cut from CCTV footage, looks at each head. If it is at least 85% sure the detector is wrong, it overrules it. On 299 test motorcycles this lifted recall from 0.71 to about 0.74 and precision from 0.89 to about 0.91.</li></ul>

<h3 id="riders">5. Keep only riders</h3>
<p>A head counts only if it sits on a motorcycle (above the bike, within its width) and has a believable size. The size check came from a mistake: enlarged crops of far-away bikes sometimes made the model draw one giant box around a whole rider and bike. Rejecting boxes that are too large for their motorcycle cut these stray detections from 158 to 6 on our early test set (9 clips).</p>

<h3 id="track">6. Track every rider separately</h3>
<p>A frame with five riders must give five verdicts. Each head gets its own track, so the system can remember what it has seen of each person and alert only once.</p>
<div class="note bad"><p><strong>What went wrong first.</strong> We started with ByteTrack, a strong tracker built for video at 25 to 30 frames per second. A CPU analyses about one frame per second, and by the next frame a fast rider has moved several head-widths. ByteTrack keeps a new head hidden until it matches it a second time, so most riders were never reported: in the first test, four of five crowded clips produced no alert at all.</p></div>
<p>The fix was a tracker designed for few frames per second. It reports a head the moment it is seen and links it to the same person by distance measured in head-widths, using the person's last speed. Crowded clips then gave alerts for most bare-headed riders.</p>

<h3 id="confirm">7. Confirm, then alert once</h3>
<ul><li>A rider is flagged after <strong>one sighting without a helmet at 55% confidence or more</strong>, or after <strong>two sightings</strong>, as long as the no-helmet evidence outweighs the helmet evidence.</li>
<li>One photo is saved per frame, with every rider boxed (red or green) and a caption: how many are new, and how many riders are in view.</li>
<li>A <strong>repeat filter</strong> stops the same person from being alerted again when the tracker loses and re-finds them. We tuned it carefully: a strict version removed repeats but also hid real, different riders, so the final setting is mild.</li></ul>
<p>Alerts go to Telegram, the dashboard and the app. The worker also sends a heartbeat every minute, so the server can warn when the PC or the camera stream stops. Alerts that cannot be uploaded wait in a local outbox and are sent later.</p>

<h3 id="video">Video mode (phone uploads)</h3>
<p>For a recorded video the server runs the helmet model with ByteTrack at the video's full frame rate, adds each head's evidence over time and gives each person <strong>one verdict</strong>: the confidences of every sighting are summed per class, so a long clear view beats a single blurry frame. The best frame of each person is saved as the photo. People seen too few times, or too small, are ignored.</p>

<h3 id="training">Training: data and method</h3>
<ol>
<li><strong>Base model.</strong> YOLOv8s fine-tuned on about 11.7 thousand images from seven public Roboflow datasets, merged into two classes: helmet and no helmet, including caps, hats, hijabs and scarves.</li>
<li><strong>CCTV fine-tune.</strong> The HELMET dataset (Myanmar traffic cameras, 910 clips of 100 frames, 1080p, CC BY 4.0) labels every motorcycle with the helmet state of each person on it. We turned that into head labels by running our detector inside each motorcycle's box and giving each head the bike's label whenever every person on the bike agreed. Mixed bikes were left out.</li>
<li><strong>Training.</strong> Fine-tuned on a free Google Colab T4 GPU at 960 px for up to 30 epochs, together with a replay set of the old data so the model does not forget.</li>
<li><strong>Honest testing.</strong> The dataset ships its own split into training, validation and test clips. We never trained on the test clips, and our results are measured on them.</li>
<li><strong>Phone model.</strong> An ONNX build at 416 px runs on the phone with ONNX Runtime to draw live boxes while framing a shot; the server distributes it, so a new model reaches phones without an app release.</li></ol>

<h3 id="infra">Servers and apps</h3>
<p>The backend is FastAPI with PostgreSQL behind nginx and Cloudflare on an AWS Lightsail server. It has JWT sign-in, role-based access, rate limiting, an optional admin IP allow-list, and resumable uploads. The heavy CCTV analysis runs on a PC next to the camera and only sends photos and heartbeats to the server, so a small shared server is enough. The Android app is written in Flutter.</p>

<h3 id="stack">Technology table</h3>
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
'''


def results_html():
    return f'''
<h3>How we measured</h3>
<ul>
<li><strong>Data.</strong> The HELMET dataset: 910 clips (100 frames each, 1080p, 10 fps) from traffic cameras in Myanmar, CC BY 4.0. It labels every motorcycle with the helmet state of each person on it.</li>
<li><strong>Honest split.</strong> We use the dataset's own split. Training used only the training clips; the numbers below come from validation or test clips the model never saw.</li>
<li><strong>"Riders caught".</strong> For each clip, alerts are compared with the number of bare-headed people in the ground truth; an alert on a bike with a bare-headed rider counts as correct, an alert on a bike where everyone wears a helmet counts as a false alarm. Counts are approximate because the labels name bikes, not individual heads.</li>
<li><strong>Limits of the test.</strong> One country, daytime, a few hundred riders. Treat the figures as a guide, not a promise for your camera.</li></ul>

<h3>1. The model on held-out CCTV frames</h3>
<div class="table-wrap"><table><caption>500 validation frames, 1,114 riders, from clips not used for training (confidence 0.5, image size 960)</caption>
<thead><tr><th>Model</th><th class="num">Precision</th><th class="num">Recall</th><th class="num">mAP@50</th></tr></thead>
<tbody><tr><td>First model (public Roboflow data only)</td><td class="num">0.777</td><td class="num">0.617</td><td class="num">0.547</td></tr>
<tr><td><strong>After CCTV fine-tuning</strong></td><td class="num good">0.798</td><td class="num good">0.791</td><td class="num good">0.748</td></tr></tbody></table></div>
<p>Fine-tuning on a few thousand real CCTV frames matters more than anything else we tried: recall rose by 17 points.</p>

<h3>2. The first model on public test sets</h3>
<div class="table-wrap"><table><caption>Test splits of the public datasets (confidence 0.4, 640 px)</caption>
<thead><tr><th>Test set</th><th>Class</th><th class="num">Precision</th><th class="num">Recall</th></tr></thead><tbody>
<tr><td rowspan="2">Riders and people (300 images)</td><td>helmet</td><td class="num">0.93</td><td class="num">0.93</td></tr><tr><td>no helmet</td><td class="num">0.95</td><td class="num">0.84</td></tr>
<tr><td rowspan="2">Caps, hats, hijabs (87 images)</td><td>helmet</td><td class="num">0.94</td><td class="num">0.85</td></tr><tr><td>no helmet</td><td class="num">0.87</td><td class="num">0.88</td></tr></tbody></table></div>
<p>mAP@50 was 0.92 on riders and people and 0.91 on head coverings. Adding head-covering data lifted no-helmet recall on caps and hats from 0.21 to 0.88 without hurting the original set. These sets are easier than real CCTV, which is why the CCTV test above matters.</p>

<h3>3. The live CCTV worker at different speeds</h3>
<p>The worker analyses as many frames per second as the computer allows. How many riders get an alert depends strongly on that rate. Test: 14 of the busiest held-out clips with 170 bare-headed riders.</p>
<div role="group" aria-label="Share of bare-headed riders alerted">
{bar("1 frame / second", 74)}{bar("2 frames / second", 90)}</div>
<div class="table-wrap"><table><caption>Same clips, same settings</caption>
<thead><tr><th>Analysed frames per second</th><th class="num">Riders alerted</th><th class="num">Extra alerts for the same people</th><th class="num">Alerts on fully helmeted bikes</th></tr></thead><tbody>
<tr><td>1</td><td class="num">about 74%</td><td class="num">2</td><td class="num">1 (about 1%)</td></tr>
<tr><td>2</td><td class="num good">about 90%</td><td class="num">44</td><td class="num">1 (about 1%)</td></tr></tbody></table></div>
<p>Faster analysis catches more riders but also alerts the same person more than once. A repeat filter keeps this in check; a stricter filter removed the repeats but also hid real riders, so we kept it mild.</p>

<h3>4. What each part of the pipeline adds</h3>
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

<h3>5. Speed on a CPU, and the trade-off</h3>
<p>Test machine: desktop Intel Core i3-10100F, no GPU.</p>
<div class="table-wrap"><table><caption>Time per analysed frame and riders caught when frames are 0.5 s apart</caption>
<thead><tr><th>Enlarged crops around motorcycles</th><th class="num">Riders alerted</th><th>Speed</th></tr></thead><tbody>
<tr><td>Never</td><td class="num">81%</td><td>about 0.3 s per frame</td></tr>
<tr><td>Every 6th frame</td><td class="num">84%</td><td>fast</td></tr>
<tr><td>Every 3rd frame</td><td class="num">85%</td><td>medium</td></tr>
<tr><td>Every frame</td><td class="num">90%</td><td>about 1.3 s per frame</td></tr></tbody></table></div>
<p>Crops help, but they cost time, and time means fewer frames per second. We run crops on every 5th frame and reach about 1.4 analysed frames per second on this CPU. A GPU or a faster CPU would let us analyse more frames and catch more riders.</p>

<h3>6. Night</h3>
<div class="table-wrap"><table><caption>The same 200 validation frames in daylight and made to look like night (darkened, infrared-style, dusk)</caption>
<thead><tr><th>Lighting</th><th class="num">Precision</th><th class="num">Recall</th><th class="num">mAP@50</th></tr></thead><tbody>
<tr><td>Daylight</td><td class="num">0.80</td><td class="num">0.76</td><td class="num">0.72</td></tr>
<tr><td>Made to look like night</td><td class="num">0.78</td><td class="num warn">0.34</td><td class="num">0.31</td></tr></tbody></table></div>
<div class="note"><p>This was measured <em>before</em> the model saw any night-style images. We have prepared night-style training data, but it is a stand-in; real night footage from your own cameras will help far more.</p></div>

<h3>What went wrong, and what it taught us</h3>
<ul>
<li><strong>A result that was too good.</strong> Enlarged crops first showed recall 0.86. Looking at the pictures showed giant boxes covering a whole rider and bike. A size check brought recall to 0.76. <em>Always look at the pictures.</em></li>
<li><strong>A tracker built for the wrong frame rate.</strong> ByteTrack hid new riders until a second match. At one frame per second most riders never got one, and four of five crowded clips gave no alert. A tracker made for low frame rates fixed it.</li>
<li><strong>A filter that was too strict.</strong> The first repeat filter removed duplicate alerts but also hid real riders: coverage fell from about 89% to 70%. We relaxed it.</li>
<li><strong>A slow training run.</strong> Using all mined crops made classifier training take far too long on a CPU. Capping and balancing the data made it practical with no loss in accuracy.</li></ul>
'''


def cctv_html():
    return f'''
<h3>How it is built</h3>
<ul><li><strong>Worker (PC).</strong> Does the heavy AI work. Needs Python 3.11+ and the model files; no GPU.</li>
<li><strong>Server.</strong> Stores events and photos, sends Telegram messages, serves the dashboard and the app. A small shared server is enough, because the server does no AI work for CCTV.</li>
<li><strong>Safety.</strong> The worker and the server share a secret key. Camera passwords stay on the server and are never shown in full in the dashboard.</li></ul>

<h3>Set it up</h3>
<ol class="flow">
<li><b>Add the camera.</b> Dashboard &rarr; Cameras &rarr; name and RTSP address, for example <code>rtsp://user:password@192.168.1.10:554/stream1</code>.</li>
<li><b>Set the keys on the server.</b> A long random <code>CCTV_WORKER_KEY</code>, plus <code>TELEGRAM_BOT_TOKEN</code> and <code>TELEGRAM_CHAT_ID</code> from your own Telegram bot.</li>
<li><b>Configure the PC.</b> In the worker's <code>.env</code> put the same <code>CCTV_WORKER_KEY</code> and <code>CCTV_SERVER_URL</code>.</li>
<li><b>Start the worker.</b> <code>python -m services.cctv_worker --camera-id 1</code>, or install the Windows auto-start so it runs at every login and restarts if it stops.</li>
<li><b>Check.</b> The dashboard's CCTV events page and the app's Alerts tab show new alerts; the worker status card shows it is running.</li></ol>
<pre><code>.\\deploy\\pc\\install_autostart.ps1 -CameraId 1
# several cameras: -CameraId 1,2,3   (one worker each; every worker uses CPU)</code></pre>

<h3>What an alert contains</h3>
<ul><li>A photo with <strong>every rider boxed</strong>: red for no helmet, green for helmet. New people have a thicker box.</li>
<li>A line on the photo: how many are new and how many riders are in view.</li>
<li>The camera name, the time and the confidence.</li>
<li>Admins can mark an alert as a mistake in the dashboard or in the app; those frames can be exported for retraining.</li></ul>

<h3>Tuning</h3>
<div class="table-wrap"><table><caption>Main options of the worker</caption><thead><tr><th>Option</th><th>Default</th><th>What it does</th></tr></thead><tbody>
<tr><td><code>--imgsz</code></td><td>768</td><td>Whole-frame size. Larger sees smaller heads, slower.</td></tr>
<tr><td><code>--crop-every</code></td><td>5</td><td>Enlarged crops around motorcycles on every Nth frame. 1 = most accurate, slowest.</td></tr>
<tr><td><code>--single-conf</code></td><td>0.55</td><td>One sighting at this confidence is enough to alert.</td></tr>
<tr><td><code>--min-hits</code></td><td>2</td><td>Sightings needed when confidence is lower.</td></tr>
<tr><td><code>--max-fps</code></td><td>3</td><td>Upper limit of analysed frames per second.</td></tr>
<tr><td><code>--all-heads</code></td><td>off</td><td>Alert for any bare head, not only motorcycle riders.</td></tr></tbody></table></div>

<h3>How many riders will it catch?</h3>
<p>That depends on how many frames per second your computer can analyse: about 74% at one frame per second and about 90% at two in our tests (see <a href="#results">results</a>). Plan for a faster CPU or a GPU if the camera sees fast traffic or distant riders.</p>
<div class="note"><p><strong>Use it responsibly.</strong> This is a screening tool. Have a person review alerts before any action against anyone, and follow the privacy and data-protection rules for cameras in your area.</p></div>
'''


def model_html():
    return f'''
<h3>Model details</h3>
<div class="table-wrap"><table><caption>Model details</caption><tbody>
<tr><th scope="row">Name</th><td>Axom AI helmet detector, CCTV fine-tune (October 2026)</td></tr>
<tr><th scope="row">Architecture</th><td>Ultralytics YOLOv8s (about 11.1 million parameters)</td></tr>
<tr><th scope="row">Task</th><td>Object detection of heads with two classes: <code>helmet</code> (0), <code>no_helmet</code> (1)</td></tr>
<tr><th scope="row">Input</th><td>RGB image; 960 px used for training and 768 px for live CCTV; a 416 px ONNX build runs on phones</td></tr>
<tr><th scope="row">Companion models</th><td>COCO-pretrained YOLOv8s (finds motorcycles); YOLOv8n-cls head-crop classifier (second opinion)</td></tr>
<tr><th scope="row">Developer</th><td>Axom AI (Samarjit Kashyap), Guwahati, Assam, India</td></tr>
<tr><th scope="row">Code licence</th><td>MIT. The weights are derived from Ultralytics YOLOv8 (AGPL-3.0) and datasets under CC BY 4.0 and MIT.</td></tr>
<tr><th scope="row">Repository</th><td><a href="{GITHUB_BACKEND}">github.com/Samarjitkashyp/helmet-detection</a></td></tr></tbody></table></div>

<h3>Intended use</h3>
<ul><li>Screening traffic-camera footage and uploaded videos for motorcycle riders without a helmet, with <strong>human review</strong> of each alert.</li>
<li>Road-safety studies and awareness campaigns.</li>
<li>Research and education on object detection and tracking.</li></ul>
<h3>Out-of-scope use</h3>
<ul><li>Automatic fines or penalties without human review.</li>
<li>Identifying people. The system does not recognise faces or read plates, and should not be extended to.</li>
<li>Safety-critical decisions where a miss or a false alarm could cause harm.</li>
<li>Night scenes, heavy rain or very distant riders, until validated on your own footage.</li></ul>

<h3>Training data</h3>
<div class="table-wrap"><table><thead><tr><th>Source</th><th>Used for</th><th>Licence</th></tr></thead><tbody>
<tr><td>Seven public Roboflow Universe datasets (about 11.7 thousand training images; helmets, riders, caps, hats, hijabs, head accessories)</td><td>First model</td><td>CC BY 4.0, one MIT</td></tr>
<tr><td><a href="https://osf.io/4pwj8/">HELMET dataset</a>: 910 traffic-camera clips from Myanmar, 100 frames each, 1080p</td><td>CCTV fine-tune and all CCTV tests</td><td>CC BY 4.0</td></tr></tbody></table></div>
<p>Labels for the CCTV fine-tune were derived from the dataset's per-motorcycle ground truth: our detector found heads inside each motorcycle and each head received the bike's label when every person on it agreed. Caps, hats, hijabs and scarves are labelled <code>no_helmet</code>.</p>

<h3>Evaluation</h3>
<div class="table-wrap"><table><thead><tr><th>Set</th><th class="num">Precision</th><th class="num">Recall</th><th class="num">mAP@50</th></tr></thead><tbody>
<tr><td>Held-out CCTV frames (500 frames, 1,114 riders)</td><td class="num">0.798</td><td class="num">0.791</td><td class="num">0.748</td></tr></tbody></table></div>
<p>Live-worker results at one and two analysed frames per second, speed and night tests are on the <a href="#results">results page</a>.</p>

<h3>Limitations and bias</h3>
<ul><li><strong>Geography and setting.</strong> The CCTV data is from Myanmar. Clothing, helmet styles, road layouts and camera angles differ in other places.</li>
<li><strong>Light.</strong> Training data is daytime. Night recall is 0.34 on night-style test frames; night training has not been done yet.</li>
<li><strong>Size and distance.</strong> Heads a few pixels wide are missed.</li>
<li><strong>Head coverings.</strong> Turbans are not in the training data and may be judged wrongly.</li>
<li><strong>Frame rate.</strong> Fewer analysed frames per second means fewer riders caught.</li>
<li><strong>Helmet quality.</strong> The model checks whether a helmet is present, not whether it is certified or fastened correctly.</li></ul>

<h3>Ethical considerations</h3>
<ul><li>Alert photos can show faces. Keep them access-controlled (administrators only here), keep them only as long as needed, and follow local privacy law.</li>
<li>False alarms and misses happen. Design the process so that a person checks before anyone is affected.</li>
<li>Be open with the public when cameras run AI analysis, where the law or good practice requires it.</li></ul>

<h3>How to run it</h3>
<pre><code>git clone {GITHUB_BACKEND}
cd helmet-detection/backend
pip install -r requirements.txt
python -m services.cctv_worker --url rtsp://... --name Gate --local</code></pre>
<p>The Android app is at <a href="{GITHUB_APP}">github.com/Samarjitkashyp/helmet-detection-mobile-app</a>; install the published build from <a href="{APP_PAGE}">helmet-detection.aiaxom.co.in/app</a>.</p>

<h3>Version history</h3>
<ul><li><strong>26 Oct 2026.</strong> CCTV fine-tune: recall on held-out CCTV frames 0.62 &rarr; 0.79. Per-rider tracker for low frame rates, crop classifier, size check, speed profile.</li>
<li><strong>Earlier.</strong> First model: seven public datasets, caps and hats as no helmet.</li></ul>
<p>Questions or corrections: <a href="/contact">contact Axom AI</a>.</p>
'''


def overview():
    url = HD
    p = dict(path=url, title="Helmet Detection AI for CCTV & Mobile | Axom AI Research",
             og_title="Helmet Detection AI: every rider checked, from a phone or a CCTV camera",
             description="Axom AI helmet detection finds riders without helmets in phone videos and CCTV. YOLOv8, per-rider tracking, instant alerts, measured results and open source.",
             keywords=["helmet detection", "AI helmet detection", "helmet detection using YOLOv8", "no helmet detection", "CCTV helmet detection",
                       "helmet detection accuracy", "helmet detection model card", "how helmet detection works", "no helmet alert Telegram",
                       "artificial intelligence", "computer vision", "road safety AI", "Axom AI"],
             crumbs=[("Home", "/"), ("Research", "/research/"), ("Helmet detection", url)], article=True)
    p["schemas"] = [
        article_schema(url, "Helmet Detection AI: every rider checked, from a phone video or a CCTV camera", p["description"],
                       keywords=p["keywords"], about=["Helmet detection", "Computer vision", "Road safety", "YOLO", "Object tracking", "Closed-circuit television"],
                       cites=[("WHO: new guide to boost the use of life-saving helmets for motorcycle riders", WHO_URL),
                              ("HELMET dataset (Myanmar traffic cameras, CC BY 4.0)", "https://osf.io/4pwj8/"),
                              ("Ultralytics YOLOv8", "https://github.com/ultralytics/ultralytics"),
                              ("ByteTrack: multi-object tracking by associating every detection box", "https://arxiv.org/abs/2110.06864"),
                              ("COCO dataset", "https://cocodataset.org/")]),
        {"@context": "https://schema.org", "@type": "SoftwareSourceCode", "name": "helmet-detection (backend, CCTV worker, training tools)",
         "codeRepository": GITHUB_BACKEND, "programmingLanguage": "Python", "license": "https://opensource.org/licenses/MIT",
         "author": {"@type": "Person", "name": "Samarjit Kashyap"}, "runtimePlatform": "Python 3.11+"},
        {"@context": "https://schema.org", "@type": "SoftwareSourceCode", "name": "helmet-detection-mobile-app (Flutter, Android)",
         "codeRepository": GITHUB_APP, "programmingLanguage": "Dart", "license": "https://opensource.org/licenses/MIT",
         "author": {"@type": "Person", "name": "Samarjit Kashyap"}},
        faq_schema(FAQ)]
    cctv_text = ("A worker reads the RTSP stream of a camera, tracks every rider separately and raises one alert per person without a helmet. See "
                 + '<a href="#cctv">CCTV monitoring</a>.')
    svg = PIPELINE_SVG
    body = f'''
<article>
{hero("Official Axom AI Research · Road Safety",
      'Helmet Detection AI: <span class="grad">every rider checked,</span> from a phone video or a CCTV camera',
      "An end-to-end system from Axom AI that finds each motorcycle rider, decides helmet or no helmet, and sends a photo alert for every rider without one.",
      chips=[("shield", "Road safety"), ("camera", "CCTV cameras"), ("phone", "Android app"), ("bolt", "Telegram alerts"), ("cpu", "No GPU needed"), ("code", "Open source")],
      cta=f'<a class="btn primary" href="#results">See the results</a><a class="btn" href="{GITHUB_BACKEND}">View code on GitHub</a><a class="btn" href="{APP_PAGE}">Try the Android app</a>')}

<section class="wrap showcase">
<figure class="show-fig"><img src="/research/assets/detection-junction.jpg" width="1280" height="720" alt="Busy junction where each rider on several motorcycles gets their own red or green box; faces are pixelated" fetchpriority="high">
<span class="legend"><i class="r"></i>No helmet<i class="g"></i>Helmet</span>
<figcaption>Every rider gets their own verdict. Held-out frame from the public HELMET dataset (CC BY 4.0), faces pixelated.</figcaption></figure>
<div class="stats" role="list">
{stat("target", "0.79", "recall on held-out CCTV frames after fine-tuning (was 0.62)")}
{stat("users", "~90%", "of bare-headed riders alerted at 2 analysed frames per second")}
{stat("shield", "~1%", "of alerts on fully helmeted bikes (false alarms)")}
{stat("bolt", "1.4 fps", "analysed on a desktop Intel Core i3 CPU, no GPU")}
</div>
</section>

<div class="wrap"><div class="read" style="margin:0">
<div class="answer"><h2>Quick answer</h2>
<p><strong>Helmet detection is computer vision that finds motorcycle riders and decides, person by person, whether a helmet is worn.</strong> Axom AI's system does this on uploaded videos and on live CCTV streams. On traffic-camera footage it had never seen, it caught about 74% of bare-headed riders when analysing one frame per second and about 90% at two frames per second, with about 1% of alerts on fully helmeted bikes. It runs on a normal CPU, with no GPU.</p></div>

<nav class="toc" aria-label="On this page"><b>On this page</b><ol>
<li><a href="#why">Why it matters</a></li><li><a href="#built">What Axom AI built</a></li>
<li><a href="#see">See it work</a></li><li><a href="#how">How it works, A to Z</a></li>
<li><a href="#results">Results and benchmarks</a></li><li><a href="#cctv">CCTV monitoring</a></li>
<li><a href="#limits">Honest limits</a></li><li><a href="#model">Model card</a></li>
<li><a href="#open">Open source and links</a></li><li><a href="#cite">Cite this work</a></li><li><a href="#faq">FAQ</a></li></ol></nav>

<h2 id="why">Why helmet detection matters</h2>
<p>{e(WHO_TEXT)} (<a href="{WHO_URL}" rel="noopener">World Health Organization, 2023</a>). A helmet only helps when it is worn, and no team can watch every road.</p>
<p>Cameras already watch many junctions and highways. An AI model can read those streams all day, point at the riders without a helmet, and hand a human a photo to review. That is the idea behind this work: <strong>use the cameras that exist, and let people spend their time on the cases that matter.</strong></p>

<h2 id="built">What Axom AI built</h2>
{icon_cards([
    ("phone", "Video analysis", "Record or upload a clip in the Android app. The server finds every person, gives each one a single verdict and returns a photo with the time it was seen."),
    ("camera", "Live CCTV monitoring", cctv_text),
    ("chart", "Admin dashboard", "Statistics, violation review, false-positive marking, camera management and a CCTV events page."),
    ("bolt", "Alerts where people look", "Telegram, the dashboard and an Alerts tab in the app, plus a warning when the monitor itself stops."),
    ("sparkle", "A retraining loop", "Reviewers flag wrong detections; those frames become training data for the next version."),
])}

<h2 id="see">See it work</h2>
<figure><img src="/research/assets/detection-street.jpg" width="1280" height="720" alt="Street scene where an AI model marks three motorcycle riders without helmets with red boxes; faces are pixelated" loading="lazy">
<figcaption>Held-out frame from the public HELMET dataset (Myanmar traffic cameras, CC BY 4.0). Red = no helmet, green = helmet. Faces are pixelated here; the live system saves the original frame as evidence for the administrator only.</figcaption></figure>
<p>On a busy junction every rider gets their own verdict, so a bike with two people gives two results, not one (see the picture at the top of this page).</p>

<h2 id="how">How it works, from A to Z</h2>
<p>In eight steps:</p>
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
<p>The same steps in detail, with the reasons behind each choice:</p>
{how_html(svg)}

<h2 id="results">Results and benchmarks</h2>
<div class="compare" role="img" aria-label="Recall on held-out CCTV frames rose from 0.62 to 0.79 after fine-tuning">
<p class="cmp-title">Recall on held-out CCTV frames</p>
{cmp_bar("Before fine-tuning", 61.7, "0.62", True)}
{cmp_bar("After fine-tuning", 79.1, "0.79", False)}
</div>
<p>After fine-tuning on CCTV frames, recall on held-out frames rose from 0.62 to 0.79 and mAP@50 from 0.55 to 0.75. In the live CCTV worker, about 74% of bare-headed riders were alerted when one frame per second was analysed and about 90% at two frames per second, with about 1% of alerts on fully helmeted bikes. On night-like frames recall is only 0.34, and night training is still to be done. Every number below says what it was measured on.</p>
{results_html()}

<h2 id="cctv">CCTV monitoring: connect a camera</h2>
<p>Connect an IP camera, and get a photo of every rider without a helmet on Telegram, in the dashboard and in the app. A worker program runs on a PC near the camera, reads the RTSP stream, finds and tracks every rider, and uploads a photo for each rider without a helmet to the Axom AI server. A heartbeat every minute lets the server warn you if the PC or the stream stops.</p>
{cctv_html()}

<h2 id="limits">Honest limits</h2>
{icon_cards([
    ("moon", "Night", "The training data is daytime. On the same frames made to look like night, recall fell from 0.76 to 0.34. Night-style training images are prepared but the model has not been trained on them yet, and real night footage is still needed."),
    ("target", "Distance", "Heads that are only a few pixels wide are missed. Enlarged crops help; they cost speed."),
    ("bolt", "Speed decides recall", "The more frames analysed per second, the more riders are caught. A desktop CPU manages about 1.4."),
    ("camera", "Your camera is not ours", "Our test footage is from Myanmar traffic cameras. Angle, light and clothing at your site will differ, and results will too."),
    ("shield", "A screening tool, not a judge", "A person should review an alert before any action is taken against anyone."),
], "cards warn-cards")}

<h2 id="model">Model card</h2>
<p>What the model is, what it was trained on, what it should and should not be used for. A YOLOv8s object detector with two classes, <code>helmet</code> and <code>no_helmet</code>, fine-tuned on public helmet datasets and on CCTV frames from Myanmar traffic cameras. It is meant to screen road footage for riders without helmets, with a person reviewing each alert.</p>
{model_html()}

<h2 id="open">Open source and links</h2>
{link_cards([
    ("code", "Backend and CCTV worker", "Server, CCTV worker and training tools. MIT licence.", GITHUB_BACKEND, "github.com/Samarjitkashyp/helmet-detection"),
    ("phone", "Android app (Flutter)", "The app that records, uploads and shows alerts. MIT licence.", GITHUB_APP, "View on GitHub"),
    ("bolt", "Download the app", "Install the Android app and try it on your own video.", APP_PAGE, "Open the app page"),
    ("book", "Key facts as JSON", "The main numbers of this report in a machine-readable file.", url + "key-facts.json", "Open key-facts.json"),
])}

<h2 id="cite">Cite this work</h2>
<pre><code>@techreport{{axomai2026helmet,
  title  = {{Helmet Detection: every rider checked, from a phone video or a CCTV camera}},
  author = {{Kashyap, Samarjit}},
  institution = {{Axom AI}},
  year   = {{2026}},
  url    = {{{BASE}{url}}}
}}</code></pre>

<h2 id="faq">Frequently asked questions</h2>
{faq_html(FAQ)}
</div></div>
<section class="wrap"><div class="cta-band"><div><p class="cta-h">See it on your own footage</p><p>Open the Android app and analyse a video, or read the code and run the CCTV worker on your own camera.</p></div>
<div class="cta"><a class="btn primary" href="{APP_PAGE}">Try the Android app</a><a class="btn" href="{GITHUB_BACKEND}">View code on GitHub</a></div></div></section>
</article>'''
    return p, body
