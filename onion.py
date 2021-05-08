import bpy
from bpy.app.handlers import persistent
from time import time
from mathutils import Matrix, Vector
import random
from . import preferences

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
        if c and c.name.startswith('.peel_'):
            bpy.data.collections.remove(c)

    op_col = bpy.data.collections.get('.onion_peels')
    if op_col:
        bpy.data.collections.remove(op_col)
    
    dummy = bpy.data.grease_pencils.get('.dummy')
    if dummy:
        bpy.data.grease_pencils.remove(dummy)

def clear_current_peel(ob):
    name = ob.name
    col = bpy.data.collections.get(to_onion_name(name))
    if not col:
        return
    for o in col.all_objects:
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(col)

    onioncol = bpy.data.collections.get('.onion_peels')
    if not len(onioncol.children) and not len(onioncol.all_objects):
        bpy.data.collections.remove(onioncol)


def clean_peels():
    op_col = bpy.data.collections.get('.onion_peels')
    if not op_col:
        return
    for c in op_col.children:
        # name -> '.peel_obj_name'
        source_obj_name = c.name[len('.onion_'):]
        if not bpy.context.scene.objects.get(source_obj_name):
            for o in c.all_objects:
                print('in clean : deleted', o.name) #dbg
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

def scale_matrix_from_vector(scale):
    # recreate a neutral mat scale
    matscale_x = Matrix.Scale(scale[0], 4,(1,0,0))
    matscale_y = Matrix.Scale(scale[1], 4,(0,1,0))
    matscale_z = Matrix.Scale(scale[2], 4,(0,0,1))
    matscale = matscale_x @ matscale_y @ matscale_z
    return matscale

def get_new_matrix_with_offset(matrix, offset=0.0001):
    """return a copy of the matrix with applied offset and"""
    # offset from camera if any 
    # maybe add a modifier a to reduce stroke size very slightly (overkill...) # 0.0001
    cam = bpy.context.scene.camera
    if not cam:
        # TODO check viewport view if in viewport if no cam
        return
    
    cam_loc = cam.matrix_world.translation
    mat = matrix.copy()
    scale = mat.to_scale()

    if cam.data.type == 'ORTHO':
        # get the camera vector center vector
        v = Vector((0,0,-1))
        v.rotate(cam.matrix_world) # .to_quaternion()
        mat.translation += v * offset
    else:
        v = mat.translation - cam_loc
        mat.translation += v.normalized() * offset
        # scale multiplied by lenth diff factor (recalculate length with new location)
        scale = scale * ((mat.translation - cam_loc).length / v.length)

        mat_scale = scale_matrix_from_vector(scale)
        # mat = mat @ mat_scale # << maybe problematic, org scale is not neutral

        # decompose -> recompose
        loc, rot, _ = mat.decompose()
        mat_loc = Matrix.Translation(loc)
        mat_rot = rot.to_matrix().to_4x4()

        mat = mat_loc @ mat_rot @ mat_scale


    return mat


def set_layer_opacity_by_mod(mods, layer_name, value):
    mod_opa = mods.get(f'{layer_name}_opacity')
    if not mod_opa:
        mod_opa = mods.new(f'{layer_name}_opacity','GP_OPACITY')
        mod_opa.normalize_opacity = True
    mod_opa.factor = value
    mod_opa.layer = layer_name
    mod_opa.show_expanded = True

###
### MAIN FUNCTION (called on each frame change or when onion rebuild is needed)
###

@persistent
def update_onion(self, context):
    # t0 = time()
    ob = bpy.context.object
    if not ob or ob.type != 'GPENCIL' or ob.name.startswith('.peel'):
        return
    
    scene = context.scene

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

    gpl = ob.data.layers
    if not [l for l in gpl if l.use_onion_skinning and not l.hide]: # Skip if no onion layers
        return

    scene.gp_ons_setting.activated = False #Mtx avoid infinite recursion
    
    # orignal Matrix ?

    ## Full delete recrete of object seem to resolve the crash : edit stroke > change frame > ctrl-Z > Crash
    
    clean_peels()
    # clear_current_peel(ob)

    # generate_onion_peels(bpy.context)
    op_col, peel_col = create_peel_col(bpy.context)

    ## createa/assign a dummy (try resolve crash edit stroke > change frame > using ctrl-Z)
    dummy = bpy.data.grease_pencils.get('.dummy')
    if not dummy:
        dummy = bpy.data.grease_pencils.new('.dummy')
    for o in peel_col.all_objects:
        old = o.data
        o.data = dummy # no need to delete old data, "garbage collected" at update end
        bpy.data.grease_pencils.remove(old)

    # clear the data
    # for o in peel_col.all_objects:
    #     for l in reversed(o.data.layers):
    #         o.data.layers.remove(l)
        #-# try poping all materials
        # for _ in range(len(o.data.materials)):
        #     o.data.materials.pop()


    op_col.hide_viewport = False
    # Handle display/

    peelname = to_peel_name(ob.name)
    
    depth_offset = preferences.get_addon_prefs().depth_offset
    cur_frame = scene.frame_current
    settings = scene.gp_ons_setting
    opacity_factor = settings.o_general / 100
    gprev = settings.before_num
    gnext = settings.after_num

    for _ in range(gprev - len(settings.neg_frames) + 1):
        f = settings.neg_frames.add()
    for _ in range(gnext - len(settings.pos_frames) + 1):
        f = settings.pos_frames.add()

    peel = None
    used = []
    layers = []
    
    ## calculate all frame index by layer Once
    for l in gpl:
        if not l.use_onion_skinning or l.hide:
            continue
        if settings.keyframe_type == 'ALL':
            frames = [f for f in l.frames]
        else: # filtered
            frames = [f for f in l.frames if f.keyframe_type == settings.keyframe_type]

        if not frames: # complete skip of empty layers
            continue

        info = l.info
        previous = [f for f in frames if f.frame_number <= cur_frame]
        following = [f for f in frames if f.frame_number > cur_frame]

        if previous: # if there are previous, kill current off the list 
            previous.pop()
        layers.append([info, previous, following])

    if not layers:
        peel_col.hide_viewport = True
        settings.activated = True
        return
        
    count = 0
    for num in [-i for i in range(1,gprev+1)] + [i for i in range(1,gnext+1)]:
        absnum = abs(num)

        # get / create the peel object
        peel_name = f'{peelname} {num}'
        peel = op_col.all_objects.get(peel_name)

        data = bpy.data.grease_pencils.new(peel_name)#f'{peel_name} {random.randint(0,50000)}')
        for i, m in enumerate(ob.data.materials): # get same material stack
            data.materials.append(m)
            # data.materials.append(None) # cereate empty slots
            # peel.data.materials.append(None)
            # peel.material_slots[i].link = 'OBJECT' # default is DATA
            # peel.material_slots[i].material = m

        if not peel:
            peel = bpy.data.objects.new(peel_name, data)
            peel.show_bounds = True # <<< DEBUG
            peel.hide_select = False # <<< DEBUG
            peel.use_grease_pencil_lights = False
            peel_col.objects.link(peel)
        else:

            #-# try storing outapeg and kill-recreate
            # outapeg = peel.get('outapeg')
            # bpy.data.objects.remove(peel)
            
            # peel = bpy.data.objects.new(peel_name, data)
            # peel.hide_select = True
            # peel.use_grease_pencil_lights = False
            # peel_col.objects.link(peel)
            # if outapeg:
            #     peel['outapeg'] = outapeg

            #-# previously only this in else:
            peel.data = data


        peel.show_in_front = ob.show_in_front
        peel['index'] = num
        used.append(peel)
        
        # pgm = peel.grease_pencil_modifiers

        mark_prev = []
        mark_next = []
        for layer in layers:
            info, previous, following = layer[:]
            
            mark = None
            if num < 0:
                fsetting = settings.neg_frames[abs(num)]
                if absnum < len(previous)+1:   
                    mark = previous[num]
                    mark_prev.append(mark.frame_number)
            else:
                fsetting = settings.pos_frames[num]
                if absnum < len(following)+1:
                    mark = following[num-1]
                    mark_next.append(mark.frame_number)

            # skip non displayed onion layer of out for range ones
            if mark is None:
                continue

            nl = data.layers.new(info)
            f = nl.frames.copy(mark)
            f.frame_number = cur_frame
            nl.use_lights = False
            nl.opacity = fsetting.opacity / 100 * opacity_factor
            # COLOR
            if peel['index'] < 0:
                nl.tint_color = settings.before_color # ob.data.before_color
            else:
                nl.tint_color = settings.after_color # ob.data.after_color
            nl.tint_factor = 1

        # set position in space (change mark to be the closet frame)
        if mark:
            if num < 0:
                mark = sorted(mark_prev)[-1]
            else:
                mark = sorted(mark_next)[0]

        peel['frame'] = mark # can be None

        ## assigning world matrix:
        outapeg_mat = Matrix()
        if peel.get('outapeg'):
            outapeg_mat = Matrix(peel['outapeg'])

        if settings.world_space and mark: 
            context.scene.frame_set(mark)

        ## DIRECT MATRIX assignation
        # peel.matrix_world = eval(f"Matrix({peel['outapeg']})")
        ## DIFF MATRIX at time of modification
        mat = ob.matrix_world @ outapeg_mat# eval(f"Matrix({peel['outapeg']})")
        peel['mat'] = mat
        count += depth_offset # settings.depth_offset
        mat = get_new_matrix_with_offset(mat, offset=count)
        peel.matrix_world = mat
        # peel.matrix_world = mat

    # get back to original current frame
    if settings.world_space:
        context.scene.frame_set(cur_frame)
    
    # Delete too much peels
    for o in peel_col.objects:
        if o not in used:
            bpy.data.objects.remove(o)
            continue

    # Clear unused old peel data
    for gp in bpy.data.grease_pencils[:]:
        if not gp.users and gp.name.startswith('.peel'):
            bpy.data.grease_pencils.remove(gp)

    scene.gp_ons_setting.activated = True #Mtx avoid infinite recursion
    op_col.hide_viewport = peel_col.hide_viewport = False
    
    # Hide other objects onions (show only active object onion)
    for c in op_col.children:
        c.hide_viewport = c is not peel_col
    # print(time() - t0)
    # bpy.ops.ed.undo_push(message=f'Peel update {time()}') # test

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
        num = o['index']
        if num < 0:
            fsetting = settings.neg_frames[abs(num)]
        else:
            fsetting = settings.pos_frames[num]
        
        o.hide_viewport = not fsetting.visibility

        if not fsetting.opacity:
            continue
        
        # Layer settings
        for l in o.data.layers:
            l.opacity = fsetting.opacity / 100 * opacity_factor

        # Modifier settings
        # for m in o.grease_pencil_modifiers:
        #     if m.type == 'GP_OPACITY':
        #         if m.factor == 0:
        #             continue
        #         m.factor = fsetting.opacity / 100 * opacity_factor


def update_peel_color(self, context):
    settings = context.scene.gp_ons_setting
    op_col = bpy.data.collections.get('.onion_peels')
    if not op_col:
        return
    peel_col = op_col.children.get(to_onion_name(context.object.name))
    if not peel_col:
        return
    for o in peel_col.objects:
        color = settings.before_color if o['index'] < 0 else settings.after_color

        for l in o.data.layers:
            l.tint_color = color

        # modifier settings
        # for m in o.grease_pencil_modifiers:
        #     if m.type == 'GP_TINT':
        #         m.color = color


# not used, use an ops instead
def update_peel_xray(self, context):
    settings = context.scene.gp_ons_setting
    op_col = bpy.data.collections.get('.onion_peels')
    if not op_col:
        return
    peel_col = op_col.children.get(to_onion_name(context.object.name))
    if not peel_col:
        return
    context.object.show_in_front = settings.xray
    for peel in peel_col.objects:
        peel.show_in_front = settings.xray
        

## TODO case of multi GP update...

# def switch_onion(self, context):
#     if context.scene.gp_ons_setting.activated:
#         bpy.ops.gp.onion_peel_refresh(called=True)
#     else:
#         clear_current_peel()

# def update_onion(self, context):
#     if context.scene.gp_ons_setting.only_active:
#         update_ob_onion(context, context.object)
#     else:
#         for o in context.scene.objects:
#             update_ob_onion(context, o)
