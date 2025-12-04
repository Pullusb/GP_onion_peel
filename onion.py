import bpy
from bpy.app.handlers import persistent
from time import time
from mathutils import Matrix, Vector
import random
import numpy as np
from . import preferences

def to_onion_name(name):
    return f'.onion_{name}'

def to_peel_name(name):
    return f'.peel_{name}'

def matrix_to_flat(matrix):
    """Convert a 4x4 Matrix to a flattened tuple for custom property storage"""
    return tuple(sum((list(row) for row in matrix), []))

def flat_to_matrix(flat):
    """Reconstruct a 4x4 Matrix from a flattened array stored in custom properties"""
    return Matrix([flat[i:i+4] for i in range(0, 16, 4)])

def clear_native_overlay():
    if bpy.context.area.type == 'VIEW_3D':
        bpy.context.space_data.overlay.use_gpencil_onion_skin = False
        return
    ## Else search in all areas
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

    for o in reversed(obj_pool):
        if o.name.startswith('.peel_'):
            bpy.data.objects.remove(o)
    for c in reversed(col_pool):
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
    for o in reversed(col.all_objects):
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(col)

    onioncol = bpy.data.collections.get('.onion_peels')
    if not len(onioncol.children) and not len(onioncol.all_objects):
        bpy.data.collections.remove(onioncol)


def clean_peels():
    op_col = bpy.data.collections.get('.onion_peels')
    if not op_col:
        return
    for c in reversed(op_col.children):
        # name -> '.peel_obj_name'
        source_obj_name = c.name[len('.onion_'):]
        if not bpy.context.scene.objects.get(source_obj_name):
            for o in reversed(c.all_objects):
                print('in clean : deleted', o.name) #dbg
                bpy.data.objects.remove(o)
            bpy.data.collections.remove(c)
    
    if not len(op_col.children):
        for ob in reversed(op_col.all_objects[:]): # reversed not needed ? ([:] create a copy)
            if ob.name.startwith('.peel_'):
                bpy.data.objects.remove(ob)
        
        if not len(op_col.all_objects):
            bpy.data.collections.remove(op_col)

def clear_custom_transform(all_peel=False):
    op_col = bpy.data.collections.get('.onion_peels')
    if not op_col:
        return
    if all_peel:
        pool = [c for c in op_col.children if c.name.startwith('.onion')]
    else:
        current_onion = op_col.children.get(f'.onion_{bpy.context.object.name}')
        if not current_onion:
            return
        pool = [current_onion]

    ## Clear the outapeg prop
    for c in pool:
        for peel in c.all_objects:
            if peel.get('outapeg'):
                del peel['outapeg']

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
    layer_list = [l.name for l in gpob.data.layers]
    pgm = gpob.modifiers
    for m in pgm:
        if m.type not in ('GREASE_PENCIL_TIME', 'GREASE_PENCIL_OPACITY'):
            continue
        if m.layer_filter not in layer_list:
            pgm.remove(m)

def scale_matrix_from_vector(scale):
    '''recreate a neutral mat scale'''
    matscale_x = Matrix.Scale(scale[0], 4,(1,0,0))
    matscale_y = Matrix.Scale(scale[1], 4,(0,1,0))
    matscale_z = Matrix.Scale(scale[2], 4,(0,0,1))
    matscale = matscale_x @ matscale_y @ matscale_z
    return matscale

def get_new_matrix_with_offset(matrix, offset=0.0001):
    """return a copy of the matrix with applied offset and"""

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
        v.rotate(cam.matrix_world)
        mat.translation += v * offset
    else:
        v = mat.translation - cam_loc
        new_loc = mat.translation + (v.normalized() * offset)

        # scale multiplied by lenth diff factor (recalculate length with new location)
        scale = scale * ((new_loc - cam_loc).length / v.length)

        mat_scale = scale_matrix_from_vector(scale)

        # decompose -> recompose
        _loc, rot, _sca = mat.decompose()
        mat_loc = Matrix.Translation(new_loc)
        mat_rot = rot.to_matrix().to_4x4()

        mat = mat_loc @ mat_rot @ mat_scale

    return mat


def set_layer_opacity_by_mod(mods, layer_name, value):
    mod_opa = mods.get(f'{layer_name}_opacity')
    if not mod_opa:
        mod_opa = mods.new(f'{layer_name}_opacity','GREASE_PENCIL_OPACITY')
        mod_opa.normalize_opacity = True
    mod_opa.factor = value
    mod_opa.layer = layer_name
    mod_opa.show_expanded = True

def bulk_copy_attributes(source_attr, target_attr):
    # Get the data as flat numpy array based on attribute type and domain
    if source_attr.data_type == 'FLOAT':
        data = np.empty(len(source_attr.data), dtype=np.float32)
        source_attr.data.foreach_get('value', data)
        target_attr.data.foreach_set('value', data)
    elif source_attr.data_type == 'FLOAT_VECTOR':
        data = np.empty(len(source_attr.data) * 3, dtype=np.float32)
        source_attr.data.foreach_get('vector', data)
        target_attr.data.foreach_set('vector', data)
    elif source_attr.data_type == 'INT':
        data = np.empty(len(source_attr.data), dtype=np.int32)
        source_attr.data.foreach_get('value', data)
        target_attr.data.foreach_set('value', data)
    elif source_attr.data_type == 'INT8':
        data = np.empty(len(source_attr.data), dtype=np.int8)
        source_attr.data.foreach_get('value', data)
        target_attr.data.foreach_set('value', data)
    elif source_attr.data_type == 'BOOLEAN':
        data = np.empty(len(source_attr.data), dtype=bool)
        source_attr.data.foreach_get('value', data)
        target_attr.data.foreach_set('value', data)
    ## Note: COLOR_VECTOR not needed in this case

def copy_frame_at(source_frame, layer, frame_number):
    """
    Copy a frame to another frame within a specified layer at frame numer

    Args:
        source_frame (Frame): The source frame object containing the drawing to be copied.
        layer (Layer): The target layer where the new frame will be created.
        frame_number (int): The frame number at which the new frame will be created.
    """
    source_drawing = source_frame.drawing

    frame = layer.frames.new(frame_number)
    if not len(source_drawing.strokes):
        return

    dr = frame.drawing
    ## Add all strokes at once with list of point numbers
    dr.add_strokes([len(s.points) for s in source_drawing.strokes])

    ## Transfer attributes
    for attr_name in source_drawing.attributes.keys():
        ## Skip non-needed attributes (since it's colored, remove vertex and fill color as well)
        if attr_name in ('vertex_color', 'fill_color', '.selection', 'init_time', 'delta_time'):
            continue
        source_attr = source_drawing.attributes[attr_name]
        if attr_name not in dr.attributes:
            dr.attributes.new(name=attr_name, type=source_attr.data_type, domain=source_attr.domain)
        target_attr = dr.attributes[attr_name]
        bulk_copy_attributes(source_attr, target_attr)

###
### MAIN FUNCTION (called on each frame change or when onion rebuild is needed)
###

def force_update_onion(self, context):
    bpy.context.scene.gp_ons_setting.frame_prev = -9999
    if bpy.context.scene.gp_ons_setting.activated:
        clear_native_overlay()
    update_onion(self, context)
    update_opacity(self, context)

@persistent
def update_onion(self, context):
    if not hasattr(bpy.context, 'object'):
        return
    ob = bpy.context.object
    if not ob or ob.type != 'GREASEPENCIL' or ob.name.startswith('.peel'):
        return
    
    scene = context.scene

    op_col = bpy.data.collections.get('.onion_peels')
    if not scene.gp_ons_setting.activated:
        if op_col:
            op_col.hide_viewport = True
        return

    if bpy.context.screen.is_animation_playing:
        if op_col:
            op_col.hide_viewport = True
        return

    ## Frame flag to prevent tirggering multiple times on the same frame
    if scene.gp_ons_setting.frame_prev == scene.frame_current:
        return
    else:
        scene.gp_ons_setting.frame_prev = scene.frame_current


    gpl = ob.data.layers
    if not [l for l in gpl if l.use_onion_skinning and not l.hide]: # Skip if no onion layers
        return

    scene.gp_ons_setting['activated'] = False #Mtx avoid infinite recursion

    ## Full delete-recreate of object seem to resolve the crash : edit stroke > change frame > ctrl-Z > Crash
    clean_peels()

    op_col, peel_col = create_peel_col(bpy.context)

    ## create/assign a dummy (try resolve crash edit stroke > change frame > using ctrl-Z)
    dummy = bpy.data.grease_pencils.get('.dummy')
    if not dummy:
        dummy = bpy.data.grease_pencils.new('.dummy')
    for o in reversed(peel_col.all_objects):
        old = o.data
        o.data = dummy # no need to delete old data, "garbage collected" at update end
        bpy.data.grease_pencils.remove(old)

    op_col.hide_viewport = False

    peelname = to_peel_name(ob.name)
    
    depth_offset = preferences.get_addon_prefs().depth_offset
    depth_offset = depth_offset if not preferences.get_addon_prefs().peel_in_front else -depth_offset
    cur_frame = scene.frame_current
    settings = scene.gp_ons_setting
    opacity_factor = settings.o_general / 100
    gprev = settings.before_num
    gnext = settings.after_num

    for _ in range(gprev - len(settings.neg_frames) + 1):
        f = settings.neg_frames.add()
    for _ in range(gnext - len(settings.pos_frames) + 1):
        f = settings.pos_frames.add()

    # if not bpy.data.materials.get('.onion_peel_prev_stroke'): # peel_mat
    #     create_all_peel_materials() # peel_mat

    peel = None
    used = []
    layers = []

    ## calculate all frame index by layer once      
    for l in gpl:
        if not l.use_onion_skinning or l.hide:
            continue
        if settings.keyframe_type == 'ALL':
            frames = [f for f in l.frames]
        else: # filtered
            frames = [f for f in l.frames if f.keyframe_type == settings.keyframe_type]

        if not frames: # complete skip of empty layers
            continue

        info = l.name
        previous = [f for f in frames if f.frame_number <= cur_frame]
        following = [f for f in frames if f.frame_number > cur_frame]

        if previous: # if there are previous, kill current off the list 
            previous.pop()
        layers.append([info, previous, following])

    if not layers:
        peel_col.hide_viewport = True
        settings['activated'] = True
        return
        
    count = 0
    for num in [-i for i in range(1,gprev+1)] + [i for i in range(1,gnext+1)]:
        absnum = abs(num)

        # get / create the peel object
        peel_name = f'{peelname} {num}'
        peel = op_col.all_objects.get(peel_name)

        data = bpy.data.grease_pencils.new(peel_name)
        # data.pixel_factor = ob.data.pixel_factor # gpv2
        
        ## Get same material stack (gpv3: Tint color do not show in Solid view)
        for i, m in enumerate(ob.data.materials):
            data.materials.append(m)
        ## peel_mat : Create colored materal stack
        # for i, m in enumerate(ob.data.materials):
        #     if not m: # Replicate empty slot 
        #         data.materials.append(m)
        #         continue
        #     if m.grease_pencil.show_stroke and m.grease_pencil.show_fill:
        #         mat = bpy.data.materials.get(f'.onion_peel_prev_stroke_fill' if num < 0 else '.onion_peel_next_stroke_fill')
        #     elif m.grease_pencil.show_stroke:
        #         mat = bpy.data.materials.get(f'.onion_peel_prev_stroke' if num < 0 else '.onion_peel_next_stroke')
        #     elif m.grease_pencil.show_fill:
        #         mat = bpy.data.materials.get(f'.onion_peel_prev_fill' if num < 0 else '.onion_peel_next_fill')
        #     data.materials.append(mat)

        if not peel:
            peel = bpy.data.objects.new(peel_name, data)
            peel.hide_select = True
            peel.use_grease_pencil_lights = False
            peel_col.objects.link(peel)
        
        else:
            peel.data = data

        peel.show_in_front = ob.show_in_front
        peel['index'] = num
        used.append(peel)

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
            # print(mark, nl, cur_frame)
            f = copy_frame_at(mark, nl, cur_frame)
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
            outapeg_mat = flat_to_matrix(peel['outapeg'])

        if settings.world_space and mark: 
            context.scene.frame_set(mark)

        ## diff matrix at time of modification
        mat = ob.matrix_world @ outapeg_mat
        peel['mat'] = matrix_to_flat(mat)
        count += depth_offset # settings.depth_offset
        mat = get_new_matrix_with_offset(mat, offset=count)
        peel.matrix_world = mat

    # get back to original current frame
    if settings.world_space:
        context.scene.frame_set(cur_frame)
    
    # Delete too much peels
    for o in reversed(peel_col.objects):
        if o not in used:
            bpy.data.objects.remove(o)
            continue

    # reset visibility of peels items that are out of peels range
    for i, f in enumerate(settings.neg_frames):
        if i > gprev:
            f.visibility = True
    for i, f in enumerate(settings.pos_frames):
        if i > gnext:
            f.visibility = True

    # Clear unused old peel data
    for gp in bpy.data.grease_pencils[:]:
        if not gp.users and gp.name.startswith('.peel'):
            bpy.data.grease_pencils.remove(gp)

    scene.gp_ons_setting['activated'] = True #Mtx avoid infinite recursion
    op_col.hide_viewport = peel_col.hide_viewport = False
    
    # Hide other objects onions (show only active object onion)
    for c in op_col.children:
        c.hide_viewport = c is not peel_col

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

    # peel_mat : Set material color
    # base_names = [".onion_peel_prev", ".onion_peel_next"]
    # variations = ["_stroke", "_fill", "_stroke_fill"]
    # for base in base_names:
    #     for var in variations:
    #         mat_name = base + var
    #         if mat := bpy.data.materials.get(mat_name):
    #             if base == ".onion_peel_prev":
    #                 color = (*settings.before_color, 1.0)
    #             else:
    #                 color = (*settings.after_color, 1.0)
    #             mat.grease_pencil.color = color
    #             mat.grease_pencil.fill_color = color

# not used, ops used instead
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

# / peel_mat : unused for now (wont work well with texture based material)
"""
## Use material to show in Solid view... ?
## To use by batch assigning material index on either 0,1,3 (apply material index to mask)
# def set_peel_material_stack(data, prev=False):
#     '''set material stack to prev onion peel'''
#     if prev:
#         base = ".onion_peel_prev"
#     else:
#         base = ".onion_peel_next"
#     for variation in ["_stroke", "_fill", "_stroke_fill"]:
#         mat = bpy.data.materials.get(base + variation)
#         if not mat:
#             # create material if not exist
#             mat = bpy.data.materials.new(name=base + variation)
#             bpy.data.materials.create_gpencil_data(mat)
#             mat.grease_pencil.show_stroke = variation in ["_stroke", "_stroke_fill"]
#             mat.grease_pencil.show_fill = variation in ["_fill", "_stroke_fill"]
            
#             onp_setting = bpy.context.scene.gp_ons_setting
#             if prev:
#                 mat.grease_pencil.color = mat.grease_pencil.fill_color = onp_setting.before_color
#             else:
#                 mat.grease_pencil.color = mat.grease_pencil.fill_color = onp_setting.after_color

#         data.materials.append(mat)

def create_all_peel_materials():
    '''Create 6 materials for onion peels (3 prev and 3 next)'''
    base_names = [".onion_peel_prev", ".onion_peel_next"]
    variations = ["_stroke", "_fill", "_stroke_fill"]
    for base in base_names:
        for var in variations:
            mat_name = base + var
            mat = bpy.data.materials.get(mat_name)
            if not mat:
                mat = bpy.data.materials.new(name=mat_name)
                bpy.data.materials.create_gpencil_data(mat)
                mat.grease_pencil.show_stroke = var in ["_stroke", "_stroke_fill"]
                mat.grease_pencil.show_fill = var in ["_fill", "_stroke_fill"]
                if base == ".onion_peel_prev":
                    color = (*bpy.context.scene.gp_ons_setting.before_color, 1.0)
                else:
                    color = (*bpy.context.scene.gp_ons_setting.after_color, 1.0)
                mat.grease_pencil.color = color
                mat.grease_pencil.fill_color = color

def clear_all_peel_materials(full_clear=False):
    '''Remove 6 onion peels materials'''
    base_names = [".onion_peel_prev", ".onion_peel_next"]
    variations = ["_stroke", "_fill", "_stroke_fill"]
    for base in base_names:
        for var in variations:
            mat_name = base + var
            if mat := bpy.data.materials.get(mat_name):
                if mat.users and not full_clear:
                    continue
                bpy.data.materials.remove(mat)
# peel_mat /
"""

'''
## Experimental
def trigger_on_key(self, context):
    ob = bpy.context.object
    if not ob or ob.type != 'GREASEPENCIL' or ob.name.startswith('.peel'):
        return
    if not bpy.context.scene.gp_ons_setting.activated: 
        return
    l = ob.data.layers.active
    if not l:
        return
    if not hasattr(bpy.types.ViewLayer, 'gp_len_frame') or len(l.frames) != bpy.context.view_layer.gp_len_frame:
        print('update from frame len !', bpy.context.view_layer.gp_len_frame)
        bpy.types.ViewLayer.gp_len_frame = len(l.frames)
        update_onion(self, context)
'''
