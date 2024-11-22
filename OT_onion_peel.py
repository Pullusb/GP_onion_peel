from .preferences import get_addon_prefs
import bpy
from . import onion
from math import pi, isclose
import numpy as np
from mathutils import Matrix, Vector
import gpu
import blf
from gpu_extras.batch import batch_for_shader


class GPOP_OT_onion_skin_delete(bpy.types.Operator):
    bl_idname = "gp.onion_peel_delete"
    bl_label = "Delete Onion_Skin"
    bl_description = "Delete Onion Peels\
        \nShift + clic to delete all peels"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'
    
    def invoke(self, context, event):
        self.on_all = event.shift
        return self.execute(context)

    def execute(self, context):
        context.scene.gp_ons_setting.activated = False
        if self.on_all:
            onion.clear_peels(full_clear=True)
            # onion.clear_all_peel_materials(full_clear=True) # peel_mat
            return {"FINISHED"}

        onion.clear_current_peel(context.object)
        # onion.clear_all_peel_materials() # peel_mat
        return {"FINISHED"}

class GPOP_OT_onion_skin_refresh(bpy.types.Operator):
    bl_idname = "gp.onion_peel_refresh"
    bl_label = "Refresh Onion Peel"
    bl_description = "Refresh custom Onion peels (full regen if shift clicked)" 
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'

    def invoke(self, context, event):
        self.full_refresh = event.shift
        return self.execute(context)

    def execute(self, context):
        if not context.scene.gp_ons_setting.activated:
            context.scene.gp_ons_setting.activated = True
        
        gpl = context.object.data.layers
        if self.full_refresh:
            # clear and recreate
            onion.clear_peels() # full clear (delete all)
            if not [l for l in gpl if l.use_onion_skinning]: # Skip if no onion layers
                self.report({'WARNING'}, 'All layers have onion skin toggled off')
                return {'CANCELLED'}
            onion.force_update_onion(self, context)
        
        else:
            onion.clean_peels() # clean (without deleting)
            if not [l for l in gpl if l.use_onion_skinning]: # Skip if no onion layers
                self.report({'WARNING'}, 'All layers have onion skin toggled off')
                return {'CANCELLED'}
            
            # clear outapeg:
            onion.clear_custom_transform(all_peel=False)
            
            # just refresh existing (need to replace create and auto-clean if needed)
            onion.force_update_onion(self, context)
            
            ## remove native onion skin (done in force_update_onion now)
            # context.space_data.overlay.use_gpencil_onion_skin = False


        return {"FINISHED"}

class GPOP_OT_onion_peel_pyramid_fade(bpy.types.Operator):
    bl_idname = "gp.onion_peel_pyramid_fade"
    bl_label = "Onion Peel Pyramid Fade"
    bl_description = "Set basic linear Onion peeling opacity fade\n(shift+clic to put all to 100%)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'

    def invoke(self, context, event):
        self.shift = event.shift
        return self.execute(context)

    def change_opacity(self, context, scol, i):
        current_opacity = scol[abs(i)].opacity
        # current_opacity = getattr(self.settings, pid, 'opacity')
        
        if self.shift:
            opacity = 100
        else:
            if i < 0:
                opacity = int(100 - (abs(i) * (100 / (self.before + 1))))
            else:
                opacity = int(100 - (i * (100 / (self.after + 1))))
        
        if current_opacity == opacity:
            return
        
        # check current opacity level (if 0 dont change it)
        # restore opacity to 0 if it was there

        name = f'{onion.to_peel_name(self.ob.name)} {i}'
        peel = context.scene.objects.get(name)
        if not peel:
            # setattr(self.settings, pid, opacity) # trigger modification through update
            scol[abs(i)].opacity = opacity
            return

        restore = [m for m in peel.modifiers
            if m.type == 'GREASE_PENCIL_OPACITY' and m.factor == 0]

        # setattr(self.settings, pid, opacity) # trigger modification through update
        scol[abs(i)].opacity = opacity
        
        for m in restore:
            m.factor = 0

    def execute(self, context):
        self.settings = context.scene.gp_ons_setting
        self.before = self.settings.before_num
        self.after = self.settings.after_num
        self.ob = context.object
        self.gpl = context.object.data.layers


        for i in range(1,self.before+1):
            self.change_opacity(context, self.settings.neg_frames, -i)
       
        for i in range(1,self.after+1):
            self.change_opacity(context, self.settings.pos_frames, i)

        return {"FINISHED"}


### MODAL WITH FRAME HANDLER

def draw_callback_2d(self, context):
    if context.area != self._draw_area:
        return

    # green -> (0.06, 0.4, 0.040, 0.6)
    # orange -> (0.45, 0.18, 0.03, 1.0)
    osd_color = (0.06, 0.4, 0.040, 0.75)
    if bpy.app.version < (3,6,0):
        import bgl
        bgl.glLineWidth(10)
        self.shader_2d.bind()
        self.shader_2d.uniform_float("color", osd_color)
        self.screen_framing.draw(self.shader_2d)
        # Reset
        bgl.glLineWidth(1)
    else:
        gpu.state.line_width_set(10.0)
        self.shader_2d.bind()
        self.shader_2d.uniform_float("color", osd_color)
        self.screen_framing.draw(self.shader_2d)
        # Reset
        gpu.state.line_width_set(1.0)

    # Display Text
    if self.use_osd_text:
        font_id = 0
        dpi = context.preferences.system.dpi
        blf.color(font_id, *osd_color) # unpack color
        blf.position(font_id, context.region.width / 3, 15, 0)
        if bpy.app.version < (4,0,0):
            blf.size(font_id, 16, dpi)
        else:
            blf.size(font_id, 16)
        blf.draw(font_id, f'Peel transform mode : G / R / S / X')
        
        if not isclose(self.scale_offset[0], 1.0, rel_tol=0.0001):
            blf.position(font_id, context.region.width / 3, 45, 0)
            # if all([isclose(self.scale_offset[0], i, rel_tol=0.0001) for i in self.scale_offset[1:]]):
            #     scale_text = f'{self.scale_offset[0]:.2f}'
            # else:
            #     scale_text = [f'{i:.2f}' for i in self.scale_offset]
            # blf.draw(font_id, f'Scale Factor: {scale_text}')
            blf.draw(font_id, f'Scale Factor: {self.scale_offset[0]:.3f}')
            

class GPOP_OT_onion_peel_tranform(bpy.types.Operator):
    bl_idname = "gp.onion_peel_tranform"
    bl_label = "Peel Custom Transform"
    bl_description = "Place or replace the onion peel\
        \nCtrl + Click to copy transform from another peel"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'
    
    tab_press_ct = 0
    peel_num : bpy.props.IntProperty()

    def get_bbox_center(self, ob, world=False):
        bbox_center = 0.125 * sum((Vector(b) for b in ob.bound_box), Vector())
        if world:
            return ob.matrix_world @ bbox_center
        return bbox_center

    def geometry_to_origin(self, ob, world=False):
        bbox_center = self.get_bbox_center(ob, world)
        for l in ob.data.layers:
            dr = l.current_frame().drawing
            ## Substract bbox center on all positions attribute at once
            num_points = dr.attributes.domain_size('POINT')
            positions_data = np.zeros((num_points, 3), dtype=np.float32)
            
            ## np.ravel pass as flat array without changing original shape
            dr.attributes['position'].data.foreach_get('vector', np.ravel(positions_data))
            ## Apply offset
            positions_data -= bbox_center
            ## Write in position attribute
            dr.attributes['position'].data.foreach_set('vector', np.ravel(positions_data))

    def get_offset_matrix(self):
        source_mat = Matrix(self.peel['mat'])
        ## Get offset matrix
        mat = self.peel.matrix_world @ (self.geo_org_matrix.inverted() @ source_mat)
        ## Apply offset from original object  (cancel it, will be applyed at exit refresh)
        mat = self.main_obj.matrix_world.inverted() @ mat
        return mat

    def invoke(self, context, event):
        if not context.scene.gp_ons_setting.activated:
            self.report({'WARNING'}, f'Onion Peels are disabled\nEnable or refresh first')
            return {"CANCELLED"}

        if not self.peel_num:
            self.report({'ERROR'}, f'Peel number seems not valid : {self.peel_num}\nTry refreshing')
            return {"CANCELLED"}
        
        ob = context.object
        peel_name =  f'{onion.to_peel_name(ob.name)} {self.peel_num}'
        peel = context.scene.objects.get(peel_name)
        if not peel:
            self.report({'ERROR'}, f'Could not find this Onion peel, it might no exists yet ! \nTry refreshing first.')
            return {"CANCELLED"}
        
        if peel.hide_viewport:
            self.report({'ERROR'}, f"Can't edit hided peel")
            return {"CANCELLED"}

        # check if no frames
        ok = False
        for l in peel.data.layers:
            for f in l.frames:
                ok = True
                break
        if not ok:
            self.report({'WARNING'}, f'This peel is empty (probably out keyframe of range)')
            return {"CANCELLED"}
        
        self.peel = peel

        ## if control is pressed, popup a panel to copy another peel offset (outapeg)
        if event.ctrl:
            ## list other peels
            self.other_transformed_peels = [p for p in peel.users_collection[0].all_objects\
                            if p is not peel\
                            and p.get('outapeg')]
            print('other_transformed_peels: ', self.other_transformed_peels)
            if not self.other_transformed_peels:
                self.report({'ERROR'}, f'No other peel has a transform to copy')
                return {"CANCELLED"}
            return context.window_manager.invoke_props_dialog(self) # , width=popup_width

        context.scene.gp_ons_setting.frame_prev = -9999
        prefs = get_addon_prefs()
        self.use_osd_text = prefs.use_osd_text

        self.autokey = context.scene.tool_settings.use_keyframe_insert_auto
        context.scene.tool_settings.use_keyframe_insert_auto = False

        self.org_matrix = peel.matrix_world.copy()

        self.gp_last_mode = context.mode
        
        # Reset the object matrix without depth offset
        self.peel.matrix_world = Matrix(self.peel['mat'])

        self.init_frame = context.scene.frame_current
        self.scale_offset = (1.0, 1.0, 1.0)
        
        # make it selectable and set as active
        bpy.ops.object.mode_set(mode='OBJECT')
        peel.hide_select = False
        ob.select_set(False)
        context.view_layer.objects.active = peel
        peel.select_set(True)

        self.main_obj = ob
        
        ## Handle selectability (store and disable all objects selection)
        # peelcol = peel.users_collection[0]
        # self.select_list = [(o, o.hide_select) for o in context.scene.objects]
        # for o in context.scene.objects:
        #     if not peelcol in o.users_collection:
        #         o.hide_select = True
        
        ## Set the origin to center of object (new starting point)
        origin = self.get_bbox_center(self.peel, world=False)
        context.scene.cursor.location = origin
        self.geometry_to_origin(self.peel, world=False)

        T = Matrix.Translation(origin)
        self.peel.matrix_world = self.peel.matrix_world @ T

        # ## store new starting point
        self.geo_org_matrix = self.peel.matrix_world.copy()

        ## screen color frame
        r = bpy.context.region
        w = r.width
        h = r.height

        if bpy.app.version < (4,0,0):
            self.shader_2d = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
            self.screen_framing = batch_for_shader(
            self.shader_2d, 'LINE_LOOP', {"pos": [(0,0), (0,h), (w,h), (w,0)]})
        else:
            self.shader_2d = gpu.shader.from_builtin('POLYLINE_UNIFORM_COLOR')
            self.screen_framing = batch_for_shader(
            self.shader_2d, 'LINES', {"pos": [(0,0), (0,h), (w,h), (w,0)]},
                                      indices=[(0,1),(1,2),(2,3),(3,0)])

            #   "indices": [0,1,1,2,2,3,3,0]})
        
        ## OpenGL handler
        self._draw_area = context.area
        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback_2d, args, "WINDOW", "POST_PIXEL")

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def draw(self, context):
        layout = self.layout
        for p in self.other_transformed_peels:
            op = layout.operator('gp.copy_peel_transform', text=f'Copy From Peel {p.name.rsplit()[-1]}')
            op.src = p.name
            op.dest = self.peel.name

    def execute(self, context):
        return {"FINISHED"}

    def exit(self, context):
        self.peel.hide_select = True
        self.main_obj.select_set(True)
        context.view_layer.objects.active = self.main_obj
        self.peel.select_set(False)
        # restore mode
        context.area.header_text_set(None)
        bpy.ops.object.mode_set(mode=self.gp_last_mode)

        # restore selection
        # for o, state in self.select_list:
        #     o.hide_select = state

        context.scene.frame_current = self.init_frame
        context.scene.tool_settings.use_keyframe_insert_auto = self.autokey
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        context.scene.gp_ons_setting.frame_prev = -9999
        bpy.ops.ed.undo_push(message='Back To Grease Pencil')
    
    def cancel(self, context):
        self.peel.matrix_world = self.org_matrix
        # context.scene.frame_current = self.init_frame
        self.exit(context)

    def back_to_object(self, context):
        mat = self.get_offset_matrix()
        self.peel['outapeg'] = mat.copy()
        self.exit(context)

    def modal(self, context, event):
        self.scale_offset = self.get_offset_matrix().to_scale()
        context.area.header_text_set(f'Pick onion peel - use G:move / R:rotate / S:scale / X,M:mirror')
        if context.view_layer.objects.active != self.peel:
            self.report({'WARNING'}, "Only selected peel must be moved before pressing ENTER")
            tmp = context.view_layer.objects.active
            context.view_layer.objects.active = self.peel
            self.peel.select_set(True)
            tmp.select_set(False)


        # lock frame
        if context.scene.frame_current != self.init_frame:
            context.scene.frame_current = self.init_frame

        # lock everything except G R S clic
        if event.type in {'G', 'R', 'S', 'LEFTMOUSE', 'RIGHTMOUSE', 'MIDDLEMOUSE', 'WHEELDOWNMOUSE', 'WHEELUPMOUSE'}:
            return {'PASS_THROUGH'}

        if event.type in {'X', 'M'} and event.value == 'PRESS':
            if event.shift: # flip vertical
                self.peel.matrix_world @= Matrix.Rotation(pi, 4, 'X')
            else: # flip horizontal
                self.peel.matrix_world @= Matrix.Rotation(pi, 4, 'Z')
            return {'RUNNING_MODAL'}
        
        if event.type in {'TAB'} and event.value == 'PRESS':
            if event.type == 'TAB' and event.value == 'PRESS':
                self.tab_press_ct += 1
            if self.tab_press_ct < 2:
                self.report({'WARNING'}, "In Peel transform ! Pressing TAB again will Cancel")
                return {"RUNNING_MODAL"}
            self.cancel(context)
            return {"CANCELLED"}

        if event.type in {'ESC', 'DEL'}:
            self.cancel(context)
            return {"CANCELLED"}

        if event.type in {'RET', 'NUMPAD_ENTER', 'B'} and event.value == 'PRESS': # 'SPACE'
            self.back_to_object(context)
            return {"FINISHED"}

        return {'RUNNING_MODAL'}

class GPOP_OT_copy_peel_transform(bpy.types.Operator):
    bl_idname = "gp.copy_peel_transform"
    bl_label = "Copy Peel Transform"
    bl_description = "Copy the transform of a peel to another"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'

    src : bpy.props.StringProperty()
    dest : bpy.props.StringProperty()

    def execute(self, context):
        source = context.scene.objects.get(self.src)
        destination = context.scene.objects.get(self.dest)
        if not source or not destination:
            self.report({'ERROR'}, f'Could not copy peel transform from {self.src} to {self.dest}')
            return {"CANCELLED"}
        
        # Assign outapeg value
        destination['outapeg'] = source['outapeg']

        # since the property is deleted the reevaluation will reset it
        onion.force_update_onion(self, context)
        bpy.ops.ed.undo_push(message='Copy Peel transform')
        return {"FINISHED"}

class GPOP_OT_onion_reset_peel_transform(bpy.types.Operator):
    bl_idname = "gp.reset_peel_transform"
    bl_label = "Reset Peel Transform"
    bl_description = "Reset the transform of selected onion peel"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'

    peel_num : bpy.props.IntProperty()

    def execute(self, context):
        if not self.peel_num:
            self.report({'ERROR'}, f'Peel number seems not valid : {self.peel_num}\nTry refreshing')
            return {"CANCELLED"}

        ob = context.object
        peel_name =  f'{onion.to_peel_name(ob.name)} {self.peel_num}'
        
        peel = context.scene.objects.get(peel_name)
        if not peel:
            self.report({'ERROR'}, f'Could not find this Onion peel!\nTry refreshing')
            return {"CANCELLED"}

        del peel['outapeg']
        # since the propery is deleted the reevaluation will reset it
        onion.force_update_onion(self, context)
        bpy.ops.ed.undo_push(message='Reset Peel transform')
        return {"FINISHED"}


class GPOP_OT_onion_swap_xray(bpy.types.Operator):
    bl_idname = "gp.onion_swap_xray"
    bl_label = "Onion Swap Xray"
    bl_description = "Toggle In Front for both object and it's peel\nShit + clic to only affect peels"
    bl_options = {"REGISTER", "UNDO"}

    use_xray : bpy.props.BoolProperty()

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GREASEPENCIL'
    
    def invoke(self, context, event):
        self.peel_only = event.shift
        return self.execute(context)

    def execute(self, context):
        op_col = bpy.data.collections.get('.onion_peels')
        if not op_col:
            return {"CANCELLED"}
        peel_col = op_col.children.get(onion.to_onion_name(context.object.name))
        if not peel_col:
            return {"CANCELLED"}
        if not self.peel_only:
            context.object.show_in_front = self.use_xray

        for peel in peel_col.objects:
            peel.show_in_front = self.use_xray

        return {"FINISHED"}


### --- REGISTER ---

classes=(
GPOP_OT_onion_skin_refresh,
GPOP_OT_onion_skin_delete,
GPOP_OT_onion_peel_pyramid_fade,
GPOP_OT_copy_peel_transform,
GPOP_OT_onion_peel_tranform,
GPOP_OT_onion_reset_peel_transform,
GPOP_OT_onion_swap_xray,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)