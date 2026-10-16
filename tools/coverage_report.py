"""Coverage report (host side): per-category contact sheets + COVERAGE.md from renders/coverage/results.json.
    python tools/coverage_report.py"""
import os, json, datetime
from PIL import Image, ImageDraw
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(root, "renders", "coverage", "results.json")))
notes_path = os.path.join(root, "tools", "coverage_notes.json")
notes = json.load(open(notes_path, encoding="utf-8")) if os.path.exists(notes_path) else {}
cats = {}
for name, v in R.items():
    cats.setdefault(v["category"], []).append(name)
for cat, names in cats.items():
    tiles = [(f"{n} {r['layers']['era']} {r['layers']['genre_mood']} {r['layers']['time']} {r['layers']['weather']}", r)
             for n in sorted(names) for r in R[n]["runs"]]
    tw, th, cols = 427, 240, 3
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 16)), (240, 232, 214))
    dr = ImageDraw.Draw(sheet)
    for i, (label, r) in enumerate(tiles):
        x, y = (i % cols) * tw, (i // cols) * (th + 16)
        if r.get("ok"):
            sheet.paste(Image.open(os.path.join(root, r["render"])).convert("RGB").resize((tw, th)), (x, y + 16))
        else:
            dr.rectangle((x, y + 16, x + tw - 1, y + th + 15), fill=(120, 30, 30))
        dr.text((x + 4, y + 2), label, fill=(0, 0, 0))
    sheet.save(os.path.join(root, "renders", "coverage", f"{cat}_sheet.jpg"), quality=82)
lines = ["# Coverage", "", f"Generated {datetime.datetime.now():%Y-%m-%d %H:%M} by `tools/coverage.py` + `tools/coverage_report.py`. "
         "Every entry renders through the COMPOSED generator (story layers -> kits) in the ink style; "
         "per-category contact sheets are in `renders/coverage/<category>_sheet.jpg`.", "",
         "| entry | category | kit | eras (sensible) | runs ok | focus points | last render | known issues |", "|---|---|---|---|---|---|---|---|"]
for cat in sorted(cats):
    for n in sorted(cats[cat]):
        v = R[n]
        ok = sum(r["ok"] for r in v["runs"])
        fp = max((len(r.get("focus", [])) for r in v["runs"]), default=0)
        last = next((r["render"] for r in reversed(v["runs"]) if r.get("ok")), "-")
        issue = notes.get(n, "")
        errs = "; ".join(r["error"] for r in v["runs"] if not r.get("ok"))
        lines.append(f"| {n} | {cat} | {v['kit']} | {', '.join(v['eras'])} | {ok}/{len(v['runs'])} | {fp} | `{last}` | {issue}{(' ERR: ' + errs) if errs else ''} |")
open(os.path.join(root, "COVERAGE.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("COVERAGE.md", len(R), "entries,", len(cats), "categories")
