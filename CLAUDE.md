# Procedural Worlds — Blender add-on (handoff for Claude Code)

## What this is
**A story app.** The user pastes any story and gets it told in the hand-inked graphic-novel style: Phase 1 as an animated comic, Phase 2 across any kind of setting, Phase 3 as a world they walk through in first person as the protagonist. One data format, one pipeline:
`story text -> story.json (story/parse.py) -> Blender builds settings (procedural_worlds generators + ink.py) -> outputs (comic panels/clips, later walkable GLB) -> web app (web/) deployed on Vercel.`
The Blender add-on (`procedural_worlds/`, panel View3D > N > Worlds) is the engine: it builds complete seeded scenes (geometry, materials, lights, camera) and renders them as inked panels. No character models: stories are told through places, objects, POV, captions and off-panel dialogue.

**Current phase: 1** (animated ink comic). Master prompt rules: commit+push after every working step; never ask; look at every visual change (3-line critique vs reference); parallel subagents for independent work; invariants below.

## Art direction: hand-drawn ink flow look
Every render must look DRAWN, not 3D-rendered; target is `reference/ink_style_ref.png` (cluttered kitchen panel).
- Ink: thick, slightly wobbly black brush outlines with varying weight; heavier on silhouettes, thinner inside.
- Shading: flat 2-3 tone cel shading; shadows are a darker, muted version of the same hue.
- Texture: hatching in shadows, ink blots/drips/smudges/grimy stains near edges, paper grain over the frame.
- Palette: muted, slightly dirty (sage/teal, ochre, cream, faded terracotta) unified by black ink.
- Shapes: hand-made, wonky, never perfectly straight.
- Implemented once in `procedural_worlds/ink.py`, applied automatically by `core.generate()` to ANY scene; never hand-tune per scene (scenes may only pass hints, see Contracts).

## Session log
- Final 5-hour session started **2026-10-16 19:13 IST** (checkpoints 20:43 / 22:13 / 23:13 / 23:53).
- Remote: **https://github.com/fabastic/procedural-worlds** (private), branch `master` tracks `origin/master`. Push after every commit.

## Status (read this first)
- **Ink style module (`ink.py`) — done, applied to every scene by `core.generate()`:** Line Art (GP v3) heavy silhouettes + thin inner/crease/intersection lines with noise, taper, overshoot; `PW_InkToon` cel bands + muted shadow hue + occlusion-gated hatching + AO grime/stains/drips; `PW_InkWonk` GN wobble; inked sky world (bands, outlined clouds, sun/moon disc, stars); compositor (line wobble, paper tint/mottle/grain, blots, smudges, warm vignette, bloom for strong emitters).
- **Scenes (all three registered, grids looked at, invariants pass):**
  - `COASTAL_ISLAND` (`scene_island.py`): cliffs with inked strata, lighthouse + cottage, sea stacks, GN grass, ink-authored sea with foam rings (baked `pw_shore` attribute), gulls. Heroes: `renders/hero/coastal_island_*.jpg`.
  - `KITCHEN` (`scene_kitchen.py`, the showpiece, built by a subagent): checker floor, teal trim, cabinets, cork board, pans, fridge, hallway beyond doorway, per-mood lamps. Heroes: `renders/hero/kitchen_*.jpg`.
  - `CYBERPUNK_ALLEY` (`scene_alley.py`, built by a subagent): modular buildings, fire escapes, blade neon signs, cables, lanterns, wet road with streak reflection decals. Heroes: `renders/hero/cyberpunk_alley_*.jpg`. Slow: 15-35 s/frame at 960x540 (Line Art).
- **Fly-through:** `anim.py` (`setup_flythrough`, `set_video_output`), operator `pw.flythrough`, `tools/flythrough.py` -> MP4; GP noise reseeds every 2 frames + compositor wobble keyed to frame = line boil. `tools/video_frames.py` decodes MP4 frames via the sequencer (no ffmpeg on this machine).
- **Panel:** presets, Ink/Realistic style toggle, quality, fly-through box. `blender_manifest.toml` present (not yet tested as an extension install).
- **Known issues:** night kitchen outlines *look* dark brown but measured line cores are ~0.04 (near-black); it is antialiasing over warm-lit surfaces, not a pipeline bug (GP layer/object lights are off); NIGHT palette is dark on lit scenes (alley lifts its own colours); realistic mode keeps the stylized island sea; island gulls tiny.

## Phase 1 status (verified vs not)
- VERIFIED: `story/schema.json`; `story/catalog.json` (stageable generators + focus points + keywords); `story/parse.py` offline path (parses `story/texts/the_night_shift.txt` into 4 scenes/12 beats, validates); 3 example stories in `story/examples/` validate (`the_last_watch` 12 beats, `neon_debt` 11, `the_night_shift` 12); `procedural_worlds/shots.py` + `focus_points` in all 3 generators; `tools/render_story.py --stills-only` for both main stories (every panel looked at: reads as its shot/focus); `tools/export_animatic.py` (tested on stills: title card, captions in a hand-lettered font, cross-fades, end card).
- NOT VERIFIED YET: Gemini path of parse.py (needs `GEMINI_API_KEY`, user will provide at the end; model via `GEMINI_MODEL`, default gemini-2.5-flash); full clip renders + MP4 encode; web player (subagent building it in a worktree); Vercel deploy (Vercel MCP connected, team "Vectre" `team_UlrEstSY0rSG0sWAY2YhnCw5`; plan: `create_git_project` repo fabastic/procedural-worlds, rootDirectory `web`).
- Timing: kitchen/island beats ~3-6 s per drawing at 1280x720, alley 15-35 s per drawing (Line Art). A 3 s beat = 18 drawings (on twos).

## In progress right now
- Rendering clips for `the-last-watch` (background), then `neon-debt`; web player subagent; then sync -> deploy.

## Running Blender headless on this machine (important)
- The Store install's `blender.exe` (`C:\Program Files\WindowsApps\BlenderFoundation.Blender_5.2.2.0_x64__ppwjx1n5r4v9t\Blender\blender.exe`) **cannot be exec'd from Git Bash or PowerShell ("Access denied")**. Use the app-execution alias via **`tools/blender.sh`** (wraps `%LOCALAPPDATA%\Microsoft\WindowsApps\blender-launcher.exe`). The launcher drops stdout, so the wrapper redirects Python stdout/stderr to a temp log, replays it, and propagates the exit code (`--python-exit-code 3`).
- `tools/blender.sh -b --factory-startup -P tools/smoke_test.py -- COASTAL_ISLAND 1 [MOOD] [OUT] [RX RY]` — EEVEE ink render, ~4-15 s.
- `tools/blender.sh -b --factory-startup -P tools/grid.py -- COASTAL_ISLAND [1,7,42] [DAY,GOLDEN,DUSK,NIGHT]` — 12 renders in one session (~50 s) + contact sheet `renders/grid/<scene>_sheet.png`. Judge the sheet next to the reference.
- `tools/blender.sh -b --factory-startup -P tools/check_invariants.py -- [SCENE ...]`.
- Scripts delete the factory cube/camera/light first (they'd pollute renders).

## Blender 5.x API facts (don't relearn)
- EEVEE engine id `BLENDER_EEVEE`; Principled sockets `Transmission Weight`, `Emission Color`, `Emission Strength`; `ShaderNodeMix` sockets share names -> look up by identifier (`Factor_Float`, `A_Color`, `B_Color`, out `Result_Color`); enum introspection unreliable -> try/except assignments.
- **Compositor:** `scene.node_tree` is gone; use `scene.compositing_node_group = bpy.data.node_groups.new(name, "CompositorNodeTree")`; output is a `NodeGroupOutput` (+ `tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")`), there is no Composite node. Shader texture/math nodes (`ShaderNodeTexNoise`, `TexVoronoi`, `TexWhiteNoise`, `TexWave`, `Math`, `Mix`, `MapRange`, `VectorMath`, `SeparateXYZ`) work inside compositor trees; coordinates come from `CompositorNodeImageCoordinates` (outputs `Uniform`, `Normalized`, `Pixel`). Render Layers only exposes `Image`/`Alpha` unless passes are enabled.
- **Grease Pencil v3:** data is `bpy.data.grease_pencils` (type `GreasePencil`), object type `GREASEPENCIL`. Line Art is an object modifier `"LINEART"` (`GreasePencilLineartModifier`), thickness is **`radius` in world metres** (default 0.0025 = invisible at scene scale; no screen-space option) -> ink.py derives it from camera distance + lens. Other modifiers: `GREASE_PENCIL_NOISE/THICKNESS/LENGTH/SUBDIV/...`; layer filter is `tree_node_filter`. Set `gp.stroke_depth_order = "2D"` for Line Art (with "3D" the strokes z-fight under the surfaces and vanish). Length modifier `random_*_factor` is a fraction of stroke length (0.6 = huge stray tails); keep `use_curvature=False`.
- **Geometry Nodes modifier inputs:** `md["Socket_1"] = v` raises in 5.x; use `md.properties.inputs.Socket_1.value = v` (+ `obj.update_tag()`); see `ink.set_modifier_input`.
- `obj.matrix_world` is stale right after creating/moving objects in a script -> `context.view_layer.update()` before reading it.
- Light Path "Is Camera Ray" works in the EEVEE world shader (camera sees the inked sky, lighting sees a flat ambient).
- Freestyle still exists (`scene.render.use_freestyle`) but is unused.
- Live bridge: Blender 5.x needs **Preferences > System > Network > Allow Online Access** ON, then Preferences > Add-ons > MCP > **Start MCP Bridge Server** (port 9876).

## Layout
```
procedural_worlds/        the add-on package (zip this folder to install)
  __init__.py             bl_info, PropertyGroup, operators (generate / random seed), panel
  core.py                 collection mgmt + purge, fbm noise, material helpers, mood lighting, camera, render setup, generate()
  ink.py                  ink style: toon group, wobble GN group, Line Art outlines, inked sky world, compositor
  scenes.py               REGISTRY only
  scene_island.py         coastal island generator
  scene_kitchen.py        kitchen interior generator
  scene_alley.py          cyberpunk alley generator
tools/blender.sh          headless Blender wrapper (see above)
tools/smoke_test.py       one EEVEE ink render + invariant asserts
tools/grid.py             seed x mood grid + contact sheet
tools/check_invariants.py determinism / leak / naming check
tools/hero.py             1920x1080 full-quality JPEG heroes -> renders/hero/
renders/                  output stills (png gitignored except renders/hero/)
```

## Contracts
- A scene generator is a class with `LABEL` and `build(col, seed, size, detail, height, mood="GOLDEN", **kw) -> dict`. It must add ALL objects to `col` (collection `PW_Generated`), name them `PW_*`, be deterministic for a seed (`random.Random(seed)` only), and returns info: `camera` (`target`, `distance`, `height`, `angle`, `lens`, or explicit `location`; `clip_end`, `shift_y`), optional `sun_dir=(elev_deg, azim_deg)`, `sun_scale`, `sky_scale`, `ink={line_scale, wobble, grime, hatch, sea_color, ao_distance}`. Register it in `scenes.REGISTRY`; the panel enum picks it up.
- `core.generate(..., ink=True)` clears previous `PW_*` objects + purges zero-user `PW_*` datablocks, builds, applies mood lighting (DAY/GOLDEN/DUSK/NIGHT, `core.MOODS`), camera, then `ink.apply()` and render setup (ink forces `BLENDER_EEVEE` + Standard view transform). `ink=False` strips ink nodes and renders realistic (Cycles/AgX by default).
- **Focus points (story contract, Phase 1):** every generator returns `info["focus_points"] = {name: {"pos", "view", "size"}}` (built with `shots.focus_point` / `shots.focus_from_objects`; `view` points to the side the focus is best seen from) and `info["spawn"]`. `shots.compute_shot(info, shot, focus)` turns a shot type (establishing|wide|medium|close|POV|low|high|OTS) + camera_move into a start/end camera, ray-casting so cameras stay out of walls and above floors (interiors: probe down from just above the camera, never from the sky). `ink.retarget(scene, distance, lens)` re-sizes Line Art per shot.
- Ink hints: `obj["pw_line"]=0` (no outlines), `obj["pw_wonk"]` (wobble multiplier, 0 = off), `mat["pw_flat"]=1` (flat unlit), `mat["pw_hatch"]`, `mat["pw_grime"]`, `mat["pw_ink_custom"]=1` (material authored for ink already; untouched). Materials with Emission Strength > 0 become flat bright "neon ink" (>= 2 also blooms).
- How ink converts materials: keeps the original node tree, inserts group `PW_InkToon` fed by whatever drives the Principled Base Color, relinks the output (original link remembered in `mat["pw_ink_orig"]`, restored by `ink.remove()`).

## How to verify (do this loop)
1. Change code, render (`tools/grid.py` for the seed x mood sheet, smoke test for a single frame).
2. LOOK at the image next to `reference/ink_style_ref.png`; write a 3-line critique (reads hand-drawn? worst issue? next fix?); fix it. "No errors" is not success.
3. `tools/check_invariants.py` before committing.

## Roadmap (Story App phases)
- **Phase 1 — animated ink comic.** `story/schema.json` (shared format for all phases), `story/parse.py` (**Gemini API** via `GEMINI_API_KEY` — user decision 2026-10-16, key supplied at the very end; offline keyword fallback; schema validation), `story/examples/` (2+ stories, 10-14 beats), `procedural_worlds/shots.py` (scene info + shot type + focus -> camera; every generator exposes named `focus_points`), `tools/render_story.py` (per beat 2-4 s clip at 12 fps on twos, 1280x720, + still.jpg -> `story_out/<slug>/`), `web/` (Vite+TS motion-comic player: inked borders, caption/speech boxes, ink-wipe transitions, 2-4 panel pages, keyboard/click/autoplay, chapters, library, "Paste your story" page), `tools/export_animatic.py` (full MP4 via Blender sequencer, captions, transitions), deploy to Vercel. EXIT: 2 example stories play end to end in the deployed player + export MP4; every panel reads as its shot/focus; feels like an inked graphic novel that quietly moves.
- **Phase 2 — every kind of story.** Layers as data in `presets/` (base, setting kits, era, genre/mood grade, conditions, state), tagged prop library + scatter rules, parser maps stories onto layers, coverage across domestic/civic/urban/transit/nature/settlements/fantasy-scifi/dramatic, `tools/coverage.py` + `COVERAGE.md`, `tools/beats.txt` (50 beats). EXIT: 45/50 beats read correctly, every category has entries, 4+ new example stories deployed.
- **Phase 3 — walk the story in first person.** `tools/build_world.py` -> GLB per scene (baked ink colours, collision, spawn/focus/trigger empties, interactables), web "Walk" mode (Three.js FPS controller, real-time toon + edge ink + boil + grain, beats at triggers, Comic/Walk toggle), 60 fps. EXIT: both modes work for every example story deployed; the kitchen in Walk mode feels like stepping into the reference.

## Conventions
- No external deps; pure `bpy`/`bmesh`/`mathutils` (+ numpy only in tools). Everything procedural, no image textures.
- Commit messages short and imperative. Don't commit large renders (>2 MB); keep hero renders in `renders/hero/`.
