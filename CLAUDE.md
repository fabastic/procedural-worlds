# Procedural Worlds — Blender add-on (handoff for Claude Code)

## What this is
A Blender add-on (Python/`bpy`). One sidebar panel (View3D > N > **Worlds**): pick a scene type, seed, size, mood -> it builds a *complete* scene: geometry, procedural materials, lighting, camera, render settings. Goal: impressive showcase renders + a reusable tool. Not a web/Three.js project.

## Status (read this first)
- **Verified in Blender 5.2.2 LTS (Windows), everything checked:** headless `tools/smoke_test.py` runs (`blender -b --factory-startup -P tools/smoke_test.py -- COASTAL_ISLAND 1`, ~24 s, writes `renders/coastal_island_1.png`, real Cycles render, looked at); installing `procedural_worlds` zip via Preferences > Add-ons > Install from Disk works, enables, panel ("Worlds" N-tab) registers; `pw.generate` / `pw.randomize` FINISHED; 4 moods apply; seeds differ; regenerate is leak-free (81 objects). Blender binary on this machine: `C:\Program Files\WindowsApps\BlenderFoundation.Blender_5.2.2.0_x64__ppwjx1n5r4v9t\Blender\blender.exe` (Store install; call it with the full path, or from live Blender via `bpy.app.binary_path` + subprocess).
- **What the first Cycles render actually shows (fix these first):** water plane EDGE visible at the horizon (plane too small / needs infinite ocean or camera clip + fog); sky is a flat orange wall (use Nishita/Sky Texture or gradient + sun disc); rocks are faceted low-poly blobs (smooth shading, subdivision, noise displacement, varied shapes); island is beige, flat and low-contrast (more relief, cliffs, darker wet sand band, real grass colour, stronger key light/shadows); stones too small to read as a focal point; no foliage, no foam, no atmosphere/fog, default framing.
- **Blender 5.x API facts found (don't relearn):** EEVEE engine id is `BLENDER_EEVEE` (`BLENDER_EEVEE_NEXT` no longer exists); `scene.cycles` exists when Cycles add-on is on; Principled sockets are `Transmission Weight`, `Emission Color`, `Emission Strength`; `ShaderNodeMix` input sockets share names, so look up by **identifier** (`Factor_Float`, `A_Color`, `B_Color`, output `Result_Color`); introspecting `bl_rna.properties[...].enum_items` for engine/view_transform is unreliable (static lists) -- just try/except the assignment.
- Live bridge: Blender 5.x needs **Preferences > System > Network > Allow Online Access** ON, then Preferences > Add-ons > MCP > **Start MCP Bridge Server** (port 9876; Auto Start is available). Target is Blender 5.2 (`bl_info` says 4.0+ minimum).

## Layout
```
procedural_worlds/        the add-on package (zip this folder to install)
  __init__.py             bl_info, PropertyGroup, operators (generate / random seed), panel
  core.py                 collection mgmt, fbm noise, material helpers, mood lighting, camera, render setup, generate()
  scenes.py               scene generators + REGISTRY  (CoastalIsland is the only one)
tools/smoke_test.py       headless: blender -b -P tools/smoke_test.py -- COASTAL_ISLAND 1  -> renders/coastal_island_1.png
renders/                  output stills
```

## Contracts
- A scene generator is a class with `LABEL` and `build(col, seed, size, detail, height) -> dict`. It must add ALL objects to `col` (collection `PW_Generated`), name them `PW_*`, be deterministic for a seed, and may return `{"camera": {target, distance, height, angle, lens}}`. Register it in `scenes.REGISTRY`; the panel enum picks it up automatically.
- `core.generate()` clears previous `PW_*` objects, builds, then applies mood lighting (DAY/GOLDEN/DUSK/NIGHT), camera, render setup. Moods live in `core.MOODS`.
- Target Blender 5.2 (min 4.0 in `bl_info`); default engine Cycles w/ denoise, AgX view transform (Filmic fallback).

## How to verify (do this loop)
1. **Headless:** `blender -b -P tools/smoke_test.py -- COASTAL_ISLAND 1` then open the PNG and judge it.
2. **Live (if MCP connected):** in Blender press N > BlenderMCP tab > Start server (port 9876). Then use the Blender MCP tools: `execute_blender_code`, `get_screenshot_of_window_as_image`, `render_viewport_to_path`. Install add-on live via `sys.path.insert(0, repo); import procedural_worlds; procedural_worlds.register()`, then `bpy.ops.pw.generate()`.
3. Always look at the image. "No error" != "looks good". Check several seeds (1, 7, 42) and all four moods.

## Roadmap (in order)
1. Make CoastalIsland run + look good (water foam/shore, grass scatter via Geometry Nodes, better rock shapes, fog/volume, a lighthouse or ruin as focal point).
2. Packaging: install-from-zip works; Blender 4.2+ `blender_manifest.toml` extension format; Cycles vs EEVEE Next preset; save/restore panel presets.
3. Scene #2 **Cyberpunk alley** (modular buildings, emissive signs, wet-road reflections, volumetric haze). Scene #3 **Mountain village** (terrain + procedural houses + paths).
4. Move heavy scattering to **Geometry Nodes** node groups (instancing, weight-painting-free density by slope/height).
5. Animation: camera fly-through path + time-of-day sweep; "Render turntable/clip" operator.
6. Showcase: 6 hero renders (3 scenes x 2 moods), README with images, short MP4.

## Conventions
- No external deps; pure `bpy`/`bmesh`/`mathutils`. Keep files small; one generator per class.
- Prefer procedural materials (no image textures) so the zip stays tiny.
- Commit messages short and imperative. Don't commit large renders (>2 MB); keep hero renders in `renders/hero/`.
