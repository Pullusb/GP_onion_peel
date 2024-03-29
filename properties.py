import bpy
from . import preferences
from .onion import update_onion, force_update_onion, update_opacity, update_peel_color

from bpy.props import BoolProperty, EnumProperty, \
    IntProperty, FloatVectorProperty, CollectionProperty, \
    PointerProperty, StringProperty, FloatProperty

class GPOP_PGT_frame_settings(bpy.types.PropertyGroup):
    opacity : IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    visibility : BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)
class GPOP_PGT_settings(bpy.types.PropertyGroup):

    activated : BoolProperty(name='Activate', default=False,
        description='Activate the onion skinning with auto-refresh on frame change',
        update=force_update_onion
        )
    
    ## Wip target choice
    # only_active : BoolProperty(name='Only Active', default=True,
    # description='Refresh only active object peels, and hide other, else refresh all (can slow down)')
    
    world_space : BoolProperty(name='World Space', default=False,
        description='Consider the object animation to place onion peels in world space (Else local space)\nIf your GP object does not move, disable for better performance')

    offset_mode : EnumProperty(
        name="Mode", description="Ghost offset mode", default='KEYS', options={'HIDDEN'}, update=None, get=None, set=None,
        items=(
            ('KEYS', 'Keys', 'Ghost number are keys', 0),   
            ('FRAMES', 'Frames', 'Ghost number are frames', 1),
            ))

    # xray : BoolProperty(name='X-ray', default=False,
    #     description='Set "In Front" mode for both object and the onion peels',
    #     update=update_peel_xray)


    keyframe_type : EnumProperty(
        name="Keyframe Filter", description="Only peel the onion for keyframe of chosen type", 
        default='ALL', options={'HIDDEN'}, update=force_update_onion,
        items=(
            ('ALL', 'All', '', 0), # 'KEYFRAME'
            ('KEYFRAME', 'Keyframe', '', 'KEYTYPE_KEYFRAME_VEC', 1),
            ('BREAKDOWN', 'Breakdown', '', 'KEYTYPE_BREAKDOWN_VEC', 2),
            ('MOVING_HOLD', 'Moving Hold', '', 'KEYTYPE_MOVING_HOLD_VEC', 3),
            ('EXTREME', 'Extreme', '', 'KEYTYPE_EXTREME_VEC', 4),
            ('JITTER', 'Jitter', '', 'KEYTYPE_JITTER_VEC', 5),
            ))

    before_color : FloatVectorProperty(  
        name="Before Color",
        subtype='COLOR',
        default=(0.019, 0.15, 0.017), # (0.157, 0.496, 0.151)
        min=0.0, max=1.0,
        description="Color for previous onion peels",
        update=update_peel_color
        )

    after_color : FloatVectorProperty(  
        name="After Color",
        subtype='COLOR',
        default=(0.014, 0.01, 0.25), #  (0.579, 0.158, 0.604)
        min=0.0, max=1.0,
        description="Color for next onion peels",
        update=update_peel_color
        )

    before_num : IntProperty(
        name="Before", description="Number of previous ghost displayed",
        default=2, min=1, max=32, soft_min=1, soft_max=16, step=1, options={'HIDDEN'}, update=force_update_onion)
    
    after_num : IntProperty(
        name="After", description="Number of next ghost displayed",
        default=2, min=1, max=32, soft_min=1, soft_max=16, step=1, options={'HIDDEN'}, update=force_update_onion)    

    pos_frames : CollectionProperty(type=GPOP_PGT_frame_settings)
    neg_frames : CollectionProperty(type=GPOP_PGT_frame_settings)
    
    o_general: IntProperty(default=50, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)

    frame_prev : IntProperty(
        name="frame prev", description="previous frame holder",
        default= -9999)

### --- REGISTER ---

classes=(
GPOP_PGT_frame_settings,
GPOP_PGT_settings,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.gp_ons_setting = PointerProperty(type = GPOP_PGT_settings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.gp_ons_setting
