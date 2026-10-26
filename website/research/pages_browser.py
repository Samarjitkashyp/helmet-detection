"""Research report: Axomai Browser (free AI browser made in Assam, Windows and Android)."""
from diagram import BROWSER_SVG
from lib import BASE, article_schema, faq_schema, hero, stat
from pages_hd import faq_html, icon_cards, link_cards

BROWSER = "/research/axomai-browser/"
MINUTES = 22
SITE = "https://axomai-browser.aiaxom.co.in/"
GITHUB = "https://github.com/Samarjitkashyp/axomai-browser"

FAQ = [
    ("What is Axomai Browser?",
     "Axomai Browser is a free web browser made in Assam by Axom AI. It has an AI assistant (Axom AI) built in that can answer questions about the page you are reading, menus in Assamese, Hindi, Bengali and English, ad and tracker blocking, and five themes inspired by Assam. It runs on Windows 10 and 11 (64-bit) and on Android 7.0 or newer."),
    ("Is Axomai Browser a new browser engine?",
     "No. Web pages are drawn by Microsoft Edge WebView2, which is Chromium, so websites behave as they do in Chrome or Edge. What Axomai adds is the browser around the page: tabs, address bar, New Tab page, privacy shield, settings, sync, updates and the AI chat."),
    ("Is it free? Do I need an account?",
     "It is free, and there is no sign-in or account. The AI chat has a fair-use limit of 30 messages per installation per day."),
    ("Which AI does it use, and is my chat saved?",
     "The chat uses an OpenAI model that is chosen on Axomai's server, not in the app. Your question, and the page text if \"Use this page to answer\" is on, go to OpenAI through Axomai's server. Neither the browser nor the server saves chats; the server keeps only daily counters."),
    ("Does it work in Assamese?",
     "Yes. Menus and settings come in Assamese, Hindi, Bengali and English, and the assistant is told to answer in the language you write in. Pages can also be translated into Assamese, Hindi, Bengali and nine more languages through Google Translate."),
    ("How does it protect my privacy?",
     "It blocks requests to a built-in list of 202 advertising and tracking domains before they are fetched, adds noise to canvas, WebGL and audio fingerprinting, upgrades sites to HTTPS, sends the Global Privacy Control signal, hides cookie banners and offers private windows. Saved passwords are encrypted with your Windows account."),
    ("Is the ad blocker as strong as uBlock Origin?",
     "No. The list is deliberately small, 202 domains that exist only to serve ads or telemetry, so that blocking them does not break the sites people use. It does not use the full EasyList-style filter lists, and we have not compared it with other blockers."),
    ("Why does Windows show a warning when I install it?",
     "The installer is not code-signed yet, so Windows SmartScreen shows a blue screen. Choose More info and then Run anyway. You can compare the SHA-256 shown on the download page with the file you downloaded."),
    ("How does it update itself, and is that safe?",
     "About once a day the browser reads release.json from Axomai's server. If a newer version exists and you choose Update now, it downloads the installer and checks its SHA-256 against the published checksum file. If they differ, it refuses to install."),
    ("Does it sync between computers?",
     "Yes, without an Axomai server. You pick a folder that OneDrive, Google Drive or Dropbox already shares and a passphrase. The browser writes one encrypted file there (AES-256-GCM, key from your passphrase), and each computer merges it. The passphrase is never stored."),
    ("Can I use Chrome extensions?",
     "Unpacked Chrome extensions can be loaded (Extensions page, Load unpacked). Extensions that depend on Chrome's own services will not work, and the Chrome Web Store cannot be used to install them directly."),
    ("Is the source code open?",
     "Yes. The Windows browser, the chat proxy, the landing-page generator and the installer scripts are on GitHub under the MIT licence. The Android app is a separate Flutter project and is not in that repository."),
    ("Is it faster or lighter than Chrome?",
     "We have not benchmarked speed or memory against Chrome or Edge, so we make no such claim. Because it uses the same Chromium engine for pages, page speed should be similar; the browser's own shell is small."),
]

HOW_STEPS = [
    ("Open a page.", "Each tab holds its own Edge WebView2 view, so web pages behave as in Chrome or Edge."),
    ("Shield the request.", "Before a request leaves, it is checked against the built-in list of ad and tracker domains."),
    ("Show it.", "The page appears; the Rust shell around it draws the tabs, address bar and built-in pages."),
    ("Ask Axom AI.", "The AI button sends your question, and the page text if you allow it, to Axomai's chat proxy."),
    ("Proxy and limits.", "The proxy checks the request, applies daily limits and adds the key, a fixed prompt and a fixed model."),
    ("Answer streams back.", "OpenAI's answer is streamed to the browser word by word. Nothing is stored."),
    ("Sync and update.", "Bookmarks and settings sync through your own folder; updates are checked against a published SHA-256."),
]


def overview_browser():
    url = BROWSER
    p = dict(path=url, title="Axomai Browser: the Free AI Browser Made in Assam, Explained",
             og_title="Axomai Browser: a free AI browser made in Assam",
             description="How Axomai Browser works: Edge WebView2 pages, a Rust shell, a private Axom AI chat proxy, ad and tracker blocking, encrypted sync and checked updates.",
             keywords=["Axomai Browser", "AI browser", "Assamese browser", "browser with AI assistant", "free browser for Windows", "WebView2 browser", "Rust browser",
                       "private browser", "ad blocker browser", "Axom AI"],
             crumbs=[("Home", "/"), ("Research", "/research/"), ("Axomai Browser", url)], article=True,
             image=f"{BASE}/research/assets/og-browser.jpg",
             image_alt="Axomai Browser window with the Axom AI chat panel open beside a page about Assam tea")
    p["schemas"] = [
        article_schema(url, "Axomai Browser: how a free AI browser made in Assam works", p["description"], image=p["image"], keywords=p["keywords"],
                       about=["Web browser", "Artificial intelligence", "Online privacy", "Assamese language", "Microsoft Edge WebView2"],
                       cites=[("Microsoft Edge WebView2", "https://learn.microsoft.com/microsoft-edge/webview2/"),
                              ("wry: cross-platform WebView library for Rust", "https://github.com/tauri-apps/wry"),
                              ("Global Privacy Control", "https://globalprivacycontrol.org/"),
                              ("OpenAI API", "https://platform.openai.com/docs")]),
        {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "Axomai Browser", "applicationCategory": "BrowserApplication",
         "operatingSystem": "Windows 10, Windows 11, Android 7.0+", "softwareVersion": "4.1.2", "license": "https://opensource.org/licenses/MIT",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "INR"}, "url": SITE, "downloadUrl": SITE,
         "author": {"@type": "Person", "name": "Samarjit Kashyap"}, "publisher": {"@id": "https://aiaxom.co.in/#organization"}},
        {"@context": "https://schema.org", "@type": "SoftwareSourceCode", "name": "axomai-browser", "codeRepository": GITHUB,
         "programmingLanguage": "Rust", "license": "https://opensource.org/licenses/MIT", "author": {"@type": "Person", "name": "Samarjit Kashyap"}},
        faq_schema(FAQ)]
    body = f'''
<article>
{hero("Official Axom AI Research · Product",
      'Axomai Browser: <span class="grad">a free AI browser made in Assam</span>',
      "A Windows and Android browser with Axom AI built in. Ask about the page you are reading in Assamese, Hindi, Bengali or English, with ad blocking, encrypted sync and checked updates.",
      chips=[("book", "Assamese, Hindi, Bengali, English"), ("shield", "Private by default"), ("code", "Open source, MIT"), ("phone", "Windows and Android"), ("bolt", "No sign-in")],
      cta=f'<a class="btn primary" href="{SITE}">Download Axomai Browser</a><a class="btn" href="{GITHUB}">View code on GitHub</a>')}

<section class="wrap showcase">
<div class="stats" role="list">
{stat("shield", "202", "ad and tracker domains blocked before they are fetched")}
{stat("bolt", "30", "free AI messages per installation each day, nothing saved")}
{stat("target", "206", "automated tests in the desktop browser code")}
{stat("users", "4", "interface languages: Assamese, Hindi, Bengali, English")}
</div>
</section>

<div class="wrap"><div class="read" style="margin:0">
<div class="answer"><h2>Quick answer</h2>
<p><strong>Axomai Browser is a free web browser for Windows and Android, made in Assam, with an AI assistant built in.</strong> Pages are drawn by Microsoft Edge WebView2 (Chromium), so sites work as in Chrome or Edge. Around the page, Axomai adds its own Rust shell, menus in four languages, an ad and tracker shield, encrypted sync through your own folder, SHA-256-checked updates and Axom AI, a chat that can read the page with you. The AI key never leaves the server, and chats are not saved. The installer is not code-signed yet, and the Android app is not on Google Play yet.</p></div>

<nav class="toc" aria-label="On this page"><b>On this page</b><ol>
<li><a href="#why">Why a new browser</a></li><li><a href="#built">What is inside</a></li>
<li><a href="#how">How it works, A to Z</a></li><li><a href="#trust">Privacy and trust</a></li>
<li><a href="#numbers">By the numbers</a></li><li><a href="#limits">Honest limits</a></li>
<li><a href="#stack">Technology</a></li><li><a href="#open">Download and source</a></li>
<li><a href="#cite">Cite this work</a></li><li><a href="#faq">FAQ</a></li></ol></nav>

<h2 id="why">Why a new browser</h2>
<p>Most people in Assam read the web in a browser whose menus, help and assistant speak English first. Adding AI usually means opening another app, pasting text and losing the page. Axomai Browser puts the assistant <strong>next to the page</strong>, in the language the reader writes in, and treats privacy as the default instead of a setting to hunt for.</p>
<p>It is also a practical test of Axom AI itself: a place where the assistant meets real pages, real languages and real limits.</p>

<h2 id="built">What is inside</h2>
{icon_cards([
    ("sparkle", "Axom AI chat", "Ask anything, or ask about the page: summarise it, explain it simply, pull out the key points. Answers stream in, in Assamese, Hindi, Bengali or English. Chats are not saved."),
    ("shield", "Privacy shield", "Blocks ad and tracker requests, adds fingerprint noise, upgrades to HTTPS, sends Global Privacy Control, hides cookie banners and offers private windows."),
    ("book", "Made for Assam", "Menus in four languages, five Assam-inspired themes, a New Tab page with Assamese and North-East headlines and weather for 35 towns and cities."),
    ("chart", "Tools for research", "Tab groups and search, split view, a reading list, sticky notes on pages, sessions, picture-in-picture, a screenshot editor and read-aloud."),
    ("lock", "Sync without a server", "Bookmarks and settings sync through a folder you already share, as one encrypted file. No Axomai server sees them."),
    ("phone", "Android app", "Tabs, bookmarks, history, the AI chat and the same five themes on a phone. Installed from an APK; not on Google Play yet."),
])}

<h2 id="how">How it works, from A to Z</h2>
<p>In seven steps:</p>
<ol class="flow">
{"".join(f"<li><b>{a}</b> {b}</li>" for a, b in HOW_STEPS)}
</ol>
<figure>{BROWSER_SVG}<figcaption>The two apps and the one server behind them. The server holds the AI key; the apps never do.</figcaption></figure>
<p>The same steps in detail:</p>

<h3>1. Two halves: a shell and an engine</h3>
<p>The desktop browser is written in Rust. A native window (the <code>tao</code> library) holds the interface, and each tab holds a web view (<code>wry</code>, on top of Microsoft Edge WebView2). WebView2 is the same Chromium engine that Edge uses, so web standards, video, logins and extensions behave as expected. Everything around the page, the tab strip, toolbar, New Tab, settings, history, bookmarks, downloads, passwords, sync and updates, is Axomai's own code (about 18,000 lines of Rust plus the web pages for the built-in screens).</p>
<p>Built-in pages talk to the shell through commands, and a command is accepted only when it comes from one of the browser's own pages or carries a per-run token. A website cannot drive the browser.</p>

<h3>2. Tabs</h3>
<p>Every tab has its own web view, so its state is kept. Tabs can be pinned, duplicated, reordered, put to sleep to free memory, grouped by colour, searched (Ctrl+Shift+A) and shown side by side in split view. Open tabs are restored with the session, and sessions can be saved by name.</p>

<h3>3. The privacy shield</h3>
<ul>
<li><strong>Blocking at the network layer.</strong> Each request is matched against a built-in list of <strong>106 advertising and 96 tracking domains</strong> before it is fetched, so blocked resources are never downloaded. The list is deliberately limited to hosts that exist only to serve ads or telemetry, so that blocking them does not break real sites.</li>
<li><strong>Fingerprint noise.</strong> The Privacy Guard adds small random noise to canvas, WebGL and audio readings, which makes the browser harder to identify.</li>
<li><strong>Signals and upgrades.</strong> Every request carries the Global Privacy Control signal; HTTPS-only mode upgrades sites; a tracking-prevention level can be chosen in Settings.</li>
<li><strong>Cookie banners and permissions.</strong> Common cookie pop-ups are hidden (hidden, not clicked "reject"). Camera, microphone and location permissions are asked per site and remembered per site.</li>
<li><strong>Private windows</strong> leave no history, notes or saved data behind.</li></ul>

<h3>4. Axom AI chat, step by step</h3>
<ol class="flow">
<li><b>You ask.</b> The AI button opens a chat. "Use this page to answer" is on by default; turn it off and only your text is sent.</li>
<li><b>The app sends one request</b> to <code>/v1/chat</code> on Axomai's server with the conversation, and the page's address, title and text if allowed. The app carries a random installation ID, not an account.</li>
<li><b>The proxy checks it.</b> At most 20 messages of 4,000 characters, page text cut to 12,000 characters, whole request under 96 KB, a valid app header and installation ID. Anything else is refused.</li>
<li><b>Limits apply.</b> Per UTC day: 30 messages per installation, 60 per network address and 500 for everyone together, and at most 6 per minute. A friendly message tells you when one is reached.</li>
<li><b>The proxy adds what the app must not hold:</b> the OpenAI key, a fixed system prompt and a fixed model. The app cannot choose any of them.</li>
<li><b>The answer streams back</b> word by word, at most 900 tokens, and the server forgets the text. Only the daily counters are kept.</li></ol>
<p>The system prompt tells the assistant to answer briefly in the user's language, to use the page when one is given, to say so when the answer is not on the page, and <strong>to treat page text as untrusted data and never follow instructions found inside it</strong>. That is a defence against a web page trying to hijack the assistant (prompt injection). It reduces the risk; no prompt can remove it.</p>

<h3>5. Passwords</h3>
<p>Saved passwords are encrypted with Windows' own data-protection key (DPAPI), tied to your Windows account and with extra data mixed in so other programs' blobs cannot be fed in. An optional setting asks for Windows Hello (face, fingerprint or PIN) before a password is copied or exported. Exports are plain text in a Chrome-compatible CSV, and the page warns first.</p>

<h3>6. Sync through your own folder</h3>
<p>There is no Axomai sync server. In Settings you choose a folder that OneDrive, Google Drive or Dropbox already shares between your PCs, and a passphrase of at least 8 characters. The browser writes one file there, encrypted with <strong>AES-256-GCM</strong> using a key derived from the passphrase with <strong>PBKDF2-SHA256 (200,000 rounds)</strong>. The passphrase is never stored, and the folder service sees only ciphertext. Sync adds and combines; deleting something on one PC does not delete it on the others.</p>

<h3>7. Updates you can check</h3>
<p>The browser reads <code>release.json</code> from Axomai's server about once a day. If a newer version exists and you press <em>Update now</em>, it downloads the installer (at most 300 MB, only from a trusted host: Axomai's server or GitHub), computes its <strong>SHA-256</strong>, compares it with the published <code>.sha256</code> file and <strong>refuses to install if they differ</strong>. It then closes itself, lets the installer replace the files and restarts with your tabs back.</p>

<h3>8. The New Tab page</h3>
<p>Headlines come from the free RSS feeds of Assamese and North-East newspapers and Google News, with Assam first, with pictures where there are any, and cached for 15 minutes. Weather is shown for 35 towns and cities. Quick tools (QR code, image compression, translator) sit on the same page.</p>

<h3>9. The Android app</h3>
<p>The Android app is a separate Flutter project: tabs, bookmarks, history, the AI chat panel and the same five themes. It uses the same chat proxy and the same limits. It is installed from an APK of about 55 MB from the download page, with a published SHA-256 to compare, and it needs Android 7.0 or newer.</p>

<h3>10. The website and its admin panel</h3>
<p>The download page is generated by a small Python program, with the fact table, FAQ and structured data written for search and answer engines, an <code>llms.txt</code> for AI assistants and a robots.txt that welcomes crawlers. The owner edits its text, menu and footer in a password-protected admin panel with preview, publish and backups. A separate Node service is the chat proxy; both run as small systemd services on the same Lightsail server as the other Axom AI sites, behind Cloudflare.</p>

<h2 id="trust">Privacy and trust</h2>
{icon_cards([
    ("lock", "No AI key in the app", "The OpenAI key lives only in a file on the server that the web server cannot serve. Nothing the app sends can change the key, the model or the prompt."),
    ("shield", "Chats are not saved", "Neither the browser nor the server stores chat text. The server keeps only counters for the daily limits."),
    ("book", "Checked updates", "An update is installed only if its SHA-256 matches the published checksum, and only from a trusted host."),
    ("users", "You hold the keys", "Passwords are tied to your Windows account, sync is encrypted with your passphrase, and nothing needs an Axomai account."),
])}
<div class="note"><p><strong>What does leave your computer.</strong> When you use the AI chat, what you type, and the page text if you leave that switch on, goes to OpenAI through Axomai's server. The chat box says so. Do not use it on pages with private information you do not want shared with an AI service.</p></div>

<h2 id="numbers">By the numbers</h2>
<div class="table-wrap"><table><caption>From the source code, the release files and the server</caption>
<thead><tr><th>Measure</th><th class="num">Value</th></tr></thead><tbody>
<tr><td>Windows version</td><td class="num">4.1.2</td></tr>
<tr><td>Android version</td><td class="num">1.0.0</td></tr>
<tr><td>Windows installer size</td><td class="num">about 28 MB</td></tr>
<tr><td>Android APK size</td><td class="num">about 55 MB</td></tr>
<tr><td>Rust code of the desktop browser</td><td class="num">about 18,000 lines</td></tr>
<tr><td>Automated tests in the desktop code</td><td class="num">206</td></tr>
<tr><td>Ad and tracker domains in the shield</td><td class="num">202 (106 + 96)</td></tr>
<tr><td>Interface languages</td><td class="num">4</td></tr>
<tr><td>Heritage themes</td><td class="num">5</td></tr>
<tr><td>Weather places on the New Tab page</td><td class="num">35</td></tr>
<tr><td>Free AI messages per installation per day</td><td class="num">30</td></tr></tbody></table></div>

<h3>Release history</h3>
<div class="table-wrap"><table><caption>The main versions of the Windows browser</caption>
<thead><tr><th>Version</th><th>Date</th><th>What it added</th></tr></thead><tbody>
<tr><td>2.0</td><td>4 Oct 2026</td><td>Tab groups and search, reading list, notes on pages, dark mode for sites, cookie-banner hiding, 35 weather cities.</td></tr>
<tr><td>3.0</td><td>5 Oct 2026</td><td>Picture-in-picture, translate, read aloud, sessions, backup, voice commands, screenshot editor, search shortcuts.</td></tr>
<tr><td>4.0</td><td>5 Oct 2026</td><td>Chrome extensions (unpacked), installer and checked updates, encrypted folder sync, proxy setting, Windows Hello for passwords.</td></tr>
<tr><td>4.1</td><td>5 Oct 2026</td><td>Axom AI chat with its own proxy server, a download page and update file on Axomai's server, no console window, the Axomai icon, a phone-friendly landing page.</td></tr></tbody></table></div>
<p>The changelog also records what was <em>not</em> tested: the Windows Hello prompt (no hardware on the test PC), the file pickers, voice commands with a live microphone (tested with synthesised speech) and the YouTube and cookie-banner scripts against the live sites (tested on local pages). We list that here because a changelog that only lists successes is not a measurement.</p>

<h2 id="limits">Honest limits</h2>
{icon_cards([
    ("shield", "Not code-signed yet", "Windows SmartScreen shows a warning on first run, and the APK is not on Google Play, so Android shows an unknown-app message. Compare the SHA-256 on the download page with your file."),
    ("target", "A small blocklist", "202 domains is far smaller than the filter lists of dedicated blockers, by design. It blocks the biggest ad and tracking hosts and breaks little, but it will miss many. We have not compared it with other blockers."),
    ("bolt", "A fair-use limit, not a wall", "The 30-a-day limit counts a random installation ID plus the network address. It stops casual overuse and protects the bill; it is not strong authentication."),
    ("sparkle", "AI needs the internet", "The chat sends your question and optionally the page to OpenAI through our server. There is no offline mode."),
    ("code", "Windows only on the desktop", "No macOS, Linux or iPhone version yet. Extensions load only unpacked; the Chrome Web Store cannot install them. It is not a VPN: the proxy setting uses a proxy you provide."),
    ("clock", "Not benchmarked", "We have not measured speed or memory against Chrome or Edge, and we do not publish download or usage counts. Some page tweaks, such as the YouTube ad skipper, depend on a site's current markup and can break."),
], "cards warn-cards")}
<p>One more point to avoid confusion: the source repository also contains an <strong>experimental engine written from scratch</strong>. It is not part of the browser you download; the shipped browser uses WebView2 for web pages. Documents in that repository that describe a full multi-process engine describe that experiment and a plan, not the installed browser.</p>

<h2 id="stack">Technology</h2>
<div class="table-wrap"><table><caption>What it is built with</caption>
<thead><tr><th>Part</th><th>Tool</th></tr></thead><tbody>
<tr><td>Desktop shell</td><td>Rust 1.88, tao (windows), wry (web view), wgpu graphics layer</td></tr>
<tr><td>Web pages</td><td>Microsoft Edge WebView2 (Chromium)</td></tr>
<tr><td>Built-in pages</td><td>HTML, CSS and JavaScript in the app (New Tab, Settings, History, Bookmarks, Passwords)</td></tr>
<tr><td>Local data</td><td>SQLite (rusqlite), JSON files</td></tr>
<tr><td>Passwords, sync, updates</td><td>Windows DPAPI; AES-256-GCM with PBKDF2-SHA256; SHA-256 (sha2)</td></tr>
<tr><td>Installer</td><td>A small C# setup program built with the compiler that ships with Windows; PowerShell scripts</td></tr>
<tr><td>Chat proxy</td><td>Node.js on 127.0.0.1, streaming server-sent events, OpenAI chat completions</td></tr>
<tr><td>Website</td><td>Python page generator, static HTML with JSON-LD; Node admin panel</td></tr>
<tr><td>Android app</td><td>Flutter</td></tr>
<tr><td>Hosting</td><td>AWS Lightsail, nginx, Cloudflare, systemd</td></tr></tbody></table></div>

<h2 id="open">Download and source</h2>
{link_cards([
    ("bolt", "Download Axomai Browser", "Windows 10 and 11 installer and the Android APK, with checksums.", SITE, "axomai-browser.aiaxom.co.in"),
    ("code", "Source code", "The Windows browser, chat proxy, site generator and installer scripts. MIT licence.", GITHUB, "github.com/Samarjitkashyp/axomai-browser"),
    ("book", "Changelog", "Every version from 2.0 to 4.1.2, with what was tested and what was not.", GITHUB + "/blob/main/CHANGELOG.md", "Read the changelog"),
    ("shield", "Axom AI", "The AI platform behind the assistant: chat in Assamese, tools and research.", "https://aiaxom.co.in/", "aiaxom.co.in"),
])}

<h2 id="cite">Cite this work</h2>
<pre><code>@techreport{{axomai2026browser,
  title  = {{Axomai Browser: a free AI browser made in Assam}},
  author = {{Kashyap, Samarjit}},
  institution = {{Axom AI}},
  year   = {{2026}},
  url    = {{{BASE}{url}}}
}}</code></pre>

<h2 id="faq">Frequently asked questions</h2>
{faq_html(FAQ)}
</div></div>
<section class="wrap"><div class="cta-band"><div><p class="cta-h">Try the free AI browser made in Assam</p><p>Download Axomai Browser for Windows or Android and ask Axom AI about the next page you read.</p></div>
<div class="cta"><a class="btn primary" href="{SITE}">Download</a><a class="btn" href="{GITHUB}">View code on GitHub</a></div></div></section>
</article>'''
    return p, body
