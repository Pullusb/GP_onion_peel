import bpy
from bpy.app.handlers import persistent
from time import time

def to_onion_name(name):
    return f'.onion_{name}'

def to_peel_name(name):
    return f'.peel_{name}'

def clear_native_overlay():
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].overlay.use_gpencil_onion_skin = False

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


def create_peel_col(context):
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
    colname = to_onion_name(context.object.name)
    peel_col = op_col.children.get(colname)
    if not peel_col:
        peel_col = bpy.data.collections.get(colname)
        if not peel_col:
            peel_col = bpy.data.collections.new(colname)
        op_col.children.link(peel_col)
        peel_col.hide_render = True
        ons_vl.children[colname].exclude = False
    
    return op_col, peel_col

def clean_mods(gpob):
    layer_list = [l.info for l in gpob.data.layers]
    pgm = gpob.grease_pencil_modifiers
    for m in pgm:
        if m.type not in ('GP_TIME', 'GP_OPACITY'):
            continue
        if m.layer not in layer_list:
            pgm.remove(m)

### MAIN FUNCTION (called on each frame change or when onion rebuild is needed)

@persistent
def update_onion(self, context):
    # t0 = time()

    scene = context.scene
    ob = bpy.context.object
    if not ob or ob.type != 'GPENCIL' or ob.name.startswith('.peel'):
        return

    #/ Handle display
    op_col = bpy.data.collections.get('.onion_peels')
    if not scene.gp_ons_setting.activated:
        if op_col:
            op_col.hide_viewport = True
        return

    if bpy.context.screen.is_animation_playing:
        if op_col:
            op_col.hide_viewport = True
        # dont do anything and leave
        return

    mat = ob.matrix_world
    gpl = ob.data.layers
    if not [l for l in gpl if l.use_onion_skinning]: # Skip if no onion layers
        return

    ## TODO (optimise clean  withing update)
    # clean_peels() 

    # generate_onion_peels(bpy.context)
    op_col, peel_col = create_peel_col(bpy.context)

    op_col.hide_viewport = False
    # Handle display/

    peelname = to_peel_name(ob.name)
    
    cur_frame = scene.frame_current
    settings = scene.gp_ons_setting
    opacity_factor = settings.o_general / 100
    gprev = settings.before_num
    gnext = settings.after_num

    for _ in range(gprev - len(settings.neg_frames) + 1):
        f = settings.neg_frames.add()
    for _ in range(gnext - len(settings.pos_frames) + 1):
        f = settings.pos_frames.add()

    # if setting.offset_mode == 'FRAMES':
    #     pos = get_keys(ob)
    #     all_previous = [f for f in pos if f <= cur_frame]
    #     all_following = [f for f in pos if f > cur_frame]

    #     previous = all_previous[-gprev-1:-1]
    #     current = previous[-1:]
    #     if current:# int
    #         current = current[0]
    #     following = all_following[:gnext]

    #     for i in [-i for i in range(1,gprev+1)][::-1] + [i for i in range(1,gnext+1)]:
    #         peel = scene.objects.get(f'.peel_{ob.name} {i}')
    #         if peel:
    #             peel.grease_pencil_modifiers['time_offset'].offset = i

    ## Create/update per layer
    # KEYS offset mode
    # for i, frame in enumerate(reversed(previous)):
    # avoid reparsing frames layer for-loop comed first

    peel = None
    used = []
    for l in gpl:
        info = l.info
        frames = [f.frame_number for f in l.frames] # l.frames.foreach_get() ?
        if not frames: continue
        previous = [f for f in frames if f <= cur_frame]
        following = [f for f in frames if f > cur_frame]
        # print(f'{info} previous: ', previous)#dbg
        # print(f'{info} following: ', following)#dbg
        
        if previous:
            if len(previous) > 1:
                current = previous.pop()
        #     else:
        #         current = previous[-1]
        # else: # meaning cursor is behing everything so lets put a number behind first key
        #     current = cur_frame# following[0] - 1
        
        ## all asked
        # for num in [-i for i in range(1,gprev+1)][::-1] + [i for i in range(1,gnext+1)]:
        ## all asked limited by scanned number
        for num in [-i for i in range(1,gprev+1)][len(previous)-1::-1] + [i for i in range(1,gnext+1)][:len(following)]:
            absnum = abs(num)
            mark = None
            if num < 0:
                fsetting = settings.neg_frames[abs(num)]
                if absnum < len(previous):   
                    mark = previous[num]
            else:
                fsetting = settings.pos_frames[num]
                if absnum < len(following):
                    mark = following[num-1]

            # get / create the peel object
            peel_name = f'{to_peel_name(ob.name)} {num}'
            used.append(peel)
            peel = op_col.all_objects.get(peel_name)
            if not peel:
                peel = bpy.data.objects.new(peel_name, ob.data)
                peel.hide_select = True
                peel_col.objects.link(peel)
            peel['frame'] = num

            peel.matrix_world = mat
            
            pgm = peel.grease_pencil_modifiers


            # hide and skip non displayed onion layer of out for range ones
            if not mark or not l.use_onion_skinning:
                mod_opa = pgm.get(f'{info}_opacity')
                if not mod_opa:
                    mod_opa = pgm.new(f'{info}_opacity','GP_OPACITY')
                    mod_opa.normalize_opacity = True
                mod_opa.factor = 0
                mod_opa.layer = info
                mod_opa.show_expanded = True
                continue
            
            # COLOR
            tint = peel.grease_pencil_modifiers.get('peel_color')
            if not tint:
                # if first creation initiate the tint
                tint = peel.grease_pencil_modifiers.new('peel_color','GP_TINT')
                tint.factor = 1.0
                tint.show_expanded = False
                if peel['frame'] < 0:
                    tint.color = ob.data.before_color
                else:
                    tint.color = ob.data.after_color

            # TIME OFFSET
            mod_time = pgm.get(f'{info}_time')
            if not mod_time:
                mod_time = pgm.new(f'{info}_time','GP_TIME')
                mod_time.use_keep_loop = False
                mod_time.mode = 'FIX'
                mod_time.layer = info
                mod_time.show_expanded = False
            mod_time.offset = mark# - cur_frame

            # OPACITY
            mod_opa = pgm.get(f'{info}_opacity')
            if not mod_opa:
                mod_opa = pgm.new(f'{info}_opacity','GP_OPACITY')
                mod_opa.normalize_opacity = True
                mod_opa.layer = info
                mod_opa.show_expanded = False
            mod_opa.factor = fsetting.opacity / 100 * opacity_factor
    
    for o in peel_col.objects:
        if o not in used:
            bpy.data.objects.remove(o)
        # maybe just disable opacity if stil in peeling range ?


def update_opacity(self, context):
    settings = context.scene.gp_ons_setting
    op_col = bpy.data.collections.get('.onion_peels')
    if not op_col:
        return

    peel_col = op_col.children.get(to_onion_name(context.object.name))
    if not peel_col:
        return

    opacity_factor = settings.o_general / 100

    for o in peel_col.objects:
        num = o['frame']
        if num < 0:
            fsetting = settings.neg_frames[abs(num)]
        else:
            fsetting = settings.pos_frames[num]
        
        o.hide_viewport = not fsetting.visibility

        if not fsetting.opacity:
            continue
       
        for m in o.grease_pencil_modifiers:
            if m.type == 'GP_OPACITY':
                if m.factor == 0:
                    continue
                m.factor = fsetting.opacity / 100 * opacity_factor

""" 
def generate_onion_peels(context):
    t0 = time()
    ob = context.object
    mat = ob.matrix_world
    mat_inv = ob.matrix_parent_inverse

    gprev = context.scene.gp_ons_setting.before_num
    gnext = context.scene.gp_ons_setting.after_num

    # create collections
    op_col, peel_col = create_peel_col(bpy.context)

    #-# create all peels
    # oblist = []
    # [f'{ob.name} 0'] + # need current ??

    ## equal peels from left to right
    # peel_list = [f'.peel_{ob.name} {i*j}' for j in [1,-1] for i in range(1,gnext+1)]
    # peel_list.sort()
    ## dont create useless peels (no need to reverse sort [::-1])
    peel_list = [f'.peel_{ob.name} {i}' for i in range(1,gprev+1)] + [f'.peel_{ob.name} {i}' for i in range(1,gnext+1)]
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

    update_onion(context.scene)

    print(f'time {time()-t0:.2f}s')
    return op_col, peel_col """