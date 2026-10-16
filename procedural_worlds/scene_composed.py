"""COMPOSED generator: builds any setting from story layers (presets/settings.json + era + genre +
conditions) through the kits. A story scene uses generator "COMPOSED" with layers.setting = an entry
name (diner, tavern, library, ...)."""
import bpy
from . import core
from .kits.room import Room
from .kits.street import Street
from .kits.terrain import Terrain

KITS = {"room": Room, "street": Street, "terrain": Terrain}


class Composed:
    """Any setting from story layers (setting, era, genre, weather, time, state)."""
    LABEL = "Composed (story layers)"

    @staticmethod
    def build(col, seed, size, detail, height, mood="DAY", layers=None, **kw):
        layers = dict(layers or {})
        settings = core.load_preset("settings")
        name = layers.get("setting") if layers.get("setting") in settings else "diner"
        entry = dict(settings[name])
        entry["_name"] = name
        layers.setdefault("era", entry["eras"][0])
        return KITS[entry["kit"]](col, entry, layers, seed, mood).run()
