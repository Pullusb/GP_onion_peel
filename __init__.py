bl_info = {
    "name": "GP Onion Peel",
    "description": "Custom Onion skinning using refreshed linked GP duplications",
    "author": "Samuel Bernou",
    "version": (0, 5, 2),
    "blender": (2, 92, 0),
    "location": "View3D",
    "warning": "Beta",
    "doc_url": "https://github.com/Pullusb/GP_onion_peel",
    "category": "Object" }

if 'bpy' in locals():
    import importlib as imp
    imp.reload(OT_onion_peel)
    imp.reload(OT_peel_modal)
    imp.reload(properties)
    imp.reload(ui_panels)
    imp.reload(onion)

else:
    from . import OT_onion_peel
    from . import OT_peel_modal
    from . import properties
    from . import ui_panels
    from . import onion


from . import onion

# from . import preferences

import bpy
from bpy.app.handlers import persistent
### --- REGISTER ---

@persistent
def delete_onion(dummy):
    # for o in bpy.context.scene.objects:
    #     if o.type != 'GPENCIL':
    #         continue
    
    #-#  for now just clear everything.
    # TODO -> need to backup the out of peg values at least for current object..
    bpy.types.ViewLayer.onion_was_active = bpy.context.scene.gp_ons_setting.activated
    onion.clear_peels(full_clear=False)

@persistent
def restore_onion(dummy):
    on = getattr(bpy.context.view_layer, 'onion_was_active')
    if not on:
        return
    else:
        # launch a refresh
        onion.update_onion(dummy, bpy.context)




def register():
    properties.register()
    OT_onion_peel.register()
    OT_peel_modal.register()
    ui_panels.register()

    bpy.app.handlers.frame_change_post.append(onion.update_onion)

    bpy.app.handlers.save_pre.append(delete_onion)
    bpy.app.handlers.save_post.append(restore_onion)

def unregister():

    bpy.app.handlers.save_pre.remove(delete_onion)
    bpy.app.handlers.save_post.remove(restore_onion)

    bpy.app.handlers.frame_change_post.remove(onion.update_onion)

    ui_panels.unregister()
    OT_peel_modal.unregister()
    OT_onion_peel.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()