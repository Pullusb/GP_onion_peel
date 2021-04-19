import bpy
from . import onion
from mathutils import Matrix, Vector

def location_to_region(worldcoords):
    from bpy_extras import view3d_utils
    return view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.space_data.region_3d, worldcoords)

def region_to_location(viewcoords, depthcoords):
    from bpy_extras import view3d_utils
    return view3d_utils.region_2d_to_location_3d(bpy.context.region, bpy.context.space_data.region_3d, viewcoords, depthcoords)


class GPOP_OT_peel_custom_transform(bpy.types.Operator):
    bl_idname = "gp.peel_custom_transform"
    bl_label = "Peel Custom Transform"
    bl_description = "Replace the peel"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'GPENCIL'
    
    peel_num : bpy.props.IntProperty()

    def invoke(self, context, event):
        if not self.peel_num:
            self.report({'ERROR'}, f'Peel number seems not valid : {self.peel_num}\nTry refreshing')
            return {"CANCELLED"}

        ob = context.object
        peel_name =  f'{onion.to_peel_name(ob.name)} {self.peel_num}'
        
        self.peel = context.scene.objects.get(peel_name)
        if not self.peel:
            self.report({'ERROR'}, f'Could not find this Onion peel!\nTry refreshing')
            return {"CANCELLED"}

        # Get median of all points
        coords = []
        for l in self.peel.data.layers:
            for f in l.frames:
                for s in f.strokes:
                    coords += [p.co for p in s.points]

        if not coords:
            self.report({'ERROR'}, f'No coordinate found on this peel {peel_name}')
            return {"CANCELLED"}
        self.pivot = sum(coords, Vector()) / len(coords)
        # print("Local:", self.pivot)
        self.pivot = self.peel.matrix_world @ self.pivot
        # print("Global:", self.pivot)
        self.pivot2d = location_to_region(self.pivot)
        print('self.pivot2d: ', self.pivot2d)
        self.matrix_ts = Matrix()
        
        # context.window.cursor_warp(self.pivot2d[0], self.pivot2d[1]) # warp is in region coordinate
        ## inits
        self.mode = 'GRAB'
        self.depth_vector = self.peel.matrix_world.translation
        self.init_mouse_x = event.mouse_x
        self.init_mouse_y = event.mouse_y
        self.mouse = Vector((event.mouse_x, event.mouse_y))
        self.init_matrix = self.peel.matrix_world.copy()

        self.pos_transition = location_to_region(self.depth_vector)

        context.window_manager.modal_handler_add(self)
        context.area.header_text_set(f'Move onion peel: use G:move / R:rotate / S:scale / M:mirror | Mode: {self.mode}')
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        context.area.header_text_set(f'Move onion peel: use G:move / R:rotate / S:scale / M:mirror | Mode: {self.mode}')
        if event.type in {'MOUSEMOVE'}:
            self.mouse = Vector((event.mouse_x, event.mouse_y))
            if self.mode == 'GRAB':
                # location from self.pivot 
                # apply offset 
                offset = self.pivot2d - self.mouse
                self.peel.matrix_world.translation = region_to_location(offset, self.depth_vector)
        
        if event.type in {'G'} and event.value == 'PRESS':
            self.mode = 'GRAB'

        if event.type in {'M'} and event.value == 'PRESS':
            # Mirror object from pivot
            pass
            # self.mode = 'distance' if self.mode == 'proportional' else 'proportional'

        if event.type in {'RET'} and event.value == 'PRESS':
            context.area.header_text_set(None)
            return {"FINISHED"}
        
        if event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            self.peel.matrix_world = self.init_matrix
            context.area.header_text_set(None)
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}


def register():
    bpy.utils.register_class(GPOP_OT_peel_custom_transform)

def unregister():
    bpy.utils.unregister_class(GPOP_OT_peel_custom_transform)