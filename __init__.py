bl_info = {
    "name": "GP Onion Peel",
    "description": "Custom Onion skinning using refreshed linked GP duplications",
    "author": "Samuel Bernou",
    "version": (0, 2, 0),
    "blender": (2, 92, 0),
    "location": "View3D",
    "warning": "WIP",
    "doc_url": "https://github.com/Pullusb/GP_Onion_peel",
    "category": "Object" }

import bpy
from time import time
from bpy.app.handlers import persistent

def get_collection_childs_recursive(col, cols=[]):
    for sub in col.children:
        if sub not in cols:
            cols.append(sub)
        if len(sub.children):
            cols = get_collection_childs_recursive(sub, cols)
    return cols


def clear_peels(full_clear=False):
    '''Clear all onion peels collection and object
    :full_clear: Clear .peels even if outside of onion peels collection
    '''
    if full_clear:
        obj_pool = bpy.data.objects
        col_pool = bpy.data.collections
    else:
        op_col = bpy.data.collections.get('.onion_peels')
        if not op_col:
            return
        obj_pool = op_col.all_objects
        col_pool = get_collection_childs_recursive(op_col)

    for o in obj_pool:
        if o.name.startswith('.peel_'):
            bpy.data.objects.remove(o)
    for c in col_pool:
        if c.name.startswith('.peel_'):
            bpy.data.collections.remove(c)

    op_col = bpy.data.collections.get('.onion_peels')
    if op_col:
        bpy.data.collections.remove(op_col)


def clean_peels():
    op_col = bpy.data.collections.get('.onion_peels')
    if not op_col:
        return
    for c in op_col.children:
        # name -> '.peel_obj_name'
        source_obj_name = c.name[len('.peel_'):]
        if not bpy.context.scene.objects.get(source_obj_name):
            for o in c.all_objects:
                bpy.data.objects.remove(o)
            bpy.data.collections.remove(c)
    
    if not len(op_col.children):
        for ob in op_col.all_objects[:]:
            if ob.name.startwith('.peel_'):
                bpy.data.objects.remove(ob)
        
        if not len(op_col.all_objects):
            bpy.data.collections.remove(op_col)

        

def get_keys(ob, evaluate_gp_obj_key=True):
    '''Return sorted keys frame number of GP object'''

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
    for layer in gpl:
        if not layer.use_onion_skinning:
            continue
        for frame in layer.frames:
            if frame.frame_number not in position:
                position.append(frame.frame_number)

    return sorted(position)


def set_offset(scene):
    print('Evaluated')
    t0 = time()

    #/ Handle display
    op_col = bpy.data.collections.get('.onion_peels')
    if not op_col:
        return
    if not scene.gp_ons_setting.activated:
        op_col.hide_viewport = True
        return

    if bpy.context.screen.is_animation_playing:
        op_col.hide_viewport = True
        # dont do anything and leave
        return

    op_col.hide_viewport = False
    # Handle display/

    ob = bpy.context.object
    gpl = ob.data.layers
    
    cur_frame = scene.frame_current
    gprev = scene.gp_ons_setting.before_num
    gnext = scene.gp_ons_setting.after_num
    
    if scene.gp_ons_setting.offset_mode == 'FRAMES':
        pos = get_keys(ob)
        all_previous = [f for f in pos if f <= cur_frame]
        all_following = [f for f in pos if f > cur_frame]

        previous = all_previous[-gprev-1:-1]
        current = previous[-1:]
        if current:# int
            current = current[0]
        following = all_following[:gnext]

        for i in [-i for i in range(1,gprev+1)][::-1] + [i for i in range(1,gnext+1)]:
            peel = scene.objects.get(f'.peel_{ob.name} {i}')
            if peel:
                peel.grease_pencil_modifiers['time_offset'].offset = i
    
    else:
        # KEYS offset mode
        # for i, frame in enumerate(reversed(previous)):
        # avoid reparsing frames layer for-loop comed first
        for l in gpl:
            info = l.info
            frames = [f.frame_number for f in l.frames] # l.frames.foreach_get() ?
            if not frames: continue
            previous = [f for f in frames if f <= cur_frame]
            following = [f for f in frames if f > cur_frame]
            print('previous: ', previous)
            print('following: ', following)
            
            if previous:
                if len(previous) > 1:
                    current = previous.pop()
                else:
                    current = previous[-1]
            else: # meaning cursor is behing everything so lets put a number behind first key
                current = cur_frame# following[0] - 1
            
            ## all asked
            # for num in [-i for i in range(1,gprev+1)][::-1] + [i for i in range(1,gnext+1)]:
            ## all asked limited by scanned number
            print('len(previous): ', len(previous))
            for num in [-i for i in range(1,gprev+1)][len(previous)-1::-1] + [i for i in range(1,gnext+1)][:len(following)]:
                print('num: ', num)
                peel = scene.objects.get(f'.peel_{ob.name} {num}')
                if not peel:
                    # should create here
                    continue
                pgm = peel.grease_pencil_modifiers            
                mod_time = pgm[f'{info}_time']
                mod_time.layer = info
                # calculate offset from current to prev
                if num < 0:
                    mark = previous[num]
                else:
                    mark = following[num]
                mod_time.offset = mark - cur_frame
                # opacity = pmg[f'{info}_opacity']
                


        # for i, frame in enumerate(following):
        #     peel = scene.objects.get(f'.peel_{ob.name} {i+1}')
        #     if not peel:
        #         continue
        #     peel.grease_pencil_modifiers['time_offset'].offset = frame - current
        
    print(f'Update time: {time()-t0:.5f}s')
    # TODO : hide/disable unused stuff...


def generate_onion_peels(context):
    t0 = time()
    ob = context.object
    mat = ob.matrix_world
    mat_inv = ob.matrix_parent_inverse

    gprev = context.scene.gp_ons_setting.before_num
    gnext = context.scene.gp_ons_setting.after_num

    # get/create onion skin collection
    op_col = bpy.data.collections.get('.onion_peels')
    if not op_col:
        op_col = bpy.data.collections.new('.onion_peels')
        op_col.hide_render = True
        context.scene.collection.children.link(op_col)
    # ensure collection is visible in current viewlayer
    ons_vl = context.view_layer.layer_collection.children['.onion_peels']
    ons_vl.exclude = False

    #-# create current objects peels collection if needed
    colname = f'.onion_{ob.name}'
    peel_col = bpy.data.collections.get(colname)
    if not peel_col:
        peel_col = bpy.data.collections.new(colname)
        op_col.children.link(peel_col)
        peel_col.hide_render = True
        ons_vl.children[colname].exclude = False

    #-# create all peels
    # oblist = []
    # [f'{ob.name} 0'] + # need current ??
    peel_list = [f'.peel_{ob.name} {i*j}' for j in [1,-1] for i in range(1,gnext+1)]
    peel_list.sort()
    for peel_name in peel_list:
        on_ob = op_col.all_objects.get(peel_name)
        
        if not on_ob:
            on_ob = bpy.data.objects.new(peel_name, ob.data)
            peel_col.objects.link(on_ob)
        
        # apply matrix of evaluated position in world space and maybe just parent in local.
        # on_ob.matrix_world = mat # apply the matrix of the object ?

        # oblist.append(on_ob)
        # [l for l in ob.data.layer if l.use_onion_skinning:
        # continuening]
        ## Tint
        tint = on_ob.grease_pencil_modifiers.new('peel_color','GP_TINT')
        tint.factor = 1.0
        if peel_name.split()[-1].startswith('-'):
            tint.color = ob.data.before_color
        else:
            tint.color = ob.data.after_color
        
        # PER LAYERS mods
        for l in ob.data.layers:
            info = l.info
            if not l.use_onion_skinning:
                # hide with opacity modifier
                mod_opa = on_ob.grease_pencil_modifiers.new(f'{info}_opacity','GP_OPACITY')
                mod_opa.factor = 0
                mod_opa.layer = info
                continue

            mod_time = on_ob.grease_pencil_modifiers.new(f'{info}_time','GP_TIME')
            mod_time.use_keep_loop = False
            mod_time.layer = info
            mod_opa = on_ob.grease_pencil_modifiers.new(f'{info}_opacity','GP_OPACITY')
            mod_opa.normalize_opacity = True # maybe not...
            mod_opa.layer = info


            ## here add differential transform to match evaluated position compared to main object
            # transfo = on_ob.grease_pencil_modifiers.new(f'{info}_time','GP_TIME')


    # print('oblist: ', oblist)
    # oblist.sort(key=lambda x: x.name)
    # print('oblist.sorted: ', oblist)

    set_offset(context.scene)

    print(f'time {time()-t0:.2f}s')
    return

def to_peel_name(name):
    return f'.peel_{name}'

class GPOP_OT_onion_skin_delete(bpy.types.Operator):
    bl_idname = "gp.onion_skin_delete"
    bl_label = "Delete Onion_Skin"
    bl_description = "Delete all custom Onion skins"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'
    
    def invoke(self, context, event):
        self.on_all = event.shift
        return self.execute(context)

    def execute(self, context):
        context.scene.gp_ons_setting.activated = False
        if self.on_all:
            clear_peels(full_clear=True)
            return {"FINISHED"}

        pool = [context.object.name]
        for name in pool:
            peel = to_peel_name(name)


        return {"FINISHED"}

class GPOP_OT_onion_skin_refresh(bpy.types.Operator):
    bl_idname = "gp.onion_peel_refresh"
    bl_label = "Refresh Onion Peel"
    bl_description = "Refresh custom Onion peels (full regen if shift clicked)" 
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'
    
    def invoke(self, context, event):
        # self.on_all = event.shift
        self.full_refresh = event.shift
        return self.execute(context)

    def execute(self, context):
        if not context.scene.gp_ons_setting.activated:
            context.scene.gp_ons_setting.activated = True
        
        if self.full_refresh:
            # clear and recreate
            clear_peels()
            generate_onion_peels(context)
        
        else:
            # just refresh existing (in the future the refresh might auto-clean if needed )
            set_offset(context.scene)

        return {"FINISHED"}

class GPOP_OT_onion_skin_generate(bpy.types.Operator):
    bl_idname = "gp.onion_skinning_gen"
    bl_label = "Activate Onion Skin"
    bl_description = "Generate or reset Onion skinning"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'
    
    def invoke(self, context, event):
        self.on_all = event.shift
        return self.execute(context)

    def execute(self, context):
        ob = context.object
        pos = get_keys(ob)
        context.scene.gp_ons_setting.activated = True
        
        ### Non needed here anymore
        # num_to_display = 3
        # # found previous and next pos:
        # cur_frame = context.scene.frame_current
        # # num 3 (so 3*2=6 +current = 7)
        # all_previous = [f for f in pos if f <= cur_frame]
        # all_following = [f for f in pos if f > cur_frame]
        # previous = all_previous[-4:-1]
        # current = previous[-1]
        # following = all_following[:3]
        
        # print('previous: ', previous)
        # print('current: ', current)
        # print('following: ', following)

        # Create all peels
        generate_onion_peels(context)
        
        # get  frame equal of just after current (if None, were past the end)
        # next((f for f in pos if f >= current), None)


        return {"FINISHED"}




class GPOP_PT_onion_skinning_ui(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Gpencil"
    bl_label = "Onion Peel"

    def draw(self, context):
        ob = context.object
        if not ob or ob.type != 'GPENCIL':
            return

        settings = context.scene.gp_ons_setting
        layout = self.layout
        layout.prop(settings, 'activated', text='On', emboss=True)
        layout.prop(settings, 'offset_mode')
        row = layout.row(align=True)
        row.prop(settings, 'before_num', text='')
        row.prop(ob.data, 'before_color', text='')
        row.separator()
        row.prop(ob.data, 'after_color', text='')
        row.prop(settings, 'after_num', text='')
        num_to_display = 2
        # layout.prop(settings, 'str prop')
        # layout.prop(settings, 'bool prop')
        # layout.prop(settings, 'int prop')

        
        layout.operator('gp.onion_skinning_gen', text='Generate Onion Peels', icon='ONIONSKIN_ON')
        if ob:
            ### ADDON PROPERTIE BASED PANEL
            # TODO change to left-right different display ?
            for i in sorted([0] + [i*j for j in [1,-1] for i in range(1,num_to_display+1)]):
                if i == 0:
                    layout.separator()
                    layout.label(text='', icon='REMOVE')
                    layout.separator()
                    continue
                # peel = context.scene.objects.get(f'{ob.name} {i}')
                # if not peel:
                #     continue # create a GP place holder ?

                row = layout.row(align=True)
                # CHECKBOX_DEHLT, CHECKBOX_HLT # TODO show/hide with checkboxes (more clear)
                
                # row.prop(peel.grease_pencil_modifiers['opacity'], 'factor', text='', slider=True)
                row.label(icon='DOT')
                sens = f'p{abs(i)}' if i < 0 else f'n{i}'
                row.prop(settings, f'o_{sens}', text='', slider=True)
                row.prop(settings, f'v_{sens}', text='', icon = 'HIDE_OFF')

                # (data, property, text, text_ctxt, translate, icon, expand, slider, toggle, icon_only, event, full_event, emboss, index, icon_value

            #### OBJECT BASED PANEL
            # for i in sorted([0] + [i*j for j in [1,-1] for i in range(1,num_to_display+1)]):
            #     if i == 0:
            #         layout.separator()
            #         layout.label(text='-')
            #         layout.separator()
            #     peel = context.scene.objects.get(f'{ob.name} {i}')
            #     if not peel:
            #         continue # need to display a placeholder prop (or create a GP place holder ?)

            #     row = layout.row(align=True)
            #     # CHECKBOX_DEHLT, CHECKBOX_HLT # TODO show/hide with checkboxes (more clear)
                
            #     row.label(icon_only=True, icon='DOT')
            #     row.prop(peel.grease_pencil_modifiers['opacity'], 'factor', text='', slider=True)
            #     row.prop(peel, 'hide_viewport', icon_only=True, icon = 'HIDE_OFF')

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
        #(key, label, descr, id[, icon])

    before_num : bpy.props.IntProperty(
        name="Before", description="Number of previous ghost displayed", default=2, min=1, max=32, soft_min=1, soft_max=10, step=1, options={'HIDDEN'})
    
    after_num : bpy.props.IntProperty(
        name="After", description="Number of next ghost displayed", default=2, min=1, max=32, soft_min=1, soft_max=10, step=1, options={'HIDDEN'})
    
    activated : bpy.props.BoolProperty(name='Activate', default=True)

    # opacity
    o_p3: bpy.props.IntProperty(default=100, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)
    o_p4: bpy.props.IntProperty(default=100, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)
    o_p2: bpy.props.IntProperty(default=100, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)
    o_p1: bpy.props.IntProperty(default=100, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)
    o_general: bpy.props.IntProperty(default=100, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)
    o_n2: bpy.props.IntProperty(default=100, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)
    o_n1: bpy.props.IntProperty(default=100, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)
    o_n3: bpy.props.IntProperty(default=100, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)
    o_n4: bpy.props.IntProperty(default=100, min=0, max=100, subtype='PERCENTAGE', options={'HIDDEN'}, update=None, get=None, set=None)

    # visibility
    v_p3: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=None, get=None, set=None)
    v_p4: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=None, get=None, set=None)
    v_p2: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=None, get=None, set=None)
    v_p1: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=None, get=None, set=None)
    v_general: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=None, get=None, set=None)
    v_n2: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=None, get=None, set=None)
    v_n1: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=None, get=None, set=None)
    v_n3: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=None, get=None, set=None)
    v_n4: bpy.props.BoolProperty(default=True, options={'HIDDEN'}, update=None, get=None, set=None)


""" class GPOP_addon_prefs(bpy.types.AddonPreferences):
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
            # layout.use_property_split = True
            # flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=False)
            # layout = flow.column()
            layout.label(text='Some text')

 """
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



### --- REGISTER ---

classes=(
GPOP_PGT_settings,
GPOP_OT_onion_skin_generate,
GPOP_PT_onion_skinning_ui,
)

# TODO Add handler on frame post to refresh the timeline offset

def register():
    # other_file.register()
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # if not bpy.app.background:
    #register_keymaps()
    bpy.types.Scene.gp_ons_setting = bpy.props.PointerProperty(type = GPOP_PGT_settings)
    # bpy.app.handlers.load_post.append(activator)

def unregister():
    # if not bpy.app.background:
    #unregister_keymaps()
    # other_file.unregister()
    # bpy.app.handlers.load_post.remove(activator)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.gp_ons_setting

if __name__ == "__main__":
    register()
