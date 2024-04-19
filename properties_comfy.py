import bpy
from . import utils
from .sd_backends import comfyui_api

from pprint import pprint
from colorama import Fore


def create_property_from_workflow(self, context):
    """ Creates the properties and add the to the comfyui_nodes collection"""

    selected_workflow_file = self.comfyui_workflow
    selected_workflow = comfyui_api.load_workflow(context, selected_workflow_file)
    print(Fore.WHITE + "CREATING PROPERTIES FROM WORKFLOW: " + Fore.RESET + selected_workflow_file)

    selected_class_types = ["LoraLoader", "ControlNetApplyAdvanced", "CheckpointLoaderSimple", "SelfAttentionGuidance"]
    print(Fore.WHITE + "\nSELECTED CLASS TYPE: " + Fore.RESET + str(selected_class_types))

    # Clear the comfyui_nodes collections TODO: Do it with a loop
    self.comfyui_lora_nodes.clear()
    self.comfyui_control_net_nodes.clear()
    self.comfyui_checkpoint_loader_simple.clear()
    self.comfyui_self_attention_guidance.clear()

    # Cycle through the nodes in the selected workflow and create the properties
    for node_id, node in selected_workflow.items():
        if node["class_type"] in selected_class_types:

            if node["class_type"] == "CheckpointLoaderSimple":
                print(Fore.MAGENTA + "\nNODE: " + node_id)
                pprint(node)

                # {'_meta': {'title': 'Load Checkpoint'},
                #  'class_type': 'CheckpointLoaderSimple',
                #  'inputs': {'ckpt_name': 'SD15\\3D\\3dAnimationDiffusion_lcm.safetensors'}}

                comfyui_checkpoint_loader_simple = self.comfyui_checkpoint_loader_simple.add()
                comfyui_checkpoint_loader_simple.name = node_id
                comfyui_checkpoint_loader_simple.current_model = node["inputs"]["ckpt_name"]

                print(Fore.WHITE + "PROPERTY CREATED: " + comfyui_checkpoint_loader_simple.name + Fore.RESET)

            elif node["class_type"] == "LoraLoader":
                print(Fore.YELLOW + "\nNODE: " + node_id)
                pprint(node)

                # {'_meta': {'title': 'Load LoRA'},
                #  'class_type': 'LoraLoader',
                #  'inputs': {'clip': ['28', 1],
                #             'lora_name': 'SD15\\Robotic_Jackal-ish.safetensors',
                #             'model': ['28', 0],
                #             'strength_clip': 1,
                #             'strength_model': 1}}

                comfyui_lora_node = self.comfyui_lora_nodes.add()
                comfyui_lora_node.name = node_id
                comfyui_lora_node.lora_name = node["inputs"]["lora_name"]
                comfyui_lora_node.strength_model = node["inputs"]["strength_model"]
                comfyui_lora_node.strength_clip = node["inputs"]["strength_clip"]

                print(Fore.WHITE + "PROPERTY CREATED: " + Fore.RESET + comfyui_lora_node.name)

            elif node["class_type"] == "ControlNetApplyAdvanced":
                print(Fore.CYAN + "\nNODE: " + node_id)
                pprint(node)

                # {'_meta': {'title': 'Apply ControlNet (Advanced)'},
                #  'class_type': 'ControlNetApplyAdvanced',
                #  'inputs': {'control_net': ['14', 0],
                #             'end_percent': 1,
                #             'image': ['15', 0],
                #             'negative': ['7', 0],
                #             'positive': ['6', 0],
                #             'start_percent': 0,
                #             'strength': 1}}

                # Find ControlNet model connected to the ControlNetApplyAdvanced
                control_net_node = selected_workflow[node["inputs"]["control_net"][0]]
                control_net_node_model_path = control_net_node["inputs"]["control_net_name"]

                comfyui_control_net_node = self.comfyui_control_net_nodes.add()
                comfyui_control_net_node.name = node_id
                comfyui_control_net_node.control_net_name = control_net_node_model_path
                comfyui_control_net_node.strength = node["inputs"]["strength"]
                comfyui_control_net_node.start_percent = node["inputs"]["start_percent"]
                comfyui_control_net_node.end_percent = node["inputs"]["end_percent"]

                print(Fore.WHITE + "PROPERTY CREATED: " + comfyui_control_net_node.name + Fore.RESET)

            elif node["class_type"] == "SelfAttentionGuidance":
                print(Fore.BLUE + "\nNODE: " + node_id)
                pprint(node)

                # {'_meta': {'title': 'Self-Attention Guidance'},
                #  'class_type': 'SelfAttentionGuidance',
                #  'inputs': {'blur_sigma': 2, 'model': ['26', 0], 'scale': 1}}

                comfyui_self_attention_guidance = self.comfyui_self_attention_guidance.add()
                comfyui_self_attention_guidance.name = node_id
                comfyui_self_attention_guidance.blur_sigma = node["inputs"]["blur_sigma"]
                comfyui_self_attention_guidance.scale = node["inputs"]["scale"]

                print(Fore.WHITE + "PROPERTY CREATED: " + comfyui_self_attention_guidance.name + Fore.RESET)


def set_current_sd_model(self, context):
    # I dont know why I'm doing this...
    self.current_model = self.model_enum


class ComfyUICheckpointLoaderSimple(bpy.types.PropertyGroup):
    expanded: bpy.props.BoolProperty(
        name="expanded",
        default=False,
        description="Expanded"
    )

    model_enum: bpy.props.EnumProperty(
        name="Available Models",
        default=0,
        items=comfyui_api.create_models_enum,
        description="A list of the available checkpoints",
        update=set_current_sd_model
    )
    current_model: bpy.props.StringProperty(
        name="Checkpoint Name",
        default="",
        description="Name of the checkpoint model"
    )


class ComfyUILoraNode(bpy.types.PropertyGroup):
    expanded: bpy.props.BoolProperty(
        name="expanded",
        default=False,
        description="Expanded"
    )
    lora_name: bpy.props.StringProperty(
        name="Lora Name",
        default="",
        description="Name of the LoRA model"
    )
    strength_model: bpy.props.FloatProperty(
        name="Lora Model Strength",
        default=1,
        soft_min=0,
        soft_max=1,
        min=0,
        max=10,
        description="Strength of the LoRA model"
    )
    strength_clip: bpy.props.FloatProperty(
        name="Lora Clip Strength",
        default=1,
        soft_min=0,
        soft_max=1,
        min=0,
        max=10,
        description="Strength of the CLIP model"
    )


class ComfyUIControlNetNode(bpy.types.PropertyGroup):
    expanded: bpy.props.BoolProperty(
        name="expanded",
        default=False,
        description="Expanded"
    )
    control_net_name: bpy.props.StringProperty(
        name="ControlNet Name",
        default="",
        description="Name of the ControlNet model"
    )
    strength: bpy.props.FloatProperty(
        name="ControlNet Strength",
        default=1,
        soft_min=0,
        soft_max=1,
        min=0,
        max=10,
        description="Strength of the ControlNet model",
    )
    start_percent: bpy.props.FloatProperty(
        name="ControlNet Start Percent",
        default=0,
        min=0,
        max=1,
        description="Start percent of the ControlNet model"
    )
    end_percent: bpy.props.FloatProperty(
        name="ControlNet End Percent",
        default=1,
        min=0,
        max=1,
        description="End percent of the ControlNet model"
    )


class ComfyUISelfAttentionGuidance(bpy.types.PropertyGroup):
    expanded: bpy.props.BoolProperty(
        name="expanded",
        default=False,
        description="Expanded"
    )
    blur_sigma: bpy.props.FloatProperty(
        name="Self-Attention Guidance Blur Sigma",
        default=2,
        soft_min=0,
        soft_max=10,
        min=0,
        max=10,
        description="Blur sigma"
    )
    scale: bpy.props.FloatProperty(
        name="Self-Attention Guidance Scale",
        default=0.5,
        min=-2,
        max=6,
        description="Scale"
    )


class ComfyUIProps(bpy.types.PropertyGroup):
    comfyui_workflow: bpy.props.EnumProperty(
        name="comfyui_workflow",
        default=0,
        items=comfyui_api.create_workflows_enum,
        description="A list of the available workflows in the path specified in the addon preferences",
        update=create_property_from_workflow
    )
    comfyui_checkpoint_loader_simple: bpy.props.CollectionProperty(type=ComfyUICheckpointLoaderSimple)
    comfyui_lora_nodes: bpy.props.CollectionProperty(type=ComfyUILoraNode)
    comfyui_control_net_nodes: bpy.props.CollectionProperty(type=ComfyUIControlNetNode)
    comfyui_self_attention_guidance: bpy.props.CollectionProperty(type=ComfyUISelfAttentionGuidance)


classes = [
    ComfyUICheckpointLoaderSimple,
    ComfyUILoraNode,
    ComfyUIControlNetNode,
    ComfyUISelfAttentionGuidance,
    ComfyUIProps
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.comfyui_props = bpy.props.PointerProperty(type=ComfyUIProps)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.comfyui_props
