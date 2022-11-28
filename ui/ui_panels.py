import bpy
import math
from .. import (
    addon_updater_ops,
    config,
    operators,
    utils,
)


def show_error_if_it_exists(layout, context, width_guess):
    props = context.scene.air_props
    if (props.error_message):

        box = layout.box()
        row = box.row()

        col = row.column()
        col.alert = True
        col.label(text="Error:", icon="ERROR")

        col = row.column()
        col.label(text="", icon="COLORSET_01_VEC")

        utils.label_multiline(box, text=props.error_message, width=width_guess)


class AIR_PT_main(bpy.types.Panel):
    bl_label = "AI Render"
    bl_idname = "AIR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.air_props

        width_guess = 220

        if not utils.is_installation_valid():
            utils.show_invalid_installation_message(layout, width_guess)

        elif not props.is_enabled:

            # Show enable button and message
            row = layout.row()
            row.operator(operators.AIR_OT_enable.bl_idname)

            utils.label_multiline(layout, text="Enable AI Render in this scene to start using Stable Diffusion", alignment="CENTER")

            # Show updater if update is available
            addon_updater_ops.update_notice_box_ui(self, context)


class AIR_PT_setup(bpy.types.Panel):
    bl_label = "Setup"
    bl_idname = "AIR_PT_setup"
    bl_parent_id = "AIR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    @classmethod
    def is_api_key_valid(cls, context):
        return utils.get_dream_studio_api_key(context) != '' and context.scene.air_props.error_key != 'api_key'

    @classmethod
    def are_dimensions_valid(cls, context):
        return utils.are_dimensions_valid(context.scene)

    @classmethod
    def are_dimensions_small_enough(cls, context):
        return not utils.are_dimensions_too_large(context.scene)

    @classmethod
    def poll(cls, context):
        return utils.is_installation_valid() and context.scene.air_props.is_enabled

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.air_props

        width_guess = 220

        # if the api key is invalid, show the initial setup instructions
        if not AIR_PT_setup.is_api_key_valid(context) and utils.sd_backend(context) == "dreamstudio":

            utils.label_multiline(layout, text="Setup is quick and easy. No downloads or installation. Just register for a Dream Studio API Key.", icon="INFO", width=width_guess)

            row = layout.row()
            col = row.column()
            col.operator(operators.AIR_OT_setup_instructions_popup.bl_idname, text="Instructions", icon="HELP")

            row = layout.row()
            row.operator("wm.url_open", text="Watch Full Tutorial", icon="URL").url = config.VIDEO_TUTORIAL_URL

            row = layout.row()
            row.operator("wm.url_open", text="Sign Up For DreamStudio (free)", icon="URL").url = config.DREAM_STUDIO_URL

            row = layout.row()
            row.prop(utils.get_addon_preferences(context), "dream_studio_api_key")

        # show the image dimension help if the dimensions are invalid or too large
        elif not AIR_PT_setup.are_dimensions_valid(context) or not AIR_PT_setup.are_dimensions_small_enough(context):
            if not AIR_PT_setup.are_dimensions_valid(context):
                utils.label_multiline(layout, text=f"Adjust Image Size: \nStable Diffusion only works on a few specific image dimensions.", icon="INFO", width=width_guess)
            else:
                utils.label_multiline(layout, text=f"Adjust Image Size: \nImage dimensions are too large. Please decrease width and/or height.", icon="INFO", width=width_guess)

            row = layout.row(align=True)
            col = row.column()
            col.operator(operators.AIR_OT_set_valid_render_dimensions.bl_idname)
            col = row.column()
            col.operator(operators.AIR_OT_show_other_dimension_options.bl_idname, text="", icon="QUESTION")

        # else, show the ready / getting started message
        else:
            utils.label_multiline(layout, text="You're ready to start rendering!", width=width_guess, alignment="CENTER")
            row = layout.row()
            row.operator("wm.url_open", text="Help Getting Started", icon="URL").url = config.VIDEO_TUTORIAL_URL


class AIR_PT_prompt(bpy.types.Panel):
    bl_label = "Prompt"
    bl_idname = "AIR_PT_prompt"
    bl_parent_id = "AIR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    @classmethod
    def poll(cls, context):
        return utils.is_installation_valid() and context.scene.air_props.is_enabled

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.air_props

        width_guess = 220

        # Show updater if update is available
        addon_updater_ops.update_notice_box_ui(self, context)

        # Show the error if we have one
        show_error_if_it_exists(layout, context, width_guess)

        # Prompt
        if props.use_animated_prompts:
            row = layout.row()
            row.label(text="You are using animated prompts")

            row = layout.row()
            row.operator(operators.AIR_OT_edit_animated_prompts.bl_idname)

            layout.separator()

        else:
            row = layout.row()
            row.label(text="Prompt:")

            row = layout.row()
            row.scale_y = 1.8
            row.prop(props, "prompt_text", text="")

        # Preset Styles
        box = layout.box()
        row = box.row()
        label = "Apply a Preset Style (to All Prompts)" if props.use_animated_prompts else "Apply a Preset Style"
        row.prop(props, "use_preset", text=label)

        if props.use_preset:
            row = box.row()
            row.template_icon_view(props, "preset_style", show_labels=True, scale_popup=7.7)

            row = box.row()
            col = row.column()
            col.label(text=f"\"{props.preset_style}\"")

            col = row.column()
            col.operator(operators.AIR_OT_copy_preset_text.bl_idname, text="", icon="COPYDOWN")


class AIR_PT_advanced_options(bpy.types.Panel):
    bl_label = "Advanced Options"
    bl_idname = "AIR_PT_advanced_options"
    bl_parent_id = "AIR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return utils.is_installation_valid() and context.scene.air_props.is_enabled

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.air_props

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


class AIR_PT_operation(bpy.types.Panel):
    bl_label = "Operation"
    bl_idname = "AIR_PT_operation"
    bl_parent_id = "AIR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return utils.is_installation_valid() and context.scene.air_props.is_enabled

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.air_props

        width_guess = 220

        # Auto Run
        row = layout.row()
        row.prop(props, 'auto_run')

        # Generate Image
        manual_buttons_enabled = 'Render Result' in bpy.data.images and bpy.data.images['Render Result'].has_data

        layout.separator()

        row = layout.row()
        row.label(text="Run Manually:")

        row = layout.row()
        row.enabled = manual_buttons_enabled
        row.operator(operators.AIR_OT_generate_new_image_from_render.bl_idname)

        row = layout.row()
        row.enabled = manual_buttons_enabled
        row.operator(operators.AIR_OT_generate_new_image_from_current.bl_idname)

        layout.separator()

        row = layout.row()
        row.label(text="Automatically Save Images:")

        row = layout.row()
        row.prop(props, "do_autosave_before_images")

        row = layout.row()
        row.prop(props, "do_autosave_after_images")

        row = layout.row()
        row.prop(props, "autosave_image_path", text="Path")

        if (props.do_autosave_before_images or props.do_autosave_after_images) and not props.autosave_image_path:
            utils.label_multiline(layout, text="Please specify a path", icon="ERROR", width=width_guess)


class AIR_PT_animation(bpy.types.Panel):
    bl_label = "Animation"
    bl_idname = "AIR_PT_animation"
    bl_parent_id = "AIR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return utils.is_installation_valid() and context.scene.air_props.is_enabled

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.air_props

        width_guess = 220

        # Render Animation
        row = layout.row()
        is_animation_enabled_button_enabled = props.animation_output_path != ""
        if is_animation_enabled_button_enabled:
            num_frames = math.floor(((scene.frame_end - scene.frame_start) / scene.frame_step) + 1)
            frame_or_frames = "Frame" if num_frames == 1 else "Frames"
            render_animation_text = f"Render Animation ({num_frames} {frame_or_frames})"
        else:
            render_animation_text = "Render Animation"

        row.operator(operators.AIR_OT_render_animation.bl_idname, icon="RENDER_ANIMATION", text=render_animation_text)
        row.enabled = is_animation_enabled_button_enabled

        # Path
        row = layout.row()
        row.prop(props, "animation_output_path", text="Path")

        # Animated Prompts
        layout.separator()

        row = layout.row()
        row.prop(props, "use_animated_prompts", text="Use Animated Prompts")

        if props.use_animated_prompts:
            row = layout.row()
            row.operator(operators.AIR_OT_edit_animated_prompts.bl_idname)

        # Tips
        if round(props.image_similarity, 2) < 0.7 and not props.close_animation_tips:
            layout.separator()

            box = layout.box()
            row = box.row()
            row.label(text="Animation Tip:", icon="INFO")
            split = row.split(align=True)
            split.prop(props, "close_animation_tips", text="", icon="X", emboss=False)

            utils.label_multiline(box, text="For more stable animations, consider increasing \"Image Similarity\" to at least 0.7", width=width_guess)

            row = box.row()
            row.operator("wm.url_open", text="Get Animation Tips", icon="URL").url = config.ANIMATION_TIPS_URL


classes = [
    AIR_PT_main,
    AIR_PT_setup,
    AIR_PT_prompt,
    AIR_PT_advanced_options,
    AIR_PT_operation,
    AIR_PT_animation,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
