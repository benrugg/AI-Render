import bpy
from . import operators

class SDRProperties(bpy.types.PropertyGroup):
    api_key: bpy.props.StringProperty(
        name="API Key",
        description="Your DreamStudio API KEY",
        update=operators.clear_error,
    )
    prompt_text: bpy.props.StringProperty(
        name="Prompt",
        description="Describe anything for Stable Diffusion to create",
        default="knitted knight",
        update=operators.clear_error,
    )
    prompt_strength: bpy.props.FloatProperty(
        name="Prompt Strength",
        default=0.5,
        min=0,
        max=1,
        description="How much the text prompt will influence the final image",
    )
    image_strength: bpy.props.FloatProperty(
        name="Image Strength",
        default=0.3,
        min=0,
        max=1,
        description="How much the initial image will influence the final image",
    )
    use_random_seed: bpy.props.BoolProperty(
        name="Random Seed",
        default=True,
        description="Use a random seed to create a new starting point for each rendered image"
    )
    seed: bpy.props.IntProperty(
        name="Seed",
        default=0,
        min=0,
        description="The seed for the initial randomization of the algorithm. Use the same seed between images to keep the result more stable",
    )
    error_message: bpy.props.StringProperty(
        name="Error Message",
        default="",
        description="An error message that will be shown if present",
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
