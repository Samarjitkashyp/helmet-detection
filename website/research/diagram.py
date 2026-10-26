"""Pipeline diagram as inline SVG. Colours come from the page's CSS classes, so it is right in both light and dark themes."""

PIPELINE_SVG = '''<div class="diagram"><svg viewBox="0 0 940 270" role="img" aria-labelledby="flowT flowD" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">
<title id="flowT">Helmet detection pipeline</title>
<desc id="flowD">A camera or phone sends frames to a worker that finds motorcycles, heads and helmet verdicts, tracks each rider and confirms once. The worker sends the alert to the server, which notifies Telegram, the admin dashboard and the Android app.</desc>
<defs><marker id="ah" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" class="arrow-head"/></marker></defs>
<g font-size="15" text-anchor="middle">
<rect class="box-em" x="10" y="95" width="140" height="80" rx="16" stroke-width="1.5"/>
<text x="80" y="128" font-weight="800">Camera</text><text class="sub" x="80" y="150" font-size="13">or phone video</text>

<rect class="box" x="205" y="22" width="270" height="226" rx="18" stroke-width="1.5"/>
<text class="accent" x="340" y="52">Worker (PC or server)</text>
<text x="340" y="86">1 &#183; find motorcycles</text><text x="340" y="115">2 &#183; find heads (frame + crops)</text>
<text x="340" y="144">3 &#183; helmet or no helmet</text><text x="340" y="173">4 &#183; track every rider</text><text x="340" y="202">5 &#183; confirm, alert once</text>
<text class="sub" x="340" y="232" font-size="12.5">YOLOv8 &#183; classifier &#183; tracker</text>

<rect class="box-em" x="530" y="95" width="150" height="80" rx="16" stroke-width="1.5"/>
<text x="605" y="128" font-weight="800">Server</text><text class="sub" x="605" y="150" font-size="13">API + database</text>

<rect class="box" x="735" y="12" width="195" height="62" rx="14" stroke-width="1.5"/><text x="832" y="49">Telegram message</text>
<rect class="box" x="735" y="104" width="195" height="62" rx="14" stroke-width="1.5"/><text x="832" y="141">Admin dashboard</text>
<rect class="box" x="735" y="196" width="195" height="62" rx="14" stroke-width="1.5"/><text x="832" y="233">Android app Alerts</text>
</g>
<g class="link" stroke-width="2.4" fill="none" marker-end="url(#ah)"><path d="M150 135 H201"/><path d="M475 135 H526"/><path d="M680 128 C708 128 708 43 731 43"/><path d="M680 135 H731"/><path d="M680 142 C708 142 708 227 731 227"/></g>
</svg></div>'''


CRAWLER_SVG = '''<div class="diagram"><svg viewBox="0 0 940 300" role="img" aria-labelledby="crT crD" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">
<title id="crT">Crawler bot pipeline</title>
<desc id="crD">A website is fetched, its text extracted, checked for changes, cleaned and cut into passages that each get one AI-written question. Scanned documents are read by vision AI and approved by an administrator first. Both end in the Axom AI chat knowledge base.</desc>
<defs><marker id="ah2" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" class="arrow-head"/></marker></defs>
<g font-size="15" text-anchor="middle">
<rect class="box-em" x="10" y="40" width="140" height="80" rx="16" stroke-width="1.5"/>
<text x="80" y="76" font-weight="800">Website</text><text class="sub" x="80" y="98" font-size="13">pages, API, JavaScript</text>
<rect class="box-em" x="10" y="180" width="140" height="80" rx="16" stroke-width="1.5"/>
<text x="80" y="216" font-weight="800">Scans and PDFs</text><text class="sub" x="80" y="238" font-size="13">photos, any language</text>

<rect class="box" x="205" y="14" width="400" height="140" rx="18" stroke-width="1.5"/>
<text class="accent" x="405" y="42">Crawler</text>
<text x="300" y="78">fetch</text><text x="405" y="78">extract</text><text x="510" y="78">change check</text>
<text x="300" y="116">clean</text><text x="405" y="116">passages</text><text x="510" y="116">1 question each</text>
<text class="sub" x="405" y="142" font-size="12.5">HTTPX &#183; Playwright &#183; WordPress API &#183; Gemini</text>

<rect class="box" x="205" y="180" width="400" height="80" rx="18" stroke-width="1.5"/>
<text class="accent" x="405" y="208">Document reader</text>
<text x="405" y="238">Gemini vision &#8594; OpenAI vision &#8594; Tesseract</text>

<rect class="box" x="650" y="180" width="120" height="80" rx="16" stroke-width="1.5"/>
<text x="710" y="215" font-weight="800">Admin</text><text class="sub" x="710" y="238" font-size="13">checks, approves</text>

<rect class="box-em" x="800" y="80" width="130" height="100" rx="16" stroke-width="1.5"/>
<text x="865" y="122" font-weight="800">Axom AI</text><text x="865" y="144" font-weight="800">chat</text><text class="sub" x="865" y="166" font-size="13">knowledge base</text>
</g>
<g class="link" stroke-width="2.4" fill="none" marker-end="url(#ah2)"><path d="M150 80 H201"/><path d="M150 220 H201"/><path d="M605 84 C700 84 730 110 796 120"/><path d="M605 220 H646"/><path d="M770 220 C790 220 790 160 796 150"/></g>
</svg></div>'''
