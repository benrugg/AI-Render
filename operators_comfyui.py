import os
import platform
import bpy
import pprint

# Colorama Placeholder
from . import Fore

from . import utils
from .operators import *
from .properties_comfy import create_props_from_workflow
from .sd_backends import comfyui_api

from .sd_backends.comfyui_api import (
    COMFY_WORKFLOWS,
    COMFY_CKPT_MODELS,
    COMFY_LORA_MODELS,
    COMFY_SAMPLERS,
    COMFY_CONTROL_NETS,
    COMFY_UPSCALE_MODELS,
)

def comfy_generate(scene, prompts=None, use_last_sd_image=False):
    """Post to the API to generate a Stable Diffusion image and then process it"""

    props = scene.air_props
    comfyui_props = scene.comfyui_props

    # get the prompt if we haven't been given one
    if not prompts:
        if props.use_animated_prompts:
            print(Fore.LIGHTGREEN_EX + "USING ANIMATED PROMPTS" + Fore.RESET)
            prompt, negative_prompt = validate_and_process_animated_prompt_text_for_single_frame(
                scene, scene.frame_current)
            if not prompt:
                return False
        else:
            print(Fore.LIGHTGREEN_EX + "USING SINGLE PROMPT" + Fore.RESET)
            prompt = get_full_prompt(scene)
            negative_prompt = props.negative_prompt_text.strip()
    else:
        print(Fore.LIGHTGREEN_EX + "USING PROMPTS" + Fore.RESET)
        prompt = prompts["prompt"]
        negative_prompt = prompts["negative_prompt"]

    # validate the parameters we will send
    if not validate_params(scene, prompt):
        print(Fore.RED + "COULD NOT VALIDATE PARAMS" + Fore.RESET)
        return False

    # generate a new seed, if we want a random one
    generate_new_random_seed(scene)

    # prepare the output filenames
    before_output_filename_prefix = utils.get_image_filename(
        scene, prompt, negative_prompt, "-1-before")

    after_output_filename_prefix = utils.get_image_filename(
        scene, prompt, negative_prompt, "-2-after")

    animation_output_filename_prefix = "ai-render-"

    # if we want to use the last SD image, try loading it now
    if use_last_sd_image:
        if not props.last_generated_image_filename:
            return handle_error("Couldn't find the last Stable Diffusion image", "last_generated_image_filename")
        try:
            img_file = open(props.last_generated_image_filename, 'rb')
        except:
            return handle_error("Couldn't load the last Stable Diffusion image. It's probably been deleted or moved. You'll need to restore it or render a new image.", "load_last_generated_image")
    else:
        # else, use the rendered image...

        # save the rendered image and then read it back in
        temp_input_file = save_render_to_file(scene, before_output_filename_prefix)

        if not temp_input_file:
            print(Fore.RED + "Couldn't save the rendered image to a temp file" + Fore.RESET)
            return False

        img_file = open(temp_input_file, 'rb')

        # autosave the before image, if we want that, and we're not rendering an animation
        if (
            props.do_autosave_before_images
            and props.autosave_image_path
            and not props.is_rendering_animation
            and not props.is_rendering_animation_manually
        ):
            print(Fore.YELLOW + "Autosaving before image")
            save_before_image(scene, before_output_filename_prefix)

    # prepare data for the API request
    params = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "seed": props.seed,
        "sampler": props.sampler,
        "steps": props.steps,
        "cfg_scale": props.cfg_scale,
        "width": utils.get_output_width(scene),
        "height": utils.get_output_height(scene),
        "image_similarity": props.image_similarity,
    }

    # send to whichever API we're using
    start_time = time.time()

    print(Fore.YELLOW + "Using ComfyUI API" + Fore.RESET)
    generated_image_file = comfyui_api.generate(
        params,
        img_file,
        after_output_filename_prefix,
        props,
        comfyui_props)

    # if we didn't get a successful image, stop here (an error will have been handled by the api function)
    if not generated_image_file:
        return False

    # autosave the after image, if we should
    if utils.should_autosave_after_image(props):

        print(Fore.YELLOW + "Autosaving after image")
        generated_image_file = save_after_image(
            scene, after_output_filename_prefix, generated_image_file)

        if not generated_image_file:
            return False

    # store this image filename as the last generated image
    props.last_generated_image_filename = generated_image_file

    # if we're rendering an animation manually, save the image to the animation output path
    if props.is_rendering_animation_manually:

        print(Fore.YELLOW + "Rendering animation manually")
        generated_image_file = save_animation_image(
            scene, animation_output_filename_prefix, generated_image_file)

        if not generated_image_file:
            return False

    # load the image into our scene
    try:
        img = load_image(generated_image_file, after_output_filename_prefix)
    except:
        return handle_error("Couldn't load the image from Stable Diffusion", "load_sd_image")

    try:
        # View the image in the Render Result view
        utils.view_sd_in_render_view(img, scene)
    except:
        return handle_error("Couldn't switch the view to the image from Stable Diffusion", "view_sd_image")

    # return success
    return True


class AIR_OT_open_comfyui_input_folder(bpy.types.Operator):
    "Open the input folder in the windows explorer or macOSfinder"
    bl_idname = "ai_render.open_comfyui_input_folder"
    bl_label = "Open Output Folder"

    def execute(self, context):
        input_folder = comfyui_api.get_comfyui_input_path(context)
        print(f"Opening folder: {input_folder}")

        if platform.system() == "Windows":
            os.system(f"explorer '{input_folder}'")
        elif platform.system() == "Darwin":
            os.system(f"open '{input_folder}'")

        return {'FINISHED'}


class AIR_OT_open_comfyui_output_folder(bpy.types.Operator):
    "Open the output folder in the windows explorer or macOSfinder"
    bl_idname = "ai_render.open_comfyui_output_folder"
    bl_label = "Open Output Folder"

    def execute(self, context):
        output_folder = comfyui_api.get_comfyui_output_path(context)
        print(f"Opening folder: {output_folder}")

        if platform.system() == "Windows":
            os.system(f"explorer '{output_folder}'")
        elif platform.system() == "Darwin":
            os.system(f"open '{output_folder}'")

        return {'FINISHED'}


class AIR_OT_open_comfyui_workflows_folder(bpy.types.Operator):
    "Open the workflow folder in the windows explorer or macOSfinder"
    bl_idname = "ai_render.open_comfyui_workflows_folder"
    bl_label = "Open Workflow Folder"

    def execute(self, context):
        workflow_folder = utils.get_addon_preferences().comfyui_workflows_path
        print(f"Opening folder: {workflow_folder}")

        if platform.system() == "Windows":
            os.system(f"explorer '{workflow_folder}'")
        elif platform.system() == "Darwin":
            os.system(f"open '{workflow_folder}'")

        return {'FINISHED'}


class AIR_OT_convert_path_in_workflow(bpy.types.Operator):
    bl_idname = "ai_render.convert_path_in_workflow"
    bl_label = "Convert Path in Workflow"
    bl_description = "Use this operator to change the slashes to the ones your mac or windows uses"

    def invoke(self, context, event):
        # Ask for confirmation
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        comfyui_api.convert_path_in_workflow(context)
        return {'FINISHED'}


class AIR_OT_ReloadWorkflow(bpy.types.Operator):
    bl_idname = "ai_render.reload_workflow"
    bl_label = "Update Workflow Enum"
    bl_description = "Save the selected workflow to the scene properties"

    def execute(self, context):
        print(Fore.GREEN + "UPDATING WORKFLOW ENUM..." + Fore.RESET)

        # Ensure the compositor nodes are available (DISABLED FOR NOW)
        comfyui_api.ensure_compositor_nodes(context)

        global COMFY_WORKFLOWS
        COMFY_WORKFLOWS.clear()
        workflows_list = comfyui_api.get_workflows(context)  # Ensure comfyui_api is available
        for workflow in workflows_list:
           COMFY_WORKFLOWS.append(workflow)

        # Trigger the update of the update of the enums before setting the new values
        bpy.ops.ai_render.update_ckpt_enum()
        bpy.ops.ai_render.update_sampler_enum()
        bpy.ops.ai_render.update_lora_enum()
        bpy.ops.ai_render.update_upscale_model_enum()
        bpy.ops.ai_render.update_control_net_enum()
        bpy.ops.ai_render.update_upscale_model_enum()

        # Trigger property creation from the selected workflow
        create_props_from_workflow(context.scene.comfyui_props, context)

        return {'FINISHED'}


class AIR_OT_UpdateSDModelEnum(bpy.types.Operator):
    bl_idname = "ai_render.update_ckpt_enum"
    bl_label = "Update Model Enum"
    bl_description = "Update the model enum with the available models"

    def execute(self, context):
        print(Fore.MAGENTA + "\nUPDATING SD MODEL ENUM..." + Fore.RESET)
        global COMFY_CKPT_MODELS
        COMFY_CKPT_MODELS.clear()
        models_list = comfyui_api.get_ckpt_models(context)
        for model in models_list:
            COMFY_CKPT_MODELS.append(model)

        return {'FINISHED'}


class AIR_OT_UpdateLoraModelEnum(bpy.types.Operator):
    bl_idname = "ai_render.update_lora_enum"
    bl_label = "Update Model Enum"
    bl_description = "Update the model enum with the available models"

    def execute(self, context):
        print(Fore.YELLOW + "\nUPDATING LORA MODEL ENUM..." + Fore.RESET)
        global COMFY_LORA_MODELS
        COMFY_LORA_MODELS.clear()
        models_list = comfyui_api.get_lora_models(context)
        for model in models_list:
            COMFY_LORA_MODELS.append(model)

        return {'FINISHED'}


class AIR_OT_UpdateSamplerEnum(bpy.types.Operator):
    bl_idname = "ai_render.update_sampler_enum"
    bl_label = "Update Sampler Enum"
    bl_description = "Update the sampler enum with the available samplers"

    def execute(self, context):
        print(Fore.GREEN + "\nUPDATING SAMPLER ENUM..." + Fore.RESET)
        global COMFY_SAMPLERS
        COMFY_SAMPLERS.clear()
        samplers_list = comfyui_api.get_comfy_samplers(context)
        for sampler in samplers_list:
            COMFY_SAMPLERS.append(sampler)

        return {'FINISHED'}


class AIR_OT_UpdateControlNetEnum(bpy.types.Operator):
    bl_idname = "ai_render.update_control_net_enum"
    bl_label = "Update Control Net Enum"
    bl_description = "Update the control net enum with the available control nets"

    def execute(self, context):
        print(Fore.BLUE + "\nUPDATING CONTROL NET ENUM..." + Fore.RESET)
        global COMFY_CONTROL_NETS
        COMFY_CONTROL_NETS.clear()
        control_nets_list = comfyui_api.get_control_nets(context)
        for control_net in control_nets_list:
            COMFY_CONTROL_NETS.append(control_net)

        return {'FINISHED'}


class AIR_OT_UpdateUpscaleModelEnum(bpy.types.Operator):
    bl_idname = "ai_render.update_upscale_model_enum"
    bl_label = "Update Upscale Model Enum"
    bl_description = "Update the upscale model enum with the available models"

    def execute(self, context):
        print(Fore.CYAN + "\nUPDATING UPSCALE MODEL ENUM..." + Fore.RESET)
        global COMFY_UPSCALE_MODELS
        COMFY_UPSCALE_MODELS.clear()
        upscale_models_list = comfyui_api.get_upscale_models(context)
        for upscale_model in upscale_models_list:
            COMFY_UPSCALE_MODELS.append(upscale_model)

        return {'FINISHED'}


class AIR_OT_SetComfyAsBackend(bpy.types.Operator):
    bl_idname = "ai_render.set_comfy_as_backend"
    bl_label = "Set ComfyUI as Backend"

    def execute(self, context):
        # Set the Adddon Preference AIR_Preferences.sd_backend
        utils.get_addon_preferences(context).sd_backend = "comfyui"
        utils.get_addon_preferences(context).local_sd_url = "http://127.0.0.1:8188"
        utils.get_addon_preferences(context).is_local_sd_enabled = True
        utils.get_addon_preferences(context).comfyui_path = "E:\\COMFY\\ComfyUI-robe"

        return {'FINISHED'}


classes = [
    AIR_OT_UpdateSDModelEnum,
    AIR_OT_UpdateLoraModelEnum,
    AIR_OT_UpdateSamplerEnum,
    AIR_OT_UpdateControlNetEnum,
    AIR_OT_UpdateUpscaleModelEnum,
    AIR_OT_open_comfyui_input_folder,
    AIR_OT_open_comfyui_output_folder,
    AIR_OT_open_comfyui_workflows_folder,
    AIR_OT_convert_path_in_workflow,
    AIR_OT_ReloadWorkflow,
    AIR_OT_SetComfyAsBackend
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
