bl_info = {
    "name": "GP Onion Peel",
    "description": "Custom Onion skinning using refreshed linked GP duplications",
    "author": "Samuel Bernou",
    "version": (0, 3, 1),
    "blender": (2, 92, 0),
    "location": "View3D",
    "warning": "WIP",
    "doc_url": "https://github.com/Pullusb/GP_onion_peel",
    "category": "Object" }

from . import OT_onion_peel
from . import properties
from . import ui_panels
from .onion import update_onion
# from . import preferences

import bpy

### --- REGISTER ---

def register():
    properties.register()
    OT_onion_peel.register()
    ui_panels.register()
    bpy.app.handlers.frame_change_post.append(update_onion)

def unregister():
    bpy.app.handlers.frame_change_post.remove(update_onion)
    ui_panels.unregister()
    OT_onion_peel.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()