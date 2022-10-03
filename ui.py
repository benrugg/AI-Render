import bpy
from . import (
    config,
    operators,
)


class SDR_PT_main(bpy.types.Panel):
    bl_label = "Stable Diffusion Render"
    bl_idname = "SDR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_order = 0


    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdr_props


class SDR_PT_setup(bpy.types.Panel):
    bl_label = "Setup"
    bl_idname = "SDR_PT_setup"
    bl_parent_id = "SDR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdr_props

        row = layout.row()
        col = row.column()
        col.label(text="Setup is easy!")
        col = row.column()
        col.operator(operators.SDR_OT_setup_instructions_popup.bl_idname, text="Setup Instructions", icon="HELP")

        row = layout.row()
        row.operator("wm.url_open", text="Sign Up For DreamStudio (free)", icon="URL").url = config.DREAM_STUDIO_URL
        
        row = layout.row()
        row.prop(props, 'api_key')


class SDR_PT_core(bpy.types.Panel):
    bl_label = "Core"
    bl_idname = "SDR_PT_core"
    bl_parent_id = "SDR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdr_props

        # Prompt
        row = layout.row()
        row.scale_y = 1.8
        row.prop(props, 'prompt_text')

        # Seed
        row = layout.row()
        sub = row.column()
        sub.prop(props, 'use_random_seed')

        sub = row.column()
        sub.prop(props, 'seed')
        sub.enabled = not props.use_random_seed

        # Image Similarity
        row = layout.row()
        sub = row.column()
        sub.label(text="Image Similarity")
        sub = row.column()
        sub.prop(props, 'image_similarity', text="", slider=False)


class SDR_PT_advanced_options(bpy.types.Panel):
    bl_label = "Advanced Options"
    bl_idname = "SDR_PT_advanced_options"
    bl_parent_id = "SDR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdr_props

        # Prompt Strength
        row = layout.row()
        sub = row.column()
        sub.label(text="Prompt Strength")
        sub = row.column()
        sub.prop(props, 'cfg_scale', text="", slider=False)

        # Steps
        row = layout.row()
        sub = row.column()
        sub.label(text="Steps")
        sub = row.column()
        sub.prop(props, 'steps', text="", slider=False)

        # Sampler
        row = layout.row()
        sub = row.column()
        sub.label(text="Sampler")
        sub = row.column()
        sub.prop(props, 'sampler', text="")


class SDR_PT_operation(bpy.types.Panel):
    bl_label = "Operation"
    bl_idname = "SDR_PT_operation"
    bl_parent_id = "SDR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdr_props

        # Generate Image
        row = layout.row()
        row.operator(operators.SDR_OT_send_to_api.bl_idname)

        # Checkboxes for automatically running, and automatically running
        # TODO...


class SDR_PT_output(bpy.types.Panel):
    bl_label = "Output"
    bl_idname = "SDR_PT_output"
    bl_parent_id = "SDR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdr_props

        if props.error_message == '':
            col = self.layout.column()

            if 'previewTexture' in bpy.data.textures:
                col.template_preview(bpy.data.textures['previewTexture'])

        else:
            row = self.layout.row()
            col = row.column()
            col.label(text="", icon="COLORSET_01_VEC")
            col = row.column()
            col.label(text="", icon="ERROR")
            col = row.column()
            col.label(text="*** Error: ***")
            col = row.column()
            col.label(text="", icon="ERROR")
            col = row.column()
            col.label(text="", icon="COLORSET_01_VEC")

            row = self.layout.row()
            row.label(text=props.error_message)


classes = [
    SDR_PT_main,
    SDR_PT_setup,
    SDR_PT_core,
    SDR_PT_advanced_options,
    SDR_PT_operation,
    SDR_PT_output,
]


def register_ui():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_ui():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    