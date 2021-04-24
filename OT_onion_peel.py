import bpy
from . import onion
from math import pi
from mathutils import Matrix, Vector

class GPOP_OT_onion_skin_delete(bpy.types.Operator):
    bl_idname = "gp.onion_peel_delete"
    bl_label = "Delete Onion_Skin"
    bl_description = "Delete Onion Peels\nShift + clic to delete all peels"
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
            onion.clear_peels(full_clear=True)
            return {"FINISHED"}

        onion.clear_current_peel(context.object)

        return {"FINISHED"}

class GPOP_OT_onion_skin_refresh(bpy.types.Operator):
    bl_idname = "gp.onion_peel_refresh"
    bl_label = "Refresh Onion Peel"
    bl_description = "Refresh custom Onion peels (full regen if shift clicked)" 
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'
    
    # called : bpy.props.BoolProperty(default=False)

    def invoke(self, context, event):
        # self.on_all = event.shift
        self.full_refresh = event.shift
        return self.execute(context)

    def execute(self, context):
        # if not self.called:
            # do not touch activate if called by it. 
        if not context.scene.gp_ons_setting.activated:
            context.scene.gp_ons_setting.activated = True
        # self.called = False
        
        gpl = context.object.data.layers
        if self.full_refresh:
            # clear and recreate
            onion.clear_peels() # full clear (delete all)
            if not [l for l in gpl if l.use_onion_skinning]: # Skip if no onion layers
                self.report({'WARNING'}, 'All layers have onion skin toggled off')
                return {'CANCELLED'}
            onion.update_onion(self, context)
        
        else:
            onion.clean_peels() # clean (without deleting)
            if not [l for l in gpl if l.use_onion_skinning]: # Skip if no onion layers
                self.report({'WARNING'}, 'All layers have onion skin toggled off')
                return {'CANCELLED'}
            
            # just refresh existing (need to replace create and auto-clean if needed)
            onion.update_onion(self, context)
            context.space_data.overlay.use_gpencil_onion_skin = False


        return {"FINISHED"}

class GPOP_OT_onion_peel_pyramid_fade(bpy.types.Operator):
    bl_idname = "gp.onion_peel_pyramid_fade"
    bl_label = "Onion Peel Pyramid Fade"
    bl_description = "Set basic linear Onion peeling opacity fade\n(shift+clic to put all to 100%)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'

    def invoke(self, context, event):
        self.shift = event.shift
        return self.execute(context)

    def change_opacity(self, context, scol, i):
        # pid = f'{pid_prefix}{i}'
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

        restore = [m for m in peel.grease_pencil_modifiers
            if m.type == 'GP_OPACITY' and m.factor == 0]

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


class GPOP_OT_onion_peel_tranform(bpy.types.Operator):
    bl_idname = "gp.onion_peel_tranform"
    bl_label = "Peel Custom Transform"
    bl_description = "Place or replace the onion peel"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'
    
    tab_press_ct = 0
    peel_num : bpy.props.IntProperty()

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
        
        # check if no frames
        ok = False
        for l in peel.data.layers:
            for f in l.frames:
                ok = True
                break
        if not ok:
            self.report({'WARNING'}, f'This peel is empty (probably out keyframe of range)')
            return {"CANCELLED"}

    
        self.gp_last_mode = context.mode
        self.org_matrix = peel.matrix_world.copy()
        self.init_frame = context.scene.frame_current
        bpy.ops.object.mode_set(mode='OBJECT')
        # make it selectable and set as active
        peel.hide_select = False
        ob.select_set(False)
        context.view_layer.objects.active = peel
        peel.select_set(True)

        self.peel = peel

        self.source = ob
        
        
        # Handle selectability (store and disable all objects selection)
        # peelcol = peel.users_collection[0]
        # self.select_list = [(o, o.hide_select) for o in context.scene.objects]
        # for o in context.scene.objects:
        #     if not peelcol in o.users_collection:
        #         o.hide_select = True

        # launching ops dont work
        # bpy.ops.transform.translate() 
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    

    def exit(self, context):
        self.peel.hide_select = True
        self.source.select_set(True)
        context.view_layer.objects.active = self.source
        self.peel.select_set(False)
        self.peel.location = self.peel.location
        # restore mode
        context.area.header_text_set(None)
        bpy.ops.object.mode_set(mode=self.gp_last_mode)

        # restore selection
        # for o, state in self.select_list:
        #     o.hide_select = state

        bpy.ops.ed.undo_push(message='Back To Grease Pencil')
    
    def cancel(self, context):
        self.peel.matrix_world = self.org_matrix
        self.exit(context)

    def back_to_object(self, context):
        mat = self.source.matrix_world.inverted() @ self.peel.matrix_world
        self.peel['outapeg'] = [v[:] for v in mat] # mat # str(list(mat))
        self.exit(context)

    def modal(self, context, event):
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

        if event.type in {'RET'} and event.value == 'PRESS':
            context.scene.frame_current = self.init_frame
            self.back_to_object(context)
            return {"FINISHED"}

        return {'RUNNING_MODAL'}

class GPOP_OT_onion_reset_peel_transform(bpy.types.Operator):
    bl_idname = "gp.reset_peel_transform"
    bl_label = "Reset Peel Transform"
    bl_description = "Reset the transform of selected onion peel"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'

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
        onion.update_onion(self, context)
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
        return context.object and context.object.type == 'GPENCIL'
    
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
GPOP_OT_onion_peel_tranform,
GPOP_OT_onion_reset_peel_transform,
GPOP_OT_onion_swap_xray,
)

# TODO Add handler on frame post to refresh the timeline offset

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)