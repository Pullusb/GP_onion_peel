import bpy
from .onion import update_onion, update_opacity, update_peel_color#, switch_onion

from bpy.props import BoolProperty, EnumProperty, \
    IntProperty, FloatVectorProperty, CollectionProperty, \
    PointerProperty, StringProperty

class GPOP_PGT_frame_settings(bpy.types.PropertyGroup):
    opacity : IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    visibility : BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)

    ## Tranforms need to be stored at object level since there are multiple objects...
    # matrix : FloatVectorProperty(subtype='MATRIX', size=16, options={'HIDDEN'}) # default=(0.0, 0.0, 0.0, 0.0), 
    # transformed : BoolProperty(default=False) #Tell if a transform (matrix) is applied to the peel.
    
    ## works like this
    # frames[0].add()
    # frames.remove(index)

class GPOP_PGT_settings(bpy.types.PropertyGroup):

    activated : BoolProperty(name='Activate', default=False,
    description='Activate the onion skinning with auto-refresh on frame change',
    # update=switch_onion
    )
    
    # only_active : BoolProperty(name='Only Active', default=True,
    # description='Refresh only active object peels, and hide other, else refresh all (can slow down)')
    
    world_space : BoolProperty(name='World Space', default=False,
    description='Consider the object animation to place onion peels in world space (Else local space)\nIf your GP object does not move, disable for better performance')

    offset_mode : EnumProperty(
        name="Mode", description="Ghost offset mode", default='KEYS', options={'HIDDEN'}, update=None, get=None, set=None,
        items=(
            ('KEYS', 'Keys', 'Ghost number are keys', 1),   
            ('FRAMES', 'Frames', 'Ghost number are frames', 0),
            ))
        # (key, label, descr, id[, icon])

    before_color : FloatVectorProperty(  
        name="Before Color",
        subtype='COLOR',
        default=(0.019, 0.15, 0.017),
        min=0.0, max=1.0,
        description="Color for previous onion peels",
        update=update_peel_color
        )

    after_color : FloatVectorProperty(  
        name="After Color",
        subtype='COLOR',
        default=(0.014, 0.01, 0.25),
        min=0.0, max=1.0,
        description="Color for next onion peels",
        update=update_peel_color
        )

    before_num : IntProperty(
        name="Before", description="Number of previous ghost displayed",
        default=2, min=1, max=10, soft_min=1, soft_max=10, step=1, options={'HIDDEN'}, update=update_onion)
    
    after_num : IntProperty(
        name="After", description="Number of next ghost displayed",
        default=2, min=1, max=10, soft_min=1, soft_max=10, step=1, options={'HIDDEN'}, update=update_onion)    

    # frames : CollectionProperty(type=GPOP_PGT_frame_settings)
    pos_frames : CollectionProperty(type=GPOP_PGT_frame_settings)
    neg_frames : CollectionProperty(type=GPOP_PGT_frame_settings)
    
    o_general: IntProperty(default=50, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)

### --- REGISTER ---

classes=(
GPOP_PGT_frame_settings,
GPOP_PGT_settings,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.gp_ons_setting = PointerProperty(type = GPOP_PGT_settings)
    # bpy.app.handlers.load_post.append(activator)

def unregister():
    # bpy.app.handlers.load_post.remove(activator)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.gp_ons_setting
