import bpy
class GPOP_PT_onion_skinning_ui(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Gpencil"
    bl_label = "Onion Peel"

    def draw(self, context):
        ob = context.object
        if not ob or ob.type != 'GREASEPENCIL':
            return
        settings = context.scene.gp_ons_setting
        layout = self.layout
        layout = layout.column_flow(columns=0, align=False)

        #-## PEEL TRANSFORM PANEL
        if ob.name.startswith('.peel_'):
            layout.label(text='-- Peel object edit --')
            layout.label(text='Transforms onion peel')
            layout.label(text='- Controls -')
            layout.label(text='ENTER / B : Valid')
            layout.label(text='ESC : Cancel')
            layout.label(text='G/R/S : Transform')
            layout.label(text='X : horizontal flip (Shift X : vertical)')
            layout.label(text='- - -')
            return

        row = layout.row(align=False)

        icon = 'OUTLINER_OB_LIGHT' if settings.activated else 'LIGHT_DATA'
        state = 'Enabled' if settings.activated else 'Disabled'
        row.prop(settings, 'activated', text=state, emboss=True, icon=icon)
        row.prop(settings, 'world_space', text='World Space')
        # row.prop(settings, 'only_active', text='Only Active') # wip multi object use
        
        row = layout.row(align=False)
        row.operator('gp.onion_peel_refresh', text='Refresh', icon='ONIONSKIN_ON') # FILE_REFRESH
        row.operator('gp.onion_peel_delete', text='Delete', icon='LOCKVIEW_OFF')
        
        row = layout.row(align=True)
        # layout.prop(settings, 'offset_mode') # wip multi draw type mode
        row.prop(settings, 'keyframe_type', text='Filter')
        row.separator()
        

        row.scale_x = 0.69
        row.operator('gp.onion_swap_xray', text='X-ray', icon='XRAY').use_xray = True # xray ops swap
        row.operator('gp.onion_swap_xray', text='Off').use_xray = False # xray ops swap
        
        row = layout.row(align=True)
        row.prop(settings, 'before_num', text='')
        row.prop(settings, 'before_color', text='')
        
        row.separator()
        row.prop(settings, 'after_color', text='')
        row.prop(settings, 'after_num', text='')        
        
        col = layout.column()

        ### PROPERTIE BASED PANEL
        for i in [-i for i in range(1, settings.before_num+1)][::-1] + [0] + [i for i in range(1, settings.after_num+1)]:
            if i == 0:
                ###  MIDDLE LINE
                row = col.row(align=True)
                row.label(text='0')
                row.label(text='', icon='BLANK1')
                row.operator('gp.onion_peel_pyramid_fade', text='', icon='RIGHTARROW') # LINCURVE
                row.prop(settings, 'o_general', text='', slider=True)
                # row.prop(ob, 'hide_viewport', text='', icon='HIDE_OFF')
                row.prop(ob, 'show_in_front', text='', icon='XRAY')
                continue
            
            ### PEEL LINE
            if i < 0:
                if abs(i) > len(settings.neg_frames) - 1:
                    continue
                fsetting = settings.neg_frames[abs(i)]
            else:
                if i > len(settings.pos_frames) - 1:
                    continue
                fsetting = settings.pos_frames[i]

            peel = context.scene.objects.get(f'.peel_{ob.name} {i}')
            row = col.row(align=True)

            # row.label(text=str(i), icon='DOT') # basic dot
            row.active = fsetting.visibility
            row.label(text=str(i))
            if peel and peel.get('outapeg'):
                row.operator('gp.reset_peel_transform', text='', icon='X').peel_num = i # RADIOBUT_ON, TRANSFORM_ORIGINS, RADIOBUT_OFF, TRACKER
                row.operator('gp.onion_peel_tranform', text='', icon='MESH_CIRCLE').peel_num = i
            else:
                #> Go to object mode
                row.label(text='', icon='BLANK1')
                row.operator('gp.onion_peel_tranform', text='', icon='DOT').peel_num = i
                #> MODAL
                # row.operator('gp.peel_custom_transform', text='', icon='DOT').peel_num = i

            # pid = f'p{abs(i)}' if i < 0 else f'n{i}'
            row.prop(fsetting, 'opacity', text='', slider=True)
            row.prop(fsetting, 'visibility', text='', icon='HIDE_OFF')
        
        if context.space_data.shading.type == 'SOLID':
            layout.separator()
            layout.label(text='Peels not colored in Solid view', icon='INFO')
            # layout.label(text='Switch to Material or Rendered mode')

### --- REGISTER ---

classes=(
GPOP_PT_onion_skinning_ui,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()