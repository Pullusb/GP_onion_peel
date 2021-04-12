import bpy
from .onion import update_onion, update_opacity



class GPOP_PGT_settings(bpy.types.PropertyGroup) :
    ## HIDDEN to hide the animatable dot thing
    # stringprop : bpy.props.StringProperty(
    #     name="str prop", description="", default="")# update=None, get=None, set=None

    # mode : bpy.props.EnumProperty(
    #     name="bool prop", description="", default=False, options={'HIDDEN'})#options={'ANIMATABLE'},subtype='NONE', update=None, get=None, set=None
    offset_mode : bpy.props.EnumProperty(
        name="Mode", description="Ghost offset mode", default='KEYS', options={'HIDDEN'}, update=None, get=None, set=None,
        items=(
            ('KEYS', 'Keys', 'Ghost number are keys', 1),   
            ('FRAMES', 'Frames', 'Ghost number are frames', 0),
            ))
        # (key, label, descr, id[, icon])

    before_num : bpy.props.IntProperty(
        name="Before", description="Number of previous ghost displayed",
        default=2, min=1, max=10, soft_min=1, soft_max=10, step=1, options={'HIDDEN'}, update=update_onion)
    
    after_num : bpy.props.IntProperty(
        name="After", description="Number of next ghost displayed",
        default=2, min=1, max=10, soft_min=1, soft_max=10, step=1, options={'HIDDEN'}, update=update_onion)
    
    activated : bpy.props.BoolProperty(name='Activate', default=True)

    # opacity
    o_p1: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_p2: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_p3: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_p4: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_p5: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_p6: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_p7: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_p8: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_p9: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_p10: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_general: bpy.props.IntProperty(default=50, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_n1: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_n2: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_n3: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_n4: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_n5: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_n6: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_n7: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_n8: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_n9: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    o_n10: bpy.props.IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)

    # visibility
    v_p1: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_p2: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_p3: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_p4: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_p5: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_p6: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_p7: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_p8: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_p9: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_p10: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    # v_general: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_n1: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_n2: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_n3: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_n4: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_n5: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_n6: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_n7: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_n8: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_n9: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
    v_n10: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)

    # # Matrix move store ## Nope, should be at object level
    # mat_p1: bpy.props.StringProperty(default='')
    # mat_p2: bpy.props.StringProperty(default='')
    # mat_p3: bpy.props.StringProperty(default='')
    # mat_p4: bpy.props.StringProperty(default='')
    # mat_p5: bpy.props.StringProperty(default='')
    # mat_p6: bpy.props.StringProperty(default='')
    # mat_p7: bpy.props.StringProperty(default='')
    # mat_p8: bpy.props.StringProperty(default='')
    # mat_p9: bpy.props.StringProperty(default='')
    # mat_p10: bpy.props.StringProperty(default='')
    # mat_n1: bpy.props.StringProperty(default='')
    # mat_n2: bpy.props.StringProperty(default='')
    # mat_n3: bpy.props.StringProperty(default='')
    # mat_n4: bpy.props.StringProperty(default='')
    # mat_n5: bpy.props.StringProperty(default='')
    # mat_n6: bpy.props.StringProperty(default='')
    # mat_n7: bpy.props.StringProperty(default='')
    # mat_n8: bpy.props.StringProperty(default='')
    # mat_n9: bpy.props.StringProperty(default='')
    # mat_n10: bpy.props.StringProperty(default='')

### --- REGISTER ---

classes=(
GPOP_PGT_settings,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
 
    bpy.types.Scene.gp_ons_setting = bpy.props.PointerProperty(type = GPOP_PGT_settings)
    # bpy.app.handlers.load_post.append(activator)

def unregister():
    # bpy.app.handlers.load_post.remove(activator)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.gp_ons_setting
