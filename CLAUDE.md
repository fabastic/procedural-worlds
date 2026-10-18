# Procedural Worlds — Blender add-on (handoff for Claude Code)

## What this is
**A story app.** The user pastes any story and gets it told in the hand-inked graphic-novel style: Phase 1 as an animated comic, Phase 2 across any kind of setting, Phase 3 as a world they walk through in first person as the protagonist. One data format, one pipeline:
`story text -> story.json (story/parse.py) -> Blender builds settings (procedural_worlds generators + ink.py) -> outputs (comic panels/clips, later walkable GLB) -> web app (web/) deployed on Vercel.`
The Blender add-on (`procedural_worlds/`, panel View3D > N > Worlds) is the engine: it builds complete seeded scenes (geometry, materials, lights, camera) and renders them as inked panels. No character models: stories are told through places, objects, POV, captions and off-panel dialogue.

**Current phase: 2** (every kind of story); Phase 1 exit criteria met 2026-10-17 00:15 IST. Master prompt rules: commit+push after every working step; never ask; look at every visual change (3-line critique vs reference); parallel subagents for independent work; invariants below.

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

## Phase 1 — DONE (verified 2026-10-17)
- Deployed player: **https://procedural-worlds-gamma.vercel.app** (alias procedural-worlds-vectre.vercel.app); Vercel project `procedural-worlds` in team Vectre (`web/.vercel/project.json`, gitignored). The Vercel MCP `create_git_project` returns 403 (account cannot create projects), so deploy with the logged-in CLI: `cd web && npx vercel deploy --prod --yes`. Not git-linked: redeploy after `npm run sync`.
- Both stories (`the-last-watch` 12 beats, `neon-debt` 11) rendered with `tools/render_story.py`, animatics via `tools/export_animatic.py` (38 s / 34 s), play end to end in the deployed reader (checked live: clips play, captions, balloons, ink-wipe). Story media is committed in `web/public/stories/` (~40 MB, deliberate exception to the 2 MB render rule: the static deploy needs it).
- Web player `web/` (Vite + TS, subagent-built): inked panel pages, caption boxes, off-panel balloons (spiky for RADIO/PHONE), ink-wipe transitions, autoplay, chapters, library, paste page. `npm run sync -- --from <story_out>`.
- Parser: **Gemini works** (`gemini-3.8-flash`, newest-first fallback list in `story/parse.py`; 2.5 is closed to new users). Key lives ONLY in the gitignored repo-root `.env` (`GEMINI_API_KEY=...`, template `.env.example`); `parse.py` loads it. Never print or commit it. Test output: `story/examples/the_night_shift_gemini.json` (3 scenes, 13 beats).
- Nits: neon-debt b04 (puddle close-up) very dark; joined-prop inner contours thin/doubled at close range.

## Phase 2 status (verified vs not)
- VERIFIED: layers as data in `procedural_worlds/presets/` (`genre.json` 10 grades, `era.json` 7 eras, `conditions.json`, `settings.json` 33 entries); kits in `procedural_worlds/kits/` (`room.py` 22 features, `street.py`, `terrain.py` 9 biomes + landmarks); tagged prop library `kits/props.py`; `COMPOSED` generator takes `layers`; genre grades drive palette/ink/hatch/vignette + dutch angle; lamp-lit night interiors via `info["ink"]["light_tint"]`. `tools/coverage.py` + `tools/coverage_report.py` -> `COVERAGE.md` + `renders/coverage/<category>_sheet.jpg`: **99/99 OK**. `tools/layers_grid.py` renders arbitrary layer specs. `story/catalog.json` `composed` section generated by `tools/build_catalog.py`.
- NOT YET: parser choosing composed settings (offline + Gemini prompt), `tools/beats.txt` (50 beats) + judging, transit/underground/water bases, more civic rooms (shop, factory, lab, courtroom, kids room, bathroom, attic), 4+ new example stories deployed.

## In progress right now (2026-10-17 20:00 IST)
- 4 asset-pack subagents in worktrees (interiors, urban+transit, nature+settlements, fantasy/sci-fi/horror), each writing only `procedural_worlds/kits/ext/<pack>*.py` + `presets/settings.d/<pack>.json`; briefed on the 15-era timeline. Review their prop sheets + layer sheets, merge, run coverage.
- Godot walk mode RUNS (Godot 4.7.2 extracted to gitignored `.tools/godot/`; launch `walk.bat [slug]`). Verified by screenshots of all 3 scenes of the-last-watch + the story picker. Lighting: `ink_toon.gdshader` is UNSHADED and computes the 3 cel bands itself from `key_dir` (imported glTF lamp energies are unusable); tints are plain vec3 (NOT source_color: that double-converted sRGB and made everything dark navy). Test hook: `--shot <png> --frames N --scene i [--debug-raw|--debug-edges|--debug-albedo|--debug-lights]`. Not yet tried by hand with keyboard/mouse.
- Asset packs relaunched 2026-10-18 as 4 new subagents finishing the saved WIP in worktrees `agent-ae90ac0f5ff0c18f0` (interiors), `agent-ac3247cb77b1ee879` (urban+transit), `agent-nature`, `agent-genre-fx`; review sheets, then merge each branch.
- Walk mode verified for both stories (the-last-watch, neon-debt worlds built).

## Phase 3 groundwork (verified vs not)
- VERIFIED: `tools/build_world.py` exports per-scene GLB (COLOR_0 baked ink colours, alpha 0 = unlit faces, GN wobble applied, PW_Spawn / PW_Focus_* / PW_Trigger_* empties with extras, `__nocol` on sky cards/decals, KHR lights) + `world.json` (Godot coords, sky colours, sun dir, beats with trigger pos/radius). the-last-watch: 3 GLBs in 9 s.
- NOT VERIFIED: `godot/` project (main.gd loader + story flow, player.gd FPS controller, hud.gd caption/balloons/ink-wipe, shaders ink_toon / ink_post (depth+normal edges boiling at 6 fps, hatching, paper) / sky / ink_wipe). Run: `godot --path godot -- --story ../story_out/<slug>/world` (no arg = story picker).

## Weather (done 2026-10-18)
- `ink._weather` in the compositor reads `layers.weather` via `presets/conditions.json`: rain/storm = slanted inked strokes, snow = flakes with ink rim (both step on twos), fog/mist = paper-coloured horizon band, heat-haze = warm streaky haze. Terrain also gets snow cover when `snow_cover`.

## Era timeline (data)
- `presets/era.d/timeline.json`: 15 eras (classical_antiquity, early_high_middle_ages, renaissance_discovery, enlightenment_piracy, victorian_industrial, interwar, cold_war, analog_digital, contemporary, near_future, cyberpunk, solarpunk, post_apocalyptic, space_age, far_future) with 41 cultures (layers.culture). `core.resolve_era(layers)` resolves aliases + culture overrides; each era has a legacy `family` and `props.OLD/MID/NOW/FUT` include the new keys (`props.in_family`). Extension points: `kits/ext/*.py` auto-imported (props, room/street FEATURES, terrain BIOMES/SCATTER/LANDMARKS, new KITS), `presets/<kind>.d/*.json` merged by `core.load_preset`. `tools/prop_sheet.py` renders the prop catalog per era.

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
- **Installing into the user's Blender (Store/MSIX app):** its AppData is virtualized; the addons folder seen from bash is NOT what Blender reads (real path under `%LOCALAPPDATA%\Packages\BlenderFoundation.Blender_ppwjx1n5r4v9t\LocalCache\Roaming\...`). Reinstall from inside Blender via MCP `execute_blender_code`: shutil.copytree repo `procedural_worlds` -> `bpy.utils.user_resource("SCRIPTS", path="addons")`, purge `sys.modules`, `addon_utils.enable`. Done + verified 2026-10-17 (all 4 scene types generate from the panel operator).
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
- **Phase 3 — walk the story in first person.** USER DECISION 2026-10-17: **no Three.js. Blender builds every asset/world; Godot (4.x) runs the game** from Blender-exported GLBs. `tools/build_world.py` -> `story_out/<slug>/world/<scene>.glb` (baked ink colours as vertex colours, emissives kept, spawn/focus/trigger empties with extras) + `world.json`; `godot/` project loads any story folder at runtime (people run it on their own machines): FPS controller, collision from meshes, real-time ink (toon bands + screen-space edge ink with boil + paper grain), captions/dialogue at triggers, interact key. EXIT: both modes work for every example story deployed; the kitchen in Walk mode feels like stepping into the reference.

## Conventions
- No external deps; pure `bpy`/`bmesh`/`mathutils` (+ numpy only in tools). Everything procedural, no image textures.
- Commit messages short and imperative. Don't commit large renders (>2 MB); keep hero renders in `renders/hero/`.
