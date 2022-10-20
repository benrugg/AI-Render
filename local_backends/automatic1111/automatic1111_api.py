import bpy
import json
import base64
import re
import requests
from ... import (
    operators,
    utils,
)


def send_to_api(params, img_file):
    # load the initial params object
    automatic1111_params = load_params_obj()

    # update our actual params in the properties we're touching
    map_params(automatic1111_params, params)

    # add a base 64 encoded image to the params
    automatic1111_params["image_0"] = "data:image/png;base64," + base64.b64encode(img_file.read()).decode()
    img_file.close()

    # format the params for the gradio api
    body = {
        "data": list(automatic1111_params.values()),
        "fn_index": "33" # this is the img2img function in the Automatic1111 Web UI
    }

    # create the headers
    headers = {
        "User-Agent": "Blender/" + bpy.app.version_string,
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
    }

    # send the API request
    response = requests.post("http://127.0.0.1:7860/api/predict", json=body, headers=headers, timeout=20)

    if response.status_code == 200:
        return handle_success(response)
    else:
        return handle_error(response)


def handle_success(response):
    # parse the response for the filename
    try:
        return get_image_filename_from_response(response)
    except:
        print("Automatic1111 response content: ")
        print(response.content)
        return handle_error("Received an unexpected response from the Automatic1111 Stable Diffusion server.")


def handle_error(response):
    return operators.handle_error("An error occurred in the Automatic1111 Stable Diffusion server. Check the server logs for more info.")


def load_params_obj():
    params_filename = utils.get_filepath_in_package("", "params.json", __file__)
    with open(params_filename) as file:
        params_obj = json.load(file)
    return params_obj


def map_params(automatic1111_params, params):
    automatic1111_params["prompt"] = params["prompt"]
    automatic1111_params["width"] = params["width"]
    automatic1111_params["height"] = params["height"]
    automatic1111_params["strength"] = 1 - params["image_similarity"]
    automatic1111_params["seed"] = params["seed"]
    automatic1111_params["guidance_scale"] = params["cfg_scale"]
    automatic1111_params["nb_steps"] = params["steps"]
    automatic1111_params["sampling_method"] = map_sampler(params["sampler"])


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

    regex = r"[a-z0-9_\-\.\/]+\.png"
    match = re.search(regex, content, re.MULTILINE | re.IGNORECASE)
    return match.group(0) if match else None
