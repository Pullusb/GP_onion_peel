import bpy
from . import onion

class GPOP_OT_onion_skin_delete(bpy.types.Operator):
    bl_idname = "gp.onion_peel_delete"
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
            onion.clear_peels(full_clear=True)
            return {"FINISHED"}

        pool = [context.object.name]
        for name in pool:
            col = bpy.data.collections.get(onion.to_onion_name(name))
            for o in col.all_objects:
                bpy.data.objects.remove(o)
            bpy.data.collections.remove(col)
        
        onioncol = bpy.data.collections.get('.onion_peels')
        if not len(onioncol.children) and not len(onioncol.all_objects):
            bpy.data.collections.remove(onioncol)

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
            onion.clear_peels()
            if not [l for l in gpl if l.use_onion_skinning]: # Skip if no onion layers
                self.report({'WARNING'}, 'All layers have onion skin toggled off')
                return {'CANCELLED'}
            onion.generate_onion_peels(self, context)
        
        else:
            onion.clean_peels()
            gpl = context.object.data.layers
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

    def change_opacity(self, context, i, pid_prefix):
        pid = f'{pid_prefix}{i}'
        current_opacity = getattr(self.settings, pid, 'opacity')
        
        if self.shift:
            opacity = 100
        else:
            opacity = int(100 - (i * (100 / (self.before + 1))))
        
        if current_opacity == opacity:
            return
        
        # check current opacity level (if 0 dont change it)
        # restore opacity to 0 if it was there
        name = f'{onion.to_peel_name(self.ob.name)} {-i}'
        peel = context.scene.objects.get(name)
        if not peel:
            setattr(self.settings, pid, opacity) # trigger modification through update
            return

        restore = [m for m in context.object.grease_pencil_modifiers
            if m.type == 'GP_OPACITY' and m.factor == 0]

        setattr(self.settings, pid, opacity) # trigger modification through update
        
        for m in restore:
            m.factor = 0

    def execute(self, context):
        self.settings = context.scene.gp_ons_setting
        self.before = self.settings.before_num
        self.after = self.settings.after_num
        self.ob = context.object
        self.gpl = context.object.data.layers

        for i in range(1,self.before+1):
            self.change_opacity(context, i, pid_prefix='o_p')
        for i in range(1,self.after+1):
            self.change_opacity(context, i, pid_prefix='o_n')

        return {"FINISHED"}

class GPOP_OT_onion_back_to_object(bpy.types.Operator):
    bl_idname = "gp.onion_back_to_object"
    bl_label = "Back to GP"
    bl_description = "Get back to GP editing from selected Onion peel"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'
    
    def invoke(self, context, event):
        self.on_all = event.shift
        return self.execute(context)

    def execute(self, context):
        ob = context.object
        collec = ob.users_collection[0]
        if not collec.name.startswith('.onion_'):
            self.report({'ERROR'}, 'this operator works if a ".peel_" object is selected within an onion collection')
            return {"CANCELLED"}
        
        source = collec.name.replace('.onion_', '')
        source_ob = context.scene.objects.get(source)
        if not source_ob:
            self.report(f'Could not find object named "{source}"')
            return {"CANCELLED"}
        ob.hide_select = True
        context.view_layer.objects.active = source_ob
        return {"FINISHED"}



class GPOP_OT_onion_skin_generate(bpy.types.Operator):
    bl_idname = "gp.onion_peel_gen"
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
        pos = onion.get_keys(ob)
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
        onion.generate_onion_peels(context)
        
        # get  frame equal of just after current (if None, were past the end)
        # next((f for f in pos if f >= current), None)
        return {"FINISHED"}

### --- REGISTER ---

classes=(
GPOP_OT_onion_skin_generate,
GPOP_OT_onion_skin_refresh,
GPOP_OT_onion_skin_delete,
GPOP_OT_onion_back_to_object,
GPOP_OT_onion_peel_pyramid_fade,
)

# TODO Add handler on frame post to refresh the timeline offset

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)