import bpy
import random
from . import (
    config,
    operators,
    utils,
)
from .ui import ui_preset_styles
from .sd_backends import automatic1111_api
from .sd_backends import comfyui_api

from colorama import Fore


def ensure_upscaler_model(context):
    # """Ensure that the upscale model is set to a valid value"""
    print(Fore.GREEN + "ENSURE UPSCALER MODEL" + Fore.RESET)
    scene = context.scene
    if (
        utils.sd_backend() != "comfyui"
        and utils.get_active_backend().is_upscaler_model_list_loaded(context)
        and not scene.air_props.upscaler_model
    ):
        scene.air_props.upscaler_model = get_default_upscaler_model()


def update_local_sd_url(context):
    """
    If is set to Automatic1111, the url is http://127.0.0.1:7860
    If is set to ComfyUI, the url is http://127.0.0.1:8188
    """

    print(Fore.GREEN + "UPDATE LOCAL SD URL TO: " + Fore.RESET + utils.sd_backend())
    addonprefs = utils.get_addon_preferences(context)

    if utils.sd_backend() == "automatic1111":
        addonprefs.local_sd_url = "http://127.0.0.1:7860"
    elif utils.sd_backend() == "comfyui":
        addonprefs.local_sd_url = "http://127.0.0.1:8188"


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


def get_available_samplers(self, context):
    return utils.get_active_backend().get_samplers()


def get_default_sampler():
    return utils.get_active_backend().default_sampler()


def ensure_sampler(context):
    """Ensure that the sampler is set to a valid value"""
    print(Fore.GREEN + "ENSURE SAMPLER" + Fore.RESET)

    if not context.scene.air_props.sampler:
        context.scene.air_props.sampler = get_default_sampler()


def get_available_schedulers(self, context):
    if utils.sd_backend() == "comfyui":
        return comfyui_api.get_schedulers()
    else:
        return [("none", "None", "", 0)]


def get_default_scheduler():
    return utils.get_active_backend().default_scheduler()


def ensure_scheduler(context):
    """Ensure that the scheduler is set to a valid value"""
    print(Fore.GREEN + "ENSURE SCHEDULER" + Fore.RESET)

    if not context.scene.air_props.scheduler:
            context.scene.air_props.scheduler = get_default_scheduler()


def ensure_use_passes(context):
    """Ensure that the render passes are enabled"""

    # Get active ViewLayer
    view_layer = context.view_layer

    # Activate needed use_passes
    view_layer.use_pass_combined = True
    view_layer.use_pass_z = True
    view_layer.use_pass_normal = True
    view_layer.use_pass_mist = True


def ensure_film_transparent(context):
    context.scene.render.film_transparent = True


def normalpass2normalmap_node_group(context):

    # Create a new node tree
    normalpass2normalmap = bpy.data.node_groups.new(
        type="CompositorNodeTree", name="NormalPass2NormalMap")

    # normalpass2normalmap interface
    # Socket Image
    image_socket = normalpass2normalmap.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    image_socket.attribute_domain = 'POINT'

    # Socket Image
    image_socket_1 = normalpass2normalmap.interface.new_socket(name="Image", in_out='INPUT', socket_type='NodeSocketColor')
    image_socket_1.attribute_domain = 'POINT'

    # Socket Alpha
    alpha_socket = normalpass2normalmap.interface.new_socket(name="Alpha", in_out='INPUT', socket_type='NodeSocketFloat')
    alpha_socket.subtype = 'FACTOR'
    alpha_socket.default_value = 1.0
    alpha_socket.min_value = 0.0
    alpha_socket.max_value = 1.0
    alpha_socket.attribute_domain = 'POINT'

    # initialize normalpass2normalmap nodes
    # node Group Output
    group_output = normalpass2normalmap.nodes.new("NodeGroupOutput")
    group_output.name = "Group Output"
    group_output.is_active_output = True

    # node Mix
    mix = normalpass2normalmap.nodes.new("CompositorNodeMixRGB")
    mix.name = "Mix"
    mix.blend_type = 'MULTIPLY'
    mix.use_alpha = False
    mix.use_clamp = False
    # Fac
    mix.inputs[0].default_value = 1.0
    # Image_001
    mix.inputs[2].default_value = (0.5, 0.5, 0.5, 1.0)

    # node Mix.001
    mix_001 = normalpass2normalmap.nodes.new("CompositorNodeMixRGB")
    mix_001.name = "Mix.001"
    mix_001.blend_type = 'ADD'
    mix_001.use_alpha = False
    mix_001.use_clamp = False
    # Fac
    mix_001.inputs[0].default_value = 1.0
    # Image_001
    mix_001.inputs[2].default_value = (0.5, 0.5, 0.5, 1.0)

    # node Invert Color
    invert_color = normalpass2normalmap.nodes.new("CompositorNodeInvert")
    invert_color.name = "Invert Color"
    invert_color.invert_alpha = False
    invert_color.invert_rgb = True
    # Fac
    invert_color.inputs[0].default_value = 1.0

    # node Combine Color
    combine_color = normalpass2normalmap.nodes.new("CompositorNodeCombineColor")
    combine_color.name = "Combine Color"
    combine_color.mode = 'RGB'
    combine_color.ycc_mode = 'ITUBT709'
    # Alpha
    combine_color.inputs[3].default_value = 1.0

    # node Separate Color
    separate_color = normalpass2normalmap.nodes.new("CompositorNodeSeparateColor")
    separate_color.name = "Separate Color"
    separate_color.mode = 'RGB'
    separate_color.ycc_mode = 'ITUBT709'

    # node Group Input
    group_input = normalpass2normalmap.nodes.new("NodeGroupInput")
    group_input.name = "Group Input"

    # Set locations
    group_output.location = (590.0, 0.0)
    mix.location = (-399.99993896484375, 0.0)
    mix_001.location = (-199.99993896484375, 0.0)
    invert_color.location = (6.103515625e-05, 0.0)
    combine_color.location = (400.0, 0.0)
    separate_color.location = (200.0, 0.0)
    group_input.location = (-622.678955078125, -0.7322563529014587)

    # Set dimensions
    group_output.width, group_output.height = 140.0, 100.0
    mix.width, mix.height = 140.0, 100.0
    mix_001.width, mix_001.height = 140.0, 100.0
    invert_color.width, invert_color.height = 140.0, 100.0
    combine_color.width, combine_color.height = 140.0, 100.0
    separate_color.width, separate_color.height = 140.0, 100.0
    group_input.width, group_input.height = 140.0, 100.0

    # initialize normalpass2normalmap links
    # invert_color.Color -> separate_color.Image
    normalpass2normalmap.links.new(invert_color.outputs[0], separate_color.inputs[0])
    # separate_color.Blue -> combine_color.Green
    normalpass2normalmap.links.new(separate_color.outputs[2], combine_color.inputs[1])
    # mix_001.Image -> invert_color.Color
    normalpass2normalmap.links.new(mix_001.outputs[0], invert_color.inputs[1])
    # separate_color.Red -> combine_color.Red
    normalpass2normalmap.links.new(separate_color.outputs[0], combine_color.inputs[0])
    # separate_color.Green -> combine_color.Blue
    normalpass2normalmap.links.new(separate_color.outputs[1], combine_color.inputs[2])
    # mix.Image -> mix_001.Image
    normalpass2normalmap.links.new(mix.outputs[0], mix_001.inputs[1])
    # group_input.Image -> mix.Image
    normalpass2normalmap.links.new(group_input.outputs[0], mix.inputs[1])
    # combine_color.Image -> group_output.Image
    normalpass2normalmap.links.new(combine_color.outputs[0], group_output.inputs[0])
    return normalpass2normalmap


def ensure_compositor_nodes(context):
    """Ensure that use nodes is enabled and the compositor nodes are set up correctly"""

    print(Fore.YELLOW + "ENSURE COMPOSITOR NODES" + Fore.RESET)

    # Ensure that the render passes are enabled
    ensure_use_passes(context)
    ensure_film_transparent(context)

    scene = context.scene
    if not scene.use_nodes:
        scene.use_nodes = True

    tree = scene.node_tree
    nodes = tree.nodes

    # remove all nodes except the render layers and the Composite node
    for node in nodes:
        nodes.remove(node)

    # scene_1 interface

    # initialize scene_1 nodes
    # Create a new node group
    NormalNodeGroup = nodes.new("CompositorNodeGroup")
    NormalNodeGroup.name = "NormalPass2NormalMap"
    NormalNodeGroup.label = "NormalPass  2NormalMap"

    # Create a new Normal NodeTree if there is not one already
    if not bpy.data.node_groups.get("NormalPass2NormalMap"):
        Normal_Node_Tree = normalpass2normalmap_node_group(context)
    else:
        Normal_Node_Tree = bpy.data.node_groups.get("NormalPass2NormalMap")

    # Set the node group to the normalpass2normalmap node group
    NormalNodeGroup.node_tree = Normal_Node_Tree
    # Socket_2
    NormalNodeGroup.inputs[1].default_value = 1.0

    # node Color Ramp
    color_ramp = nodes.new("CompositorNodeValToRGB")
    color_ramp.name = "Color Ramp"
    color_ramp.color_ramp.color_mode = 'RGB'
    color_ramp.color_ramp.hue_interpolation = 'NEAR'
    color_ramp.color_ramp.interpolation = 'EASE'

    # initialize color ramp elements
    color_ramp.color_ramp.elements.remove(color_ramp.color_ramp.elements[0])
    color_ramp_cre_0 = color_ramp.color_ramp.elements[0]
    color_ramp_cre_0.position = 0.913193
    color_ramp_cre_0.alpha = 1.0
    color_ramp_cre_0.color = (1.0, 1.0, 1.0, 1.0)

    color_ramp_cre_1 = color_ramp.color_ramp.elements.new(0.965278)
    color_ramp_cre_1.alpha = 1.0
    color_ramp_cre_1.color = (0.0, 0.0, 0.0, 1.0)

    # node normal_file_output
    normal_file_output = nodes.new("CompositorNodeOutputFile")
    normal_file_output.label = "Normal"
    normal_file_output.name = "normal_file_output"
    normal_file_output.active_input_index = 0
    normal_file_output.base_path = comfyui_api.get_normal_file_input_path(context)

    # node Render Layers
    render_layers = nodes.new("CompositorNodeRLayers")
    render_layers.label = "Render Layers"
    render_layers.name = "Render Layers"
    render_layers.layer = 'ViewLayer'

    # node Viewer
    viewer = nodes.new("CompositorNodeViewer")
    viewer.name = "Viewer"
    viewer.center_x = 0.5
    viewer.center_y = 0.5
    viewer.tile_order = 'CENTEROUT'
    viewer.use_alpha = True
    # Alpha
    viewer.inputs[1].default_value = 1.0

    # node Composite
    composite = nodes.new("CompositorNodeComposite")
    composite.label = "Composite"
    composite.name = "Composite"
    composite.use_alpha = True
    # Alpha
    composite.inputs[1].default_value = 1.0

    # node color_file_output
    color_file_output = nodes.new("CompositorNodeOutputFile")
    color_file_output.label = "Color"
    color_file_output.name = "color_file_output"
    color_file_output.active_input_index = 0
    color_file_output.base_path = comfyui_api.get_color_file_input_path(context)

    # node depth_file_output
    depth_file_output = nodes.new("CompositorNodeOutputFile")
    depth_file_output.label = "Depth"
    depth_file_output.name = "depth_file_output"
    depth_file_output.active_input_index = 0
    depth_file_output.base_path = comfyui_api.get_depth_file_input_path(context)

    # Set locations
    NormalNodeGroup.location = (361.5553894042969, -169.21304321289062)
    color_ramp.location = (365.3896179199219, 73.5697250366211)
    normal_file_output.location = (691.8238525390625, -7.402432441711426)
    render_layers.location = (3.578803300857544, 178.27804565429688)
    viewer.location = (370.6922302246094, 283.4913330078125)
    composite.location = (377.6049499511719, 407.1597900390625)
    color_file_output.location = (693.7745971679688, 238.85935974121094)
    depth_file_output.location = (694.5862426757812, 120.32701873779297)

    # Set dimensions
    NormalNodeGroup.width, NormalNodeGroup.height = 244.50103759765625, 100.0
    color_ramp.width, color_ramp.height = 240.0, 100.0
    normal_file_output.width, normal_file_output.height = 300.0, 100.0
    render_layers.width, render_layers.height = 240.0, 100.0
    viewer.width, viewer.height = 236.62774658203125, 100.0
    composite.width, composite.height = 232.3331756591797, 100.0
    color_file_output.width, color_file_output.height = 300.0, 100.0
    depth_file_output.width, depth_file_output.height = 300.0, 100.0

    # initialize links
    links = tree.links
    # render_layers.Image -> composite.Image
    links.new(render_layers.outputs[0], composite.inputs[0])
    # render_layers.Image -> color_file_output.Image
    links.new(render_layers.outputs[0], color_file_output.inputs[0])
    # render_layers.Normal -> normalpass2normalmap_1.Image
    links.new(render_layers.outputs[4], NormalNodeGroup.inputs[0])
    # normalpass2normalmap_1.Image -> normal_file_output.Image
    links.new(NormalNodeGroup.outputs[0], normal_file_output.inputs[0])
    # color_ramp.Image -> depth_file_output.Image
    links.new(color_ramp.outputs[0], depth_file_output.inputs[0])
    # render_layers.Mist -> color_ramp.Fac
    links.new(render_layers.outputs[3], color_ramp.inputs[0])
    # render_layers.Image -> viewer.Image
    links.new(render_layers.outputs[0], viewer.inputs[0])

    # Deselect all nodes
    for node in nodes:
        node.select = False


def ensure_ckpt_models(context):
    print(Fore.MAGENTA + "ENSURE CKPT MODELS" + Fore.RESET)
    # TODO: Implement this


def ensure_properties(self, context):
    """Ensure that any properties which could change with a change in preferences are set to valid values"""
    print(Fore.WHITE + "ENSURE PROPERTIES" + Fore.RESET)
    ensure_sampler(context)
    update_local_sd_url(context)

    if utils.sd_backend() == "comfyui":
        ensure_scheduler(context)
        ensure_compositor_nodes(context)
        ensure_ckpt_models(context)
    else:  # only if not comfyui
        ensure_upscaler_model(context)


def update_denoise(self, context):
    """round(1 - params["image_similarity"], 2)"""

    context.scene.air_props.denoising_strength = round(
        1 - context.scene.air_props.image_similarity, 4)


def update_image_similarity(self, context):
    """1 - params["denoising_strength"]"""

    context.scene.air_props.image_similarity = round(
        1 - context.scene.air_props.denoising_strength, 4)


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
        description="Optionally, describe what Stable Diffusion should steer away from",
        default="ugly, bad art",
    )
    image_similarity: bpy.props.FloatProperty(
        name="Image Similarity",
        default=0.3,
        min=0.0,
        max=0.999,
        description="How closely the final image will match the initial rendered image. Values around 0.1-0.4 will turn simple renders into new creations. Around 0.5 will keep a lot of the composition, and transform into something like the prompt. 0.6-0.7 keeps things more stable between renders. Higher values may require more steps for best results. You can set this to 0.0 to use only the prompt",
        # update=update_denoise
    )
    # denoising_strength: bpy.props.FloatProperty(
    #     name="Denoising Strength",
    #     default=0.7,
    #     min=0.001,
    #     max=1.0,
    #     description="How much to denoise the image. Higher values will remove more noise, but may also remove detail",
    #     update=update_image_similarity
    # )
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
        default=15,
        soft_min=1,
        soft_max=50,
        min=1,
        max=150,
        description="How long to process the image. Values in the range of 20-40 generally work well. Higher values take longer (and use more credits) and may or may not improve results",
    )
    sd_model: bpy.props.EnumProperty(
        name="Stable Diffusion Model",
        default=120,
        items=[
            ("stable-diffusion-xl-1024-v1-0", "SDXL 1.0", "", 120),
        ],
        description="The Stable Diffusion model to use. SDXL is comparable to Midjourney. Older versions have now been removed, but newer versions may be added in the future",
    )
    sampler: bpy.props.EnumProperty(
        name="Sampler",
        default=130,  # maps to DPM++ 2M, which is a good, fast sampler
        items=get_available_samplers,
        description="Which sampler method to use",
    )
    scheduler: bpy.props.EnumProperty(
        name="Scheduler",
        default=10,
        items=get_available_schedulers,
        description="Which scheduler method to use",
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
        default=False,
        description="Optionally use a preset style to apply modifier words to your prompt",
    )
    preset_style: bpy.props.EnumProperty(
        name="Preset Style",
        items=ui_preset_styles.enum_thumbnail_icons,
    )
    image_filename_template: bpy.props.StringProperty(
        name="Filename Template",
        default=config.default_image_filename_template,
        description=f"The filename template for generated images. Can include any of the following keywords: {'{' + '}, {'.join(config.filename_template_allowed_vars) + '}'}",
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
        default=2.0,
        soft_min=2.0,
        soft_max=4.0,
        min=1.0,
        max=8.0,
        precision=1,
        step=10,
        description="The factor to upscale the image by. The resulting image will be its original size times this factor",
    )
    do_upscale_automatically: bpy.props.BoolProperty(
        name="Upscale Automatically",
        default=False,
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


classes = [AIRProperties]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.air_props = bpy.props.PointerProperty(type=AIRProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.air_props
