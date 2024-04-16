import os
import platform
import bpy

from . import utils
from .sd_backends import comfyui_api

from colorama import Fore


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

    print(Fore.YELLOW + "ENSURE COMPOSITOR NODES")

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


# Comfy specific operators
class AIR_OT_open_comfyui_input_folder(bpy.types.Operator):
    "Open the input folder in the windows explorer or macOSfinder"
    bl_idname = "ai_render.open_comfyui_input_folder"
    bl_label = "Open Output Folder"

    def execute(self, context):
        input_folder = comfyui_api.get_comfyui_input_path(context)
        print(f"Opening folder: {input_folder}")

        if platform.system() == "Windows":
            os.system(f"start {input_folder}")
        elif platform.system() == "Darwin":
            os.system(f"open {input_folder}")

        return {'FINISHED'}


class AIR_OT_open_comfyui_output_folder(bpy.types.Operator):
    "Open the output folder in the windows explorer or macOSfinder"
    bl_idname = "ai_render.open_comfyui_output_folder"
    bl_label = "Open Output Folder"

    def execute(self, context):
        output_folder = comfyui_api.get_comfyui_output_path(context)
        print(f"Opening folder: {output_folder}")

        if platform.system() == "Windows":
            os.system(f"start {output_folder}")
        elif platform.system() == "Darwin":
            os.system(f"open {output_folder}")

        return {'FINISHED'}


class AIR_OT_open_comfyui_workflows_folder(bpy.types.Operator):
    "Open the workflow folder in the windows explorer or macOSfinder"
    bl_idname = "ai_render.open_comfyui_workflows_folder"
    bl_label = "Open Workflow Folder"

    def execute(self, context):
        workflow_folder = utils.get_addon_preferences().comfyui_workflows_path
        print(f"Opening folder: {workflow_folder}")

        if platform.system() == "Windows":
            os.system(f'explorer "{workflow_folder}"')
        elif platform.system() == "Darwin":
            os.system(f"open {workflow_folder}")

        return {'FINISHED'}


classes = [
    AIR_OT_open_comfyui_input_folder,
    AIR_OT_open_comfyui_output_folder,
    AIR_OT_open_comfyui_workflows_folder
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
