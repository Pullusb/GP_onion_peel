bl_info = {
    "name": "GP Onion Peel",
    "description": "Custom Onion skinning using refreshed linked GP duplications",
    "author": "Samuel Bernou",
    "version": (0, 3, 0),
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
# from bpy.app.handlers import persistent

# def update_p1(scene):
#     ob = bpy.context.scene.objects.get(bpy.context.object.name + ' -1')
#     if ob:
#         ob.grease_pencil_modifiers.get('tint')


### --- HANDLERS

# def update(dummy):
#     if bpy.context.screen.is_animation_playing:
#         op_col = bpy.data.collections.get('.onion_peels')
#         if op_col:
#             op_col.hide_viewport = True
        

## Is an on-load really needed ?
# @persistent
# def activator(dummy):
#     if bpy.context.scene.gp_ons_setting.activated:
        
    # if not lock_time_handle.__name__ in [hand.__name__ for hand in bpy.app.handlers.frame_change_pre]:
        # bpy.app.handlers.frame_change_pre.append(lock_time_handle)
        # lock_time()

# @persistent
# def onion_peel_update(scene):
#     update_onion(scene)

### --- REGISTER ---



# TODO Add handler on frame post to refresh the time offset

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