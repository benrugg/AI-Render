import bpy
import platform
from .. import utils
from pprint import pprint


class AIR_PT_comfyui(bpy.types.Panel):
    bl_label = "ComfyUI"
    bl_idname = "AIR_PT_comfyui"
    bl_parent_id = "AIR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    @classmethod
    def poll(cls, context):
        return utils.is_installation_valid() and context.scene.air_props.is_enabled and utils.sd_backend(context) == "comfyui"

    def draw(self, context):
        scene = context.scene
        props = scene.comfyui_props

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        row = layout.row(align=True)
        row.scale_y = 1.5
        row.prop(props, 'comfy_current_workflow', text='Current Workflow', emboss=False)

        # ComfyUI Workflows selector
        split = layout.split(factor=0.8)
        col1, col2 = (split.column(), split.column())

        # Reload Workflow
        col1.prop(props, 'comfyui_workflow', text="")
        col2.operator('ai_render.reload_workflow', text='Reload', icon='FILE_REFRESH')
        split.scale_y = 1.5

        # Convert Path in workflow
        if platform.system() == "Darwin":
            text = 'Convert "\\\\" to "/" in Workflow'
        elif platform.system() == "Windows":
            text = 'Convert "/" to "\\\\" in Workflow'
        layout.operator('ai_render.convert_path_in_workflow', text=text)

        layout.separator(factor=2)

        # Cycle all the Properties inside the comfyui_props
        for prop in props.bl_rna.properties.items():

            # Check if the property is a CollectionProperty and it has items
            if prop[1].type == 'COLLECTION' and getattr(props, prop[0]):
                # Create a box for each CollectionProperty with all the items inside
                main_box = layout.box()
                main_row = main_box.row()
                main_row.label(text=prop[0].upper().replace('_', ' ').replace('COMFYUI', ''), icon='COLLECTION_NEW')
                main_row.prop(props, prop[0], text="")
                main_row.scale_y = 1

                # Create the expand/collapse button
                for item in getattr(props, prop[0]):
                    is_expanded = item.expanded
                    if is_expanded:
                        icon = 'TRIA_DOWN'
                    else:
                        icon = 'TRIA_LEFT'
                main_row.prop(item, 'expanded', text='', icon=icon, emboss=False)

                # TODO: Check if the collection contains animated subproperties, if so, set expand to True

                for item in getattr(props, prop[0]) if is_expanded else []:
                    box = main_box.box()
                    box.scale_y = 1
                    row = box.row()
                    # Display the node number
                    # row.label(text=item.name, icon='NODE')
                    for sub_prop in item.bl_rna.properties.items():

                        if sub_prop[1].type == 'ENUM':
                            # Display the available enums.
                            # Those can update the corresponding strings which is commented below
                            row = box.row()
                            row.scale_y = 1.25
                            split = row.split(factor=0.15)
                            col2, col1 = (split.column(), split.column())

                            col1.prop(item, sub_prop[0], text="")
                            if sub_prop[0] == 'ckpt_enum':
                                col2.operator('ai_render.update_ckpt_enum', text='', icon='FILE_REFRESH')
                            elif sub_prop[0] == 'lora_enum':
                                col2.operator('ai_render.update_lora_enum', text='', icon='FILE_REFRESH')
                            elif sub_prop[0] == 'control_net_enum':
                                col2.operator('ai_render.update_control_net_enum', text='', icon='FILE_REFRESH')
                            elif sub_prop[0] == 'upscale_model_enum':
                                col2.operator('ai_render.update_upscale_model_enum', text='', icon='FILE_REFRESH')

                        # elif sub_prop[1].type == 'STRING' and sub_prop[0] != 'name':
                        #     # Display the model name not editable as a string (emboss=False)
                        #     col = box.column()
                        #     col.prop(item, sub_prop[0], text='', emboss=False)

                        elif sub_prop[1].type == 'FLOAT' or sub_prop[1].type == 'INT':
                            col = box.column()
                            col = col.split()
                            col.label(text=sub_prop[0])
                            col.use_property_split = True
                            col.use_property_decorate = True
                            # Display the available props
                            col.prop(item, sub_prop[0], text='', expand=True)

                # Separator
                layout.separator(factor=1)


classes = [
    AIR_PT_comfyui,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
