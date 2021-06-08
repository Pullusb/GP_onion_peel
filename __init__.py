bl_info = {
    "name": "GP Onion Peel",
    "description": "Custom Onion skinning using refreshed linked GP duplications",
    "author": "Samuel Bernou",
    "version": (0, 7, 5),
    "blender": (2, 92, 0),
    "location": "View3D",
    "warning": "",
    "doc_url": "", # https://github.com/Pullusb/GP_onion_peel
    "category": "Object" }

if 'bpy' in locals():
    import importlib as imp
    imp.reload(OT_onion_peel)
    imp.reload(properties)
    imp.reload(ui_panels)
    imp.reload(preferences)
    imp.reload(onion)

else:
    from . import OT_onion_peel
    from . import properties
    from . import ui_panels
    from . import preferences
    from . import onion


from . import onion


import bpy
from bpy.app.handlers import persistent
### --- REGISTER ---

@persistent
def delete_onion(dummy):
    op_col = bpy.data.collections.get('.onion_peels')
    if not op_col:
        return
    transfo_list = []
    for o in op_col.all_objects:
        outapeg = o.get('outapeg')
        if not outapeg:
            continue
        outapeg = [v.to_list() for v in outapeg]
        transfo_list.append([o.name, outapeg])
    if transfo_list:
        bpy.types.ViewLayer.onion_custom_transform = transfo_list
    bpy.types.ViewLayer.onion_was_active = bpy.context.scene.gp_ons_setting.activated
    onion.clear_peels(full_clear=False)

@persistent
def restore_onion(dummy):
    on = getattr(bpy.context.view_layer, 'onion_was_active', None)
    if not on:
        return
    else:
        # launch a refresh
        onion.update_onion(dummy, bpy.context)
    
    transfo_list = getattr(bpy.context.view_layer, 'onion_custom_transform', None)
    if not transfo_list:
        return
    for name, outapeg in transfo_list:
        ob = bpy.data.objects.get(name)
        if not ob:
            continue
        ob['outapeg'] = outapeg
    # re-refresh to set the offset
    onion.update_onion(dummy, bpy.context)
    del bpy.types.ViewLayer.onion_custom_transform


@persistent
def load_onion(dummy):
    # restricted context during register so needed here.
    pref = preferences.get_addon_prefs()
    if pref.use_default_color:
        bpy.context.scene.gp_ons_setting.before_color = pref.default_before_color
        bpy.context.scene.gp_ons_setting.after_color = pref.default_after_color


def register():
    preferences.register()
    properties.register()
    OT_onion_peel.register()
    ui_panels.register()
    #-# assign default color if needed
    ## CANT DO here - restricted context

    bpy.app.handlers.frame_change_post.append(onion.update_onion)
    
    ## try trigerring on new key
    # bpy.types.ViewLayer.gp_len_frame = 0
    # bpy.app.handlers.depsgraph_update_post.append(onion.trigger_on_key)

    bpy.app.handlers.save_pre.append(delete_onion)
    bpy.app.handlers.save_post.append(restore_onion)
    bpy.app.handlers.load_post.append(load_onion)

def unregister():

    bpy.app.handlers.load_post.remove(load_onion)
    bpy.app.handlers.save_pre.remove(delete_onion)
    bpy.app.handlers.save_post.remove(restore_onion)

    bpy.app.handlers.frame_change_post.remove(onion.update_onion)
    # bpy.app.handlers.depsgraph_update_post.remove(onion.trigger_on_key)

    ui_panels.unregister()
    OT_onion_peel.unregister()
    properties.unregister()
    preferences.unregister()

if __name__ == "__main__":
    register()
