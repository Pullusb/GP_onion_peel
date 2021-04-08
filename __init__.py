bl_info = {
    "name": "GP Onion Skinning",
    "description": "Custom onion skinning using refreshed GP linked duplication",
    "author": "Samuel Bernou",
    "version": (0, 1, 0),
    "blender": (2, 92, 0),
    "location": "View3D",
    "warning": "WIP",
    "doc_url": "https://github.com/Pullusb/GP_Onion_skinning",
    "category": "Object" }

import bpy

def get_keys(ob, evaluate_gp_obj_key=True):
    '''Return sorted keys frame number of cu'''
    position = []
    if evaluate_gp_obj_key:
        # Get objet keyframe position
        anim_data = ob.animation_data
        action = None

        if anim_data:
            action = anim_data.action
        if action:
            for fcu in action.fcurves:
                for kf in fcu.keyframe_points:
                    if kf.co.x not in position:
                        position.append(int(kf.co.x)) # int ?

    # Get GP frame position
    gpl = ob.data.layers
    layer = gpl.active
    if layer:
        for frame in layer.frames:
            if frame.frame_number not in position:
                position.append(frame.frame_number)
    
    return sorted(position)


def set_offset(scene):
    ob = bpy.context.object
    pos = get_keys(ob)

    # num_to_display = 3
    cur_frame = scene.frame_current
    all_previous = [f for f in pos if f <= cur_frame]
    all_following = [f for f in pos if f > cur_frame]

    previous = all_previous[-4:-1]
    current = previous[-1]
    following = all_following[:3]

    for i, frame in enumerate(reversed(previous)):
        peel = scene.objects.get(f'{ob.name} {(i+1)*-1}')
        if peel:
            peel.grease_pencil_modifiers['time_offset'].offset = frame - current
    for i, frame in enumerate(following):
        peel = scene.objects.get(f'{ob.name} {i+1}')
        if peel:
            peel.grease_pencil_modifiers['time_offset'].offset = frame - current



class GPOS_OT_onion_skin_generate(bpy.types.Operator):
    bl_idname = "gp.onion_skinning_gen"
    bl_label = "Onion Skin Generate"
    bl_description = "Generate Onion skinning"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'
    
    def execute(self, context):
        ob = context.object
        pos = get_keys(ob)

        num_to_display = 3
        # found previous and next pos:
        cur_frame = context.scene.frame_current
        # num 3 (so 3*2=6 +current = 7)
        all_previous = [f for f in pos if f <= cur_frame]
        all_following = [f for f in pos if f > cur_frame]
        previous = all_previous[-4:-1]
        current = previous[-1]
        following = all_following[:3]
        print('previous: ', previous)
        print('current: ', current)
        print('following: ', following)

        mat = ob.matrix_world
        # get/create onion skin collection
        ons_col = bpy.data.collections.get('.onion_skin')
        if not ons_col:
            ons_col = bpy.data.collections.new('.onion_skin')
            ons_col.hide_render = True
            context.scene.collection.children.link(ons_col)


        oblist = []
        # [f'{ob.name} 0'] + # need current ??
        namelist = [f'{ob.name} {i*j}' for j in [1,-1] for i in range(1,num_to_display+1)]
        namelist.sort()
        print('namelist: ', namelist)
        for name in namelist:
            on_ob = ons_col.all_objects.get(name)
            if not on_ob:
                on_ob = bpy.data.objects.new(name, ob.data)
                on_ob.matrix_world = mat
                ons_col.objects.link(on_ob)
                oblist.append(on_ob)

                time = on_ob.grease_pencil_modifiers.new('time_offset','GP_TIME')
                time.use_keep_loop = False
                tint = on_ob.grease_pencil_modifiers.new('skin_color','GP_TINT')
                tint.factor = 1.0
                opa = on_ob.grease_pencil_modifiers.new('opacity','GP_OPACITY')
                opa.normalize_opacity = True # maybe not...


        print('oblist: ', oblist)
        # oblist.sort(key=lambda x: x.name)
        # print('oblist.sorted: ', oblist)

        set_offset(context.scene)
        # get  frame equal of just after current (if None, were past the end)
        # next((f for f in pos if f >= current), None)


        return {"FINISHED"}




class GPOS_PT_onion_skinning_ui(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Onion Skin"
    bl_label = "Onion Skinning"

    def draw(self, context):
        settings = context.scene.gp_ons_setting
        ob = context.object
        layout = self.layout
        num_to_display = 3
        # layout.prop(settings, 'str prop')
        # layout.prop(settings, 'bool prop')
        # layout.prop(settings, 'int prop')

        layout.operator('gp.onion_skinning_gen', text='Generate Onion Peels', icon='ONIONSKIN_ON')
        if ob:
            for i in sorted([0] + [i*j for j in [1,-1] for i in range(1,num_to_display+1)]):
                if i == 0:
                    layout.separator()
                peel = context.scene.objects.get(f'{ob.name} {i}')
                if not peel:
                    continue # need to display a placeholder prop (or create a GP place holder ?)
                row = layout.row(align=True)
                # CHECKBOX_DEHLT, CHECKBOX_HLT # TODO show/hide with checkboxes (more clear)
                row.label(text=f'{i}', icon='DOT')
                # (data, property, text, text_ctxt, translate, icon, expand, slider, toggle, icon_only, event, full_event, emboss, index, icon_value
                row.prop(peel.grease_pencil_modifiers['opacity'], 'factor', text='', slider=True)
                row.prop(peel, 'hide_viewport', icon_only=True, icon = 'HIDE_OFF')


        # layout.prop(settings, 'p3')
        # layout.prop(settings, 'p2')
        # layout.prop(settings, 'p1')
        # layout.prop(settings, 'cur')
        # layout.prop(settings, 'n1')
        # layout.prop(settings, 'n2')
        # layout.prop(settings, 'n3')
        

def update_p1(scene):
    ob = bpy.context.scene.objects.get(bpy.context.object.name + ' -1')
    if ob:
        ob.grease_pencil_modifiers.get('tint')

class GPOS_PGT_settings(bpy.types.PropertyGroup) :
    ## HIDDEN to hide the animatable dot thing
    # stringprop : bpy.props.StringProperty(
    #     name="str prop", description="", default="")# update=None, get=None, set=None
    
    # boolprop : bpy.props.BoolProperty(
    #     name="bool prop", description="", default=False, options={'HIDDEN'})#options={'ANIMATABLE'},subtype='NONE', update=None, get=None, set=None

    # IntProperty : bpy.props.IntProperty(
    #     name="int prop", description="", default=25, min=1, max=2**31-1, soft_min=1, soft_max=2**31-1, step=1, options={'HIDDEN'})#, subtype='PIXEL'

    p3: bpy.props.IntProperty(default=0, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)
    p2: bpy.props.IntProperty(default=0, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)
    p1: bpy.props.IntProperty(default=0, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)
    cur: bpy.props.IntProperty(default=0, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)
    n1: bpy.props.IntProperty(default=0, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)
    n2: bpy.props.IntProperty(default=0, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)
    n3: bpy.props.IntProperty(default=0, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)


class GPOS_addon_prefs(bpy.types.AddonPreferences):
    ## can be just __name__ if prefs are in the __init__ mainfile
    # Else need the splitext '__name__ = addonname.subfile' (or use a static name)
    bl_idname = __name__.split('.')[0] # or with: os.path.splitext(__name__)[0]

    # some_bool_prop to display in the addon pref
    super_special_option : bpy.props.BoolProperty(
        name='Use super special option',
        description="This checkbox toggle the use of the super special options",
        default=False)

    def draw(self, context):
            layout = self.layout

            ## some 2.80 UI options
            # layout.use_property_split = True
            # flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
            # layout = flow.column()

            layout.label(text='Some text')

            # display the bool prop
            layout.prop(self, "super_special_option")

            # draw something only if a prop evaluate True
            if self.super_special_option:
                layout.label(text="/!\ Carefull, the super special option is especially powerfull")
                layout.label(text="    and with great power... well you know !")


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


### --- REGISTER ---

classes=(
GPOS_PGT_settings,
GPOS_OT_onion_skin_generate,
GPOS_PT_onion_skinning_ui,
)

def register():
    # other_file.register()
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # if not bpy.app.background:
    #register_keymaps()
    bpy.types.Scene.gp_ons_setting = bpy.props.PointerProperty(type = GPOS_PGT_settings)

def unregister():
    # if not bpy.app.background:
    #unregister_keymaps()
    # other_file.unregister()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.gp_ons_setting

if __name__ == "__main__":
    register()
