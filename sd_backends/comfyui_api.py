import os
import bpy
import base64
import requests
import json
from time import sleep
from .. import (
    config,
    operators,
    utils,
)
import pprint
from colorama import Fore, Style, init

# Initialize Colorama
init()

# CORE FUNCTIONS:

def load_workflow(context, workflow_file):
    workflow_path = os.path.join(get_workflows_path(context), workflow_file)
    with open(workflow_path, 'r') as file:
        return json.load(file)


def get_active_workflow(context):
    return context.scene.air_props.comfyui_workflows


def upload_image(img_file):

    # Get the image path from _io.BufferedReader
    image_path = img_file.name
    # print("\nLOG IMAGE PATH:")
    # print(image_path)

    # Post the image to the /upload/image endpoint
    server_url = get_server_url("/upload/image")
    print(Fore.WHITE + "\nREQUEST TO: " + server_url)

    # prepare the data
    headers = create_headers()
    data = {"subfolder": "test", "type": "input"}
    files = {'image': (os.path.basename(image_path), open(image_path, 'rb'))}
    resp = requests.post(server_url, files=files, data=data, headers=headers)

    # print(Fore.WHITE + "\nUPLOAD IMAGE RESPONSE OBJECT:" + Fore.RESET)
    print(resp.content)
    # b'{"name": "ai-render-1712271170-cat-1-before-y939nzr0.png", "subfolder": "", "type": "input"}'

    # add a base 64 encoded image to the params
    # params["init_images"] = ["data:image/png;base64," + base64.b64encode(img_file.read()).decode()]
    # img_file.close()

    return resp.json()["subfolder"], resp.json()["name"]


def generate(params, img_file, filename_prefix, props):

    # Load the workflow
    workflow = load_workflow(bpy.context, get_active_workflow(bpy.context))
    print(f"{Fore.LIGHTWHITE_EX}\nLOG WORKFLOW: {Fore.RESET}{get_active_workflow(bpy.context)}")
    # pprint.pp(workflow)

    params["denoising_strength"] = round(1 - params["image_similarity"], 4)
    params["sampler_index"] = params["sampler"]

    # upload the image, get the subfolder and image name
    subfolder, img_name = upload_image(img_file)

    # Add the image path to the params
    params["init_images"] = [f"{subfolder}/{img_name}"]

    # map the params to the ComfyUI nodes
    json_obj = map_params(params, workflow)
    data = {"prompt": json_obj}

    # prepare the server url
    try:
        server_url = get_server_url("/prompt")
    except:
        return operators.handle_error(f"You need to specify a location for the local Stable Diffusion server in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_url_missing")

    # send the API request
    response = do_post(url=server_url, data=data)

    if response == False:
        return False

    # handle the response
    if response.status_code == 200:
        return handle_success(response, filename_prefix)
    else:
        return handle_error(response)


def handle_success(response, filename_prefix):

    # Get the prompt_id from the response
    try:
        response_obj = response.json()
        prompt_id = response_obj.get("prompt_id")

        # print(Fore.WHITE + "QUEUE PROMPT RESPONSE OBJECT: " + Fore.RESET)
        # print(json.dumps(response_obj, indent=2))
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
        # print(Fore.WHITE + "\nREQUEST TO: " + server_url)

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
                print(Fore.LIGHTWHITE_EX + "STATUS: " + Fore.RESET + status.get("status_str"))
                # print(Fore.WHITE + "\nHISTORY RESPONSE OBJECT: " + Fore.RESET)
                # print(json.dumps(response_obj, indent=2))

                # Get the NODE NUMBER of the SaveImage node
                save_image_node = None
                for item in response_obj[prompt_id]["prompt"]:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            # print(Fore.WHITE + "\nNODE NUMBER: " + Fore.RESET + key)
                            # print(Fore.WHITE + "\nNODE VALUE: " + Fore.RESET)
                            # print(json.dumps(value, indent=2))
                            if value.get("class_type") == "SaveImage":
                                save_image_node = key
                print(Fore.LIGHTWHITE_EX + "IMAGE NODE_NUMBER: " + Fore.RESET + save_image_node)

                image_file_name = response_obj[prompt_id]["outputs"][save_image_node]["images"][0]["filename"]
                print(Fore.LIGHTWHITE_EX + "IMAGE FILE NAME: " + Fore.RESET + image_file_name)  # ComfyUI_00057_.png
                break
        else:
            return handle_error(response)

    # Query the view endpoint with the image_file_name to get the image
    server_url = get_server_url(f"/view?filename={image_file_name}")
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
            if response_obj.get('detail') and response_obj['detail'] == "Not Found":
                return operators.handle_error(f"It looks like the Automatic1111 server is running, but it's not in API mode. [Get help]({config.HELP_WITH_AUTOMATIC1111_NOT_IN_API_MODE_URL})", "automatic1111_not_in_api_mode")
            elif response_obj.get('detail') and response_obj['detail'] == "Sampler not found":
                return operators.handle_error("The sampler you selected is not available on the Automatic1111 Stable Diffusion server. Please select a different sampler.", "invalid_sampler")
            else:
                return operators.handle_error(f"An error occurred in the ComfyUI server. Full server response: {json.dumps(response_obj)}", "unknown_error")
        except:
            return operators.handle_error(f"It looks like the Automatic1111 server is running, but it's not in API mode. [Get help]({config.HELP_WITH_AUTOMATIC1111_NOT_IN_API_MODE_URL})", "automatic1111_not_in_api_mode")

    else:
        print(Fore.GREEN + "ERROR DETAILS: " + Fore.RESET)
        print(json.dumps(response.json(), indent=2))
        return operators.handle_error(f"AN ERROR occurred in the ComfyUI server.", "unknown_error_response")


# PRIVATE SUPPORT FUNCTIONS:

def print_with_colors(json_dict):

    # Loop through all items in the data
    for key, value in json_dict.items():
        # Check if value is a dictionary and the class type is CLIPTextEncode
        if isinstance(value, dict) and value.get("class_type") == "CLIPTextEncode":
            # Check the _meta title for the color
            text_color = Fore.GREEN if value["_meta"]["title"] == "positive" else Fore.RED

            # Print the text value in the appropriate color
            print(text_color + value["inputs"]["text"])

    for key, value in json_dict.items():
        if isinstance(value, dict):
            # print(Fore.WHITE + f"{key}: {Fore.LIGHTWHITE_EX}")
            print_with_colors(value)
        else:
            if key in ['sampler', 'scheduler', 'denoising_strength', 'steps', 'seed', 'cfg_scale', 'denoise', 'sampler_name', 'cfg']:
                print(Fore.MAGENTA + f"{key}: {Fore.LIGHTMAGENTA_EX}{value}" + Fore.RESET)
            elif key in ['init_images', 'image']:
                print(Fore.YELLOW + f"{key}: {Fore.LIGHTYELLOW_EX}{value}" + Fore.RESET)
            elif key == 'prompt':
                print(Fore.GREEN + f"{key}: {Fore.LIGHTGREEN_EX}{value}" + Fore.RESET)
            elif key == 'negative_prompt':
                print(Fore.RED + f"{key}: {Fore.LIGHTRED_EX}{value}" + Fore.RESET)


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


def map_KSampler(params, json_obj):
    """Map the params to the KSampler node in the ComfyUI JSON object."""
    # TODO: Is not working if multiple KSampler nodes are present in the JSON object

    KSampler_Node = None

    for key, value in json_obj.items():
        if value['class_type'] == 'KSampler':
            KSampler_Node = key

            value['inputs']['seed'] = params['seed']
            value['inputs']['steps'] = params['steps']
            value['inputs']['cfg'] = params['cfg_scale']
            value['inputs']['sampler_name'] = params['sampler']
            value['inputs']['scheduler'] = params['scheduler']
            value['inputs']['denoise'] = params['denoising_strength']

    return json_obj, KSampler_Node


def map_prompts(params, json_obj):
    """Map the params to the positive and negative prompts in the ComfyUI JSON object."""

    # Is assuming that the positive and negative prompts are named 'positive' and 'negative' in the JSON object
    # "6": {
    #     "inputs": {
    #       "text": "positive",
    #       "clip": [
    #         "4",
    #         1
    #       ]
    #     },
    #     "class_type": "CLIPTextEncode",
    #     "_meta": {
    #       "title": "positive"
    #     }
    #   },

    Positive_Node = None
    Negative_Node = None

    for key, value in json_obj.items():
        if value['class_type'] == 'CLIPTextEncode':
            if value.get('_meta') and value['_meta'].get('title') == 'positive':
                Positive_Node = key
                value['inputs']['text'] = params['prompt']

            elif value.get('_meta') and value['_meta'].get('title') == 'negative':
                Negative_Node = key
                value['inputs']['text'] = params['negative_prompt']

    return json_obj, Positive_Node, Negative_Node


def map_init_image(params, json_obj):

    connected_image = None

    # Get the node number of the VAEEncode
    for key, value in json_obj.items():
        if value['class_type'] == 'VAEEncode':
            connected_image = value['inputs']['pixels'][0]

    for key, value in json_obj.items():
        if value['class_type'] == 'LoadImage':
            if key == connected_image:  # If the LoadImage is connected to the VAEEncode
                value['inputs']['image'] = params['init_images'][0]

    return json_obj, connected_image


def map_params(params, workflow):

    print("\nLOG PARAMS:")
    # pprint.pp(params)
    print_with_colors(params)

    # Map the params to the ComfyUI nodes
    workflow, KSampler = map_KSampler(params, workflow)
    workflow, positive, negative = map_prompts(params, workflow)
    workflow, connected_image = map_init_image(params, workflow)

    print("\nMAPPING COMFYUI NODES:")
    print(Fore.MAGENTA + "KSAMPLER: " + Fore.RESET + KSampler)
    print(Fore.GREEN + "POSITIVE PROMPT: " + Fore.RESET + positive)
    print(Fore.RED + "NEGATIVE PROMPT: " + Fore.RESET + negative)
    print(Fore.YELLOW + "IMAGE CONNECTED TO VAE ENCODER: " + Fore.RESET + connected_image)

    # Save mapped json to local file
    with open('sd_backends/comfyui/_mapped.json', 'w') as f:
        json.dump(workflow, f, indent=4)

    # send the API request
    print("\nLOG MAPPED JSON:")
    # pprint.pp(json_obj)
    print_with_colors(workflow)

    return workflow


def do_post(url, data):
    print(Fore.WHITE + "\nREQUEST TO: " + url)
    try:
        return requests.post(url, json=data, headers=create_headers(), timeout=utils.local_sd_timeout())
    except requests.exceptions.ConnectionError:
        return operators.handle_error(f"The local Stable Diffusion server couldn't be found. It's either not running, or it's running at a different location than what you specified in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_not_found")
    except requests.exceptions.MissingSchema:
        return operators.handle_error(f"The url for your local Stable Diffusion server is invalid. Please set it correctly in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_url_invalid")
    except requests.exceptions.ReadTimeout:
        return operators.handle_error("The local Stable Diffusion server timed out. Set a longer timeout in AI Render preferences, or use a smaller image size.", "timeout")


def debug_log(response):
    print("request body:")
    print(response.request.body)
    print("\n")

    print("response body:")
    # print(response.content)

    try:
        print(response.json())
    except:
        print("body not json")


# PUBLIC SUPPORT FUNCTIONS:

def get_workflows_path(context):
    return utils.get_addon_preferences().workflows_path


def get_workflows():
    workflows_path = get_workflows_path(bpy.context)
    workflow_files = [f for f in os.listdir(workflows_path) if os.path.isfile(
        os.path.join(workflows_path, f)) and f.endswith(".json")]
    workflow_tuples = [(f, f, "", i) for i, f in enumerate(workflow_files)]

    return workflow_tuples


def get_samplers():
    # NOTE: Keep the number values (fourth item in the tuples) in sync with DreamStudio's
    # values (in stability_api.py). These act like an internal unique ID for Blender
    # to use when switching between the lists.
    return [
        ('euler', 'euler', '', 10),
        ('euler_ancestral', 'euler_ancestral', '', 20),
        ('heun', 'heun', '', 30),
        ('heunpp2', 'heunpp2', '', 40),
        ('dpm_2', 'dpm_2', '', 50),
        ('dpm_2_ancestral', 'dpm_2_ancestral', '', 60),
        ('lms', 'lms', '', 70),
        ('dpm_fast', 'dpm_fast', '', 80),
        ('dpm_adaptive', 'dpm_adaptive', '', 90),
        ('dpmpp_2s_ancestral', 'dpmpp_2s_ancestral', '', 100),
        ('dpmpp_sde', 'dpmpp_sde', '', 110),
        ('dpmpp_sde_gpu', 'dpmpp_sde_gpu', '', 120),
        ('dpmpp_2m', 'dpmpp_2m', '', 130),
        ('dpmpp_2m_sde', 'dpmpp_2m_sde', '', 140),
        ('dpmpp_2m_sde_gpu', 'dpmpp_2m_sde_gpu', '', 150),
        ('dpmpp_3m_sde', 'dpmpp_3m_sde', '', 160),
        ('ddpm', 'ddpm', '', 170),
        ('lcm', 'lcm', '', 180),
        ('ddim', 'ddim', '', 190),
        ('uni_pc', 'uni_pc', '', 200),
        ('uni_pc_bh2', 'uni_pc_bh2', '', 210)
    ]


def get_schedulers():
    return [
        ('normal', 'normal', '', 10),
        ('karras', 'karras', '', 20),
        ('exponential', 'exponential', '', 30),
        ('sgm_uniform', 'sgm_uniform', '', 40),
        ('simple', 'simple', '', 50),
        ('ddim_uniform', 'ddim_uniform', '', 60),
    ]


def default_sampler():
    return 'dpmpp_2m'


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
    if context is None:
        context = bpy.context
    return context.scene.air_props.automatic1111_available_upscaler_models != ""


def default_upscaler_model():
    return 'ESRGAN_4x'


def get_image_format():
    return 'PNG'


def supports_negative_prompts():
    return True


def supports_choosing_model():
    # TODO - This should be set to true
    # and a get_model() should be used to get the model list from the ComfyUI API
    return False


def supports_upscaling():
    return False


def supports_reloading_upscaler_models():
    return True


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
