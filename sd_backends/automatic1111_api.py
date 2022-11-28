import bpy
import json
import base64
import re
import requests
from .. import (
    config,
    operators,
    utils,
)


# CORE FUNCTIONS:

def send_to_api(params, img_file, filename_prefix):

    # map the generic params to the specific ones for the Automatic1111 API
    map_params(params)

    # add a base 64 encoded image to the params
    params["init_images"] = ["data:image/png;base64," + base64.b64encode(img_file.read()).decode()]
    img_file.close()

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
        server_url = server_url + "/sdapi/v1/img2img"

    # send the API request
    try:
        response = requests.post(server_url, json=params, headers=headers, timeout=utils.local_sd_timeout())
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

    # ensure we have the type of response we are expecting
    try:
        response_obj = response.json()
        base64_img = response_obj["images"][0]
    except:
        print("Automatic1111 response content: ")
        print(response.content)
        return operators.handle_error("Received an unexpected response from the Automatic1111 Stable Diffusion server.")

    # create a temp file
    try:
        output_file = utils.create_temp_file(filename_prefix + "-")
    except:
        return operators.handle_error("Couldn't create a temp file to save image.")

    # decode base64 image
    try:
        img_binary = base64.b64decode(base64_img.replace("data:image/png;base64,", ""))
    except:
        return operators.handle_error("Couldn't decode base64 image from the Automatic1111 Stable Diffusion server.")

    # save the image to the temp file
    try:
        with open(output_file, 'wb') as file:
            file.write(img_binary)
    except:
        return operators.handle_error("Couldn't write to temp file.")


    # return the temp file
    return output_file


def handle_api_error(response):
    if response.status_code == 404:
        import json

        try:
            response_obj = response.json()
            if response_obj.get('detail') and response_obj['detail'] == "Sampler not found":
                return operators.handle_error("The sampler you selected is not available on the Automatic1111 Stable Diffusion server. Please select a different sampler.")
            else:
                return operators.handle_error(f"An error occurred in the Automatic1111 Stable Diffusion server. Full server response: {json.dumps(response_obj)}")
        except:
            return operators.handle_error(f"It looks like the Automatic1111 server is running, but it's not in API mode. [Get help]({config.HELP_WITH_AUTOMATIC1111_NOT_IN_API_MODE_URL})")

    else:
        return operators.handle_error("An error occurred in the Automatic1111 Stable Diffusion server. Check the server logs for more info.")


def get_samplers():
    # NOTE: Keep the number values (fourth item in the tuples) in sync with DreamStudio's
    # values (in dreamstudio_api.py). These act like an internal unique ID for Blender
    # to use when switching between the lists.
    return [
        ('Euler', 'Euler', '', 10),
        ('Euler a', 'Euler a', '', 20),
        ('Heun', 'Heun', '', 30),
        ('DPM2', 'DPM2', '', 40),
        ('DPM2 a', 'DPM2 a', '', 50),
        ('LMS', 'LMS', '', 60),
        ('DPM fast', 'DPM fast', '', 70),
        ('DPM adaptive', 'DPM adaptive', '', 80),
        ('DPM++ 2S a Karras', 'DPM++ 2S a Karras', '', 90),
        ('DPM++ 2M Karras', 'DPM++ 2M Karras', '', 100),
        ('DPM++ 2S a', 'DPM++ 2S a', '', 110),
        ('DPM++ 2M', 'DPM++ 2M', '', 120),
        ('PLMS', 'PLMS', '', 200),
        ('DDIM', 'DDIM', '', 210),
    ]


def default_sampler():
    return 'LMS'


def get_image_format():
    return 'PNG'


def max_image_size():
    return 1024 * 1024


# SUPPORT FUNCTIONS:

def map_params(params):
    params["denoising_strength"] = round(1 - params["image_similarity"], 2)
    params["sampler_index"] = params["sampler"]
