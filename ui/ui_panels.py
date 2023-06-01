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
    def has_dimensions_issue(cls, context):
        return \
            not AIR_PT_setup.are_dimensions_valid(context) or \
            not AIR_PT_setup.are_dimensions_small_enough(context) or \
            not AIR_PT_setup.are_dimensions_large_enough(context)

    @classmethod
    def are_dimensions_valid(cls, context):
        return utils.are_dimensions_valid(context.scene) and context.scene.air_props.error_key != 'invalid_dimensions'

    @classmethod
    def are_dimensions_small_enough(cls, context):
        return not utils.are_dimensions_too_large(context.scene) and context.scene.air_props.error_key != 'dimensions_too_large'

    @classmethod
    def are_dimensions_large_enough(cls, context):
        return not utils.are_dimensions_too_small(context.scene) and context.scene.air_props.error_key != 'dimensions_too_small'

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

            utils.label_multiline(layout, text="Setup is quick and easy. No downloads or installation. Just register for a DreamStudio API Key.", icon="INFO", width=width_guess)

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
        elif AIR_PT_setup.has_dimensions_issue(context):
            if not AIR_PT_setup.are_dimensions_valid(context):
                utils.label_multiline(layout, text="Adjust Image Size: \nStable Diffusion only works on certain image dimensions.", icon="INFO", width=width_guess)
            elif not AIR_PT_setup.are_dimensions_small_enough(context):
                utils.label_multiline(layout, text=f"Adjust Image Size: \nImage dimensions are too large. Please decrease width and/or height. Total pixel area must be at most {round(utils.get_active_backend().max_image_size() / (1024*1024), 1)} megapixels.", icon="INFO", width=width_guess)
            else:
                utils.label_multiline(layout, text=f"Adjust Image Size: \nImage dimensions are too small. Please increase width and/or height. Total pixel area must be at least {round(utils.get_active_backend().min_image_size() / (1024*1024), 1)} megapixels.", icon="INFO", width=width_guess)

            layout.separator()

            row = layout.row()
            row.label(text="Set Image Size:")

            row = layout.row(align=True)
            col = row.column()
            col.operator(operators.AIR_OT_set_image_size_to_512x512.bl_idname)
            col = row.column()
            col.operator(operators.AIR_OT_set_image_size_to_768x768.bl_idname)
            col = row.column()
            col.operator(operators.AIR_OT_show_other_dimension_options.bl_idname, text="Other")

            if utils.get_active_backend().supports_upscaling() and props.do_upscale_automatically:
                layout.separator()
                box = layout.box()
                utils.label_multiline(box, text=f"Final image will be upscaled {round(props.upscale_factor)}x larger than these initial dimensions.", width=width_guess-20)

        # else, show the ready / getting started message and disable and change image size buttons
        else:
            utils.label_multiline(layout, text="You're ready to start rendering!", width=width_guess, alignment="CENTER")
            row = layout.row()
            row.operator("wm.url_open", text="Help Getting Started", icon="URL").url = config.VIDEO_TUTORIAL_URL

            row = layout.row(align=True)
            row.operator(operators.AIR_OT_show_other_dimension_options.bl_idname, text="Change Image Size")
            row.separator()
            row.operator(operators.AIR_OT_disable.bl_idname, text="Disable AI Render")


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

            if utils.get_active_backend().supports_negative_prompts():
                row = layout.row()
                row.label(text="Negative prompt:")

                row = layout.row()
                row.scale_y = 1.8
                row.prop(props, "negative_prompt_text", text="")

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

        # SD Model
        if utils.get_active_backend().supports_choosing_model():
            row = layout.row()
            sub = row.column()
            sub.label(text="Model")
            sub = row.column()
            sub.prop(props, 'sd_model', text="")

        # Sampler
        row = layout.row()
        sub = row.column()
        sub.label(text="Sampler")
        sub = row.column()
        sub.prop(props, 'sampler', text="")


class AIR_PT_controlnet(bpy.types.Panel):
    bl_label = "ControlNet"
    bl_idname = "AIR_PT_controlnet"
    bl_parent_id = "AIR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return utils.is_installation_valid() and context.scene.air_props.is_enabled and utils.sd_backend(context) == "automatic1111"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.air_props

        width_guess = 220

        # ControlNet Help
        if not props.controlnet_close_help:
            box = layout.box()
            row = box.row()
            row.label(text="ControlNet Help:", icon="INFO")
            split = row.split(align=True)
            split.prop(props, "controlnet_close_help", text="", icon="X", emboss=False)

            utils.label_multiline(box, text="ControlNet is an extension for Automatic1111 that provides a spectacular ability to match scene details - layout, objects, poses - while recreating the scene in Stable Diffusion. It can also create much more stable animations than standard Stable Diffusion.", width=width_guess)

            row = box.row()
            row.operator("wm.url_open", text="Learn More", icon="URL").url = config.HELP_WITH_CONTROLNET_URL

            layout.separator()

        # Enable
        row = layout.row()
        row.prop(props, 'controlnet_is_enabled', text="Enable")

        # ControlNet Load Models and Modules
        if not props.controlnet_available_models:
            row = layout.row()
            row.operator(operators.AIR_OT_automatic1111_load_controlnet_models_and_modules.bl_idname, text="Load Models from Automatic1111", icon="FILE_REFRESH")
        else:
            # Heads up box
            if props.controlnet_is_enabled:
                box = layout.box()
                row = box.row()
                row.label(text="ControlNet will be used for each render")

            # ControlNet Module (Preprocessor)
            row = layout.row()
            row.prop(props, 'controlnet_module', text="Preprocessor")

            split = row.split(align=True)
            split.operator(operators.AIR_OT_automatic1111_load_controlnet_modules.bl_idname, text="", icon="FILE_REFRESH")

            # ControlNet Model
            row = layout.row()
            row.prop(props, 'controlnet_model', text="Model")

            split = row.split(align=True)
            split.operator(operators.AIR_OT_automatic1111_load_controlnet_models.bl_idname, text="", icon="FILE_REFRESH")

            # ControlNet Weight
            row = layout.row()
            sub = row.column()
            sub.label(text="Weight")
            sub = row.column()
            sub.prop(props, 'controlnet_weight', text="", slider=False)


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
        layout.separator()

        row = layout.row()
        row.label(text="Run Manually:")

        row = layout.row()
        row.enabled = 'Render Result' in bpy.data.images and bpy.data.images['Render Result'].has_data
        row.operator(operators.AIR_OT_generate_new_image_from_render.bl_idname)

        row = layout.row()
        row.enabled = props.last_generated_image_filename != ""
        row.operator(operators.AIR_OT_generate_new_image_from_last_sd_image.bl_idname)

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


class AIR_PT_upscale(bpy.types.Panel):
    bl_label = "Upscale"
    bl_idname = "AIR_PT_upscale"
    bl_parent_id = "AIR_PT_main"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return utils.is_installation_valid() and context.scene.air_props.is_enabled

    @classmethod
    def does_backend_support_upscaling(cls, context):
        return utils.get_active_backend().supports_upscaling()

    @classmethod
    def is_upscaler_model_list_loaded(cls, context):
        return utils.get_active_backend().is_upscaler_model_list_loaded(context)

    @classmethod
    def does_backend_support_reloading_upscaler_model_list(cls, context):
        return utils.get_active_backend().supports_reloading_upscaler_models()

    @classmethod
    def are_upscaled_dimensions_small_enough(cls, context):
        return not utils.are_upscaled_dimensions_too_large(context.scene)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.air_props

        width_guess = 220

        # if backend does not support upscaling, show message
        if not AIR_PT_upscale.does_backend_support_upscaling(context):
            box = layout.box()
            utils.label_multiline(box, text=f"Upscaling is not supported by {utils.sd_backend_formatted_name()}. If you'd like to upscale your image, switch to DreamStudio or Automatic1111 in AI Render's preferences.", icon="ERROR", width=width_guess)
            return

        # if the upscaler model list hasn't been loaded, show message and button
        if not AIR_PT_upscale.is_upscaler_model_list_loaded(context):
            utils.label_multiline(layout, text="To get started upscaling, load the available upscaler models", icon="ERROR", width=width_guess)
            layout.operator(operators.AIR_OT_automatic1111_load_upscaler_models.bl_idname, text="Load Upscaler Models", icon="FILE_REFRESH")
            return

        # upscale settings
        row = layout.row()
        row.prop(props, "do_upscale_automatically")

        row = layout.row()
        sub = row.column()
        sub.label(text="Upscale Factor")
        sub = row.column()
        sub.prop(props, "upscale_factor", text="", slider=False)

        row = layout.row()
        sub = row.column()
        sub.label(text="Upscaler Model")
        sub = row.column()
        sub.prop(props, "upscaler_model", text="")

        box = layout.box()
        row = box.row()
        row.label(text=f"Resulting image size: {utils.get_upscaled_width(scene)} x {utils.get_upscaled_height(scene)}")

        # if the dimensions are too large, show message
        if not AIR_PT_upscale.are_upscaled_dimensions_small_enough(context):
            utils.label_multiline(layout, text="Upscaled dimensions are too large. Please decrease the scale factor.", icon="ERROR", width=width_guess)

        # if the backend supports reloading the upscaler model list, show button
        if AIR_PT_upscale.does_backend_support_reloading_upscaler_model_list(context):
            row = layout.row()
            row.operator(operators.AIR_OT_automatic1111_load_upscaler_models.bl_idname, text="Reload Upscaler Models", icon="FILE_REFRESH")

        # show button to manually upscale
        row = layout.row()
        row.enabled = props.last_generated_image_filename != ""
        row.operator(operators.AIR_OT_upscale_last_sd_image.bl_idname, icon="FULLSCREEN_ENTER")


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

            utils.label_multiline(box, text="For more stable animations, consider using ControlNet (locally) or increasing \"Image Similarity\" to at least 0.7", width=width_guess)

            row = box.row()
            row.operator("wm.url_open", text="Get Animation Tips", icon="URL").url = config.ANIMATION_TIPS_URL


classes = [
    AIR_PT_main,
    AIR_PT_setup,
    AIR_PT_prompt,
    AIR_PT_advanced_options,
    AIR_PT_controlnet,
    AIR_PT_operation,
    AIR_PT_upscale,
    AIR_PT_animation,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
