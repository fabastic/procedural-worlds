"""Story text -> story.json (see story/schema.json).

    python story/parse.py my_story.txt -o story/examples/my_story.json [--offline] [--beats 12]

Uses the Gemini API when GEMINI_API_KEY is set (model from GEMINI_MODEL, default gemini-2.5-flash),
otherwise -- or if the call fails -- an offline keyword parser. Either way the result is repaired
against story/catalog.json (only stageable generators and focus points) and validated against the
schema. Pure standard library."""
import argparse, hashlib, json, os, re, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = json.load(open(os.path.join(HERE, "schema.json"), encoding="utf-8"))
CATALOG = json.load(open(os.path.join(HERE, "catalog.json"), encoding="utf-8"))["generators"]
SHOT_CYCLE = ["wide", "medium", "close", "POV", "low", "medium", "close", "high", "OTS"]
MOVE_CYCLE = ["push_in", "drift", "static", "pan_right", "tilt_up", "pull_out", "orbit", "pan_left"]
TIME_WORDS = {"night": ["night", "midnight", "dark", "moon", "stars", "neon"], "dusk": ["dusk", "evening", "sunset", "twilight"],
              "dawn": ["dawn", "sunrise", "first light"], "golden": ["afternoon", "golden", "late sun"],
              "day": ["morning", "noon", "day", "breakfast", "sunlight", "bright"]}
GENRE_WORDS = {"noir": ["detective", "debt", "gun", "cop", "smoke", "crime", "case", "dame"], "horror": ["ghost", "blood", "scream", "dead", "monster", "fear"],
               "romance": ["love", "kiss", "heart", "wedding", "darling"], "comedy": ["laughed", "joke", "silly", "funny"],
               "adventure": ["treasure", "map", "journey", "quest", "storm"], "sci-fi": ["robot", "android", "space", "cyber", "laser"],
               "fantasy": ["dragon", "wizard", "magic", "spell", "castle"], "war": ["soldier", "war", "battle", "bomb"],
               "mystery": ["clue", "secret", "missing", "letter", "who"], "slice-of-life": []}
ERA_WORDS = {"near-future": ["cyber", "neon", "android", "drone", "credits", "hologram"], "1920s-50s": ["radio", "telegram", "typewriter", "jazz", "1940", "1950"],
             "1700s-1800s": ["candle", "carriage", "musket", "1800"], "medieval": ["castle", "knight", "sword"], "modern": []}


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
    return score(blob, c["keywords"]) + sum(score(blob, w) for w in c["focus_keywords"].values())


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
    era = pick(text, ERA_WORDS, "modern")
    # split into chunks, one beat per chunk, scene = best generator per chunk (merged when equal)
    n = max(10, min(14, n_beats, len(sents))) if len(sents) >= 10 else len(sents)
    chunks = [sents[int(i * len(sents) / n):int((i + 1) * len(sents) / n)] for i in range(n)]
    chunks = [c for c in chunks if c]
    scenes, beats = [], []
    cur = None
    for i, ch in enumerate(chunks):
        blob = " ".join(ch)
        gen = max(CATALOG, key=lambda g: gen_score(blob, g))
        if gen_score(blob, gen) == 0 or (cur and gen_score(blob, cur["generator"]) >= gen_score(blob, gen)):
            gen = cur["generator"] if cur else max(CATALOG, key=lambda g: gen_score(text, g))
        tod = pick(blob, TIME_WORDS, cur["layers"]["time"] if cur else pick(text, TIME_WORDS, "night"))
        if cur is None or gen != cur["generator"] or tod != cur["layers"]["time"]:
            c = CATALOG[gen]
            sid = f"{c['setting']}_{tod}_{len(scenes) + 1}"
            cur = {"id": sid, "name": f"{c['setting'].title()} ({tod})",
                   "layers": {"base": c["base"], "setting": c["setting"], "era": era, "genre_mood": genre,
                              "weather": "rain" if "rain" in blob.lower() else "clear", "time": tod, "state": "lived-in"},
                   "generator": gen, "seed": c["seeds"][len(scenes) % len(c["seeds"])],
                   "spawn": {"focus": c["focus_points"][0]}, "focus_points": []}
            scenes.append(cur)
            first = True
        else:
            first = False
        c = CATALOG[cur["generator"]]
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
    return {"title": title, "slug": slugify(title), "logline": sents[0][:200],
            "protagonist": {"name": name, "eye_height_m": 1.65}, "scenes": scenes, "beats": beats}


# ----------------------------------------------------------------------------- Gemini parser
def gemini_parse(text, n_beats=12):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    catalog = {g: {"base": c["base"], "setting": c["setting"], "focus_points": c["focus_points"]} for g, c in CATALOG.items()}
    prompt = f"""You adapt stories into an animated, hand-inked graphic novel told WITHOUT drawn characters:
only places, objects, point-of-view shots, narration captions and dialogue from OFF-PANEL speakers.
Return ONLY a JSON object matching this JSON Schema:
{json.dumps(SCHEMA)}

Stageable generators (use ONLY these as scene.generator; a beat's shot.focus MUST be one of that generator's focus_points):
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
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "x-goog-api-key": key})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode())
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
        if sc.get("generator") not in CATALOG:
            blob = json.dumps(sc)
            sc["generator"] = max(CATALOG, key=lambda g: score(blob, CATALOG[g]["keywords"]))
        c = CATALOG[sc["generator"]]
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
        c = CATALOG[sc["generator"]]
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
