bl_info = {
    "name": "GP Onion Peel",
    "description": "Custom Onion skinning using refreshed linked GP duplications",
    "author": "Samuel Bernou",
    "version": (0, 5, 0),
    "blender": (2, 92, 0),
    "location": "View3D",
    "warning": "Beta",
    "doc_url": "https://github.com/Pullusb/GP_onion_peel",
    "category": "Object" }

if 'bpy' in locals():
    import importlib as imp
    imp.reload(OT_onion_peel)
    imp.reload(properties)
    imp.reload(ui_panels)
    imp.reload(onion)

else:
    from . import OT_onion_peel
    from . import properties
    from . import ui_panels
    from . import onion

# from . import preferences

import bpy

### --- REGISTER ---

def register():
    properties.register()
    OT_onion_peel.register()
    ui_panels.register()
    bpy.app.handlers.frame_change_post.append(onion.update_onion)

def unregister():
    bpy.app.handlers.frame_change_post.remove(onion.update_onion)
    ui_panels.unregister()
    OT_onion_peel.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()