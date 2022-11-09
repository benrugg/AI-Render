import bpy
import random
from . import (
    config,
    operators,
    utils,
)
from .ui import ui_preset_styles
from .sd_backends.dreamstudio import dreamstudio_api
from .sd_backends.automatic1111 import automatic1111_api


def get_available_samplers(self, context):
    if utils.do_use_local_sd():
        if utils.local_sd_backend() == "automatic1111":
            return automatic1111_api.get_samplers()
        else:
            print(f"You are trying to use a local Stable Diffusion installation that isn't supported: {utils.local_sd_backend()}")
            return []
    else:
        return dreamstudio_api.get_samplers()


def get_default_sampler():
    if utils.do_use_local_sd():
        if utils.local_sd_backend() == "automatic1111":
            return automatic1111_api.default_sampler()
        else:
            return ""
    else:
        return dreamstudio_api.default_sampler()


def ensure_sampler(self, context):
    # """Ensure that the sampler is set to a valid value"""
    scene = context.scene
    if not scene.air_props.sampler:
        scene.air_props.sampler = get_default_sampler()


class AIRProperties(bpy.types.PropertyGroup):
    is_enabled: bpy.props.BoolProperty(
        name="Enable AI Render",
        default=False,
        description="Enable AI Render in this scene. This is not done by default in new blender files, so you can render normally until you want to use this add-on",
    )
    prompt_text: bpy.props.StringProperty(
        name="Prompt",
        description="Describe anything for Stable Diffusion to create",
        default=config.default_prompt_text,
        update=operators.clear_error_handler,
    )
    image_similarity: bpy.props.FloatProperty(
        name="Image Similarity",
        default=0.4,
        soft_min=0.0,
        soft_max=0.8,
        min=0.0,
        max=1.0,
        description="How closely the final image will match the initial rendered image. Values around 0.1-0.4 will turn simple renders into new creations. Around 0.5 will keep a lot of the composition, and transform into something like the prompt. 0.6-0.7 keeps things more stable between renders. Higher values may require more steps for best results. You can set this to 0.0 to use only the prompt",
    )
    cfg_scale: bpy.props.FloatProperty(
        name="Prompt Strength",
        default=7,
        min=-24,
        max=24,
        description="How closely the text prompt will be followed. Too high can 'overcook' your image. Negative values can be used to generate the opposite of your prompt",
    )
    use_random_seed: bpy.props.BoolProperty(
        name="Random Seed",
        default=True,
        description="Use a random seed to create a new starting point for each rendered image",
    )
    seed: bpy.props.IntProperty(
        name="Seed",
        default=random.randint(1000000000, 2147483647),
        min=0,
        description="The seed for the initial randomization of the algorithm. Use the same seed between images to keep the result more stable. Changing the seed by any amount will give a completely different result",
    )
    steps: bpy.props.IntProperty(
        name="Steps",
        default=40,
        soft_min=10,
        soft_max=50,
        min=10,
        max=100,
        description="How long to process the image. Values in the range of 25-50 generally work well. Higher values take longer and won't necessarily improve results",
    )
    sampler: bpy.props.EnumProperty(
        name="Sampler",
        default=60, # maps to "k_lms" or "LMS"
        items=get_available_samplers,
        description="Which sampler method to use",
    )
    auto_run: bpy.props.BoolProperty(
        name="Run Automatically on Render",
        default=True,
        description="Generate a new image automatically after each render. When off, you will need to manually generate a new image",
    )
    error_key: bpy.props.StringProperty(
        name="Error Key",
        default="",
        description="An error key, linking an error to an api param",
    )
    error_message: bpy.props.StringProperty(
        name="Error Message",
        default="",
        description="An error message that will be shown if present",
    )
    use_preset: bpy.props.BoolProperty(
        name="Apply a Preset Style",
        default=True,
        description="Optionally use a preset style to apply modifier words to your prompt",
    )
    preset_style: bpy.props.EnumProperty(
        name="Preset Style",
        items=ui_preset_styles.enum_thumbnail_icons,
    )
    do_autosave_before_images: bpy.props.BoolProperty(
        name="Save 'Before' Images",
        default=False,
        description="When true, will save each rendered image (before processing it with AI). File format will be your scene's output settings",
    )
    do_autosave_after_images: bpy.props.BoolProperty(
        name="Save 'After' Images",
        default=False,
        description="When true, will save each rendered image (after processing it with AI). File will always be a PNG",
    )
    autosave_image_path: bpy.props.StringProperty(
        name="Autosave Image Output Path",
        default="",
        description="The path to save before/after images, if autosave is enabled (above)",
        subtype="DIR_PATH",
    )
    animation_output_path: bpy.props.StringProperty(
        name="Animation Output Path",
        default="",
        description="The path to save the animation",
        subtype="DIR_PATH",
    )
    animation_init_frame: bpy.props.IntProperty(
        name="Initial Animtion Frame",
        default=1,
        description="Internal property to track the frame the animation started on. This is used to determine if we are rendering an animation",
    )
    is_rendering: bpy.props.BoolProperty(
        name="Is Rendering",
        default=False,
        description="Internal property to track if we are currently rendering",
    )
    is_rendering_animation: bpy.props.BoolProperty(
        name="Is Rendering Animation",
        default=False,
        description="Internal property to track if we are rendering an animation",
    )
    is_rendering_animation_manually: bpy.props.BoolProperty(
        name="Is Rendering Manual Animation",
        default=False,
        description="Internal property to track if we are rendering an animation manually",
    )
    close_animation_tips: bpy.props.BoolProperty(
        name="Close Animation Tips",
        default=False,
    )


classes = [
    AIRProperties
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.air_props = bpy.props.PointerProperty(type=AIRProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.air_props
