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

    # start with a clean node tree
    for node in normalpass2normalmap.nodes:
        normalpass2normalmap.nodes.remove(node)

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
    mix.inputs[2].default_value = (1.0, 1.0, 1.0, 1.0)

    # node Mix.001
    mix_001 = normalpass2normalmap.nodes.new("CompositorNodeMixRGB")
    mix_001.name = "Mix.001"
    mix_001.blend_type = 'ADD'
    mix_001.use_alpha = False
    mix_001.use_clamp = False
    # Fac
    mix_001.inputs[0].default_value = 1.0
    # Image_001
    mix_001.inputs[2].default_value = (1.0, 1.0, 1.0, 1.0)

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
    # group_input.Alpha -> combine_color.Alpha
    normalpass2normalmap.links.new(group_input.outputs[1], combine_color.inputs[3])
    return normalpass2normalmap


def ensure_compositor_nodes(context):
    """Ensure that use nodes is enabled and the compositor nodes are set up correctly"""

    print(Fore.YELLOW + "ENSURE COMPOSITOR NODES")

    comfyui_input_path = comfyui_api.get_comfyui_input_path(context)
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
        if node.name != "Render Layers" and node.name != "Composite":
            nodes.remove(node)

    # Check if Render Layers and Composite nodes exist, if not add them
    if not any(node for node in nodes if node.name == "Render Layers"):
        render_layers_node = nodes.new("CompositorNodeRLayers")
        render_layers_node.name = "Render Layers"
        render_layers_node.label = "Render Layers"

    if not any(node for node in nodes if node.name == "Composite"):
        composite_node = nodes.new("CompositorNodeComposite")
        composite_node.name = "Composite"
        composite_node.label = "Composite"

    # Set the position of the Render Layers and Composite nodes
    render_layers_node = nodes.get("Render Layers")
    render_layers_node.location = (0, 0)
    composite_node = nodes.get("Composite")
    composite_node.location = (500, 400)

    # Color
    ColorOutputNode = nodes.new("CompositorNodeOutputFile")
    ColorOutputNode.name = "color_file_output"
    ColorOutputNode.label = "Color"
    ColorOutputNode.base_path = comfyui_input_path + "color/"
    ColorOutputNode.location = (500, 200)
    ColorOutputNode.format.file_format = "PNG"
    ColorOutputNode.width = 300

    # Depth
    MistOutputNode = nodes.new("CompositorNodeOutputFile")
    MistOutputNode.name = "depth_file_output"
    MistOutputNode.label = "Depth"
    MistOutputNode.base_path = comfyui_input_path + "depth/"
    MistOutputNode.location = (500, 0)
    MistOutputNode.format.file_format = "PNG"
    MistOutputNode.width = 300

    # Invert Node for Mist
    InvertNode = nodes.new("CompositorNodeInvert")
    InvertNode.name = "Invert"
    InvertNode.label = "Invert"
    InvertNode.location = (300, 0)

    # Normal
    NormalOutputNode = nodes.new("CompositorNodeOutputFile")
    NormalOutputNode.name = "normal_file_output"
    NormalOutputNode.label = "Normal"
    NormalOutputNode.base_path = comfyui_input_path + "normal/"
    NormalOutputNode.location = (500, -200)
    NormalOutputNode.format.file_format = "PNG"
    NormalOutputNode.width = 300

    # Create a new node group
    NormalNodeGroup = nodes.new("CompositorNodeGroup")
    NormalNodeGroup.name = "NormalPass2NormalMap"
    NormalNodeGroup.label = "NormalPass  2NormalMap"
    NormalNodeGroup.location = (300, -200)

    # Create a new Normal NodeTree if there is not one already
    if not bpy.data.node_groups.get("NormalPass2NormalMap"):
        Normal_Node_Tree = normalpass2normalmap_node_group(context)
    else:
        Normal_Node_Tree = bpy.data.node_groups.get("NormalPass2NormalMap")

    # Set the node group to the normalpass2normalmap node group
    NormalNodeGroup.node_tree = Normal_Node_Tree

    # Link the nodes
    links = tree.links
    links.new(render_layers_node.outputs["Image"], ColorOutputNode.inputs[0])
    links.new(render_layers_node.outputs["Mist"], InvertNode.inputs[1])
    links.new(InvertNode.outputs[0], MistOutputNode.inputs[0])
    links.new(render_layers_node.outputs["Normal"], NormalNodeGroup.inputs[0])
    links.new(render_layers_node.outputs["Alpha"], NormalNodeGroup.inputs[1])
    links.new(NormalNodeGroup.outputs[0], NormalOutputNode.inputs[0])

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
