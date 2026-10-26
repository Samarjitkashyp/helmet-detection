"""Card pictures for the research hub (960x540). Two come from the detection figures (faces already pixelated),
three are drawn graphics. Run after make_figures.py:  python -I website/research/make_card_images.py"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parent / "dist" / "research" / "assets"
W, H = 960, 540


def font(size, bold=True):
    for p in ("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arialbd.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def background():
    img = Image.new("RGB", (W, H), "#ecfdf5")
    px = img.load()
    for y in range(H):
        for x in range(W):
            t = (x / W * 0.55 + y / H * 0.45)
            px[x, y] = (int(236 - 40 * t), int(253 - 30 * t), int(245 - 25 * t))
    return img


def crop_figure(name, box, out):
    im = Image.open(ASSETS / name).convert("RGB").crop(box).resize((W, H), Image.LANCZOS)
    im.save(ASSETS / out, quality=84, optimize=True)


def results_card():
    img = background()
    d = ImageDraw.Draw(img)
    d.text((54, 40), "RESULTS", font=font(26), fill="#047857")
    rows = [("Recall, before", 0.617, "#94a3b8", "0.62"), ("Recall, after CCTV tuning", 0.791, "#059669", "0.79"),
            ("Riders alerted, 1 fps", 0.74, "#d97706", "74%"), ("Riders alerted, 2 fps", 0.90, "#059669", "90%")]
    y = 120
    for label, v, color, txt in rows:
        d.text((54, y), label, font=font(26, False), fill="#064e3b")
        d.rounded_rectangle((54, y + 42, 54 + 720, y + 74), 16, fill="#d1fae5")
        d.rounded_rectangle((54, y + 42, 54 + int(720 * v), y + 74), 16, fill=color)
        d.text((800, y + 36), txt, font=font(34), fill="#022c22")
        y += 98
    img.save(ASSETS / "card-results.jpg", quality=86, optimize=True)


def model_card():
    img = background()
    d = ImageDraw.Draw(img)
    d.text((54, 40), "MODEL CARD", font=font(26), fill="#047857")
    d.text((54, 120), "YOLOv8s", font=font(120), fill="#022c22")
    d.text((54, 270), "helmet  |  no_helmet", font=font(40, False), fill="#064e3b")
    x = 54
    for t in ("CC BY 4.0 data", "MIT code", "Runs on CPU"):
        w = d.textlength(t, font=font(28)) + 44
        d.rounded_rectangle((x, 380, x + w, 436), 28, fill="#ffffff", outline="#a7f3d0", width=2)
        d.text((x + 22, 390), t, font=font(28), fill="#047857")
        x += w + 16
    img.save(ASSETS / "card-model.jpg", quality=86, optimize=True)


def faq_card():
    img = background()
    d = ImageDraw.Draw(img)
    d.ellipse((560, 70, 900, 410), fill="#10b981")
    d.text((645, 80), "?", font=font(300), fill="#ffffff")
    d.text((54, 40), "FAQ", font=font(26), fill="#047857")
    d.text((54, 150), "Short answers", font=font(64), fill="#022c22")
    d.text((54, 235), "Accuracy, night, GPU,", font=font(36, False), fill="#064e3b")
    d.text((54, 285), "privacy and licences", font=font(36, False), fill="#064e3b")
    img.save(ASSETS / "card-faq.jpg", quality=86, optimize=True)


crop_figure("detection-street.jpg", (180, 90, 1000, 551), "card-how.jpg")
crop_figure("detection-junction.jpg", (560, 240, 1280, 645), "card-cctv.jpg")
results_card()
model_card()
faq_card()
for f in sorted(ASSETS.glob("card-*.jpg")):
    print(f.name, f.stat().st_size // 1024, "KB")
