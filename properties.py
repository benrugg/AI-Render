import bpy
import random
from . import (
    constants,
    operators,
)
from .ui import ui_preset_styles

class SDRProperties(bpy.types.PropertyGroup):
    prompt_text: bpy.props.StringProperty(
        name="Prompt",
        description="Describe anything for Stable Diffusion to create",
        default=constants.default_prompt_text,
        update=operators.clear_error_handler,
    )
    image_similarity: bpy.props.FloatProperty(
        name="Image Similarity",
        default=0.15,
        soft_min=0.0,
        soft_max=0.5,
        min=0.0,
        max=1.0,
        description="How closely the final image will match the initial rendered image. Values around 0.1-0.4 will turn simple renders into new creations. Higher values will adhere more closely to the initial render. If your image is blank, set this to 0.0 for best results",
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
        description="Use a random seed to create a new starting point for each rendered image"
    )
    seed: bpy.props.IntProperty(
        name="Seed",
        default=random.randint(1000000000, 2147483647),
        min=0,
        description="The seed for the initial randomization of the algorithm. Use the same seed between images to keep the result more stable. Changing the seed by any amount will give a completely different result",
    )
    steps: bpy.props.IntProperty(
        name="Steps",
        default=25,
        soft_min=10,
        soft_max=100,
        min=10,
        max=150,
        description="How long to process the image. Values in the range of 25-50 generally work well. Higher values will take longer and won't necessarily improve results",
    )
    sampler: bpy.props.EnumProperty(
        name="Sampler",
        default="k_lms",
        items=[
            ('k_euler', 'k_euler', ''),
            ('k_euler_ancestral', 'k_euler_ancestral', ''),
            ('k_heun', 'k_heun', ''),
            ('k_dpm_2', 'k_dpm_2', ''),
            ('k_dpm_2_ancestral', 'k_dpm_2_ancestral', ''),
            ('k_lms', 'k_lms', ''),
        ],
        description="Which sampler method to use",
    )
    auto_run: bpy.props.BoolProperty(
        name="Run Automatically on Render",
        default=True,
        description="Generate a new image automatically after each render. When off, you will need to manually generate a new image"
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
    preset_style: bpy.props.EnumProperty(
        name="Preset Style",
        items=ui_preset_styles.enum_thumbnail_icons
    )


classes = [
    SDRProperties
]


def register_properties():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.sdr_props = bpy.props.PointerProperty(type=SDRProperties)


def unregister_properties():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.sdr_props
