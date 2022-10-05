import bpy
from .. import (
    config,
    operators,
    utils,
)


def show_error_if_it_exists(layout, context):
    props = context.scene.sdr_props
    if (props.error_message):
        
        box = layout.box()
        row = box.row()

        col = row.column()
        col.label(text="", icon="ERROR")
        col = row.column()
        col.label(text="Error:")
        col = row.column()
        col.label(text="", icon="COLORSET_01_VEC")

        utils.label_multiline(box, text=props.error_message, width=220)


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

    @classmethod
    def poll_for_api_key(cls, context):
        return utils.get_api_key(context) == '' or context.scene.sdr_props.error_key == 'api_key'

    @classmethod
    def poll_for_dimensions(cls, context):
        return not utils.are_dimensions_valid(context.scene)

    # @classmethod
    # def poll(cls, context):
    #     return SDR_PT_setup.poll_for_api_key(context) or SDR_PT_setup.poll_for_dimensions(context)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdr_props

        width_guess = 230

        # if the api key is invalid, show the initial setup instructions
        if SDR_PT_setup.poll_for_api_key(context):

            utils.label_multiline(layout, text="Setup is quick and easy. No downloads or installation. Just register for a Dream Studio API Key.", icon="INFO", width=width_guess)
            
            row = layout.row()
            col = row.column()
            # col.label(text="Setup is easy!")
            # col = row.column()
            col.operator(operators.SDR_OT_setup_instructions_popup.bl_idname, text="Instructions", icon="HELP")

            row = layout.row()
            row.operator("wm.url_open", text="Sign Up For DreamStudio (free)", icon="URL").url = config.DREAM_STUDIO_URL
            
            row = layout.row()
            row.prop(context.preferences.addons[__package__].preferences, "dream_studio_api_key")
        
        # else, show the image dimension help
        elif SDR_PT_setup.poll_for_dimensions(context):
            utils.label_multiline(layout, text=f"Adjust Image Size: \nStable Diffusion only works on a few specific image dimensions.", icon="INFO", width=width_guess)
            
            row = layout.row(align=True)
            col = row.column()
            col.operator(operators.SDR_OT_set_valid_render_dimensions.bl_idname)
            col = row.column()
            col.operator(operators.SDR_OT_show_other_dimension_options.bl_idname, text="", icon="QUESTION")
        
        else:
            utils.label_multiline(layout, text="You're ready to start rendering!", width=width_guess)
            row = layout.row()
            row.operator("wm.url_open", text="Help Getting Started", icon="URL").url = config.GETTING_STARTED_URL


class SDR_PT_core(bpy.types.Panel):
    bl_label = "Prompt"
    bl_idname = "SDR_PT_core"
    bl_parent_id = "SDR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdr_props

        # Show the error if we have one
        show_error_if_it_exists(layout, context)

        # Prompt
        row = layout.row()
        row.label(text="Prompt:")

        row = layout.row()
        row.scale_y = 1.8
        row.prop(props, 'prompt_text', text="")

        # Preset Styles
        row = layout.row()
        row.label(text="Preset Style (optional):")

        row = layout.row()
        row.template_icon_view(props, "preset_style", show_labels=True, scale_popup=8)



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

        # Seed
        row = layout.row()
        sub = row.column()
        sub.prop(props, 'use_random_seed')

        sub = row.column()
        sub.prop(props, 'seed', text="", slider=False)
        sub.enabled = not props.use_random_seed

        # Image Similarity
        row = layout.row()
        sub = row.column()
        sub.label(text="Image Similarity")
        sub = row.column()
        sub.prop(props, 'image_similarity', text="", slider=False)

        # Steps
        row = layout.row()
        sub = row.column()
        sub.label(text="Steps")
        sub = row.column()
        sub.prop(props, 'steps', text="", slider=False)

        # Prompt Strength
        row = layout.row()
        sub = row.column()
        sub.label(text="Prompt Strength")
        sub = row.column()
        sub.prop(props, 'cfg_scale', text="", slider=False)

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
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdr_props

        # Auto Run
        row = layout.row()
        row.prop(props, 'auto_run')

        # Generate Image
        row = layout.row()
        row.label(text="Run Manually:")

        row = layout.row()
        row.operator(operators.SDR_OT_generate_new_image_from_render.bl_idname)
        row = layout.row()
        row.operator(operators.SDR_OT_generate_new_image_from_current.bl_idname)


classes = [
    SDR_PT_main,
    SDR_PT_setup,
    SDR_PT_core,
    SDR_PT_advanced_options,
    SDR_PT_operation,
]


def register_ui_panels():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_ui_panels():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    