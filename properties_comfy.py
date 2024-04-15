import os
import bpy
from . import utils
from .sd_backends import comfyui_api

from pprint import pprint
from colorama import Fore


def get_available_workflows(self, context):
    """ Query the comfyui_api for the available workflows and return them as a list of tuples"""

    if utils.sd_backend() == "comfyui":
        return comfyui_api.create_workflows_tuples()
    else:
        return [("none", "None", "", 0)]


def create_property_from_workflow(self, context):
    """ Creates the properties and add the to the comfyui_nodes collection"""

    # Get Workflows_path from the addon preferences and the selected workflow
    selected_workflow_file = self.comfyui_workflow

    # Load the selected workflow
    selected_workflow = comfyui_api.load_workflow(context, selected_workflow_file)
    print(Fore.GREEN + "CREATING PROPERTIES FROM WORKFLOW: " + Fore.RESET + selected_workflow_file)
    # pprint(selected_workflow)

    selected_class_types = ["LoraLoader", "ControlNetApplyAdvanced", "CheckpointLoaderSimple"]
    print(Fore.GREEN + "SELECTED CLASS TYPE: " + Fore.RESET + str(selected_class_types))

    # Clear the comfyui_nodes collections
    self.comfyui_lora_nodes.clear()
    self.comfyui_control_net_nodes.clear()
    self.comfyui_checkpoint_loader_simple.clear()

    # Cycle through the nodes in the selected workflow and create the properties
    for node_id, node in selected_workflow.items():
        if node["class_type"] in selected_class_types:
            if node["class_type"] == "LoraLoader":
                print(Fore.GREEN + "NODE: " + Fore.RESET + node_id)
                pprint(node)

                # {'_meta': {'title': 'Load LoRA'},
                #  'class_type': 'LoraLoader',
                #  'inputs': {'clip': ['28', 1],
                #             'lora_name': 'SD15\\Robotic_Jackal-ish.safetensors',
                #             'model': ['28', 0],
                #             'strength_clip': 1,
                #             'strength_model': 1}}

                # Create the property group
                comfyui_lora_node = self.comfyui_lora_nodes.add()
                comfyui_lora_node.name = node_id
                comfyui_lora_node.lora_name = node["inputs"]["lora_name"]
                comfyui_lora_node.strength_model = node["inputs"]["strength_model"]
                comfyui_lora_node.strength_clip = node["inputs"]["strength_clip"]

                print(Fore.GREEN + "PROPERTY CREATED: " + Fore.RESET + comfyui_lora_node.name)

            elif node["class_type"] == "ControlNetApplyAdvanced":
                print(Fore.GREEN + "NODE: " + Fore.RESET + node_id)
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

                # Create the property group
                comfyui_control_net_node = self.comfyui_control_net_nodes.add()
                comfyui_control_net_node.name = node_id
                comfyui_control_net_node.control_net_name = control_net_node_model_path
                comfyui_control_net_node.strength = node["inputs"]["strength"]
                comfyui_control_net_node.start_percent = node["inputs"]["start_percent"]
                comfyui_control_net_node.end_percent = node["inputs"]["end_percent"]

                print(Fore.GREEN + "PROPERTY CREATED: " + Fore.RESET + comfyui_control_net_node.name)

            elif node["class_type"] == "CheckpointLoaderSimple":
                print(Fore.MAGENTA + "NODE: " + Fore.RESET + node_id)
                pprint(node)

                # {'_meta': {'title': 'Load Checkpoint'},
                #  'class_type': 'CheckpointLoaderSimple',
                #  'inputs': {'ckpt_name': 'SD15\\3D\\3dAnimationDiffusion_lcm.safetensors'}}

                # Create the property group
                comfyui_checkpoint_loader_simple = self.comfyui_checkpoint_loader_simple.add()
                comfyui_checkpoint_loader_simple.name = node_id
                comfyui_checkpoint_loader_simple.ckpt_name = node["inputs"]["ckpt_name"]


def get_available_ckpts(self, context):
    """ Query the comfyui_api /object_info for the available checkpoints and return them as a list of tuples"""

    if utils.sd_backend() == "comfyui":
        return comfyui_api.create_ckpts_tuples()
    else:
        return []

def update_ckpt_name(self, context):
    """ Update the ckpt_name property with the selected checkpoint name"""

    # Get the selected checkpoint name
    selected_ckpt_name = self.available_ckpts

    # Update the ckpt_name property
    self.ckpt_name = selected_ckpt_name
    context.scene.air_props.sd_model = selected_ckpt_name


class ComfyUICheckpointLoaderSimple(bpy.types.PropertyGroup):
    ckpt_name: bpy.props.StringProperty(
        name="ckpt_name",
        default="",
        description="Name of the checkpoint model"
    )
    available_ckpts: bpy.props.EnumProperty(
        name="available_ckpts",
        default=0,
        items=get_available_ckpts,
        description="A list of the available checkpoints in the path specified in the addon preferences",
        update=update_ckpt_name
    )


class ComfyUILoraNode(bpy.types.PropertyGroup):
    lora_name: bpy.props.StringProperty(
        name="lora_name",
        default="",
        description="Name of the LoRA model"
    )
    strength_model: bpy.props.FloatProperty(
        name="strength_model",
        default=1,
        soft_min=0,
        soft_max=1,
        min=0,
        max=10,
        description="Strength of the LoRA model"
    )
    strength_clip: bpy.props.FloatProperty(
        name="strength_clip",
        default=1,
        soft_min=0,
        soft_max=1,
        min=0,
        max=10,
        description="Strength of the CLIP model"
    )


class ComfyUIControlNetNode(bpy.types.PropertyGroup):
    control_net_name: bpy.props.StringProperty(
        name="control_net_name",
        default="",
        description="Name of the ControlNet model"
    )
    strength: bpy.props.FloatProperty(
        name="strength",
        default=1,
        soft_min=0,
        soft_max=1,
        min=0,
        max=10,
        description="Strength of the ControlNet model",
    )
    start_percent: bpy.props.FloatProperty(
        name="start_percent",
        default=0,
        min=0,
        max=1,
        description="Start percent of the ControlNet model"
    )
    end_percent: bpy.props.FloatProperty(
        name="end_percent",
        default=1,
        min=0,
        max=1,
        description="End percent of the ControlNet model"
    )


class AIRPropertiesComfyUI(bpy.types.PropertyGroup):
    comfyui_workflow: bpy.props.EnumProperty(
        name="comfyui_workflow",
        default=0,
        items=get_available_workflows,
        description="A list of the available workflows in the path specified in the addon preferences",
        update=create_property_from_workflow
    )
    comfyui_checkpoint_loader_simple: bpy.props.CollectionProperty(type=ComfyUICheckpointLoaderSimple)
    comfyui_lora_nodes: bpy.props.CollectionProperty(type=ComfyUILoraNode)
    comfyui_control_net_nodes: bpy.props.CollectionProperty(type=ComfyUIControlNetNode)


classes = [
    ComfyUILoraNode,
    ComfyUIControlNetNode,
    ComfyUICheckpointLoaderSimple,
    AIRPropertiesComfyUI,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.comfyui_props = bpy.props.PointerProperty(type=AIRPropertiesComfyUI)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.comfyui_props
