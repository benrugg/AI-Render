import os
import platform
import bpy
import pprint
from colorama import Fore

from . import utils
from .properties_comfy import create_property_from_workflow
from .sd_backends import comfyui_api

from .sd_backends.comfyui_api import (
    COMFY_SD_MODELS,
    COMFY_WORKFLOWS
)


class AIR_OT_UpdateWorkflowEnum(bpy.types.Operator):
    bl_idname = "ai_render.update_workflow_enum"
    bl_label = "Update Workflow Enum"
    bl_description = "Update the workflow enum with the available workflows"

    def execute(self, context):
        print(Fore.GREEN + "UPDATING WORKFLOW ENUM..." + Fore.RESET)

        global COMFY_WORKFLOWS
        COMFY_WORKFLOWS.clear()
        workflows_list = comfyui_api.get_workflows(context)
        for workflow in workflows_list:
            COMFY_WORKFLOWS.append(workflow)

        # Ttrigger property creation from the selected workflow
        create_property_from_workflow(context.scene.comfyui_props, context)
        AIR_OT_UpdateSDModelEnum.execute(self, context)

        return {'FINISHED'}


class AIR_OT_UpdateSDModelEnum(bpy.types.Operator):
    bl_idname = "ai_render.update_sd_model_enum"
    bl_label = "Update Model Enum"
    bl_description = "Update the model enum with the available models"

    def execute(self, context):
        print(Fore.GREEN + "\nUPDATING SD MODEL ENUM..." + Fore.RESET)
        global COMFY_SD_MODELS
        COMFY_SD_MODELS.clear()
        models_list = comfyui_api.get_models(context)
        for model in models_list:
            COMFY_SD_MODELS.append(model)

        return {'FINISHED'}


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
    AIR_OT_UpdateWorkflowEnum,
    AIR_OT_UpdateSDModelEnum,
    AIR_OT_open_comfyui_input_folder,
    AIR_OT_open_comfyui_output_folder,
    AIR_OT_open_comfyui_workflows_folder,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
