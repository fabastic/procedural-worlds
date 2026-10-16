"""Contact sheet of a rendered story's stills with beat id + shot labels (host Python + Pillow).
    python tools/story_sheet.py story_out/<slug> [cols]"""
import sys, os, json
from PIL import Image, ImageDraw
d = sys.argv[1]
cols = int(sys.argv[2]) if len(sys.argv) > 2 else 4
m = json.load(open(os.path.join(d, "manifest.json"), encoding="utf-8"))
tw, th = 480, 270
rows = (len(m["beats"]) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * (th + 22)), (240, 232, 214))
dr = ImageDraw.Draw(sheet)
for i, b in enumerate(m["beats"]):
    im = Image.open(os.path.join(d, b["still"])).convert("RGB").resize((tw, th))
    x, y = (i % cols) * tw, (i // cols) * (th + 22)
    sheet.paste(im, (x, y + 22))
    dr.text((x + 6, y + 5), f'{b["id"]} {b["shot"]["type"]}:{b["shot"]["focus"]} ({b["shot"].get("camera_move")})', fill=(0, 0, 0))
out = os.path.join(d, "sheet.jpg")
sheet.save(out, quality=85)
print(out)
