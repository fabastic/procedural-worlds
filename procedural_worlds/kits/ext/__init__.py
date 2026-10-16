"""Extension modules: every .py in this package is imported once, so a module can register
- props:      from ..props import prop, _box, _cyl, OLD, MID, NOW, FUT  (decorate builder functions)
- room features:   from ..room import FEATURES as ROOM_FEATURES;  ROOM_FEATURES["name"] = fn(room)
- street features: from ..street import FEATURES as STREET_FEATURES
- terrain:   from ..terrain import BIOMES, LANDMARKS, SCATTER
- new kits:  from ...scene_composed import KITS  (import inside a function to avoid cycles)
and ship its settings as presets/settings.d/<module>.json (merged by core.load_preset)."""
import importlib, pkgutil

for _m in sorted(m.name for m in pkgutil.iter_modules(__path__)):
    importlib.import_module(f"{__name__}.{_m}")
