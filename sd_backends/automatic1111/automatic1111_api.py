import bpy
import json
import base64
import re
import requests
from ... import (
    config,
    operators,
    utils,
)


# CORE FUNCTIONS:

def send_to_api(params, img_file, filename_prefix):

    # load the initial params object
    automatic1111_params = load_params_obj()

    # update our actual params in the properties we're touching
    map_params(automatic1111_params, params)

    # add a base 64 encoded image to the params
    automatic1111_params["data"]["image_0"] = "data:image/png;base64," + base64.b64encode(img_file.read()).decode()
    img_file.close()

    # format the params for the gradio api
    automatic1111_params["data"] = list(automatic1111_params["data"].values())

    # create the headers
    headers = {
        "User-Agent": "Blender/" + bpy.app.version_string,
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
    }

    # prepare the server url
    server_url = utils.local_sd_url().rstrip("/").strip()
    if not server_url:
        return operators.handle_error(f"You need to specify a location for the local Stable Diffusion server in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})")
    else:
        server_url = server_url + "/api/predict"

    # send the API request
    try:
        response = requests.post(server_url, json=automatic1111_params, headers=headers, timeout=utils.local_sd_timeout())
    except requests.exceptions.ConnectionError:
        return operators.handle_error(f"The local Stable Diffusion server couldn't be found. It's either not running, or it's running at a different location than what you specified in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})")
    except requests.exceptions.MissingSchema:
        return operators.handle_error(f"The url for your local Stable Diffusion server is invalid. Please set it correctly in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})")
    except requests.exceptions.ReadTimeout:
        return operators.handle_error("The local Stable Diffusion server timed out. Set a longer timeout in AI Render preferences, or use a smaller image size.")

    # handle the response
    if response.status_code == 200:
        return handle_api_success(response, filename_prefix)
    else:
        return handle_api_error(response)


def handle_api_success(response, filename_prefix):
    # parse the response for the filename (if the file wasn't already on the machine,
    # this could/should use the filename_prefix)
    try:
        return get_image_filename_from_response(response)
    except:
        print("Automatic1111 response content: ")
        print(response.content)
        return operators.handle_error("Received an unexpected response from the Automatic1111 Stable Diffusion server.")


def handle_api_error(response):
    return operators.handle_error("An error occurred in the Automatic1111 Stable Diffusion server. Check the server logs for more info.")



# SUPPORT FUNCTIONS:

def load_params_obj():
    params_version = "params-v2022-10-21.json" if utils.local_sd_backend() == "automatic1111-v2022-10-21" else "params-v2022-10-20.json"
    params_filename = utils.get_filepath_in_package("", params_version, __file__)
    with open(params_filename) as file:
        params_obj = json.load(file)
    return params_obj


def map_params(automatic1111_params, params):
    automatic1111_params["data"]["prompt"] = params["prompt"]
    automatic1111_params["data"]["width"] = params["width"]
    automatic1111_params["data"]["height"] = params["height"]
    automatic1111_params["data"]["strength"] = 1 - params["image_similarity"]
    automatic1111_params["data"]["seed"] = params["seed"]
    automatic1111_params["data"]["guidance_scale"] = params["cfg_scale"]
    automatic1111_params["data"]["nb_steps"] = params["steps"]
    automatic1111_params["data"]["sampling_method"] = map_sampler(params["sampler"])


def map_sampler(sampler):
    samplers = {
        "k_euler": "Euler",
        "k_euler_ancestral": "Euler a",
        "k_heun": "Heun",
        "k_dpm_2": "DPM2",
        "k_dpm_2_ancestral": "DPM2 a",
        "k_lms": "LMS",
    }
    return samplers[sampler]


def get_image_filename_from_response(response):
    content = response.content
    if isinstance(content, (bytes, bytearray)):
        content = content.decode()

    regex = r"[a-z0-9_\-\.\/\\]+\.png"
    match = re.search(regex, content, re.MULTILINE | re.IGNORECASE)
    if match:
        # format for Windows if necessary
        filename = match.group(0)
        if filename[0] == "\\":
            filename = "C:" + filename
        return filename
    else:
        return None
