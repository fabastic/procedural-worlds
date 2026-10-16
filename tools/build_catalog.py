"""Regenerate story/catalog.json's "composed" section from procedural_worlds/presets/settings.json:
keywords per setting + the focus points its kit/features expose (host Python, no Blender).
    python tools/build_catalog.py"""
import json, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(root, "procedural_worlds", "presets", "settings.json"), encoding="utf-8"))
cat_path = os.path.join(root, "story", "catalog.json")
cat = json.load(open(cat_path, encoding="utf-8"))
FEATURE_FOCUS = {"counter_run": ["counter"], "bar_back": ["bar_back", "bottles"], "booths": ["booth"], "tables": ["table"],
                 "fireplace": ["fireplace"], "crates_pile": ["crates"], "desks_rows": ["desk"], "desk_single": ["desk"],
                 "shelves_walls": ["shelves"], "cells": ["cells"], "blackboard": ["blackboard"], "beds_row": ["beds"],
                 "bed_single": ["bed"], "sofa_set": ["sofa"], "pillars": ["pillars"], "dais": ["dais", "throne"],
                 "banquet": ["banquet"], "machines": ["machines"]}
KEYWORDS = {
    "diner": ["diner", "cafe", "café", "coffee shop", "booth", "waitress", "milkshake", "counter", "pie"],
    "bar": ["bar", "pub", "saloon", "bartender", "whiskey", "drink", "speakeasy", "cocktail"],
    "tavern": ["tavern", "inn", "ale", "mead", "innkeeper", "hearth"],
    "office": ["office", "cubicle", "desk", "boss", "meeting", "corporate"],
    "detective_office": ["detective", "private eye", "investigator", "case file", "agency"],
    "police_station": ["police", "precinct", "station house", "cell", "sergeant", "interrogation", "cop"],
    "classroom": ["classroom", "school", "teacher", "student", "lesson", "blackboard", "chalk"],
    "library": ["library", "librarian", "bookshop", "bookstore", "archive", "books", "tome"],
    "hospital_ward": ["hospital", "ward", "nurse", "doctor", "patient", "infirmary"],
    "bedroom": ["bedroom", "bed", "pillow", "nightstand", "sleep", "woke"],
    "living_room": ["living room", "lounge", "sofa", "couch", "parlour", "parlor", "fireplace"],
    "castle_hall": ["castle", "throne", "king", "queen", "hall", "court", "knight", "banquet"],
    "dungeon": ["dungeon", "prison", "chains", "jail", "cell", "torch"],
    "basement": ["basement", "cellar", "boiler", "furnace", "storage"],
    "main_street": ["street", "avenue", "downtown", "shops", "sidewalk", "traffic", "town"],
    "market": ["market", "bazaar", "stall", "vendor", "merchant", "haggle"],
    "village": ["village", "hamlet", "cottages", "villagers"],
    "harbour_town": ["harbour", "harbor", "port", "docks", "pier", "fishing"],
    "rooftop": ["rooftop", "roof", "skyline", "ledge"],
    "forest": ["forest", "woods", "trees", "pine", "woodland"],
    "jungle": ["jungle", "rainforest", "vines", "tropical"],
    "desert": ["desert", "dunes", "sand", "cactus", "oasis"],
    "snowfield": ["snow", "tundra", "ice", "frozen", "blizzard", "arctic"],
    "mountain_pass": ["mountain", "pass", "peak", "summit", "cliffs", "ridge"],
    "swamp": ["swamp", "bog", "marsh", "bayou", "mire"],
    "open_field": ["field", "meadow", "prairie", "plain", "grassland"],
    "cabin": ["cabin", "lodge", "hut", "woodsman"],
    "camp": ["camp", "campfire", "tent", "bonfire"],
    "ruins": ["ruins", "ruin", "temple", "ancient stones", "crumbling"],
    "farmstead": ["farm", "barn", "farmer", "harvest", "crops"],
    "graveyard": ["graveyard", "cemetery", "grave", "tomb", "headstone", "funeral"],
    "battlefield": ["battlefield", "battle", "trench", "war", "soldiers", "front"],
    "alien_landscape": ["alien", "planet", "crystals", "strange world", "xeno"],
}
comp = {}
for name, e in S.items():
    if name.startswith("_"):
        continue
    fp = ["room", "door", "window", "lamp"] if e["kit"] == "room" else \
        (["street", "far_end", "shopfront", "sign", "street_lamp", "vehicle"] + (["stall"] if e.get("stalls") else [])) if e["kit"] == "street" else \
        ["landmark", "path", "horizon"] + ([{"cabin": "cabin", "camp": "campfire", "ruins": "ruins", "graveyard": "graves",
                                             "battlefield": "trench", "barn": "barn"}.get(e.get("landmark"), "tree")])
    for f in e.get("features", []):
        fp += [x for x in FEATURE_FOCUS.get(f, []) if x not in fp]
    base = {"room": "interior", "street": "street", "terrain": "landscape"}[e["kit"]]
    if name == "rooftop":
        base = "rooftop"
    comp[name] = {"base": base, "setting": name, "category": e.get("category"), "eras": e["eras"],
                  "keywords": KEYWORDS.get(name, [name.replace("_", " ")]), "focus_points": fp}
cat["composed"] = comp
json.dump(cat, open(cat_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(comp), "composed settings ->", cat_path)
