import bpy
from bpy.app.handlers import persistent
from time import time
from mathutils import Matrix, Vector
import random
import numpy as np
from . import preferences

## State watched between refreshes, to detect changes that need one (see check_new_key)
## (ob_name, frame_number, [held_layer_names], layer_state) or None
_watch = None

## True while peels are being rebuilt (re-entrancy guard)
_updating = False

## True when an undo/redo needs a refresh, done at the next depsgraph update (see check_new_key)
_undo_refresh = False

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

def get_view3d_overlay():
    """Overlay settings of the current 3D view
    return first 3D area found if not current area
    None if there is no 3D view
    """
    area = getattr(bpy.context, 'area', None)
    if area and area.type == 'VIEW_3D':
        return area.spaces.active.overlay
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                return area.spaces[0].overlay

def get_layer_fade():
    """Opacity multiplier to apply to peels of inactive layers, following the viewport
    'Fade Inactive Layers' overlay (1.0 when disabled: no fade)
    """
    overlay = get_view3d_overlay()
    if not overlay or not overlay.use_gpencil_fade_layers:
        return 1.0
    return overlay.gpencil_fade_layer

def get_collection_childs_recursive(col, cols=[]):
    for sub in col.children:
        if sub not in cols:
            cols.append(sub)
        if len(sub.children):
            cols = get_collection_childs_recursive(sub, cols)
    return cols


def clear_peels(full_clear=False):
    """Clear all onion peels collection and object
    :full_clear: Clear .peels even if outside of onion peels collection
    """
    
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
            if ob.name.startswith('.peel_'):
                bpy.data.objects.remove(ob)
        
        if not len(op_col.all_objects):
            bpy.data.collections.remove(op_col)

def clear_custom_transform(all_peel=False):
    op_col = bpy.data.collections.get('.onion_peels')
    if not op_col:
        return
    if all_peel:
        pool = [c for c in op_col.children if c.name.startswith('.onion')]
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
    """Return sorted keys frame number of GP object"""

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


def get_layer_collection(layer_col, name):
    """Return the layer collection with this name, searched recursively (None if not in view layer)"""
    found = layer_col.children.get(name)
    if found:
        return found
    for child in layer_col.children:
        found = get_layer_collection(child, name)
        if found:
            return found

def create_peel_col(context):
    # get/create onion skin collection
    op_col = bpy.data.collections.get('.onion_peels')
    if not op_col:
        op_col = bpy.data.collections.new('.onion_peels')
        op_col.hide_render = True

    # ensure collection is linked in the scene (an undo can restore it unlinked) and visible in viewlayer
    ons_vl = get_layer_collection(context.view_layer.layer_collection, op_col.name)
    if not ons_vl:
        context.scene.collection.children.link(op_col)
        ons_vl = context.view_layer.layer_collection.children[op_col.name]
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

    peel_vl = ons_vl.children.get(colname)
    if peel_vl:
        peel_vl.exclude = False

    return op_col, peel_col

## Modifiers exclusion for peels
EXCLUDED_MODIFIERS = {
    'GREASE_PENCIL_TIME',    # incompatible with time remapping
    'GREASE_PENCIL_BUILD',   # incompatible build
    'LINEART',               
    'GREASE_PENCIL_TINT',    # conflicts with tint color
    'GREASE_PENCIL_COLOR',
    'GREASE_PENCIL_OPACITY', # conflicts with the peel opacity
}

def copy_curve_mapping(source, target):
    """Copy a CurveMapping (the 'custom_curve' of noise/thickness/smooth/hook modifiers)"""
    for attr in ('tone', 'use_clip', 'clip_min_x', 'clip_min_y', 'clip_max_x', 'clip_max_y',
                 'extend', 'black_level', 'white_level'):
        setattr(target, attr, getattr(source, attr))

    for scurve, tcurve in zip(source.curves, target.curves):
        spoints, tpoints = scurve.points, tcurve.points

        ## Trim down to the two extremities (a curve map cannot go under two points)
        ## Note: always re-fetch tpoints[-1], removal reallocates the point array
        for _ in range(len(tpoints) - 2):
            tpoints.remove(tpoints[-1])

        ## points.new() inserts sorted by X: set the two existing extremities first,
        ## then insert the in-between points in ascending X order
        tpoints[0].location = spoints[0].location
        tpoints[-1].location = spoints[-1].location
        for spoint in spoints[1:-1]:
            tpoints.new(spoint.location[0], spoint.location[1])

        for spoint, tpoint in zip(spoints, tpoints):
            tpoint.location = spoint.location
            tpoint.handle_type = spoint.handle_type

    target.update()

def copy_modifier(source_mod, target_ob):
    """Create a copy of source_mod on target_ob, return it (None if type is excluded)"""
    if source_mod.type in EXCLUDED_MODIFIERS:
        return
    target_mod = target_ob.modifiers.new(source_mod.name, source_mod.type)
    for p in source_mod.bl_rna.properties:
        if p.is_readonly or p.identifier in ('rna_type', 'type'):
            continue
        try:
            setattr(target_mod, p.identifier, getattr(source_mod, p.identifier))
        except (AttributeError, TypeError, ValueError, RuntimeError):
            pass
    ## 'custom_curve' is a read-only pointer, so the loop above skipped it: copy it by hand
    ## (noise, thickness, smooth, hook, opacity, tint and color modifiers have one)
    if getattr(source_mod, 'custom_curve', None):
        copy_curve_mapping(source_mod.custom_curve, target_mod.custom_curve)
    return target_mod

def transfer_modifiers(source_ob, target_ob):
    """Rebuild target_ob modifier stack from source_ob, skipping EXCLUDED_MODIFIERS"""
    clear_modifiers(target_ob)
    for m in source_ob.modifiers:
        copy_modifier(m, target_ob)

def clear_modifiers(ob):
    for m in reversed(ob.modifiers):
        ob.modifiers.remove(m)

def scale_matrix_from_vector(scale):
    """recreate a neutral mat scale"""
    matscale_x = Matrix.Scale(scale[0], 4, (1,0,0))
    matscale_y = Matrix.Scale(scale[1], 4, (0,1,0))
    matscale_z = Matrix.Scale(scale[2], 4, (0,0,1))
    matscale = matscale_x @ matscale_y @ matscale_z
    return matscale

def get_new_matrix_with_offset(matrix, offset=0.0001):
    """return a copy of the matrix with applied offset (unchanged copy if it cannot be computed)"""

    cam = bpy.context.scene.camera
    if not cam:
        # TODO check viewport view if in viewport if no cam
        return matrix.copy()
    
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
        if not v.length:
            return mat # object origin on the camera position: no depth direction
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
    if not source_drawing:
        return

    ## Skip empty drawing: it has no curve_offsets data (though a length of 1 is reported)
    num_strokes = len(source_drawing.strokes)
    if not num_strokes:
        return

    ## curve_offsets: one start index per stroke + total point count (no per-stroke python wrappers)
    offsets = np.empty(num_strokes + 1, dtype=np.int32)
    source_drawing.curve_offsets.foreach_get('value', offsets)

    dr = frame.drawing
    ## Add all strokes at once with list of point numbers
    dr.add_strokes(np.diff(offsets).tolist())
    # faster than: dr.add_strokes([len(s.points) for s in source_drawing.strokes])

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
    """Rebuild the peels (guarded against re-entrancy, e.g. the world space frame_set below
    triggering frame_change_post)"""
    global _updating
    if _updating:
        return
    _updating = True
    try:
        build_peels(self, context)
    finally:
        _updating = False

def build_peels(self, context):
    global _watch
    if not hasattr(bpy.context, 'object'):
        return
    ob = bpy.context.object
    if not ob or ob.type != 'GREASEPENCIL' or ob.name.startswith('.peel'):
        return

    scene = context.scene

    op_col = bpy.data.collections.get('.onion_peels')
    if not scene.gp_ons_setting.activated:
        _watch = None
        if op_col:
            op_col.hide_viewport = True
        return

    if bpy.context.screen.is_animation_playing:
        _watch = None
        if op_col:
            op_col.hide_viewport = True
        return

    ## Frame flag to prevent tirggering multiple times on the same frame
    if scene.gp_ons_setting.frame_prev == scene.frame_current:
        return
    else:
        scene.gp_ons_setting.frame_prev = scene.frame_current


    gpl = ob.data.layers
    if not [l for l in gpl if is_onion_layer(l)]: # Skip if no onion layers
        ## still watch the flags: re-enabling a layer needs a refresh
        _watch = (ob.name, scene.frame_current, [], get_layer_state(ob))
        return

    clean_peels()

    op_col, peel_col = create_peel_col(bpy.context)

    op_col.hide_viewport = False

    peelname = to_peel_name(ob.name)
    
    depth_offset = preferences.get_addon_prefs().depth_offset
    depth_offset = depth_offset if not preferences.get_addon_prefs().peel_in_front else -depth_offset
    use_transfer_mods = preferences.get_addon_prefs().transfer_modifiers
    cur_frame = scene.frame_current
    settings = scene.gp_ons_setting
    opacity_factor = settings.o_general / 100
    layer_fade = get_layer_fade()
    active_layer = ob.data.layers.active
    active_layer_name = active_layer.name if active_layer else None
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

    set_watch(ob, cur_frame)

    ## calculate all frame index by layer once
    for l in gpl:
        if not is_onion_layer(l):
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
        return
        
    count = 0
    for num in [-i for i in range(1,gprev+1)] + [i for i in range(1,gnext+1)]:
        absnum = abs(num)

        ## Get / create the peel object and data. Peels are reused and refilled in place
        ## creating/removing IDs outside undo push (ex: from handlers) corrupts undo stack and crashes on ctrl+Z
        peel_name = f'{peelname} {num}'
        peel = op_col.all_objects.get(peel_name)

        if not peel:
            data = bpy.data.grease_pencils.new(peel_name)
            peel = bpy.data.objects.new(peel_name, data)
            peel.hide_select = True
            peel.use_grease_pencil_lights = False
            peel_col.objects.link(peel)
        elif peel.data is None or peel.data.users > 1:
            ## Shared data ('.dummy' from older versions)
            peel.data = bpy.data.grease_pencils.new(peel_name)
        data = peel.data

        ## Clear previous content
        for l in reversed(data.layers[:]):
            data.layers.remove(l)

        ## Get same material stack (gpv3: Tint color do not show in Solid view)
        ## Use slot material (resolve slots linked to object instead of data)
        src_materials = [slot.material for slot in ob.material_slots]
        if list(data.materials) != src_materials:
            data.materials.clear()
            for m in src_materials:
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

        peel.show_in_front = ob.show_in_front

        # Replicate modifiers
        if use_transfer_mods:
            transfer_modifiers(ob, peel)
        elif peel.modifiers:
            clear_modifiers(peel)

        peel['index'] = num
        used.append(peel)

        mark_prev = []
        mark_next = []
        for layer in layers:
            info, previous, following = layer[:]
            
            mark = None
            if num < 0:
                fsetting = settings.neg_frames[abs(num)]
                if absnum < len(previous) + 1:   
                    mark = previous[num]
                    mark_prev.append(mark.frame_number)
            else:
                fsetting = settings.pos_frames[num]
                if absnum < len(following) + 1:
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
            if layer_fade < 1.0 and info != active_layer_name:
                nl.opacity *= layer_fade # viewport 'Fade Inactive Layers' overlay
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
    
    # Delete too much peels (peel number changed)
    for o in reversed(peel_col.objects):
        if o not in used:
            data = o.data
            bpy.data.objects.remove(o)
            if data and not data.users:
                bpy.data.grease_pencils.remove(data)

    # reset visibility of peels items that are out of peels range
    # only when needed: each assignment triggers update_opacity, even with the same value (added 'and not f.visibility')
    for i, f in enumerate(settings.neg_frames):
        if i > gprev and not f.visibility:
            f.visibility = True
    for i, f in enumerate(settings.pos_frames):
        if i > gnext and not f.visibility:
            f.visibility = True

    # Clear unused old peel data (only left by older versions)
    for gp in bpy.data.grease_pencils[:]:
        if not gp.users and gp.name.startswith(('.peel', '.dummy')):
            bpy.data.grease_pencils.remove(gp)

    op_col.hide_viewport = peel_col.hide_viewport = False
    
    # Hide other objects onions (show only active object onion)
    for c in op_col.children:
        c.hide_viewport = c is not peel_col

def is_onion_layer(node):
    """Layer (or group) is visible and uses onion skinning, parent groups included
    (a hidden group does not change its layers own flags)"""
    if node is None: # above top level
        return True
    return not node.hide and node.use_onion_skinning and is_onion_layer(node.parent_group)

def get_layer_state(ob):
    """Everything about the layers that changes what the peels show: flags toggled from the UI
    or by operators, plus the active layer when inactive ones are faded by the overlay"""
    fade = get_layer_fade()
    active = ob.data.layers.active
    return (tuple((l.name, l.hide, l.use_onion_skinning) for l in ob.data.layers),
            tuple((g.name, g.hide, g.use_onion_skinning) for g in ob.data.layer_groups),
            active.name if (active and fade < 1.0) else None,
            fade)

def set_watch(ob, frame):
    """Store what needs to be watched until the next refresh:
    - onion layers without key at frame (held frame): a key can be created there without frame change (auto-key)
    - layer flags: visibility and onion skinning toggles
    """
    global _watch
    held_layers = []
    for l in ob.data.layers:
        if not is_onion_layer(l):
            continue
        current = l.current_frame()
        if current is None or current.frame_number != frame:
            held_layers.append(l.name)
    _watch = (ob.name, frame, held_layers, get_layer_state(ob))

@persistent
def refresh_after_undo(*args):
    """undo/redo: peels are part of the undo data, stepping back before their creation removes them
    (a saved state has none: they are deleted on save). Rebuild from the restored state, which also
    re-evaluates the watched layers (keys restored by undo are not new keys, but later ones must trigger)"""
    global _watch, _undo_refresh
    scene = bpy.context.scene
    ob = bpy.context.object
    if (not scene.gp_ons_setting.activated
            or not ob or ob.type != 'GREASEPENCIL' or ob.name.startswith('.peel')):
        _watch = None
        _undo_refresh = False
        return
    ## Refresh at the next depsgraph update, not here: matrices are not evaluated yet at this point
    ## (they read as identity, placing the peels at world origin without depth offset).
    ## A view_layer.update() would fix it but costs a full scene evaluation on every undo
    _undo_refresh = True

@persistent
def check_new_key(scene, depsgraph):
    """depsgraph_update_post: refresh on changes that send no frame change, i.e. a key created by auto-key
    on a held frame, or a layer visibility / onion skinning toggle.
    Called very often, so bail out as early and cheaply as possible
    """
    global _undo_refresh
    if _undo_refresh:
        ## matrices are evaluated at this point (see refresh_after_undo)
        _undo_refresh = False
        if scene.gp_ons_setting.activated:
            scene.gp_ons_setting.frame_prev = -9999 # force (same frame as before the undo)
            update_onion(scene, depsgraph)
            return

    if _watch is None:
        return
    if not depsgraph.id_type_updated('GREASEPENCIL_V3'): # 'GREASEPENCIL' is legacy (annotations)
        return
    if not scene.gp_ons_setting.activated:
        return

    ob_name, frame, layer_names, layer_state = _watch
    if scene.frame_current != frame:
        return
    ob = bpy.context.object
    if not ob or ob.name != ob_name:
        return

    ## layer visibility or onion skinning toggled: the peels must follow
    if get_layer_state(ob) != layer_state:
        scene.gp_ons_setting.frame_prev = -9999
        update_onion(scene, depsgraph)
        return

    for name in layer_names:
        layer = ob.data.layers.get(name)
        if not layer:
            continue
        current = layer.current_frame()
        if current and current.frame_number == frame:
            ## Refresh right away, even during a stroke/transform (key is created at operator start).
            ## Waiting for the operator end is unreliable: transform confirm sends no further depsgraph update.
            ## Safe for undo since peels are refilled in place (no ID creation)
            scene.gp_ons_setting.frame_prev = -9999
            update_onion(scene, depsgraph)
            return

def update_opacity(self, context):
    settings = context.scene.gp_ons_setting
    op_col = bpy.data.collections.get('.onion_peels')
    if not op_col:
        return

    peel_col = op_col.children.get(to_onion_name(context.object.name))
    if not peel_col:
        return

    opacity_factor = settings.o_general / 100
    layer_fade = get_layer_fade()
    active_layer = context.object.data.layers.active
    active_layer_name = active_layer.name if active_layer else None

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
            if layer_fade < 1.0 and l.name != active_layer_name:
                l.opacity *= layer_fade # viewport 'Fade Inactive Layers' overlay

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
