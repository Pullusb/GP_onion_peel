import bpy

from bpy.props import BoolProperty, EnumProperty, \
    IntProperty, FloatVectorProperty, CollectionProperty, \
    PointerProperty, StringProperty, FloatProperty

def get_addon_prefs():
    '''
    function to read current addon preferences properties
    access with : get_addon_prefs().super_special_option
    '''
    import os 
    addon_name = os.path.splitext(__name__)[0]
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons[addon_name].preferences
    return (addon_prefs)
class GPOP_addon_prefs(bpy.types.AddonPreferences):
    bl_idname = __name__.split('.')[0]

    depth_offset : FloatProperty(name='Depth Offset', default=0.035,
        soft_min=0.001, soft_max=10,
        min=0.0001, max=100,
        precision=3, step=2,
        description='Offset the onion peels in the depth from active camera\
            \nIncrement if peels are overlapping each other'
        )

    peel_in_front : BoolProperty(name='Peel In Front',
        default=False,
        description='Show peel in front of the object instead of behind (can be usefull when doing fill color)')

    use_default_color : BoolProperty(name='Use Default Color',
        description='Set these default color as onion skin when opening a blend')

    default_before_color : FloatVectorProperty(  
        name="Before Color",
        subtype='COLOR',
        default=(0.019, 0.15, 0.017), # (0.157, 0.496, 0.151)
        min=0.0, max=1.0,
        description="Color for previous onion peels",
        )

    default_after_color : FloatVectorProperty(  
        name="After Color",
        subtype='COLOR',
        default=(0.014, 0.01, 0.25), #  (0.579, 0.158, 0.604)
        min=0.0, max=1.0,
        description="Color for next onion peels",
        )

    use_osd_text : BoolProperty(name='Show help text', default=True,
    description='Display a help text when using custom transformation')

    def draw(self, context):
            layout = self.layout
            layout.label(text='If some peels opacity overlap others, try bigger offset value')
            layout.prop(self, 'depth_offset', text='Peel Depth Offset')
            layout.prop(self, 'peel_in_front', text='Peels In Front (only usefull when working with fills)')

            box = layout.box()
            col = box.column()
            col.prop(self, 'use_default_color', text='Set following Onion peel color when opening a blend file')
            row = col.row()
            row.enabled = self.use_default_color
            row.prop(self, 'default_before_color')
            row.prop(self, 'default_after_color')

            box = layout.box()
            col = box.column()
            col.label(text='On Screen Display')
            col.prop(self, 'use_osd_text', text='Show help text on custom transformation')

classes=(
GPOP_addon_prefs,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)