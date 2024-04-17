import bpy
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
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        scene = context.scene
        props = scene.comfyui_props

        layout.separator(factor=2)

        # ComfyUI Workflows selector
        row = layout.row(align=True, heading="Select Workflow")
        # row.label(text=")
        row.prop(props, 'comfyui_workflow', text="")
        row.scale_y = 1.3

        layout.separator(factor=1)

        # Cycle all the Properties inside the comfyui_props
        for prop in props.bl_rna.properties.items():
            # Check if the property is a CollectionProperty and it has items
            if prop[1].type == 'COLLECTION' and getattr(props, prop[0]):
                # Create a box for each CollectionProperty with all the items inside
                main_box = layout.box()
                main_row = main_box.row(align=True, heading="")
                main_row.label(text=prop[0].upper().replace('_', ' ').replace('COMFYUI', ''), icon='COLLECTION_NEW')
                main_row.prop(props, prop[0], text="")
                main_row.scale_y = 1

                # Create the expand/collapse button
                for item in getattr(props, prop[0]):
                    is_expanded = item.expanded
                    if is_expanded:
                        icon = 'TRIA_DOWN'
                    else:
                        icon = 'TRIA_RIGHT'
                main_row.prop(item, 'expanded', text='', icon=icon, emboss=False)

                # TODO: Check if the collection contains animated subproperties, if so, set expand to True

                for item in getattr(props, prop[0]) if is_expanded else []:
                    box = main_box.box()
                    box.scale_y = 1
                    row = box.row()
                    # Display the node number
                    # row.label(text=item.name, icon='NODE')
                    for sub_prop in item.bl_rna.properties.items():
                        if sub_prop[1].type == 'STRING' and sub_prop[0] != 'name':
                            # Display the model name not editable as a string (emboss=False)
                            row.prop(item, sub_prop[0], text='', emboss=False)

                        elif sub_prop[1].type == 'ENUM':
                            # Display the available enums. This can update the related strings
                            row = box.row()
                            row.prop(item, sub_prop[0], text="")

                        elif sub_prop[1].type == 'FLOAT':
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
