"""Story text -> story.json (see story/schema.json).

    python story/parse.py my_story.txt -o story/examples/my_story.json [--offline] [--beats 12]

Uses the Gemini API when GEMINI_API_KEY is set (env or the gitignored repo .env; GEMINI_MODEL overrides the
newest-first model list),
otherwise -- or if the call fails -- an offline keyword parser. Either way the result is repaired
against story/catalog.json (only stageable generators and focus points) and validated against the
schema. Pure standard library."""
import argparse, hashlib, json, os, re, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv(path=os.path.join(os.path.dirname(HERE), ".env")):
    """Load KEY=VALUE lines from the repo's gitignored .env into os.environ (never printed)."""
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()
SCHEMA = json.load(open(os.path.join(HERE, "schema.json"), encoding="utf-8"))
_CAT = json.load(open(os.path.join(HERE, "catalog.json"), encoding="utf-8"))
FOCUS_WORDS = {"counter": ["counter", "bar"], "bar_back": ["bottles", "shelf", "bartender"], "bottles": ["bottle", "whiskey", "wine"],
               "booth": ["booth"], "table": ["table", "meal", "plate", "cards"], "fireplace": ["fire", "hearth", "fireplace", "embers"],
               "crates": ["crate", "barrel", "box", "sack"], "desk": ["desk", "papers", "typewriter", "computer", "file"],
               "shelves": ["shelf", "shelves", "books", "bookcase"], "cells": ["cell", "bars", "prisoner", "locked"],
               "blackboard": ["blackboard", "chalk", "lesson"], "beds": ["bed", "patient", "ward"], "bed": ["bed", "pillow", "sleep"],
               "sofa": ["sofa", "couch"], "pillars": ["pillar", "column"], "dais": ["dais", "court"], "throne": ["throne", "king", "queen"],
               "banquet": ["feast", "banquet"], "machines": ["machine", "boiler", "engine", "pipes"], "door": ["door", "knock", "entered"],
               "window": ["window", "outside", "glass"], "lamp": ["lamp", "light", "candle", "bulb"], "room": [],
               "street": ["street", "road"], "far_end": ["distance", "end of the street"], "shopfront": ["shop", "store", "display"],
               "sign": ["sign", "neon"], "street_lamp": ["streetlight", "lamppost"], "vehicle": ["car", "cart", "wagon", "taxi"],
               "stall": ["stall", "vendor", "merchant"], "landmark": [], "path": ["path", "trail", "walked"], "horizon": ["horizon", "sky", "distance"],
               "cabin": ["cabin", "hut"], "campfire": ["campfire", "fire", "tent"], "ruins": ["ruin", "ruins", "stones"], "graves": ["grave", "tomb", "headstone"],
               "trench": ["trench", "wire", "sandbag"], "barn": ["barn", "hay"], "tree": ["tree", "oak"]}
CATALOG = {}      # option key -> stage option (3 hand-built hero generators + every COMPOSED setting)
for _g, _c in _CAT["generators"].items():
    CATALOG[_g] = dict(_c, generator=_g, hero=True)
for _n, _c in _CAT.get("composed", {}).items():
    CATALOG["COMPOSED:" + _n] = dict(_c, generator="COMPOSED", hero=False, seeds=[7, 11, 23],
                                     focus_keywords={f: FOCUS_WORDS.get(f, [f]) for f in _c["focus_points"]})


def opt_key(sc):
    g = sc.get("generator")
    if g == "COMPOSED":
        return "COMPOSED:" + str(sc.get("layers", {}).get("setting"))
    return g
GEMINI_MODELS = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash", "gemini-flash-latest"]
SHOT_CYCLE = ["wide", "medium", "close", "POV", "low", "medium", "close", "high", "OTS"]
MOVE_CYCLE = ["push_in", "drift", "static", "pan_right", "tilt_up", "pull_out", "orbit", "pan_left"]
TIME_WORDS = {"night": ["night", "midnight", "dark", "moon", "stars", "neon"], "dusk": ["dusk", "evening", "sunset", "twilight"],
              "dawn": ["dawn", "sunrise", "first light"], "golden": ["afternoon", "golden", "late sun"],
              "day": ["morning", "noon", "day", "breakfast", "sunlight", "bright"]}
GENRE_WORDS = {"noir": ["detective", "debt", "gun", "cop", "smoke", "crime", "case", "dame", "gangster"],
               "horror": ["ghost", "blood", "scream", "dead", "monster", "fear", "graveyard", "grave", "headstone", "whisper", "nailed", "haunted", "footprints"],
               "romance": ["love", "kiss", "heart", "wedding", "darling", "smiled", "together", "umbrella"], "comedy": ["laughed", "joke", "silly", "funny"],
               "adventure": ["treasure", "journey", "quest", "expedition"], "sci-fi": ["robot", "android", "space", "cyber", "laser", "starship"],
               "fantasy": ["dragon", "wizard", "magic", "spell", "castle", "tithe", "throne", "king"],
               "war": ["soldier", "war", "battle", "bomb", "trench", "shell", "sergeant", "guns", "private", "wire"],
               "mystery": ["clue", "secret", "missing", "letter", "who"], "slice-of-life": []}
ERA_WORDS = {"near-future": ["cyber", "android", "drone", "credits", "hologram"], "far-future": ["starship", "warp", "colony"],
             "1920s-50s": ["radio", "telegram", "typewriter", "jazz", "jukebox"],
             "1700s-1800s": ["carriage", "musket", "lantern-lit", "candlelight"], "medieval": ["castle", "knight", "sword", "dragon", "miller", "mead", "tavern"],
             "ancient": ["pharaoh", "legion", "temple of"], "modern": []}


def era_from_years(text):
    """Explicit years beat keywords: 1952 -> 1920s-50s, 1987 -> modern, 2140 -> far-future."""
    ys = [int(y) for y in re.findall(r"(1[0-9]{3}|2[0-9]{3})s?", text)]
    if not ys:
        return None
    y = sorted(ys)[len(ys) // 2]
    for lim, era in ((500, "ancient"), (1500, "medieval"), (1915, "1700s-1800s"), (1960, "1920s-50s"),
                     (2035, "modern"), (2150, "near-future")):
        if y < lim:
            return era
    return "far-future"


# ----------------------------------------------------------------------------- validation
def validate(node, schema, path="$"):
    """Small JSON-Schema subset validator (type/required/properties/enum/pattern/min*/items)."""
    errs = []
    t = schema.get("type")
    tmap = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float)}
    if t and not isinstance(node, tmap[t]) or (t in ("integer", "number") and isinstance(node, bool)):
        return [f"{path}: expected {t}"]
    if "enum" in schema and node not in schema["enum"]:
        errs.append(f"{path}: {node!r} not in {schema['enum']}")
    if isinstance(node, str):
        if len(node) < schema.get("minLength", 0):
            errs.append(f"{path}: too short")
        if "pattern" in schema and not re.match(schema["pattern"], node):
            errs.append(f"{path}: {node!r} !~ {schema['pattern']}")
    if isinstance(node, (int, float)):
        if "minimum" in schema and node < schema["minimum"]:
            errs.append(f"{path}: < {schema['minimum']}")
        if "maximum" in schema and node > schema["maximum"]:
            errs.append(f"{path}: > {schema['maximum']}")
    if isinstance(node, dict):
        for k in schema.get("required", []):
            if k not in node:
                errs.append(f"{path}: missing {k}")
        for k, sub in schema.get("properties", {}).items():
            if k in node:
                errs += validate(node[k], sub, f"{path}.{k}")
    if isinstance(node, list):
        if len(node) < schema.get("minItems", 0):
            errs.append(f"{path}: needs >= {schema['minItems']} items")
        if "items" in schema:
            for i, x in enumerate(node):
                errs += validate(x, schema["items"], f"{path}[{i}]")
    return errs


# ----------------------------------------------------------------------------- helpers
def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48] or "story"


def score(text, words):
    t = " " + text.lower() + " "
    return sum(t.count(" " + w) for w in words)


def pick(text, table, default):
    best = max(table, key=lambda k: score(text, table[k]))
    return best if score(text, table[best]) > 0 else default


def stable_seed(*parts):
    return int(hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:6], 16) % 100000


def sentences(text):
    text = re.sub(r"\s+", " ", text.strip())
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", text) if s.strip()]


# ----------------------------------------------------------------------------- offline parser
def gen_score(blob, g):
    c = CATALOG[g]
    return score(blob, c["keywords"]) * 2 + sum(score(blob, w) for w in c["focus_keywords"].values()) * 0.5 + (0.75 if c["hero"] else 0)


def speaker_for(blob, quote):
    """Who says `quote`: 'said Name' / 'Name said' / pronoun -> protagonist / 'said a voice' -> VOICE."""
    i = blob.find(quote)
    after = blob[i + len(quote):i + len(quote) + 60]
    verbs = r"(?:said|asked|whispered|shouted|called|muttered)"
    m = re.search(verbs + r"\s+([A-Z][a-z]+)", after) or re.search(r"([A-Z][a-z]+)\s+" + verbs, after)
    if m and m.group(1) not in ("She", "He", "They", "I"):
        return m.group(1).upper()
    if re.search(r"\b(?:she|he|i)\s+" + verbs, after, re.I):
        return "PROTAGONIST"
    m = re.search(verbs + r"\s+(?:a|the)\s+([a-z]+)", after)
    return (m.group(1) if m else "voice").upper()


def offline_parse(text, n_beats=12, title=None):
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if lines and len(lines[0]) < 70 and not re.search(r"[.!?\"”]$", lines[0]):
        title = title or lines[0]
        text = text.strip()[len(lines[0]):]
    sents = sentences(text)
    if not sents:
        raise ValueError("empty story")
    title = title or (sents[0][:40].rstrip(".!?") if len(sents[0]) < 60 else "Untitled story")
    prot = re.findall(r"\b([A-Z][a-z]{2,})\b", text)
    stop = {"The", "She", "He", "They", "It", "But", "And", "When", "Then", "Every", "There", "Some", "One", "This",
            "That", "What", "Her", "His", "Its", "Inside", "Outside", "Someone", "Far", "Hello", "Go", "By", "On", "In", "You"}
    common = [w for w in prot if w not in stop]
    name = max(set(common), key=lambda w: (common.count(w), w)) if common else "Narrator"
    genre = pick(text, GENRE_WORDS, "slice-of-life")
    era = era_from_years(text) or pick(text, ERA_WORDS, "modern")
    # split into chunks, one beat per chunk, scene = best generator per chunk (merged when equal)
    n = max(10, min(14, n_beats, len(sents))) if len(sents) >= 10 else len(sents)
    chunks = [sents[int(i * len(sents) / n):int((i + 1) * len(sents) / n)] for i in range(n)]
    chunks = [c for c in chunks if c]
    scenes, beats = [], []
    cur = None
    for i, ch in enumerate(chunks):
        blob = " ".join(ch)
        gen = max(CATALOG, key=lambda g: gen_score(blob, g))
        if gen_score(blob, gen) < 2.0 or (cur and gen_score(blob, cur["_opt"]) >= gen_score(blob, gen) - 1.5):
            gen = cur["_opt"] if cur else max(CATALOG, key=lambda g: gen_score(text, g))
        tod = pick(blob, TIME_WORDS, cur["layers"]["time"] if cur else pick(text, TIME_WORDS, "night"))
        if cur is None or gen != cur["_opt"] or tod != cur["layers"]["time"]:
            c = CATALOG[gen]
            sid = f"{c['setting']}_{tod}_{len(scenes) + 1}"
            cur = {"id": sid, "name": f"{c['setting'].title()} ({tod})",
                   "layers": {"base": c["base"], "setting": c["setting"],
                              "era": era if (c["hero"] or era != "modern" or "modern" in c.get("eras", [])) else c["eras"][0],
                              "genre_mood": genre,
                              "weather": "rain" if "rain" in blob.lower() else "clear", "time": tod, "state": "lived-in"},
                   "generator": c["generator"], "_opt": gen, "seed": c["seeds"][len(scenes) % len(c["seeds"])],
                   "spawn": {"focus": c["focus_points"][0]}, "focus_points": []}
            scenes.append(cur)
            first = True
        else:
            first = False
        c = CATALOG[cur["_opt"]]
        focus = max(c["focus_keywords"], key=lambda f: score(blob, c["focus_keywords"][f]))
        if score(blob, c["focus_keywords"][focus]) == 0:
            focus = c["focus_points"][(i * 3 + 1) % len(c["focus_points"])]
        typ = "establishing" if first else SHOT_CYCLE[i % len(SHOT_CYCLE)]
        quotes = re.findall(r"[\"“]([^\"”]{2,160})[\"”]", blob)
        narration = re.sub(r"[\"“][^\"”]*[\"”]", "", blob).strip(" ,.;")
        b = {"id": f"b{len(beats) + 1:02d}", "scene_id": cur["id"],
             "shot": {"type": typ, "focus": focus, "camera_move": MOVE_CYCLE[i % len(MOVE_CYCLE)],
                      "duration_s": 3.5 if typ == "establishing" else 3.0},
             "trigger": {"type": "focus", "focus": focus, "radius_m": 3.0}}
        if narration:
            b["caption"] = (narration[:157] + "...") if len(narration) > 160 else narration + "."
        if quotes:
            b["dialogue"] = [{"speaker": speaker_for(blob, q).replace("PROTAGONIST", name.upper()),
                              "text": q.strip(" ,")} for q in quotes[:2]]
        beats.append(b)
        if focus not in cur["focus_points"]:
            cur["focus_points"].append(focus)
    for sc in scenes:
        sc.pop("_opt", None)
    return {"title": title, "slug": slugify(title), "logline": sents[0][:200],
            "protagonist": {"name": name, "eye_height_m": 1.65}, "scenes": scenes, "beats": beats}


# ----------------------------------------------------------------------------- Gemini parser
def gemini_parse(text, n_beats=12):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    models = [os.environ["GEMINI_MODEL"]] if os.environ.get("GEMINI_MODEL") else []
    models += [m for m in GEMINI_MODELS if m not in models]
    catalog = {"hand_built_generators (best quality, prefer when they fit)":
               {g: {"base": c["base"], "setting": c["setting"], "focus_points": c["focus_points"]} for g, c in CATALOG.items() if c["hero"]},
               "COMPOSED settings (use generator \"COMPOSED\" and put the key in layers.setting)":
               {c["setting"]: {"base": c["base"], "eras": c.get("eras"), "focus_points": c["focus_points"]}
                for c in CATALOG.values() if not c["hero"]}}
    prompt = f"""You adapt stories into an animated, hand-inked graphic novel told WITHOUT drawn characters:
only places, objects, point-of-view shots, narration captions and dialogue from OFF-PANEL speakers.
Return ONLY a JSON object matching this JSON Schema:
{json.dumps(SCHEMA)}

Stageable places. scene.generator is either a hand-built generator name, or "COMPOSED" with layers.setting set to one of the
COMPOSED setting keys. A beat's shot.focus MUST be one of that place's focus_points. Pick the place that best fits each scene of the
story; set layers.era / genre_mood / weather / time / state to match the story (any era works for COMPOSED settings):
{json.dumps(catalog)}

Rules: {max(10, n_beats - 2)}-{min(14, n_beats + 2)} beats in story order. Each scene's first beat is an "establishing" shot.
Vary shot types (wide, medium, close, POV, low, high, OTS) and camera_move; duration_s 2.5-4.
Captions: short, evocative narration (max ~25 words). Dialogue speakers are off-panel (names in CAPS).
layers.time: dawn|day|golden|dusk|night. Pick seeds 1-99. slug: lowercase-hyphenated title.
Every beat gets a trigger {{"type": "focus", "focus": <its focus>, "radius_m": 3}}.

STORY:
{text}"""
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.5}}
    data, last = None, None
    for model in models:                      # newest first; skip retired (404), retry busy (429/503)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        for attempt in range(3):
            req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                         headers={"Content-Type": "application/json", "x-goog-api-key": key})
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    data = json.loads(r.read().decode())
                print(f"gemini model: {model}", file=sys.stderr)
                break
            except urllib.error.HTTPError as e:
                last = f"{model}: HTTP {e.code}"
                if e.code in (429, 500, 503):
                    time.sleep(4 * (attempt + 1))
                    continue
                break
        if data is not None:
            break
    if data is None:
        raise RuntimeError(f"all Gemini models failed ({last})")
    out = data["candidates"][0]["content"]["parts"][0]["text"]
    out = re.sub(r"^```(?:json)?|```$", "", out.strip()).strip()
    return json.loads(out)


# ----------------------------------------------------------------------------- repair
def repair(story):
    """Force the story onto what Blender can stage (generators, focus points, ids, enums)."""
    story["slug"] = slugify(story.get("slug") or story.get("title", "story"))
    story.setdefault("logline", "")
    p = story.setdefault("protagonist", {})
    p.setdefault("name", "Narrator")
    p["eye_height_m"] = float(min(2.2, max(0.9, p.get("eye_height_m", 1.65))))
    layer_schema = SCHEMA["properties"]["scenes"]["items"]["properties"]["layers"]["properties"]
    sids = set()
    for sc in story["scenes"]:
        sc["id"] = re.sub(r"[^a-z0-9_-]", "_", str(sc.get("id", "scene")).lower())
        if opt_key(sc) not in CATALOG:
            blob = json.dumps(sc)
            k = max(CATALOG, key=lambda g: gen_score(blob, g))
            sc["generator"] = CATALOG[k]["generator"]
            sc.setdefault("layers", {})["setting"] = CATALOG[k]["setting"]
        c = CATALOG[opt_key(sc)]
        L = sc.setdefault("layers", {})
        defaults = {"base": c["base"], "setting": c["setting"], "era": "modern", "genre_mood": "slice-of-life",
                    "weather": "clear", "time": "night", "state": "lived-in"}
        for k, dv in defaults.items():
            enum = layer_schema[k].get("enum")
            if L.get(k) is None or (enum and L[k] not in enum):
                L[k] = dv
        sc["seed"] = int(sc.get("seed", 7)) % 100000
        sc["focus_points"] = [f for f in sc.get("focus_points", []) if f in c["focus_points"]] or c["focus_points"][:4]
        sc.setdefault("spawn", {"focus": c["focus_points"][0]})
        sids.add(sc["id"])
    shot_enum = SCHEMA["properties"]["beats"]["items"]["properties"]["shot"]["properties"]
    for i, b in enumerate(story["beats"]):
        b["id"] = f"b{i + 1:02d}"
        if b.get("scene_id") not in sids:
            b["scene_id"] = story["scenes"][0]["id"]
        sc = next(s for s in story["scenes"] if s["id"] == b["scene_id"])
        c = CATALOG[opt_key(sc)]
        sh = b.setdefault("shot", {})
        if sh.get("type") not in shot_enum["type"]["enum"]:
            sh["type"] = "medium"
        if sh.get("focus") not in c["focus_points"]:
            sh["focus"] = c["focus_points"][i % len(c["focus_points"])]
        if sh.get("camera_move") not in shot_enum["camera_move"]["enum"]:
            sh["camera_move"] = MOVE_CYCLE[i % len(MOVE_CYCLE)]
        sh["duration_s"] = float(min(4.0, max(2.0, sh.get("duration_s", 3.0))))
        b.setdefault("trigger", {"type": "focus", "focus": sh["focus"], "radius_m": 3.0})
        b["dialogue"] = [d for d in b.get("dialogue", []) if d.get("text")]
        if not b["dialogue"]:
            b.pop("dialogue")
    return story


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("story_txt")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--offline", action="store_true", help="skip the Gemini API")
    ap.add_argument("--beats", type=int, default=12)
    ap.add_argument("--title")
    a = ap.parse_args()
    text = open(a.story_txt, encoding="utf-8").read()
    used = "offline"
    story = None
    if not a.offline and os.environ.get("GEMINI_API_KEY"):
        try:
            story = gemini_parse(text, a.beats)
            used = "gemini"
        except (urllib.error.URLError, KeyError, ValueError, RuntimeError, TimeoutError) as e:
            print(f"Gemini parse failed ({e}); falling back to the offline parser", file=sys.stderr)
    if story is None:
        story = offline_parse(text, a.beats, a.title)
    if a.title:
        story["title"] = a.title
    story = repair(story)
    errs = validate(story, SCHEMA)
    if errs:
        print("schema errors:\n  " + "\n  ".join(errs[:20]), file=sys.stderr)
        sys.exit(2)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(story, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"{used}: {story['title']!r} -> {a.out} ({len(story['scenes'])} scenes, {len(story['beats'])} beats)")


if __name__ == "__main__":
    main()
