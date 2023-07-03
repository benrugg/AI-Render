import bpy
import base64
import requests
from .. import (
    config,
    operators,
    utils,
)


# CORE FUNCTIONS:

def generate(params, img_file, filename_prefix, props):

    # validate the params, specifically for the Stability API
    if not validate_params(params, props):
        return False

    # map the generic params to the specific ones for the Stability API
    mapped_params = map_params(params)

    # create the headers
    headers = create_headers()

    # prepare the URL (specifically setting the engine id)
    sd_model = props.sd_model

    if 'xl' in sd_model:
        engine = sd_model
    elif 'v2' in sd_model:
        if params["width"] >= 768 and params["height"] >= 768:
            engine = f"stable-diffusion-768-{sd_model}"
        else:
            engine = f"stable-diffusion-512-{sd_model}"
    else:
        engine = f"stable-diffusion-{sd_model}"

    api_url = f"{config.STABILITY_API_URL}{engine}/image-to-image"

    # prepare the file input
    files = {
        'init_image': img_file,
    }

    # send the API request
    try:
        response = requests.post(api_url, headers=headers, files=files, data=mapped_params, timeout=request_timeout())
        img_file.close()
    except requests.exceptions.ReadTimeout:
        img_file.close()
        return operators.handle_error(f"The server timed out. Try again in a moment, or get help. [Get help with timeouts]({config.HELP_WITH_TIMEOUTS_URL})", "timeout")

    # print log info for debugging
    # debug_log(response)

    # handle the response
    if response.status_code == 200:
        return handle_success(response, filename_prefix)
    else:
        return handle_error(response)


def upscale(img_file, filename_prefix, props):

    # create the headers
    headers = create_headers()

    # prepare the URL
    api_url = f"{config.STABILITY_API_URL}{props.upscaler_model}/image-to-image/upscale"

    # prepare the file input
    files = {
        'image': img_file,
    }

    # prepare the params
    data = {
        'width': utils.sanitized_upscaled_width(max_upscaled_image_size())
    }

    # send the API request
    try:
        response = requests.post(api_url, headers=headers, files=files, data=data, timeout=request_timeout())
        img_file.close()
    except requests.exceptions.ReadTimeout:
        img_file.close()
        return operators.handle_error(f"The server timed out during upscaling. Try again in a moment, or turn off upscaling.", "timeout")

    # print log info for debugging
    # debug_log(response)

    # handle the response
    if response.status_code == 200:
        return handle_success(response, filename_prefix)
    else:
        return handle_error(response)


def handle_success(response, filename_prefix):
    try:
        data = response.json()
        output_file = utils.create_temp_file(filename_prefix + "-")

        for i, image in enumerate(data["artifacts"]):
            with open(output_file, 'wb') as file:
                file.write(base64.b64decode(image["base64"]))

        return output_file
    except:
        return operators.handle_error(f"Couldn't create a temp file to save image", "temp_file")


def handle_error(response):
    import json
    error_key = ''

    try:
        # convert the response to JSON (hopefully)
        response_obj = response.json()

        # get the message key from the response, if it exists
        message = response_obj.get('message', str(response.content))

        # handle the different types of errors
        if response_obj.get('timeout', False):
            error_message = f"The server timed out. Try again in a moment, or get help. [Get help with timeouts]({config.HELP_WITH_TIMEOUTS_URL})"
            error_key = "timeout"
        else:
            error_message, error_key = parse_message_for_error(message)
    except:
        error_message = f"(Server Error) An unknown error occurred in the Stability API. Full server response: {str(response.content)}"
        error_key = "unknown_error_response"

    return operators.handle_error(error_message, error_key)


# PRIVATE SUPPORT FUNCTIONS:

def create_headers():
    return {
        "User-Agent": f"Blender/{bpy.app.version_string}",
        "Accept": "application/json",
        "Authorization": f"Bearer {utils.get_dream_studio_api_key()}"
    }


def map_params(params):
    # create a new dict so we don't overwrite the original
    mapped_params = {}

    # copy the params
    mapped_params["seed"] = params["seed"]
    mapped_params["cfg_scale"] = params["cfg_scale"]
    mapped_params["steps"] = params["steps"]

    # convert the params to the Stability API format
    mapped_params["image_strength"] = round(params["image_similarity"], 2)
    mapped_params["sampler"] = params["sampler"].upper()
    mapped_params["text_prompts[0][text]"] = params["prompt"]
    mapped_params["text_prompts[0][weight]"] = 1.0

    if params["negative_prompt"]:
        mapped_params["text_prompts[1][text]"] = params["negative_prompt"]
        mapped_params["text_prompts[1][weight]"] = -1.0

    return mapped_params


def validate_params(params, props):
    if 'xl' in props.sd_model:
        # for the sdxl model, only 512x512, 512x768, and 768x512 are supported
        if \
            params["width"] == 512 and params["height"] == 512 or \
            params["width"] == 512 and params["height"] == 768 or \
            params["width"] == 768 and params["height"] == 512:
                return True
        else:
            return operators.handle_error(f"The SDXL model only supports 512x512, 512x768 and 768x512 images. Please change your image size and try again.", "invalid_dimensions")
    else:
        return True


def parse_message_for_error(message):
    if "\"Authorization\" is missing" in message:
        return "Your DreamStudio API key is missing. Please enter it above.", "api_key"
    elif "Incorrect API key" in message or "Unauthenticated" in message or "Unable to find corresponding account" in message:
        return f"Your DreamStudio API key is incorrect. Please find it on the DreamStudio website, and re-enter it above. [DreamStudio website]({config.DREAM_STUDIO_URL})", "api_key"
    elif "not have enough balance" in message:
        return f"You don't have enough DreamStudio credits. Please purchase credits on the DreamStudio website or switch to a different backend in the AI Render add-on preferences. [DreamStudio website]({config.DREAM_STUDIO_URL})", "credits"
    elif "invalid_prompts" in message:
        return "Invalid prompt. Your prompt includes filtered words. Please change your prompt and try again.", "prompt"
    elif "image too large" in message:
        return "Image size is too large. Please decrease width/height.", "dimensions_too_large"
    elif "invalid_height_or_width" in message:
        return "Invalid width or height. They must be in the range 128-2048 in multiples of 64.", "invalid_dimensions"
    elif "body.sampler must be" in message:
        return "Invalid sampler. Please choose a new Sampler under 'Advanced Options'.", "sampler"
    elif "body.cfg_scale must be" in message:
        return "Invalid prompt strength. 'Prompt Strength' must be in the range 0-35.", "prompt_strength"
    elif "body.seed must be" in message:
        return "Invalid seed value. Please choose a new 'Seed'.", "seed"
    elif "body.steps must be" in message:
        return "Invalid number of steps. 'Steps' must be in the range 10-150.", "steps"
    return f"(Server Error) An error occurred in the Stability API. Full server response: {message}", "unknown_error"


def debug_log(response):
    print("request body:")
    print(response.request.body)
    print("\n")

    print("response body:")
    print(response.content)

    try:
        print(response.json())
    except:
        print("body not json")


# PUBLIC SUPPORT FUNCTIONS:

def get_samplers():
    # NOTE: Keep the number values (fourth item in the tuples) in sync with the other
    # backends, like Automatic1111. These act like an internal unique ID for Blender
    # to use when switching between the lists.
    return [
        ('k_euler', 'Euler', '', 10),
        ('k_euler_ancestral', 'Euler a', '', 20),
        ('k_heun', 'Heun', '', 30),
        ('k_dpm_2', 'DPM2', '', 40),
        ('k_dpm_2_ancestral', 'DPM2 a', '', 50),
        ('k_lms', 'LMS', '', 60),
        ('K_DPMPP_2S_ANCESTRAL', 'DPM++ 2S a', '', 110),
        ('K_DPMPP_2M', 'DPM++ 2M', '', 120),
        ('ddim', 'DDIM', '', 210),
        ('ddpm', 'DDPM', '', 220),
    ]


def default_sampler():
    return 'K_DPMPP_2M'


def get_upscaler_models(context):
    return [
        ('esrgan-v1-x2plus', 'ESRGAN X2+', ''),
    ]


def is_upscaler_model_list_loaded(context=None):
    return True


def default_upscaler_model():
    return 'esrgan-v1-x2plus'


def request_timeout():
    return 55


def get_image_format():
    return 'PNG'


def supports_negative_prompts():
    return True


def supports_choosing_model():
    return True


def supports_upscaling():
    return True


def supports_reloading_upscaler_models():
    return False


def supports_inpainting():
    return False


def supports_outpainting():
    return False


def min_image_size():
    return 256 * 1024


def max_image_size():
    return 1024 * 1024


def max_upscaled_image_size():
    return 2048 * 2048
