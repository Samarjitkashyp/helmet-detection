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
