"""Pictures for the crawler-bot report: the hub card (960x540) and the social share image (1200x630), both drawn.
Run once (the build keeps the .jpg files in dist/research/assets):  python -I website/research/make_crawler_images.py"""
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


def flow(d, x0, y0, w, h, labels, subs, scale=1.0):
    n = len(labels)
    gap = 26 * scale
    bw = (w - gap * (n - 1)) / n
    for i, (lab, sub) in enumerate(zip(labels, subs)):
        x = x0 + i * (bw + gap)
        d.rounded_rectangle((x, y0, x + bw, y0 + h), int(18 * scale), fill=(16, 38, 52), outline=(52, 211, 153), width=2)
        tw = d.textlength(lab, font=font(int(25 * scale)))
        d.text((x + (bw - tw) / 2, y0 + h * 0.22), lab, font=font(int(25 * scale)), fill=(255, 255, 255))
        sw = d.textlength(sub, font=font(int(17 * scale), False))
        d.text((x + (bw - sw) / 2, y0 + h * 0.62), sub, font=font(int(17 * scale), False), fill=(148, 190, 176))
        if i < n - 1:
            ax = x + bw + 4 * scale
            ay = y0 + h / 2
            d.line((ax, ay, ax + gap - 8 * scale, ay), fill=(251, 191, 36), width=3)
            d.polygon([(ax + gap - 8 * scale, ay - 7 * scale), (ax + gap - 8 * scale, ay + 7 * scale), (ax + gap, ay)], fill=(251, 191, 36))


labels = ["Website", "Clean text", "Questions", "Axom AI chat"]
subs = ["or scanned PDF", "no menus", "one per passage", "answers"]

# hub card 960x540
img = gradient(960, 540)
d = ImageDraw.Draw(img)
d.text((48, 40), "AXOM AI RESEARCH", font=font(24), fill=(52, 211, 153))
d.text((48, 86), "Crawler Bot", font=font(86), fill=(255, 255, 255))
d.text((48, 192), "Websites and documents,", font=font(34, False), fill=(226, 232, 240))
d.text((48, 236), "turned into answers", font=font(34, False), fill=(226, 232, 240))
flow(d, 48, 340, 864, 120, labels, subs, 0.9)
d.text((48, 484), "8.1 million words read  |  17,596 pages fingerprinted", font=font(24), fill=(251, 191, 36))
img.save(ASSETS / "card-crawler-bot.jpg", quality=86, optimize=True)

# social share 1200x630
img = gradient(1200, 630)
d = ImageDraw.Draw(img)
d.text((60, 56), "AXOM AI RESEARCH", font=font(30), fill=(52, 211, 153))
d.text((60, 110), "Axom AI Crawler Bot", font=font(84), fill=(255, 255, 255))
d.text((60, 222), "Websites and scanned documents,", font=font(42, False), fill=(226, 232, 240))
d.text((60, 276), "turned into answers for Assamese, Hindi and English", font=font(42, False), fill=(226, 232, 240))
flow(d, 60, 382, 1080, 130, labels, subs, 1.1)
d.text((60, 566), "aiaxom.co.in/research/axom-ai-crawler-bot", font=font(30), fill=(251, 191, 36))
img.save(ASSETS / "og-crawler-bot.jpg", quality=86, optimize=True)
for n in ("card-crawler-bot.jpg", "og-crawler-bot.jpg"):
    print(n, (ASSETS / n).stat().st_size // 1024, "KB")
