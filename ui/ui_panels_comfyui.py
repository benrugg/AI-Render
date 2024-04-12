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
        scene = context.scene
        props = scene.comfyui_props

        # ComfyUI Path
        box = layout.box()
        box.label(text="Addon Preferences")
        box.prop(utils.get_addon_preferences(context), 'comfyui_path', text="Comfy")

        # ComfyUI Workflows Path
        box.prop(utils.get_addon_preferences(context), 'comfyui_workflows_path', text="Workflows")

        # Open ComfyUI workflow, input and output folder operator
        box = layout.box()
        row = box.row()
        row.operator("ai_render.open_comfyui_workflows_folder", text="Workflow Folder")  # Had to do this to fix the circular import error
        row.operator("ai_render.open_comfyui_input_folder", text="Input Folder")  # Had to do this to fix the circular import error
        row.operator("ai_render.open_comfyui_output_folder", text="Output Folder")  # Had to do this to fix the circular import error

        # ComfyUI Workflows selector
        row = layout.row()
        row.label(text="Select Workflow")
        row.prop(props, 'comfyui_workflow', text="")

        row.separator()

        # Cycle all the PropertyGroups inside the comfyui_props
        for prop in props.keys():
            # if the property is a type PropertyGroup
            if isinstance(getattr(props, prop), bpy.types.PropertyGroup):
                # Access each property inside the PropertyGroup and display it in a box
                box = layout.box()
                box.label(text=prop)
                for subprop in getattr(props, prop).__annotations__.items():
                    # Create a row for each property inside the PropertyGroup
                    box.prop(getattr(props, prop), subprop[0], text=subprop[0])


classes = [
    AIR_PT_comfyui,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
