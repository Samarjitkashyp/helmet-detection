"""Research report: the Axom AI crawler bot (websites and scanned documents -> clean text -> questions -> Axom AI chat)."""
from diagram import CRAWLER_SVG
from lib import BASE, MODIFIED, article_schema, e, faq_schema, hero, stat
from pages_hd import faq_html, icon_cards, link_cards

BOT = "/research/axom-ai-crawler-bot/"
MINUTES = 24

FAQ = [
    ("What is a web crawler bot?",
     "A crawler bot is a program that visits the pages of a website one after another, follows its links and saves what it finds. Axom AI's crawler bot saves the readable text of each page, cleans it and prepares it as knowledge for the Axom AI chat."),
    ("What does the Axom AI crawler bot do?",
     "It reads a website (or a scanned document), removes menus, buttons and repeated blocks, cuts the text into short passages, asks an AI model to write one natural question for each passage, and sends passages and questions to the Axom AI chat so it can answer visitors from the site's own words."),
    ("Is the crawler bot public?",
     "No. The console is a private admin tool: only Axom AI staff with a login can start crawls, upload documents and see the results. This page describes how it works and what it has produced. The code is not published."),
    ("Which languages does it work with?",
     "Assamese, Hindi, Bengali and English are the languages it was built and tested for. The questions are written in the language of each passage, and the document reader transcribes text in its original script without translating it."),
    ("Can it read websites that need JavaScript?",
     "Yes. A switch turns on a headless Chromium browser (Playwright) that renders the page before reading it. It is slower, so it is used only when a site needs it. For client-rendered Next.js sites it can also read the page's own data, and for WordPress sites it can use the site's API instead of crawling pages."),
    ("How does it avoid reading the same page again?",
     "Every page's cleaned text gets a SHA-256 fingerprint stored in a catalogue. On the next crawl a page with the same fingerprint is marked unchanged and skipped, so only new and changed pages are processed. In our crawls, between about a third and all of the pages of a re-crawl were skipped."),
    ("How are the questions made?",
     "Each page is cut into passages of about 160 words (never more than 230). An AI model (Google Gemini, with several fallback models) writes one question per passage, in the passage's own language, using only facts from the passage. The chat later matches a visitor's question to these stored questions."),
    ("Can it read scanned PDFs and photos?",
     "Yes. Pictures and PDFs are read by Gemini vision, then OpenAI vision if Gemini is not available, then Tesseract as a free offline fallback. A PDF page that already has good text is read exactly with pdftotext. An administrator checks and corrects every document before anything reaches the chat."),
    ("Does it respect robots.txt?",
     "Not automatically yet. The crawler waits a set time between requests (1 second by default) and limits pages and depth, but it does not read robots.txt. Use it only on websites you own or have permission to collect, and we plan to add a robots.txt check."),
    ("How often is the knowledge refreshed?",
     "Websites on the auto-sync list are crawled again every 10 days, one site at a time (up to 100 pages, three links deep, with a 2-second pause). Admins can also start a crawl by hand at any time, up to 5,000 pages."),
    ("How accurate are the answers?",
     "We have not yet measured how often the chat answers correctly from this knowledge. This report measures the crawler's own steps: how much it reads, how much it skips and how much junk it removes. An answer-accuracy test is still to be done."),
    ("Is the data safe?",
     "The console sits behind a login with a three-strike lock (24 hours), sees traffic only through Cloudflare, and keeps an audit log. Uploaded documents are not sent to the chat until an administrator approves them. Keep to the privacy rules that apply to the content you collect."),
]

HOW_STEPS = [
    ("Pick the seed.", "An admin enters a website address and limits: pages (up to 5,000), depth, delay, JavaScript on or off."),
    ("Fetch.", "Plain HTTP for most pages; a headless Chromium browser for JavaScript sites; the WordPress API when a site has one."),
    ("Extract.", "The title, description and main text of each page, plus its links and documents."),
    ("Check for change.", "A fingerprint of the text decides whether the page is new, changed or unchanged."),
    ("Clean.", "Menus, buttons, repeated cards, copies and block pages are removed, with safety checks."),
    ("Passages and questions.", "The text is cut into passages and an AI writes one question for each."),
    ("Send.", "Passages and questions go to the Axom AI chat in batches, with retries."),
    ("Repeat.", "The scheduler crawls the site again every 10 days and only changed pages are redone."),
]


def overview_bot():
    url = BOT
    p = dict(path=url, title="Axom AI Crawler Bot: Website to Chatbot Knowledge, Explained",
             og_title="Axom AI Crawler Bot: websites and documents turned into answers",
             description="How Axom AI's crawler bot turns websites and scanned documents in Assamese, Hindi and English into clean text and questions for its chat, with real numbers.",
             keywords=["web crawler bot", "website crawler for chatbot", "RAG knowledge base", "Assamese AI chatbot", "PDF OCR Assamese", "Gemini vision OCR",
                       "crawler boilerplate removal", "AI question generation", "Axom AI crawler bot", "Axom AI"],
             crumbs=[("Home", "/"), ("Research", "/research/"), ("Crawler bot", url)], article=True,
             image=f"{BASE}/research/assets/og-crawler-bot.jpg",
             image_alt="Axom AI crawler bot: website, clean text, questions, Axom AI chat")
    p["schemas"] = [
        article_schema(url, "Axom AI Crawler Bot: how websites and scanned documents become answers for the Axom AI chat", p["description"],
                       image=p["image"], keywords=p["keywords"],
                       about=["Web crawler", "Retrieval-augmented generation", "Optical character recognition", "Assamese language", "Chatbot"],
                       cites=[("Playwright", "https://playwright.dev/"), ("Tesseract OCR", "https://github.com/tesseract-ocr/tesseract"),
                              ("Trafilatura", "https://github.com/adbar/trafilatura"), ("ChromaDB", "https://www.trychroma.com/"),
                              ("Google Gemini API", "https://ai.google.dev/")]),
        faq_schema(FAQ)]
    body = f'''
<article>
{hero("Official Axom AI Research · Knowledge for chat",
      'Axom AI Crawler Bot: <span class="grad">websites and documents turned into answers</span>',
      "A private tool that reads a website or a scanned document, throws away the clutter, and prepares clean passages and questions so the Axom AI chat can answer in Assamese, Hindi or English.",
      chips=[("book", "Assamese, Hindi, English"), ("code", "Crawls and scans"), ("shield", "Admin approval"), ("bolt", "Skips unchanged pages"), ("clock", "Auto-sync")])}

<section class="wrap showcase">
<div class="stats" role="list">
{stat("bolt", "8.1 million", "words read in 43 crawl runs, from about 18,100 pages")}
{stat("users", "15", "websites kept up to date automatically, every 10 days")}
{stat("target", "17,596", "pages fingerprinted so unchanged ones are never read twice")}
{stat("shield", "3", "ways to read a scan: Gemini, OpenAI vision, then Tesseract")}
</div>
</section>

<div class="wrap"><div class="read" style="margin:0">
<div class="answer"><h2>Quick answer</h2>
<p><strong>The Axom AI crawler bot is a private admin tool that turns websites and scanned documents into clean, question-ready knowledge for the Axom AI chat.</strong> It fetches pages (with a real browser when needed), extracts the main text, skips pages that have not changed, removes menus and repeated blocks with safety checks, cuts the text into passages of about 160 words and asks an AI model to write one question for each. Scans are read by vision AI and must be approved by an administrator first. It has read about 8.1 million words from 15 websites so far.</p></div>

<nav class="toc" aria-label="On this page"><b>On this page</b><ol>
<li><a href="#why">Why it exists</a></li><li><a href="#built">What it does</a></li>
<li><a href="#how">How it works, A to Z</a></li><li><a href="#documents">Scanned documents</a></li>
<li><a href="#safety">Safety and control</a></li><li><a href="#results">What we measured</a></li>
<li><a href="#limits">Honest limits</a></li><li><a href="#stack">Technology</a></li>
<li><a href="#cite">Cite this work</a></li><li><a href="#faq">FAQ</a></li></ol></nav>

<h2 id="why">Why it exists</h2>
<p>A chat assistant is only as good as what it knows. For a business website, the best source is the website itself: its services, prices, places and contact details. But a web page is mostly clutter: menus, buttons, footers, cards that repeat on every page. Feeding that straight to a chat gives poor answers.</p>
<p>Much of the content that matters in Assam is also in <strong>Assamese and Hindi</strong>, in news sites, government portals and old scanned textbooks whose text cannot be copied. The crawler bot exists to turn all of this into <strong>clean passages with a natural question for each</strong>, so the Axom AI chat can find the right passage when a visitor asks.</p>

<h2 id="built">What it does</h2>
{icon_cards([
    ("code", "Crawl a website", "Starts from one address and follows links in order, up to 5,000 pages, with a delay between requests. Handles plain pages, JavaScript sites and WordPress."),
    ("sparkle", "Clean the text", "Drops copies and junk pages, removes menus, buttons and repeated lines, and keeps the page title, prices, phone numbers and e-mail addresses."),
    ("book", "Write the questions", "Cuts each page into passages and has an AI write one question per passage, in the passage's own language."),
    ("phone", "Read scans and PDFs", "Photos and PDFs in any language are transcribed by vision AI, checked by an administrator, then added to the chat."),
    ("clock", "Stay up to date", "Every 10 days each listed site is crawled again; only new and changed pages are processed."),
    ("chart", "Test search and answers", "A built-in search over the stored text (a vector index) and a test chat, to try a crawl before it goes live."),
])}

<h2 id="how">How it works, from A to Z</h2>
<p>In eight steps:</p>
<ol class="flow">
{"".join(f"<li><b>{a}</b> {b}</li>" for a, b in HOW_STEPS)}
</ol>
<figure>{CRAWLER_SVG}<figcaption>The path from a website or a scan to the Axom AI chat. Scans take the lower road and wait for an administrator.</figcaption></figure>
<p>The same steps in detail:</p>

<h3>1. The queue of pages</h3>
<p>The crawler starts at the seed address and visits pages breadth first: the seed, then every page it links to, then theirs. Before a page is queued its address is tidied (tracking parameters such as <code>utm_source</code> and <code>fbclid</code> are removed, so one page is not read twice under two addresses) and it must be on the same website (sibling subdomains only if the admin allows them). Pictures, videos and archives are never fetched. The admin sets the page limit (1 to 5,000, 25 by default), the depth (3 by default) and the pause between requests (1 second by default, up to 10).</p>

<h3>2. Fetching a page</h3>
<ul>
<li><strong>Plain HTTP</strong> (HTTPX, 15-second timeout) is the default and the fastest.</li>
<li><strong>A real browser.</strong> When a site draws its text with JavaScript, the admin switches on rendering: headless Chromium (Playwright) opens the page, waits for it to load and reads the finished page. It is slower, so it is a switch, not the default.</li>
<li><strong>The site's own API.</strong> For WordPress sites the bot first asks the site's API (<code>/wp-json/wp/v2/</code>) for every page and post. That returns the article text without menus or footers, newest first, 100 at a time. It skips internal types (menus, templates, form plugins, shop plumbing) and login or account pages, and falls back to normal crawling if fewer than three real pages come back.</li></ul>

<h3>3. Extracting the text</h3>
<p>For each page the bot reads the title, description and canonical address, then picks the main text of the page with Trafilatura (a library that finds the article and leaves out menus), with a fallback that looks at the usual content containers. Some modern sites (Next.js) send an almost empty page and fill it in the browser; for those the bot reads the readable strings from the page's own embedded data. It also records every link, and tells web pages apart from documents such as PDFs.</p>

<h3>4. Noticing what changed</h3>
<p>The cleaned text of every page is reduced to a SHA-256 fingerprint and stored in a catalogue. On a later crawl, a page with the same fingerprint is marked <em>unchanged</em> and skipped; a different fingerprint marks it <em>updated</em>; an address never seen is <em>new</em>. An admin can force a full re-crawl. This keeps repeat crawls cheap and keeps old answers from being replaced by identical ones.</p>

<h3>5. Cleaning</h3>
<p>The finished crawl is cleaned by a rule set, with the untouched crawl always archived first so nothing is ever lost. The rules:</p>
<ul>
<li>drop pages that are exact copies of an earlier page, or whose address is a known junk pattern (tag lists, language home pages, login pages);</li>
<li>drop <strong>block pages</strong>: a firewall's or search engine's "Access Denied" or "unusual traffic" message saved instead of the page;</li>
<li>remove lines that repeat on many pages (menus, cards, widgets), but only if the line is on at least a set share of the pages and on at least three of them; a line that is on one page only is never removed;</li>
<li>remove button lines such as "Read more", "Share" or "Post a comment" (in English, Assamese and Hindi) when the whole line is one of them;</li>
<li>always keep the page title, the first lines of a page, "Day 1:" labels, long paragraphs and any line with a price, phone number or e-mail address.</li></ul>
<p><strong>Safety gates:</strong> the bot gives up and keeps the pages untouched if a must-keep phrase of the site would be lost, if more than 60% of the words would go, or if anything fails. A report tool can show a dry run on a finished crawl first, without changing a file.</p>

<h3>6. Passages and one question each</h3>
<p>The chat answers a visitor by matching the visitor's question against stored questions. A whole page stored under its title only matches broad questions. So every page is cut into <strong>passages of about 160 words (at most 230)</strong>, and an AI model writes <strong>one natural question per passage</strong>, 6 to 20 words, in the passage's language, adding no fact that is not in the passage. Each passage is stored as its own question and answer pair (the address of the page with <code>#c1</code>, <code>#c2</code> added), so "what does the SEO service include?" finds the exact paragraph.</p>
<ul>
<li>Passages go to the AI in batches of 8. Several Gemini models are tried in turn: when one is gone or out of quota, the next is used.</li>
<li>If no model works, the page is imported the old way, with a simple question made from the page name, so a crawl is never lost.</li>
<li>The rows of a page that changed are replaced; the old rows are saved to a backup file first. Pages that did not change are left alone.</li>
<li>One crawl makes at most 1,500 passages by default.</li></ul>

<h3>7. Delivery to the chat</h3>
<p>The pages go to the Axom AI chat in batches of 200, each with three retries. A wrong token stops the whole import at once, since retrying cannot help. Before this was added a whole crawl went in one request, and a crawl of a few thousand pages could time out so that nothing arrived. Now a failure costs one batch at most.</p>

<h3>8. The schedule</h3>
<p>Websites on the auto-sync list are crawled again every 10 days. The scheduler wakes every hour, runs one crawl at a time (100 pages, depth 3, 2-second pause) and relies on the fingerprints, so a site that did not change costs almost nothing.</p>

<h3>The test bench: search and answer</h3>
<p>The console also holds a small retrieval-augmented generation (RAG) pipeline for trying a crawl before it goes live: text is cut into pieces of 600 characters with overlap, stored in a ChromaDB vector index using a small CPU-friendly embedding model (all-MiniLM-L6-v2), and the five closest pieces are given to a language model (Gemini, a local Ollama model, or a simple built-in summary) with an instruction to answer only from them and to cite the pages.</p>

<h2 id="documents">Scanned documents: photos and PDFs to text</h2>
<p>Many useful Assamese and Hindi documents exist only as photos or old PDFs. The bot has an <strong>Upload and Scan Documents</strong> section for them:</p>
<ol class="flow">
<li><b>Upload.</b> PNG, JPG or WEBP pictures (up to 20 MB each), or one PDF (up to 150 MB and 600 pages), sent in 8 MB pieces so a weak connection or Cloudflare's size limit does not stop it. The real file type is checked, not the file name.</li>
<li><b>Read.</b> Each page picture goes to Gemini vision; if Gemini has no quota, to OpenAI vision; if that fails too, to Tesseract (Assamese, Hindi, English), whose result is always flagged for review. Up to 500 pages a day use the paid readers; after that only Tesseract is used.</li>
<li><b>PDF pages with text.</b> A page whose own text layer is readable is read exactly with pdftotext. Old-font PDFs (whose text copies out as symbols), pages with big pictures and pages that only hold a rotated watermark are read as pictures instead. Blank pages go to Tesseract first, so no paid page is spent. Running headers and bare page numbers are removed.</li>
<li><b>Check.</b> The administrator sees the page picture beside its text in the Axom AI admin panel (Document Verify), corrects it, and can ask for the whole document to be read again as pictures.</li>
<li><b>Approve.</b> Only then is the document saved like a crawl and sent to the chat. Nothing reaches the chat before approval.</li></ol>

<h2 id="safety">Safety and control</h2>
{icon_cards([
    ("lock", "A guarded sign-in", "Three wrong tries lock the user name and the address for 24 hours. The lock is shared with the Axom AI admin login, so it holds on both. Every sign-in event is written to the admin audit log."),
    ("shield", "Only through Cloudflare", "The server accepts traffic from Cloudflare only, over TLS 1.2 or 1.3. The console is for authorised Axom AI staff; nothing in it is public."),
    ("users", "A human in the loop", "Scanned documents are read by AI but approved by an administrator. Approving, editing and deleting documents is possible only in the admin panel."),
    ("book", "Nothing is lost", "Every crawl is archived exactly as fetched before cleaning. Replaced rows are backed up. Old backups are removed by an automatic clean-up that can be off, a dry run, or on."),
])}

<h2 id="results">What we measured</h2>
<p>The numbers below come from the bot's own saved crawls and reports. Site names are left out on purpose.</p>
<div class="table-wrap"><table><caption>Use so far, from the saved crawls</caption>
<thead><tr><th>Measure</th><th class="num">Value</th></tr></thead><tbody>
<tr><td>Saved crawl runs</td><td class="num">43</td></tr>
<tr><td>Pages saved</td><td class="num">about 18,100</td></tr>
<tr><td>Words read</td><td class="num">about 8.1 million</td></tr>
<tr><td>Websites (on the auto-sync list)</td><td class="num">15</td></tr>
<tr><td>Page addresses with a stored fingerprint</td><td class="num">17,596</td></tr>
<tr><td>Largest single crawl</td><td class="num">5,000 pages</td></tr>
<tr><td>Automated tests in the code</td><td class="num">more than 60</td></tr></tbody></table></div>

<h3>Re-crawls skip what did not change</h3>
<div class="table-wrap"><table><caption>Second crawls of three kinds of site</caption>
<thead><tr><th>Site</th><th class="num">New</th><th class="num">Updated</th><th class="num">Skipped (unchanged)</th></tr></thead><tbody>
<tr><td>A state tourism site (1,000-page limit)</td><td class="num">630</td><td class="num">73</td><td class="num good">297</td></tr>
<tr><td>A regional news site (500-page limit)</td><td class="num">40</td><td class="num">167</td><td class="num good">293</td></tr>
<tr><td>A small travel company's site</td><td class="num">0</td><td class="num">0</td><td class="num good">47</td></tr></tbody></table></div>
<p>Skipped pages are not read, cleaned or sent again. On a site that never changes, a re-crawl does almost no work.</p>

<h3>How much of a crawl is clutter</h3>
<div class="table-wrap"><table><caption>Dry-run cleaning reports (nothing was changed when these were made)</caption>
<thead><tr><th>Crawl</th><th class="num">Pages</th><th class="num">Pages kept</th><th class="num">Words before</th><th class="num">Words after</th></tr></thead><tbody>
<tr><td>A national news site</td><td class="num">5,000</td><td class="num">731</td><td class="num">5,537,645</td><td class="num">443,389 (8%)</td></tr>
<tr><td>A small travel company's site</td><td class="num">55</td><td class="num">47</td><td class="num">43,150</td><td class="num">30,719 (71%)</td></tr></tbody></table></div>
<div class="compare" role="img" aria-label="Share of words kept after cleaning: 8 percent for a large news site, 71 percent for a small business site">
<p class="cmp-title">Share of words kept after cleaning</p>
<div class="cmp-row"><span>Large news site</span><div class="bar-track"><div class="bar-fill warn" style="width:8%"></div></div><b>8%</b></div>
<div class="cmp-row"><span>Small business site</span><div class="bar-track"><div class="bar-fill" style="width:71%"></div></div><b>71%</b></div></div>
<p>A news site repeats its menus and "related story" cards on thousands of pages, so most of the words were clutter: 4,269 of 5,000 pages were exact copies or junk addresses such as tag lists and home pages of other languages. A small business site is mostly real content, so 71% of its words stay. The safety checks of both reports passed: no line found on one page only would have been removed, and none of the 17 must-keep phrases of the small site was lost. The report also flagged 342 pages of the news crawl for a human look; cleaning is a tool with a check, not a promise.</p>

<h2 id="limits">Honest limits</h2>
{icon_cards([
    ("shield", "No robots.txt check yet", "The bot waits between requests but does not read a site's robots.txt. Use it only on websites you own or have permission to collect. A check is planned."),
    ("target", "Answer quality is not measured yet", "This report measures how the bot reads and cleans. How often the chat then answers correctly from this knowledge has not been tested; that test is still to be done."),
    ("bolt", "Questions depend on an AI service", "Question writing relies on Gemini models and their quotas. When none works, a plain fallback question is used, which matches fewer visitor questions."),
    ("clock", "Slow for JavaScript sites", "Rendering opens a browser for each page, so it is much slower than plain fetching. It is used only when a site needs it."),
    ("book", "Assamese in pictures", "Vision AI reads Assamese well, but Tesseract is weaker, which is why its pages are always flagged for review. Handwriting and rough scans need a human check."),
    ("moon", "Fresh to within 10 days", "Automatic crawls run every 10 days, so a changed page can take that long to reach the chat unless an admin starts a crawl."),
], "cards warn-cards")}
<p>It is also a <strong>private tool</strong>: its code is not published, and a crawl is limited to 5,000 pages.</p>

<h2 id="stack">Technology</h2>
<div class="table-wrap"><table><caption>What it is built with</caption>
<thead><tr><th>Part</th><th>Tool</th></tr></thead><tbody>
<tr><td>Service</td><td>FastAPI on Uvicorn, behind nginx and Cloudflare</td></tr>
<tr><td>Fetching</td><td>HTTPX; Playwright (headless Chromium) for JavaScript sites; WordPress REST API</td></tr>
<tr><td>Reading pages</td><td>BeautifulSoup, lxml, Trafilatura, Next.js page data</td></tr>
<tr><td>Change detection</td><td>SHA-256 fingerprints in a URL catalogue</td></tr>
<tr><td>Questions</td><td>Google Gemini models, with fallbacks</td></tr>
<tr><td>Document reading</td><td>Gemini vision, OpenAI vision, Tesseract (asm, hin, eng), poppler (pdftotext, pdfimages)</td></tr>
<tr><td>Test search</td><td>ChromaDB with the all-MiniLM-L6-v2 embedder; Gemini or Ollama for answers</td></tr>
<tr><td>Storage</td><td>JSON files for crawls and raw archives; PostgreSQL for the chat's questions and the login lock</td></tr>
<tr><td>Hosting</td><td>AWS Lightsail with nginx, Cloudflare and systemd</td></tr></tbody></table></div>

<h2 id="cite">Cite this work</h2>
<pre><code>@techreport{{axomai2026crawler,
  title  = {{Axom AI Crawler Bot: websites and scanned documents turned into answers}},
  author = {{Kashyap, Samarjit}},
  institution = {{Axom AI}},
  year   = {{2026}},
  url    = {{{BASE}{url}}}
}}</code></pre>

<h2 id="faq">Frequently asked questions</h2>
{faq_html(FAQ)}
</div></div>
<section class="wrap"><div class="cta-band"><div><p class="cta-h">A chat that knows your website</p><p>Want the Axom AI chat to answer from your own website or documents, in Assamese, Hindi or English? Talk to us.</p></div>
<div class="cta"><a class="btn primary" href="/contact">Contact Axom AI</a><a class="btn" href="https://chat.aiaxom.co.in/">Open Axom AI Chat</a></div></div></section>
</article>'''
    return p, body
