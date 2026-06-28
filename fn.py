import bpy

def get_keyconfig_item(idname, catname=None, keymap_type='user',
                       allow_mouse=False, only_active=True, properties=None):
    """Return first keymap_item matching idname (and optional filters).
    If catname is given, restrict the search to keymaps whose name contains it.
    If properties is given (dict), the keymap_item's op properties must match all entries.
    Returns None if not found.
    examples: 
        get_keyconfig_item('wm.call_menu', properties={'name': 'VIEW3D_MT_object'})
        get_keyconfig_item('transform.translate', catname='Object Mode', properties={'release_confirm': True})
    """
    wm = bpy.context.window_manager

    keyconfigs = {
        'user': wm.keyconfigs.user,
        'default': wm.keyconfigs.default,
        'addon': wm.keyconfigs.addon,
    }
    keyconf = keyconfigs.get(keymap_type)
    if keyconf is None:
        print("keymap_type not in ('default', 'user', 'addon')")
        return None

    for cat, keymap in keyconf.keymaps.items():
        if catname is not None and catname not in cat:
            continue
        for k in keymap.keymap_items:
            if k.idname != idname:
                continue
            if only_active and not k.active:
                continue
            if not allow_mouse and k.map_type in ('MOUSE', 'TRACKPAD'):
                continue
            if properties:
                if k.properties is None:
                    continue
                if not all(getattr(k.properties, key, None) == val
                           for key, val in properties.items()):
                    continue
            return k
    return None


