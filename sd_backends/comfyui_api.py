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
from colorama import Fore

LOG_PROPS = True
LOG_WORKFLOW = False
LOG_PARAMS = True
LOG_MAPPED_WORKFLOW = False

LOG_REQUEST_TO = True
LOG_RESPONSE = True
LOG_HISTORY_RESPONSE = False

LOG_UPLOAD_IMAGE = False
LOG_DOWNLOAD_IMAGE = True

ORIGINAL_DATA = {
    "3": {
        "inputs": {
            "seed": 265216098348317,
            "steps": 10,
            "cfg": 7.5,
            "sampler_name": "dpmpp_2m_sde_gpu",
            "scheduler": "karras",
            "denoise": 1,
            "model": [
                "26",
                0
            ],
            "positive": [
                "16",
                0
            ],
            "negative": [
                "16",
                1
            ],
            "latent_image": [
                "10",
                0
            ]
        },
        "class_type": "KSampler",
        "_meta": {
            "title": "main_sampler"
        }
    },
    "4": {
        "inputs": {
            "ckpt_name": "v1-5-pruned-emaonly.safetensors"
        },
        "class_type": "CheckpointLoaderSimple",
        "_meta": {
            "title": "Load Checkpoint"
        }
    },
    "6": {
        "inputs": {
            "text": "positive",
            "clip": [
                "26",
                1
            ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
            "title": "positive"
        }
    },
    "7": {
        "inputs": {
            "text": "negative",
            "clip": [
                "26",
                1
            ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
            "title": "negative"
        }
    },
    "8": {
        "inputs": {
            "samples": [
                "3",
                0
            ],
            "vae": [
                "11",
                0
            ]
        },
        "class_type": "VAEDecode",
        "_meta": {
            "title": "VAE Decode"
        }
    },
    "9": {
        "inputs": {
            "filename_prefix": "ComfyUI",
            "images": [
                "8",
                0
            ]
        },
        "class_type": "SaveImage",
        "_meta": {
            "title": "output_image"
        }
    },
    "10": {
        "inputs": {
            "pixels": [
                "12",
                0
            ],
            "vae": [
                "11",
                0
            ]
        },
        "class_type": "VAEEncode",
        "_meta": {
            "title": "VAE Encode"
        }
    },
    "11": {
        "inputs": {
            "vae_name": "vae-ft-mse-840000-ema-pruned.safetensors"
        },
        "class_type": "VAELoader",
        "_meta": {
            "title": "Load VAE"
        }
    },
    "12": {
        "inputs": {
            "image": "castel-3dscan-color.png",
            "upload": "image"
        },
        "class_type": "LoadImage",
        "_meta": {
            "title": "color"
        }
    },
    "13": {
        "inputs": {
            "strength": 1,
            "start_percent": 0,
            "end_percent": 1,
            "positive": [
                "6",
                0
            ],
            "negative": [
                "7",
                0
            ],
            "control_net": [
                "14",
                0
            ],
            "image": [
                "15",
                0
            ]
        },
        "class_type": "ControlNetApplyAdvanced",
        "_meta": {
            "title": "Apply ControlNet (Advanced)"
        }
    },
    "14": {
        "inputs": {
            "control_net_name": "SD15\\control_v11\\control_v11f1p_sd15_depth.pth"
        },
        "class_type": "ControlNetLoader",
        "_meta": {
            "title": "Load ControlNet Model"
        }
    },
    "15": {
        "inputs": {
            "image": "castle-3dmodel-depth.png",
            "upload": "image"
        },
        "class_type": "LoadImage",
        "_meta": {
            "title": "depth"
        }
    },
    "16": {
        "inputs": {
            "strength": 1,
            "start_percent": 0,
            "end_percent": 1,
            "positive": [
                "13",
                0
            ],
            "negative": [
                "13",
                1
            ],
            "control_net": [
                "17",
                0
            ],
            "image": [
                "18",
                0
            ]
        },
        "class_type": "ControlNetApplyAdvanced",
        "_meta": {
            "title": "Apply ControlNet (Advanced)"
        }
    },
    "17": {
        "inputs": {
            "control_net_name": "SD15\\control_v11\\control_v11p_sd15_normalbae.pth"
        },
        "class_type": "ControlNetLoader",
        "_meta": {
            "title": "Load ControlNet Model"
        }
    },
    "18": {
        "inputs": {
            "image": "castle-3dmodel-normal.png",
            "upload": "image"
        },
        "class_type": "LoadImage",
        "_meta": {
            "title": "normal"
        }
    },
    "26": {
        "inputs": {
            "lora_name": "SD15\\add_detail.safetensors",
            "strength_model": 1,
            "strength_clip": 1,
            "model": [
                "4",
                0
            ],
            "clip": [
                "4",
                1
            ]
        },
        "class_type": "LoraLoader",
        "_meta": {
            "title": "Load LoRA"
        }
    }
}
PARAM_TO_WORKFLOW = {
    "seed": {
        "class_type": "KSampler",
        "input_key": "seed",
        "meta_title": "main_sampler"
    },
    "steps": {
        "class_type": "KSampler",
        "input_key": "steps",
        "meta_title": "main_sampler"
    },
    "cfg_scale": {
        "class_type": "KSampler",
        "input_key": "cfg",
        "meta_title": "main_sampler"
    },
    "sampler": {
        "class_type": "KSampler",
        "input_key": "sampler_name",
        "meta_title": "main_sampler"
    },
    "scheduler": {
        "class_type": "KSampler",
        "input_key": "scheduler",
        "meta_title": "main_sampler"
    },
    "denoising_strength": {
        "class_type": "KSampler",
        "input_key": "denoise",
        "meta_title": "main_sampler"
    },
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
    }
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


def upload_image(img_file, subfolder):
    """Upload the image to the input folder of ComfyUI"""
    # This function is here for future use if we decide to use a remote ComfyUI server.

    # At the moment we're not using this function:
    # ComfyUI is running local and we can render the image directly
    # from Blender to the ComfyUI input path without the need to upload it through the API.

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

    if LOG_REQUEST_TO:
        print(Fore.WHITE + "\nREQUEST TO: " + server_url)

    # send the API request
    try:
        resp = requests.post(server_url, files=files, data=data, headers=headers)
    except requests.exceptions.ConnectionError:
        return operators.handle_error(f"The local Stable Diffusion server couldn't be found. It's either not running, or it's running at a different location than what you specified in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_not_found")
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
        # Continue only if the parameter is in the params dictionary
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

    updated_workflow = map_param_to_workflow(params, workflow)

    # Save mapped json to local file
    with open('sd_backends/comfyui/example_api_mapped.json', 'w') as f:
        json.dump(updated_workflow, f, indent=4)

    if LOG_MAPPED_WORKFLOW:
        print(Fore.WHITE + "\LOG_MAPPED_WORKFLOW:" + Fore.RESET)
        pprint.pp(updated_workflow)

    return updated_workflow


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

    params["denoising_strength"] = round(1 - params["image_similarity"], 4)
    params["sampler_index"] = params["sampler"]

    # Get the input path of local ComfyUI
    comfyui_input_path = get_comfyui_input_path(bpy.context)

    # get the frame number for the filename
    frame_number = bpy.context.scene.frame_current

    # format the frame number to 4 digits
    frame_number = str(frame_number).zfill(4)

    color_image_path = comfyui_input_path + "color/Image" + frame_number + ".png"
    depth_image_path = comfyui_input_path + "depth/Image" + frame_number + ".png"
    normal_image_path = comfyui_input_path + "normal/Image" + frame_number + ".png"

    params['color_image'] = color_image_path
    params['depth_image'] = depth_image_path
    params['normal_image'] = normal_image_path

    # map the params to the ComfyUI nodes
    json_obj = map_params(params, selected_workflow)
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
        print(Fore.WHITE + "\nREQUEST TO: " + server_url)

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
                if LOG_HISTORY_RESPONSE:
                    print(Fore.WHITE + "\nHISTORY RESPONSE: " + Fore.RESET)
                    print(json.dumps(response_obj, indent=2))

                # Get the NODE NUMBER of the SaveImage node

                save_image_node = None
                for item in response_obj[prompt_id]["prompt"]:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if value.get("class_type") == "SaveImage":
                                save_image_node = key
                                break

                if LOG_DOWNLOAD_IMAGE:
                    print(Fore.LIGHTWHITE_EX + "IMAGE NODE_NUMBER: " + Fore.RESET + save_image_node)

                image_file_name = response_obj[prompt_id]["outputs"][save_image_node]["images"][0]["filename"]

                if LOG_DOWNLOAD_IMAGE:
                    print(Fore.LIGHTWHITE_EX + "IMAGE FILE NAME: " + Fore.RESET + image_file_name)  # ComfyUI_00057_.png
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
            if response_obj.get('detail') and response_obj['detail'] == "Not Found":
                return operators.handle_error(f"It looks like the Automatic1111 server is running, but it's not in API mode. [Get help]({config.HELP_WITH_AUTOMATIC1111_NOT_IN_API_MODE_URL})", "automatic1111_not_in_api_mode")
            elif response_obj.get('detail') and response_obj['detail'] == "Sampler not found":
                return operators.handle_error("The sampler you selected is not available on the Automatic1111 Stable Diffusion server. Please select a different sampler.", "invalid_sampler")
            else:
                return operators.handle_error(f"An error occurred in the ComfyUI server. Full server response: {json.dumps(response_obj)}", "unknown_error")
        except:
            return operators.handle_error(f"It looks like the Automatic1111 server is running, but it's not in API mode. [Get help]({config.HELP_WITH_AUTOMATIC1111_NOT_IN_API_MODE_URL})", "automatic1111_not_in_api_mode")

    else:
        print(Fore.RED + "ERROR DETAILS:")
        pprint.pp(response.json(), indent=2)
        print(Fore.RESET)
        return operators.handle_error(f"AN ERROR occurred in the ComfyUI server.", "unknown_error_response")


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


def do_post(url, data):
    if LOG_REQUEST_TO:
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
    return utils.get_addon_preferences().comfyui_workflows_path


def create_workflows_tuples():
    workflows_path = get_workflows_path(bpy.context)
    workflow_files = [f for f in os.listdir(workflows_path) if os.path.isfile(
        os.path.join(workflows_path, f)) and f.endswith(".json")]
    workflows_tuples = [(f, f, "", i) for i, f in enumerate(workflow_files)]

    return workflows_tuples


def get_comfyui_input_path(context):
    comfyui_path = utils.get_addon_preferences(context).comfyui_path
    return comfyui_path + "input/"


def get_comfyui_output_path(context):
    comfyui_path = utils.get_addon_preferences(context).comfyui_path
    return comfyui_path + "output/"


def get_models():
    # TODO - get the models from the ComfyUI API
    return []


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
    # TODO: False until a get_models() function is implemented
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
