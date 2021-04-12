import bpy
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
        # layout.use_property_split = True
        if ob.name.startswith('.peel_'):
            layout.label(text='- Peel object edit -')
            layout.label(text='Use transforms to place')
            layout.label(text='/!\ Use only object mode !')
            layout.operator('gp.onion_back_to_object', text='Back to GP', icon='LOOP_BACK')
            return

        row = layout.row(align=False)
        # row.operator('gp.onion_peel_gen', text='Generate', icon='ONIONSKIN_ON')
        # if settings.

        icon = 'OUTLINER_OB_LIGHT' if settings.activated else 'LIGHT_DATA'
        state = 'Enabled' if settings.activated else 'Disabled'
        row.prop(settings, 'activated', text=state, emboss=True, icon =icon)
        row = layout.row(align=False)
        row.operator('gp.onion_peel_refresh', text='Refresh', icon='ONIONSKIN_ON') # FILE_REFRESH
        row.operator('gp.onion_peel_delete', text='Delete', icon='LOCKVIEW_OFF')
        # layout.prop(settings, 'offset_mode') # WIP
        row = layout.row(align=True)
        row.prop(settings, 'before_num', text='')
        row.prop(ob.data, 'before_color', text='')
        row.separator()
        row.prop(ob.data, 'after_color', text='')
        row.prop(settings, 'after_num', text='')        
        
        col = layout.column()
        ### ADDON PROPERTIE BASED PANEL
        # for i in sorted([0] + [i*j for j in [1,-1] for i in range(1,num_to_display+1)]):
        for i in [-i for i in range(1, settings.before_num+1)][::-1] + [0] + [i for i in range(1, settings.after_num+1)]:
            if i == 0:
                # col.separator()
                row = col.row(align=True)
                row.label(text='0')
                # row.label(text='0', icon='REMOVE') # without transforms
                # row.label(text='', icon='REMOVE')
                # row.label(text='', icon='COLLAPSEMENU')
                row.operator('gp.onion_peel_pyramid_fade', text='', icon='RIGHTARROW') # LINCURVE
                row.prop(settings, 'o_general', text='', slider=True)
                # row.prop(ob, 'hide_viewport', text='', icon='HIDE_OFF')
                row.prop(ob, 'show_in_front', text='', icon='XRAY')
                # col.separator()
                continue
            # if not peel:
            #     continue # create a GP place holder ?

            peel = context.scene.objects.get(f'.peel{ob.name} {i}')
            row = col.row(align=True)
            # row = col.split(align=True, factor=0.2)
            # CHECKBOX_DEHLT, CHECKBOX_HLT ? # show/hide with checkboxes (if more clear)

            # row.label(text=str(i), icon='DOT') # basic dot
            row.label(text=str(i))
            if peel and hasattr(peel, 'is_transformed'):
                row.operator('gp.reset_peel_transform', text='', icon='MESH_CIRCLE').peel_num = i # TRACKER, RADIOBUT_ON
            else:
                row.operator('gp.onion_peel_tranform', text='', icon='DOT').peel_num = i
            # row.separator()
            pid = f'p{abs(i)}' if i < 0 else f'n{i}'
            row.prop(settings, f'o_{pid}', text='', slider=True)
            row.prop(settings, f'v_{pid}', text='', icon='HIDE_OFF')

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