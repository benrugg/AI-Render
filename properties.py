import bpy
import random
from . import (
    config,
    operators,
    utils,
)
from .ui import ui_preset_styles
from .sd_backends import automatic1111_api


def get_available_samplers(self, context):
    return utils.get_active_backend().get_samplers()


def get_default_sampler():
    return utils.get_active_backend().default_sampler()


def get_available_upscaler_models(self, context):
    return utils.get_active_backend().get_upscaler_models(context)


def get_default_upscaler_model():
    return utils.get_active_backend().default_upscaler_model()


def get_available_controlnet_models(self, context):
    if utils.sd_backend() == "automatic1111":
        return automatic1111_api.get_available_controlnet_models(context)
    else:
        return []


def get_available_controlnet_modules(self, context):
    if utils.sd_backend() == "automatic1111":
        return automatic1111_api.get_available_controlnet_modules(context)
    else:
        return []


def get_outpaint_directions(self, context):
    return [
        ("up", "up", ""),
        ("down", "down", ""),
        ("left", "left", ""),
        ("right", "right", ""),
    ]


def ensure_sampler(context):
    # """Ensure that the sampler is set to a valid value"""
    scene = context.scene
    if not scene.air_props.sampler:
        scene.air_props.sampler = get_default_sampler()


def ensure_upscaler_model(context):
    # """Ensure that the upscale model is set to a valid value"""
    scene = context.scene
    if utils.get_active_backend().is_upscaler_model_list_loaded(context) and not scene.air_props.upscaler_model:
        scene.air_props.upscaler_model = get_default_upscaler_model()


def ensure_properties(self, context):
    # """Ensure that any properties which could change with a change in preferences are set to valid values"""
    ensure_sampler(context)
    ensure_upscaler_model(context)


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
    negative_prompt_text: bpy.props.StringProperty(
        name="Negative Prompt",
        description="Optionally, describe what Stable Diffusion needs to steer away from",
        default="ugly, bad art, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, extra limbs, disfigured, deformed, body out of frame, blurry, bad anatomy, blurred, watermark, grainy, tiling, signature, cut off, draft",
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
        soft_min=1,
        soft_max=24,
        min=0,
        max=35,
        description="How closely the text prompt will be followed. Too high can 'overcook' your image",
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
        default=30,
        soft_min=10,
        soft_max=50,
        min=10,
        max=150,
        description="How long to process the image. Values in the range of 25-50 generally work well. Higher values take longer (and use more credits) and may or may not improve results",
    )
    sd_model: bpy.props.EnumProperty(
        name="Stable Diffusion Model",
        default=40,
        items=[
            ('v1-5', 'SD 1.5', '', 20),
            ('v2-0', 'SD 2.0', '', 30),
            ('v2-1', 'SD 2.1', '', 40),
            ('stable-diffusion-xl-beta-v2-2-2', 'SDXL Beta', '', 100),
        ],
        description="The Stable Diffusion model to use. SDXL is optimized for photorealism and detailed portraits (comparable to Midjourney). 2.x is more accurate than 1.5 with some types of images, and prompts differently from earlier versions. 1.5 is best for using artist names and art styles in prompts",
    )
    sampler: bpy.props.EnumProperty(
        name="Sampler",
        default=120, # maps to DPM++ 2M, which is a good, fast sampler
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
    last_generated_image_filename: bpy.props.StringProperty(
        name="Last Stable Diffusion Image",
        default="",
        description="The full path and filename of the last image generated from Stable Diffusion (before any upscaling)",
    )
    upscale_factor: bpy.props.FloatProperty(
        name="Upscale Factor",
        default=4.0,
        soft_min=2.0,
        soft_max=4.0,
        min=1.0,
        max=8.0,
        precision=1,
        step=10,
        description="The factor to upscale the image by. The resulting image will be its original size times this factor"
    )
    do_upscale_automatically: bpy.props.BoolProperty(
        name="Upscale Automatically",
        default=True,
        description="When true, will automatically upscale the image after each render",
    )
    upscaler_model: bpy.props.EnumProperty(
        name="Upscaler Model",
        items=get_available_upscaler_models,
        description="Which upscaler model to use",
    )
    automatic1111_available_upscaler_models: bpy.props.StringProperty(
        name="Automatic1111 Upscaler Models",
        default="Lanczos||||Nearest||||ESRGAN_4x||||LDSR||||ScuNET GAN||||ScuNET PSNR||||SwinIR 4x",
        description="A list of the available upscaler models (loaded from the Automatic1111 API)",
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
    use_animated_prompts: bpy.props.BoolProperty(
        name="Use Animated Prompts",
        default=False,
        description="When true, will use the prompts from a text file to animate the image",
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
    controlnet_is_enabled: bpy.props.BoolProperty(
        name="Enable ControlNet",
        default=False,
        description="When true, will use ControlNet for each rendered image",
    )
    controlnet_weight: bpy.props.FloatProperty(
        name="ControlNet Weight",
        default=1.0,
        soft_min=0.0,
        soft_max=1.0,
        min=0.0,
        max=2.0,
        description="How much influence ControlNet will have on guiding the rendered image output",
    )
    controlnet_close_help: bpy.props.BoolProperty(
        name="Close ControlNet Help",
        default=False,
    )
    controlnet_available_models: bpy.props.StringProperty(
        name="ControlNet Models",
        default="",
        description="A list of the available ControlNet models (loaded from the Automatic1111 API)",
    )
    controlnet_available_modules: bpy.props.StringProperty(
        name="ControlNet Modules (Preprocessors)",
        default="",
        description="A list of the available ControlNet modules (preprocessors) (loaded from the Automatic1111 API)",
    )
    controlnet_model: bpy.props.EnumProperty(
        name="ControlNet Model",
        items=get_available_controlnet_models,
        description="Which ControlNet model to use (these must be downloaded and installed locally)",
    )
    controlnet_module: bpy.props.EnumProperty(
        name="ControlNet Module",
        items=get_available_controlnet_modules,
        description="Which ControlNet module (preprocessor) to use (these come with the ControlNet extension)",
    )
    inpaint_mask_path: bpy.props.StringProperty(
        name="Inpaint Mask Path",
        default="",
        description="Upload Inpaint Mask",
        subtype="FILE_PATH",
    )
    inpaint_full_res: bpy.props.BoolProperty(
        name="Inpaint at Full Resolution",
        default=True,
        description="",
    )
    inpaint_padding: bpy.props.IntProperty(
        name="Inpaint Padding",
        max=256,
        min=0,
        default=32,
        step=4,
        description="",
    )
    outpaint_direction: bpy.props.EnumProperty(
        name="Outpaint Direction",
        items=get_outpaint_directions,
        description="The image will expand in this direction",
    )
    outpaint_pixels_to_expand: bpy.props.IntProperty(
        name="Outpaint Pixels to Expand",
        min=8,
        max=256,
        step=8,
        default=8,
        description="",
    )
    outpaint_mask_blur: bpy.props.IntProperty(
        name="Outpaint Mask Blur",
        description="this changes how much the inpainting mask is blurred. This helps to avoid sharp edges on the image.",
        min=0,
        max=64,
        step=1,
        default=0,
    )
    outpaint_noise_q: bpy.props.FloatProperty(
        min=0.0,
        max=4.0,
        default=1.0,
        step=0.01,
        name="Outpaint Noise Quotient",
    )
    outpaint_color_variation: bpy.props.FloatProperty(
        min=0.0,
        max=1.0,
        default=0.05,
        step=0.01,
        name="Outpaint Color Variation",
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
