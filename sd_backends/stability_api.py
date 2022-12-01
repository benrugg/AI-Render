import bpy
import json
import requests
from .. import (
    config,
    operators,
    utils,
)


# CORE FUNCTIONS:

def send_to_api(params, img_file, filename_prefix, sd_model):

    # map the generic params to the specific ones for the Stability API
    map_params(params)

    # create the headers
    headers = {
        "User-Agent": "Blender/" + bpy.app.version_string,
        "Accept": "image/png",
        "Accept-Encoding": "gzip, deflate, br",
        "Authorization": utils.get_dream_studio_api_key()
    }

    # prepare the file input
    files = {
        'init_image': img_file,
        'options': (None, json.dumps(params)),
    }

    # prepare the URL
    if sd_model == 'v2-0':
        if params["width"] >= 768 and params["height"] >= 768:
            engine = f"stable-diffusion-768-{sd_model}"
        else:
            engine = f"stable-diffusion-512-{sd_model}"
    else:
        engine = f"stable-diffusion-{sd_model}"

    api_url = f"{config.STABILITY_API_URL}{engine}/image-to-image"

    # send the API request
    try:
        response = requests.post(api_url, headers=headers, files=files, timeout=request_timeout())
        img_file.close()
    except requests.exceptions.ReadTimeout:
        img_file.close()
        return operators.handle_error(f"The server timed out. Try again in a moment, or get help. [Get help with timeouts]({config.HELP_WITH_TIMEOUTS_URL})", "timeout")

    # NOTE: For debugging:
    # print("request body:")
    # print(response.request.body)
    # print("\n")
    # print("response body:")
    # print(response.content)
    # try:
    #     print(response.json())
    # except:
    #     print("body not json")

    # handle the response
    if response.status_code == 200:
        return handle_api_success(response, filename_prefix)
    else:
        return handle_api_error(response)


def handle_api_success(response, filename_prefix):
    try:
        output_file = utils.create_temp_file(filename_prefix + "-")

        with open(output_file, 'wb') as file:
            for chunk in response:
                file.write(chunk)

        return output_file
    except:
        return operators.handle_error(f"Couldn't create a temp file to save image", "temp_file")


def handle_api_error(response):
    # handle 404
    if response.status_code in [403, 404]:
        return operators.handle_error("It looks like the web server this add-on relies on is missing. It's possible this is temporary, and you can try again later.", "server_missing")

    # handle all other errors
    else:
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

def map_params(params):
    params["step_schedule_start"] = round(1 - params["image_similarity"], 2)
    params["sampler"] = params["sampler"].upper()
    params["text_prompts"] = [
        {"text": params["prompt"], "weight": 1},
    ]
    if params["negative_prompt"]:
        params["text_prompts"].append({"text": params["negative_prompt"], "weight": -1})


def parse_message_for_error(message):
    if "\"Authorization\" is missing" in message:
        return "Your DreamStudio API key is missing. Please enter it above.", "api_key"
    elif "Incorrect API key" in message or "Unauthenticated" in message or "Unable to find corresponding account" in message:
        return f"Your DreamStudio API key is incorrect. Please find it on the DreamStudio website, and re-enter it above. [DreamStudio website]({config.DREAM_STUDIO_URL})", "api_key"
    elif "image too large" in message:
        return "Image size is too large. Please decrease width/height.", "dimensions_too_large"
    elif "body.width must be" in message or "body.height must be" in message:
        return "Invalid width or height. They must be in the range 512-2048 in multiples of 64.", "invalid_dimensions"
    elif "body.sampler must be" in message:
        return "Invalid sampler. Please choose a new Sampler under 'Advanced Options'.", "sampler"
    elif "body.cfg_scale must be" in message:
        return "Invalid prompt strength. 'Prompt Strength' must be in the range 0-35.", "prompt_strength"
    elif "body.seed must be" in message:
        return "Invalid seed value. Please choose a new 'Seed'.", "seed"
    elif "body.steps must be" in message:
        return "Invalid number of steps. 'Steps' must be in the range 10-150.", "steps"
    return f"(Server Error) An error occurred in the Stability API. Full server response: {message}", "unknown_error"


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
    ]


def default_sampler():
    return 'k_lms'


def request_timeout():
    return 60


def get_image_format():
    return 'PNG'


def supports_negative_prompts():
    return True


def supports_choosing_model():
    return True


def max_image_size():
    return 1024 * 1024
