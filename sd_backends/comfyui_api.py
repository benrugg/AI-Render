import os
import bpy
import base64
import requests
import json
import pprint
import platform
import numpy as np
from time import sleep
from .. import Fore

from .. import (
    config,
    operators,
    utils,
)

LOG_PROPS = False
LOG_WORKFLOW = False
LOG_PARAMS = False
LOG_MAPPED_WORKFLOW = False

LOG_REQUEST = False
LOG_RESPONSE = False
LOG_LONG_RESPONSE = False

LOG_UPLOAD_IMAGE = True
LOG_DOWNLOAD_IMAGE = True

LOG_MODEL_RESPONSE = False

PARAM_TO_WORKFLOW = {
    "prompt": {
        "class_type": "CLIPTextEncode",
        "input_key": "text",
        "meta_title": "positive"
    },
    "negative_prompt": {
        "class_type": "CLIPTextEncode",
        "input_key": "text",
        "meta_title": "negative"
    },
    "color_image": {
        "class_type": "LoadImage",
        "input_key": "image",
        "meta_title": "color"
    },
    "depth_image": {
        "class_type": "LoadImage",
        "input_key": "image",
        "meta_title": "depth"
    },
    "normal_image": {
        "class_type": "LoadImage",
        "input_key": "image",
        "meta_title": "normal"
    },
    "openpose_body_image": {
        "class_type": "LoadImage",
        "input_key": "image",
        "meta_title": "openpose_body"
    },
}


# CORE FUNCTIONS:
def load_workflow(context, workflow_file) -> dict:
    """ Given the context and the workflow file name, load the workflow JSON. and output it as a dictionary."""

    workflow_path = os.path.join(get_workflows_path(context), workflow_file)
    try:
        with open(workflow_path, 'r') as file:
            return json.load(file)
    except:
        return operators.handle_error(f"Couldn't load the workflow file: {workflow_file}.", "workflow_file_not_found")


def upload_image(img_file, subfolder: str):
    """Upload the image to the input folder of ComfyUI"""

    # Get the image path from the name of _io.BufferedReader
    image_path = img_file.name

    if LOG_UPLOAD_IMAGE:
        print(Fore.WHITE + f"\nLOG IMAGE PATH:" + Fore.RESET)
        print(image_path)

    # prepare the data
    server_url = get_server_url("/upload/image")
    headers = create_headers()
    data = {"subfolder": subfolder, "type": "input"}
    files = {'image': (os.path.basename(image_path), open(image_path, 'rb'))}

    if LOG_REQUEST:
        print(Fore.WHITE + "\nREQUEST TO: " + server_url)

    # send the API request
    try:
        resp = requests.post(server_url, files=files, data=data, headers=headers)
    except requests.exceptions.ConnectionError:
        return operators.handle_error(f"The ComfyUI Server cannot be found. It's either not running, or it's running at a different location than what you specified in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_not_found")
    except requests.exceptions.MissingSchema:
        return operators.handle_error(f"The url for your local Stable Diffusion server is invalid. Please set it correctly in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_url_invalid")
    except requests.exceptions.ReadTimeout:
        return operators.handle_error("The local Stable Diffusion server timed out. Set a longer timeout in AI Render preferences, or use a smaller image size.", "timeout")

    # if LOG_RESPONSE:
        # print(Fore.WHITE + "\nUPLOAD IMAGE RESPONSE:" + Fore.RESET)
        # pprint.pp(resp.content)

    img_file.close()

    # return the image name
    return resp.json().get("name")


def find_node_by_title(workflow: dict,
                       class_type: str,
                       meta_title: str):
    """Find the node key based on class_type and meta_title."""

    for key, value in workflow.items():
        if value['class_type'] == class_type:
            if value.get('_meta', {}).get('title') == meta_title:
                return key

    return None


def map_param_to_workflow(params, workflow):
    """Map parameters to the appropriate nodes in the workflow JSON."""

    for param_name, param_info in PARAM_TO_WORKFLOW.items():
        # Check if the parameter is in the params dictionary
        if param_name in params:
            class_type = param_info["class_type"]
            input_key = param_info["input_key"]
            meta_title = param_info["meta_title"]

            # Find the node by title in the workflow
            node_key = find_node_by_title(workflow, class_type, meta_title)

            # If the node is found, update the input_key with the parameter's value
            if node_key is not None:
                workflow[node_key]["inputs"][input_key] = params[param_name]

    return workflow


def map_params(params, workflow):
    """Map the parameters to the workflow."""

    if LOG_PARAMS:
        print(Fore.WHITE + "\nLOG PARAMS:" + Fore.RESET)
        pprint.pp(params)

    mapped_workflow = map_param_to_workflow(params, workflow)

    return mapped_workflow


def map_comfy_props(comfyui_props, workflow):
    """Map the ComfyUI properties to the workflow."""

    updated_workflow = workflow

    if (LOG_PROPS):
        print(Fore.WHITE + "\nLOG COMFYUI PROPS:" + Fore.RESET)

    for prop in comfyui_props.bl_rna.properties.items():
        if prop[1].type == 'COLLECTION':
            for item in getattr(comfyui_props, prop[0]):
                node_key = item.name
                for sub_prop in item.bl_rna.properties.items():
                    # Access the updated workflow at node_key and change in the inputs only if key exists
                    if sub_prop[0] in updated_workflow[node_key]["inputs"]:
                        updated_workflow[node_key]["inputs"][sub_prop[0]] = getattr(
                            item, sub_prop[0])
                        if (LOG_PROPS):
                            print(
                            f"Updated workflow at node_key: {node_key} with {sub_prop[0]}: {getattr(item, sub_prop[0])}")
                print()

    if LOG_MAPPED_WORKFLOW:
        print(Fore.WHITE + "\nLOG_MAPPED_WORKFLOW:" + Fore.RESET)
        print(type(updated_workflow))
        pprint.pp(updated_workflow)

    # Save mapped json to local file
    workflow_path = utils.get_addon_preferences().comfyui_workflows_path

    workflow_file_name = comfyui_props.comfy_current_workflow[:-5] + '_mapped.json'

    # Add _mapped to the filename only and save it for debugging
    workflow_file_path = workflow_path + '/../' + workflow_file_name

    with open(workflow_file_path, 'w') as f:
        json.dump(updated_workflow, f, indent=4)

    return workflow


def generate(params, img_file, filename_prefix, props, comfyui_props):

    if LOG_PROPS:
        print(Fore.WHITE + "\nLOG PROPS:" + Fore.RESET)
        pprint.pp(props)
        pprint.pp(comfyui_props)

    # Load the workflow
    selected_workflow = load_workflow(bpy.context, comfyui_props.comfyui_workflow)

    if LOG_WORKFLOW:
        print(f"{Fore.LIGHTWHITE_EX}\nLOG WORKFLOW: {Fore.RESET}{(bpy.context)}")
        pprint.pp(selected_workflow)

    # get the frame number for the filename
    frame_number = bpy.context.scene.frame_current

    # format the frame number to 4 digits
    frame_number = str(frame_number).zfill(4)

    # Create the paths
    color_image_path = f"{get_color_file_input_path(bpy.context)}Image{frame_number}.png"
    depth_image_path = f"{get_depth_file_input_path(bpy.context)}Image{frame_number}.png"
    normal_image_path = f"{get_normal_file_input_path(bpy.context)}Image{frame_number}.png"
    openpose_body_image_path = f"{get_openpose_body_file_input_path(bpy.context)}Image{frame_number}.png"

    # Add the paths to the params
    params['color_image'] = color_image_path
    params['depth_image'] = depth_image_path
    params['normal_image'] = normal_image_path
    params['openpose_body_image'] = openpose_body_image_path

    # Create Color Image from pixels data
    if (bpy.data.images['Viewer Node'].pixels):

        pixels = bpy.data.images['Viewer Node'].pixels
        print(len(pixels)) # size is always width * height * 4 (rgba)

        # copy buffer to numpy array for faster manipulation
        arr = np.array(pixels[:])
        print('pixels max: %f; pixels min: %f' % (arr.max(), arr.min()))

        # Save a temp image from the pixels
        # temp_image = bpy.data.images.new(name="temp_image", width=512, height=512, alpha=True, float_buffer=False)
        # temp_image.pixels = pixels
        # temp_image.file_format = "PNG"
        # temp_image.save_render(filepath=f"{get_color_file_input_path(bpy.context)}temp_image.png")

        # # Upload the image to the input folder of ComfyUI
        # upload_image(temp_image, "color")

    # map the params to the ComfyUI nodes
    mapped_workflow = map_params(params, selected_workflow)

    # Add additional comfyUI param mappings here
    updated_workflow = map_comfy_props(comfyui_props, mapped_workflow)

    data = {"prompt": updated_workflow}

    # prepare the server url
    try:
        server_url = get_server_url("/prompt")
    except:
        return operators.handle_error(f"You need to specify a location for the local Stable Diffusion server in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_url_missing")

    # send the API request
    response = do_post(url=server_url, data=data)

    if response == False:
        return False

    # Check if the response is successful and not containing node_errors
    if response.status_code == 200 and not response.json().get("node_errors"):
        return handle_success(response, filename_prefix)
    else:
        return handle_error(response)


def handle_success(response, filename_prefix):

    # Get the prompt_id from the response
    try:
        response_obj = response.json()
        prompt_id = response_obj.get("prompt_id")

        if LOG_RESPONSE:
            print(Fore.WHITE + "\nPROMPT RESPONSE: " + Fore.RESET)
            print(json.dumps(response_obj, indent=2))
            print(Fore.LIGHTWHITE_EX + "\nPROMPT ID: " + Fore.RESET + prompt_id)

    except:

        print("ComfyUI response content: ")
        print(response.content)
        return operators.handle_error("Received an unexpected response from the ComfyUI.", "unexpected_response")

    # Query the history with the prompt_id until the status.status_str is "success"
    status_completed = None
    image_file_name = None
    server_url = get_server_url(f"/history/{prompt_id}")

    while not status_completed:
        if LOG_REQUEST:
            print(Fore.WHITE + "\nGET REQUEST TO: " + server_url)

        response = requests.get(server_url, headers=create_headers(), timeout=utils.local_sd_timeout())
        response_obj = response.json()

        # Wait 1 second before querying the history again
        sleep(1)

        if response.status_code == 200:
            # Access the status object in the response through the prompt_id key, for exmaple:
            # {"b8c4f253-05e1-44e1-9706-1c9b4456d995": { "status": { "status_str": "success", }}}
            status = response_obj.get(prompt_id, {}).get("status", {})
            status_completed = status.get("status_str") == "success"

            if status_completed:

                if LOG_DOWNLOAD_IMAGE:
                    print(Fore.LIGHTWHITE_EX + "STATUS: " + Fore.RESET + status.get("status_str"))
                if LOG_RESPONSE:
                    print(Fore.WHITE + "\nHISTORY RESPONSE: " + Fore.RESET)
                if LOG_LONG_RESPONSE:
                    print(json.dumps(response_obj, indent=2))
                else:
                    print("LONG RESPONSE LOGGING IS DISABLED")

                # Get the NODE NUMBER of the SaveImage node

                save_image_node = None
                for item in response_obj[prompt_id]["prompt"]:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if value.get("class_type") == "SaveImage":
                                save_image_node = key
                                break

                if LOG_DOWNLOAD_IMAGE:
                    print(Fore.LIGHTWHITE_EX + "SAVE IMAGE NODE_NUMBER: " + Fore.RESET + save_image_node)

                image_file_name = response_obj[prompt_id]["outputs"][save_image_node]["images"][0]["filename"]

                if LOG_DOWNLOAD_IMAGE:
                    print(Fore.LIGHTWHITE_EX + "SAVE IMAGE FILE NAME: " + Fore.RESET + image_file_name)  # ComfyUI_00057_.png
                break
        else:
            return handle_error(response)

    # Query the view endpoint with the image_file_name to get the image
    server_url = get_server_url(f"/view?filename={image_file_name}")

    if LOG_DOWNLOAD_IMAGE:
        print(Fore.WHITE + "\nREQUEST TO: " + server_url)

    response = requests.get(server_url, headers=create_headers(), timeout=utils.local_sd_timeout())

    if response.status_code != 200:
        return handle_error(response)

    # Assuming the server returns the raw image data, we use response.content
    img_binary = response.content

    # create a temp file
    try:
        output_file = utils.create_temp_file(filename_prefix + "-")
    except:
        return operators.handle_error("Couldn't create a temp file to save image.", "temp_file")

    # save the image to the temp file
    try:
        with open(output_file, 'wb') as file:
            file.write(img_binary)

    except:
        return operators.handle_error("Couldn't write to temp file.", "temp_file_write")

    # return the temp file
    return output_file


def handle_error(response):
    if response.status_code == 404:

        try:
            response_obj = response.json()
            return operators.handle_error(f"An error occurred in the ComfyUI server. Full server response: {json.dumps(response_obj)}", "unknown_error")
        except:
            return operators.handle_error(f"It looks like the ComfyUI server is running, but it's not in API mode.")

    else:
        print(Fore.RED + "ERROR DETAILS:")
        pprint.pp(response.json())
        print(Fore.RESET)
        return operators.handle_error(f"AN ERROR occurred in the ComfyUI server.\n {response.json()}", "unknown_error_response")


# PRIVATE SUPPORT FUNCTIONS:
def create_headers():
    return {
        "User-Agent": f"Blender/{bpy.app.version_string}",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
    }


def get_server_url(path):
    base_url = utils.local_sd_url().rstrip("/").strip()
    if not base_url:
        raise Exception("Couldn't get the Automatic1111 server url")
    else:
        return base_url + path


def do_get(url):
    if LOG_REQUEST:
        print(Fore.WHITE + "\nGET REQUEST TO: " + url)
    try:
        return requests.get(url, headers=create_headers(), timeout=utils.local_sd_timeout())
    except requests.exceptions.ConnectionError:
        return operators.handle_error(f"The ComfyUI Server cannot be found. It's either not running, or it's running at a different location than what you specified in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_not_found")
    except requests.exceptions.MissingSchema:
        return operators.handle_error(f"The url for your local Stable Diffusion server is invalid. Please set it correctly in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_url_invalid")
    except requests.exceptions.ReadTimeout:
        return operators.handle_error("The local Stable Diffusion server timed out. Set a longer timeout in AI Render preferences, or use a smaller image size.", "timeout")


def do_post(url, data):
    if LOG_REQUEST:
        print(Fore.WHITE + "\nPOST REQUEST TO: " + url)

    try:
        return requests.post(url, json=data, headers=create_headers(), timeout=utils.local_sd_timeout())
    except requests.exceptions.ConnectionError:
        return operators.handle_error(f"The ComfyUI Server cannot be found. It's either not running, or it's running at a different location than what you specified in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_not_found")
    except requests.exceptions.MissingSchema:
        return operators.handle_error(f"The url for your local Stable Diffusion server is invalid. Please set it correctly in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_url_invalid")
    except requests.exceptions.ReadTimeout:
        return operators.handle_error("The local Stable Diffusion server timed out. Set a longer timeout in AI Render preferences, or use a smaller image size.", "timeout")


# SUPPORT FUNCTIONS:
def get_workflows_path(context):
    return utils.get_addon_preferences().comfyui_workflows_path


COMFY_WORKFLOWS = []


def create_workflows_enum(self, context):
    enum_items = []
    for i, workflow in enumerate(COMFY_WORKFLOWS):
        enum_items.append((workflow, workflow, "", i))
    return enum_items


def create_workflow_enum_realtime(self, context):
    workflows_path = get_workflows_path(bpy.context)
    workflow_list = [f for f in os.listdir(workflows_path) if os.path.isfile(
        os.path.join(workflows_path, f)) and f.endswith(".json")]

    enum_items = []
    for i, workflow in enumerate(workflow_list):
        enum_items.append((workflow, workflow, "", i))
    return enum_items


def get_workflows(context):
    workflows_path = get_workflows_path(bpy.context)
    workflow_list = [f for f in os.listdir(workflows_path) if os.path.isfile(
        os.path.join(workflows_path, f)) and f.endswith(".json")]

    return workflow_list


def convert_path_in_workflow(context):
    """ Convert "\\" to "/" and "/" to "\\" in the current json workflow overwriting it"""

    current_workflow = context.scene.comfyui_props.comfy_current_workflow
    current_workflow_path = get_workflows_path(
        context) + "/" + current_workflow

    print(Fore.WHITE + "\nCURRENT WORKFLOW PATH:" + Fore.RESET)
    print(current_workflow_path)

    if current_workflow is None or current_workflow == "":
        print(Fore.RED + "Please select a workflow first")
        return

    if platform.system() == "Darwin":
        print(Fore.GREEN + "Changing Paths to '/'")
        with open(current_workflow_path, "r") as f:
            lines = f.readlines()
        with open(current_workflow_path, "w") as f:
            for line in lines:
                line = line.replace('\\\\', '/') if '\\\\' in line else line
                f.write(line)
                print(Fore.GREEN + "Updated:" + line[:-1]) if '/' in line else None

    elif platform.system() == "Windows":
        print(Fore.GREEN + "Changing Paths to '\\\\'")
        with open(current_workflow_path, "r") as f:
            lines = f.readlines()
        with open(current_workflow_path, "w") as f:
            for line in lines:
                line = line.replace('/', '\\\\') if '/' in line else line
                f.write(line)
                print(Fore.GREEN + "Updated:" + line[:-1]) if '\\\\' in line else None
    return


COMFY_CKPT_MODELS = []


def create_models_enum(self, context):
    enum_items = []
    for i, model in enumerate(COMFY_CKPT_MODELS):
        enum_items.append((model, model, "", i))
    return enum_items


def get_ckpt_models(context):
    """ GET /object_info/CheckpointLoaderSimple endpoint
    to get the available models"""

    # prepare the server url
    try:
        server_url = get_server_url("/object_info/CheckpointLoaderSimple")
    except:
        return handle_error("It seems that you local ComfyUI server is not running", "local_server_url_missing")

    # send the API request
    response = do_get(server_url)

    if response == False:
        return None

    models_list = []

    # handle the response
    if response.status_code == 200:

        models_list = response.json()["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]

        if LOG_MODEL_RESPONSE:
            print(Fore.MAGENTA + "\nMODELS RESPONSE: " + Fore.RESET)
            if LOG_LONG_RESPONSE:
                print(response.json())
            else:
                print("LONG RESPONSE LOGGING IS DISABLED")

    else:
        return handle_error(response)

    return models_list


COMFY_LORA_MODELS = []


def create_lora_enum(self, context):
    enum_items = []
    for i, model in enumerate(COMFY_LORA_MODELS):
        enum_items.append((model, model, "", i))
    return enum_items


def get_lora_models(context):
    """ GET /object_info/LoraLoader endpoint """

    # prepare the server url
    try:
        server_url = get_server_url("/object_info/LoraLoader")
    except:
        return handle_error("It seems that you local ComfyUI server is not running", "local_server_url_missing")

    # send the API request
    response = do_get(server_url)

    if response == False:
        return None

    models_list = []

    # handle the response
    if response.status_code == 200:

        models_list = response.json()["LoraLoader"]["input"]["required"]["lora_name"][0]

        if LOG_MODEL_RESPONSE:
            print(Fore.YELLOW + "\nMODELS RESPONSE: " + Fore.RESET)
            if LOG_LONG_RESPONSE:
                print(response.json())
            else:
                print("LONG RESPONSE LOGGING IS DISABLED")

    else:
        return handle_error(response)

    return models_list


COMFY_SAMPLERS = []


def create_comfy_sampler_enum(self, context):
    enum_items = []
    for i, sampler in enumerate(COMFY_SAMPLERS):
        enum_items.append((sampler, sampler, "", i))
    return enum_items


def get_comfy_samplers(context):
    """ GET /object_info/KSampler endpoint to get the available models"""

    # prepare the server url
    try:
        server_url = get_server_url("/object_info/KSampler")
    except:
        return handle_error("It seems that you local ComfyUI server is not running", "local_server_url_missing")

    # send the API request
    response = do_get(server_url)

    if response == False:
        return None

    samplers_list = []

    # handle the response
    if response.status_code == 200:

        samplers_list = response.json()["KSampler"]["input"]["required"]["sampler_name"][0]

        if LOG_MODEL_RESPONSE:
            print(Fore.MAGENTA + "\nSAMPLERS RESPONSE: " + Fore.RESET)
            if LOG_LONG_RESPONSE:
                print(response.json())
            else:
                print("LONG RESPONSE LOGGING IS DISABLED")

    else:
        return handle_error(response)

    return samplers_list


def get_samplers():
    # Not using this in Comfy, it's here only for compatibility with others backends
    return [
        ('default', 'default', '', 20),
    ]


def default_sampler():
    # Not using this in Comfy, it's here only for compatibility with others backends
    return 'default'


COMFY_SCHEDULERS = []


def create_comfy_scheduler_enum(self, context):
    enum_items = []
    for i, scheduler in enumerate(COMFY_SCHEDULERS):
        enum_items.append((scheduler, scheduler, "", i))
    return enum_items


def get_comfy_schedulers(context):
    """ GET /object_info/KSampler endpoint to get the available models"""

    # prepare the server url
    try:
        server_url = get_server_url("/object_info/KSampler")
    except:
        return handle_error("It seems that you local ComfyUI server is not running", "local_server_url_missing")

    # send the API request
    response = do_get(server_url)

    if response == False:
        return None

    scheduler_list = []

    # handle the response
    if response.status_code == 200:

        scheduler_list = response.json()["KSampler"]["input"]["required"]["scheduler"][0]

        if LOG_MODEL_RESPONSE:
            print(Fore.MAGENTA + "\nSCHEDULERS RESPONSE: " + Fore.RESET)
            if LOG_LONG_RESPONSE:
                print(response.json())
            else:
                print("LONG RESPONSE LOGGING IS DISABLED")

    else:
        return handle_error(response)

    return scheduler_list


COMFY_CONTROL_NETS = []


def create_control_net_enum(self, context):
    enum_items = []
    for i, control_net in enumerate(COMFY_CONTROL_NETS):
        enum_items.append((control_net, control_net, "", i))
    return enum_items


def get_control_nets(context):
    """ GET /object_info/ControlNetLoader endpoint """

    # prepare the server url
    try:
        server_url = get_server_url("/object_info/ControlNetLoader")
    except:
        return handle_error("It seems that you local ComfyUI server is not running", "local_server_url_missing")

    # send the API request
    response = do_get(server_url)

    if response == False:
        return None

    control_nets_list = []

    # handle the response
    if response.status_code == 200:

        control_nets_list = response.json()["ControlNetLoader"]["input"]["required"]["control_net_name"][0]

        if LOG_MODEL_RESPONSE:
            print(Fore.BLUE + "\nCONTROL NETS RESPONSE: " + Fore.RESET)
            if LOG_LONG_RESPONSE:
                print(response.json())
            else:
                print("LONG RESPONSE LOGGING IS DISABLED")

    else:
        return handle_error(response)

    return control_nets_list


COMFY_UPSCALE_MODELS = []


def create_upscale_model_enum(self, context):
    enum_items = []
    for i, model in enumerate(COMFY_UPSCALE_MODELS):
        enum_items.append((model, model, "", i))
    return enum_items


def get_upscale_models(context):
    """ GET /object_info/UpscaleModelLoader endpoint """

    # prepare the server url
    try:
        server_url = get_server_url("/object_info/UpscaleModelLoader")
    except:
        return handle_error("It seems that you local ComfyUI server is not running", "local_server_url_missing")

    # send the API request
    response = do_get(server_url)

    if response == False:
        return None

    upscale_models_list = []

    # handle the response
    if response.status_code == 200:

        upscale_models_list = response.json()["UpscaleModelLoader"]["input"]["required"]["model_name"][0]

        if LOG_MODEL_RESPONSE:
            print(Fore.CYAN + "\nUPSCALE MODELS RESPONSE: " + Fore.RESET)
            if LOG_LONG_RESPONSE:
                print(response.json())
            else:
                print("LONG RESPONSE LOGGING IS DISABLED")

    else:
        return handle_error(response)

    return upscale_models_list


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

    print(Fore.RED + "ENSURE COMPOSITOR NODES" + Fore.RESET)

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
    NormalNodeGroup.inputs[1].default_value = 1.0
    NormalNodeGroup.location = (360, -170)
    NormalNodeGroup.width, NormalNodeGroup.height = 245, 100

    # node Color Ramp
    color_ramp = nodes.new("CompositorNodeValToRGB")
    color_ramp.name = "Color Ramp"
    color_ramp.color_ramp.color_mode = 'RGB'
    color_ramp.color_ramp.hue_interpolation = 'NEAR'
    color_ramp.color_ramp.interpolation = 'EASE'
    color_ramp.location = (360, 74)
    color_ramp.width, color_ramp.height = 245.0, 100.0

    # initialize color ramp elements
    color_ramp.color_ramp.elements.remove(color_ramp.color_ramp.elements[0])
    color_ramp_cre_0 = color_ramp.color_ramp.elements[0]
    color_ramp_cre_0.position = 0
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
    normal_file_output.base_path = get_normal_file_input_path(context)
    normal_file_output.location = (690, -7)
    normal_file_output.width, normal_file_output.height = 300.0, 100.0

    # node Render Layers
    render_layers = nodes.new("CompositorNodeRLayers")
    render_layers.label = "Render Layers"
    render_layers.name = "Render Layers"
    render_layers.layer = 'ViewLayer'
    render_layers.location = (3.5, 180)
    render_layers.width, render_layers.height = 240.0, 100.0

    # node Viewer
    viewer = nodes.new("CompositorNodeViewer")
    viewer.name = "Viewer"
    # viewer.center_x = 0.5  æ not compatible with 4.2.0 LTS
    # viewer.center_y = 0.5  æ not compatible with 4.2.0 LTS
    # viewer.tile_order = 'CENTEROUT'  æ not compatible with 4.2.0 LTS
    viewer.use_alpha = True

    # Alpha
    viewer.inputs[1].default_value = 1.0
    viewer.location = (370, 280)
    viewer.width, viewer.height = 235, 100.0

    # node Composite
    composite = nodes.new("CompositorNodeComposite")
    composite.label = "Composite"
    composite.name = "Composite"
    composite.use_alpha = True
    # Alpha
    composite.inputs[1].default_value = 1.0
    composite.location = (380, 400)
    composite.width, composite.height = 240.0, 100.0

    # node color_file_output
    color_file_output = nodes.new("CompositorNodeOutputFile")
    color_file_output.label = "Color"
    color_file_output.name = "color_file_output"
    color_file_output.active_input_index = 0
    color_file_output.base_path = get_color_file_input_path(context)
    color_file_output.location = (690, 240)
    color_file_output.width, color_file_output.height = 300.0, 100.0

    # node depth_file_output
    depth_file_output = nodes.new("CompositorNodeOutputFile")
    depth_file_output.label = "Depth"
    depth_file_output.name = "depth_file_output"
    depth_file_output.active_input_index = 0
    depth_file_output.base_path = get_depth_file_input_path(context)
    depth_file_output.location = (700, 120)
    depth_file_output.width, depth_file_output.height = 300.0, 100.0

    # if Openpose_body view layer exists
    if context.scene.view_layers.get("Openpose_body"):

        # node OpenPose_body file_output
        openpose_body_file_output = nodes.new("CompositorNodeOutputFile")
        openpose_body_file_output.label = "OpenPose_body"
        openpose_body_file_output.name = "OpenPose_body_file_output"
        openpose_body_file_output.active_input_index = 0
        openpose_body_file_output.base_path = get_openpose_body_file_input_path(context)
        openpose_body_file_output.location = (700, -260)
        openpose_body_file_output.width, openpose_body_file_output.height = 300.0, 100.0

        # node OpenPose Render Layers
        open_pose_render_layer = nodes.new("CompositorNodeRLayers")
        open_pose_render_layer.label = "OpenPose Render Layers"
        open_pose_render_layer.name = "OpenPose Render Layers"
        open_pose_render_layer.layer = 'Openpose_body'
        open_pose_render_layer.location = (3.5, -300)
        open_pose_render_layer.width, open_pose_render_layer.height = 240.0, 100.0

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

    if context.scene.view_layers.get("Openpose_body"):
        # open_pose_render_layer.Image -> openpose_body_file_output.Image
        links.new(open_pose_render_layer.outputs[0], openpose_body_file_output.inputs[0])

    # Deselect all nodes
    for node in nodes:
        node.select = False


# PATH FUNCTIONS:
def get_default_comfy_workflows_path():
    workflows_path = os.path.join(os.path.dirname(__file__), "comfyui", "workflows_api")
    return workflows_path


def get_comfyui_input_path(context):
    comfyui_path = utils.get_addon_preferences(context).comfyui_path
    return comfyui_path + "input/"


def get_comfyui_output_path(context):
    comfyui_path = utils.get_addon_preferences(context).comfyui_path
    return comfyui_path + "output/"


def get_color_file_input_path(context):
    return get_comfyui_input_path(context) + "color/"


def get_depth_file_input_path(context):
    return get_comfyui_input_path(context) + "depth/"


def get_normal_file_input_path(context):
    return get_comfyui_input_path(context) + "normal/"


def get_openpose_body_file_input_path(context):
    return get_comfyui_input_path(context) + "openpose_body/"


# AI RENDER
def get_upscaler_models(context):
    models = context.scene.air_props.automatic1111_available_upscaler_models

    if (not models):
        return []
    else:
        enum_list = []
        for item in models.split("||||"):
            enum_list.append((item, item, ""))
        return enum_list


def is_upscaler_model_list_loaded(context=None):
    return False  # In ComfyUI, the upscaler is managed by the nodes, so we don't need to load the list


def default_upscaler_model():
    return ''


def get_image_format():
    return 'PNG'


def supports_negative_prompts():
    return True


def supports_choosing_model():
    return False  # Setting to False, because we can select the model from the CheckpointLoaderSimple node


def supports_upscaling():
    return False  # In ComfyUI, the upscaler is managed by the nodes, so we don't need to load the list here


def supports_reloading_upscaler_models():
    return False


def supports_inpainting():
    return False


def supports_outpainting():
    return False


def min_image_size():
    return 128 * 128


def max_image_size():
    return 2048 * 2048


def max_upscaled_image_size():
    return 4096 * 4096


def is_using_sdxl_1024_model(props):
    # TODO: Use the actual model loaded in Automatic1111. For now, we're just
    # returning false, because that way the UI will allow the user to select
    # more image size options.
    return False
