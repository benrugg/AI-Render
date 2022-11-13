import bpy
import json
import base64
import time
import re
import requests

from ... import (
    config,
    operators,
    utils,
)

API_URL = "https://stablehorde.net/api/v2/generate/sync"
SAMPLER_MAP = {
    "DDIM": "k_ddim",
    "PLMS": ""
}
# CORE FUNCTIONS:

def send_to_api(params, img_file, filename_prefix):

    # Open img_file png and convert to webp
    # TODO: Change operators.py to render directly to webp
    # image = PIL.Image.open(img_file)  # Open image
    # webp_filename = img_file + ".webp"
    # image.save(webp_filename, format="webp")  # Convert image to webp
    print("Sending: " + str(img_file))

    # map the generic params to the specific ones for the Automatic1111 API
    # map_params(params)
    stablehorde_params = {
        "prompt": params["prompt"],
        # add a base 64 encoded image to the params
        "source_image": base64.b64encode(img_file.read()).decode(),
        "params": {
            "cfg_scale": params["cfg_scale"],
            "width": params["width"],
            "height": params["height"],
            "denoising_strength": round(1 - params["image_similarity"], 2),
            "seed": str(params["seed"]),
            "steps": params["steps"],
            #"sampler_name": params["sampler"],
        }
    }

    #webp_filename.close()
    img_file.close()

    # create the headers
    headers = {
        "User-Agent": "Blender/" + bpy.app.version_string,
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "apikey": utils.get_api_key()
    }

    # send the API request
    # try:
    #     response = requests.post(API_URL, json=params, headers=headers)
    # except requests.exceptions.ConnectionError:
    #     return operators.handle_error(f"The local Stable Diffusion server couldn't be found. It's either not running, or it's running at a different location than what you specified in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})")
    # except requests.exceptions.MissingSchema:
    #     return operators.handle_error(f"The url for your local Stable Diffusion server is invalid. Please set it correctly in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})")
    # except requests.exceptions.ReadTimeout:
    #     return operators.handle_error("The local Stable Diffusion server timed out. Set a longer timeout in AI Render preferences, or use a smaller image size.")

    # send the API request
    print("Sending to Stable Horde: " + str(stablehorde_params))
    start_time = time.monotonic();
    try:
        response = requests.post(API_URL, json=stablehorde_params, headers=headers, timeout=config.request_timeout)
        img_file.close()
    except requests.exceptions.ReadTimeout:
        img_file.close()
        return operators.handle_error(f"The server timed out. Try again in a moment, or get help. [Get help with timeouts]({config.HELP_WITH_TIMEOUTS_URL})")
    print("The horde took " + str(time.monotonic() - start_time) + " seconds to imagine this frame.")

    # handle the response
    if response.status_code == 200:
        return handle_api_success(response, filename_prefix)
    else:
        return handle_api_error(response)


def handle_api_success(response, filename_prefix):

    # ensure we have the type of response we are expecting
    try:
        response_obj = response.json()
        # print(str(response_obj))
        # print(str(response_obj["generations"]))
        # print(str(response_obj["generations"][0]))

        base64_img = response_obj["generations"][0]["img"]
    except:
        print("Stable Horde response content: ")
        print(response.content)
        return operators.handle_error("Received an unexpected response from the Stable Horde server.")

    # create a temp file
    try:
        output_file = utils.create_temp_file(filename_prefix + "-.webp")
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

    # Convert the file from webp to png
    # return the temp file
    return output_file


def handle_api_error(response):
    return operators.handle_error("the Stable Horde server returned an error: " + str(response.content))
    # if response.status_code == 404:
    #     import json
    #
    #     try:
    #         response_obj = response.json()
    #         if response_obj.get('detail') and response_obj['detail'] == "Sampler not found":
    #             return operators.handle_error("The sampler you selected is not available on the Automatic1111 Stable Diffusion server. Please select a different sampler.")
    #         else:
    #             return operators.handle_error(f"An error occurred in the Automatic1111 Stable Diffusion server. Full server response: {json.dumps(response_obj)}")
    #     except:
    #         return operators.handle_error(f"It looks like the Automatic1111 server is running, but it's not in API mode. [Get help]({config.HELP_WITH_AUTOMATIC1111_NOT_IN_API_MODE_URL})")
    #
    # else:
    #     return operators.handle_error("An error occurred in the Automatic1111 Stable Diffusion server. Check the server logs for more info.")


def get_samplers():
    def get_samplers():
        # NOTE: Keep the number values (fourth item in the tuples) in sync with DreamStudio's
        # values (in dreamstudio_apy.py). These act like an internal unique ID for Blender
        # to use when switching between the lists.
        return [
            ('k_euler', 'Euler', '', 10),
            ('k_euler_a', 'Euler a', '', 20),
            ('k_heun', 'Heun', '', 30),
            ('k_dpm_2', 'DPM2', '', 40),
            ('k_dpm_2_a', 'DPM2 a', '', 50),
            ('k_dpm_fast', 'DPM fast', '', 70),
            ('k_dpm_adaptive', 'DPM adaptive', '', 80),
            ('k_lms', 'LMS', '', 60),
            ('k_dpmpp_2s_a', 'DPM++ 2S a', '', 110),
            ('k_dpmpp_2m', 'DPM++ 2M', '', 120),
            # TODO: Stable horde does have karras support, but it's a separate boolean
        ]

def default_sampler():
    return 'Euler a'


# SUPPORT FUNCTIONS:

def map_params(params):
    params["denoising_strength"] = round(1 - params["image_similarity"], 2)
    params["sampler_index"] = params["sampler"]
