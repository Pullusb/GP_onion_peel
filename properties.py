import bpy
from .onion import update_onion, update_opacity

from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty, CollectionProperty, PointerProperty

class GPOP_PGT_frame_settings(bpy.types.PropertyGroup):
    opacity : IntProperty(default=100, min=1, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=update_opacity)
    visibility : BoolProperty(default=True, options={'HIDDEN'}, update=update_opacity)

# frames[0].add()
# frames.remove(index)

class GPOP_PGT_settings(bpy.types.PropertyGroup):

    activated : BoolProperty(name='Activate', default=False)

    offset_mode : EnumProperty(
        name="Mode", description="Ghost offset mode", default='KEYS', options={'HIDDEN'}, update=None, get=None, set=None,
        items=(
            ('KEYS', 'Keys', 'Ghost number are keys', 1),   
            ('FRAMES', 'Frames', 'Ghost number are frames', 0),
            ))
        # (key, label, descr, id[, icon])

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
