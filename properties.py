import bpy

class SDRProperties(bpy.types.PropertyGroup):
    api_key: bpy.props.StringProperty(
        name="API Key",
        description="Your DreamStudio API KEY",
    )
    prompt_text: bpy.props.StringProperty(
        name="Prompt",
        description="Describe anything for Stable Diffusion to create",
        default="asdfdsa",
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
        default=0.4,
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