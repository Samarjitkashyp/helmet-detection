"""Pictures for the Axomai Browser report: hub card (960x540) and social share image (1200x630), both drawn.
Run once (the build keeps the .jpg files in dist/research/assets):  python -I website/research/make_browser_images.py"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parent / "dist" / "research" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)


def font(size, bold=True):
    for p in ("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arialbd.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def gradient(w, h):
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = x / w * 0.6 + y / h * 0.4
            px[x, y] = (int(7 + 10 * t), int(17 + 38 * t), int(31 + 34 * t))
    return img


def window(d, x, y, w, h, s):
    """A drawn browser window: tab strip, address bar, page lines, and an AI panel on the right."""
    d.rounded_rectangle((x, y, x + w, y + h), int(22 * s), fill=(14, 30, 44), outline=(52, 211, 153), width=2)
    # tab strip
    for i, (label, on) in enumerate((("Tea in Assam", True), ("New Tab", False), ("Weather", False))):
        tx = x + 18 * s + i * 150 * s
        d.rounded_rectangle((tx, y + 14 * s, tx + 138 * s, y + 52 * s), int(12 * s), fill=(22, 52, 64) if on else (16, 38, 50))
        d.text((tx + 14 * s, y + 20 * s), label, font=font(int(17 * s), on), fill=(226, 232, 240) if on else (148, 190, 176))
    # address bar
    d.rounded_rectangle((x + 18 * s, y + 66 * s, x + w - 18 * s, y + 104 * s), int(19 * s), fill=(10, 22, 34))
    d.text((x + 38 * s, y + 72 * s), "https://assam-tea.example/notes", font=font(int(17 * s), False), fill=(148, 190, 176))
    # page text lines
    py = y + 130 * s
    pw = w * 0.52
    d.text((x + 28 * s, py), "Tea in Assam", font=font(int(26 * s)), fill=(255, 255, 255))
    for i in range(4):
        ww = pw * (0.95 if i % 3 else 0.7)
        d.rounded_rectangle((x + 28 * s, py + (50 + i * 24) * s, x + 28 * s + ww, py + (60 + i * 24) * s), int(5 * s), fill=(38, 70, 84))
    # AI panel
    ax = x + w * 0.62
    d.rounded_rectangle((ax, y + 122 * s, x + w - 18 * s, y + h - 18 * s), int(16 * s), fill=(18, 44, 56), outline=(251, 191, 36), width=1)
    d.text((ax + 16 * s, y + 132 * s), "Axom AI", font=font(int(19 * s)), fill=(251, 191, 36))
    d.rounded_rectangle((ax + 14 * s, y + 172 * s, x + w - 32 * s, y + 210 * s), int(12 * s), fill=(30, 74, 88))
    d.text((ax + 28 * s, y + 180 * s), "What is this page about?", font=font(int(16 * s), False), fill=(226, 232, 240))
    d.rounded_rectangle((ax + 14 * s, y + 224 * s, x + w - 32 * s, y + 282 * s), int(12 * s), fill=(16, 90, 70))
    d.text((ax + 28 * s, y + 232 * s), "Tea gardens of the", font=font(int(16 * s), False), fill=(255, 255, 255))
    d.text((ax + 28 * s, y + 256 * s), "Brahmaputra valley.", font=font(int(16 * s), False), fill=(255, 255, 255))


def card(w, h, title_y, win_box, scale, path, url=None, big=86):
    img = gradient(w, h)
    d = ImageDraw.Draw(img)
    d.text((48 if w == 960 else 60, 40 if w == 960 else 56), "AXOM AI RESEARCH", font=font(24 if w == 960 else 30), fill=(52, 211, 153))
    d.text((48 if w == 960 else 60, title_y), "Axomai Browser", font=font(big), fill=(255, 255, 255))
    x, y, ww, hh = win_box
    window(d, x, y, ww, hh, scale)
    if url:
        d.text((60, h - 64), url, font=font(30), fill=(251, 191, 36))
    img.save(ASSETS / path, quality=86, optimize=True)


card(960, 540, 86, (48, 214, 864, 304), 0.95, "card-browser.jpg", big=74)
d_img = Image.open(ASSETS / "card-browser.jpg")
d = ImageDraw.Draw(d_img)
d.text((48, 190), "", font=font(10))
d_img.save(ASSETS / "card-browser.jpg", quality=86, optimize=True)

img = gradient(1200, 630)
d = ImageDraw.Draw(img)
d.text((60, 52), "AXOM AI RESEARCH", font=font(30), fill=(52, 211, 153))
d.text((60, 100), "Axomai Browser", font=font(84), fill=(255, 255, 255))
d.text((60, 206), "A free AI browser made in Assam, for Windows and Android", font=font(34, False), fill=(226, 232, 240))
window(d, 60, 252, 1080, 304, 1.0)
d.text((60, 576), "aiaxom.co.in/research/axomai-browser", font=font(28), fill=(251, 191, 36))
img.save(ASSETS / "og-browser.jpg", quality=86, optimize=True)
for n in ("card-browser.jpg", "og-browser.jpg"):
    print(n, (ASSETS / n).stat().st_size // 1024, "KB")
