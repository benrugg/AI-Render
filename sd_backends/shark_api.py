import bpy
import base64
import requests
import random
from .. import (
    config,
    operators,
    utils,
)


# img2img generate should prabably work as is
# TODO: Controlnet Supprt
# TODO: Support Model Choice

def generate(params, img_file, filename_prefix, props):
    # Configuring custom params for shark
    params["denoising_strength"] = round(1 - params["image_similarity"], 2)

    # add a base 64 encoded image to the params
    params["init_images"] = ["data:image/png;base64," +
                             base64.b64encode(img_file.read()).decode()]
    img_file.close()

    # get server url
    try:
        server_url = get_server_url("/sdapi/v1/img2img")
    except:
        return operators.handle_error(f"You need to specify a location for the local Stable Diffusion server in the add-on preferences. [Get help]({config.HELP_WITH_SHARK_INSTALLATION_URL})", "local_server_url_missing")

    # send the API request
    response = do_post(server_url, params)

    # Error already handled
    if response is False:
        return False

    if response.status_code == 200:
        return handle_success(response, filename_prefix)
    else:
        return handle_error(response)


def upscale(img_file, filename_prefix, props):

    data = {
        "prompt": "",
        "negative_prompt": "",
        "seed": random.randint(1000000000, 2147483647),
        "height": utils.sanitized_upscaled_height(max_upscaled_image_size()),
        "width": utils.sanitized_upscaled_width(max_upscaled_image_size()),
        "steps": 50,
        "noise_level": 20,
        "cfg_scale": 7
    }

    data["init_images"] = ["data:image/png;base64," +
                           base64.b64encode(img_file.read()).decode()]
    img_file.close()

    try:
        server_url = get_server_url("/sdapi/v1/upscaler")
    except:
        return operators.handle_error(f"You need to specify a location for the local Stable Diffusion server in the add-on preferences. [Get help]({config.HELP_WITH_SHARK_INSTALLATION_URL})", "local_server_url_missing")

    response = do_post(server_url, data)

    if response is False:
        return False

    if response.status_code == 200:
        return handle_success(response, filename_prefix)
    else:
        return handle_error(response)


def handle_success(response, filename_prefix):

    # ensure we have the type of response we are expecting
    try:
        response_obj = response.json()
        base64_img = response_obj.get("images", [False])[
            0] or response_obj.get("image")
    except:
        print("SHARK response content: ")
        print(response.content)
        return operators.handle_error("Received an unexpected response from the Shark Stable Diffusion server.", "unexpected_response")

    # create a temp file
    try:
        output_file = utils.create_temp_file(filename_prefix + "-")
    except:
        return operators.handle_error("Couldn't create a temp file to save image.", "temp_file")

    # decode base64 image
    try:
        img_binary = base64.b64decode(
            base64_img.replace("data:image/png;base64,", ""))
    except:
        return operators.handle_error("Couldn't decode base64 image from the Shark Stable Diffusion server.", "base64_decode")

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
        import json

        try:
            response_obj = response.json()
            if response_obj.get('detail') and response_obj['detail'] == "Not Found":
                return operators.handle_error(f"It looks like the SHARK server is running, but it's not in API mode. [Get help]({config.HELP_WITH_SHARK_TROUBLESHOOTING_URL})", "automatic1111_not_in_api_mode")
            elif response_obj.get('detail') and response_obj['detail'] == "Sampler not found":
                return operators.handle_error("The sampler you selected is not available on the SHARK Stable Diffusion server. Please select a different sampler.", "invalid_sampler")
            else:
                return operators.handle_error(f"An error occurred in the SHARK Stable Diffusion server. Full server response: {json.dumps(response_obj)}", "unknown_error")
        except:
            return operators.handle_error(f"It looks like the SHARK server is running, but it's not in API mode. [Get help]({config.HELP_WITH_SHARK_TROUBLESHOOTING_URL})", "automatic1111_not_in_api_mode")

    else:
        return operators.handle_error(f"An error occurred in the SHARK Stable Diffusion server. Check the server logs for more info, or check out the SHARK Troubleshooting guide. [Get help]({config.HELP_WITH_SHARK_TROUBLESHOOTING_URL})", "unknown_error_response")


def create_headers():
    return {
        "User-Agent": f"Blender/{bpy.app.version_string}",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
    }


def do_post(url, data):
    # send the API request
    try:
        return requests.post(url, json=data, headers=create_headers(), timeout=utils.local_sd_timeout())
    except requests.exceptions.ConnectionError:
        return operators.handle_error(f"The local Stable Diffusion server couldn't be found. It's either not running, or it's running at a different location than what you specified in the add-on preferences. [Get help]({config.HELP_WITH_SHARK_INSTALLATION_URL})", "local_server_not_found")
    except requests.exceptions.MissingSchema:
        return operators.handle_error(f"The url for your local Stable Diffusion server is invalid. Please set it correctly in the add-on preferences. [Get help]({config.HELP_WITH_SHARK_INSTALLATION_URL})", "local_server_url_invalid")
    except requests.exceptions.ReadTimeout:
        return operators.handle_error("The local Stable Diffusion server timed out. Set a longer timeout in AI Render preferences, or use a smaller image size.", "timeout")


def get_server_url(path):
    base_url = utils.local_sd_url().rstrip("/").strip()
    if not base_url:
        raise Exception("Couldn't get the shark server url")
    else:
        return base_url + path


def min_image_size():
    return 384 * 384


def max_image_size():
    return 768 * 768


def max_upscaled_image_size():
    return 512 * 512


def supports_upscaling():
    return True


def get_image_format():
    return 'PNG'


def supports_negative_prompts():
    return True


def supports_choosing_model():
    return False


def is_upscaler_model_list_loaded(context=None):
    return True


def supports_reloading_upscaler_models():
    return False


def get_upscaler_models(context):
    # NOTE: Shark does not look at model in API Req and defaults to stabilityai
    return [
        ('stabilityai/stable-diffusion-2-1-base', 'stabilityai', ''),
    ]


def default_upscaler_model():
    return 'stabilityai/stable-diffusion-2-1-base'


def get_samplers():
    # NOTE: Keep the number values (fourth item in the tuples) in sync with the other
    # backends, like Automatic1111. These act like an internal unique ID for Blender
    # to use when switching between the lists.
    # NOTE: Shark does not look at sampler in API Req and defaults to EulerDiscrete
    return [
        ('k_euler', 'Euler', '', 10),
    ]


def default_sampler():
    return 'k_euler'