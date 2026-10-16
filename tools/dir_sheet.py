"""Labelled contact sheet of every .jpg/.png in a folder (host Python + Pillow).
    python tools/dir_sheet.py FOLDER OUT.jpg [cols]"""
import sys, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 3
files = sorted(f for f in os.listdir(d) if f.lower().endswith((".jpg", ".png")) and "sheet" not in f)
tw, th = 640, 360
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, max(1, rows) * (th + 20)), (240, 232, 214))
dr = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(os.path.join(d, f)).convert("RGB").resize((tw, th))
    x, y = (i % cols) * tw, (i // cols) * (th + 20)
    sheet.paste(im, (x, y + 20))
    dr.text((x + 6, y + 4), os.path.splitext(f)[0], fill=(0, 0, 0))
sheet.save(out, quality=85)
print(out, len(files))
