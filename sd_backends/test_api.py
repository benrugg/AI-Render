import logging # STRUDEL_IMPORT_0
import bpy
import base64
import requests
from .. import (
    config,
    operators,
    utils,
)


# CORE FUNCTIONS:


strudel = logging.getLogger(__name__) # STRUDEL_IMPORT_1
strudel.addHandler(logging.StreamHandler()) # STRUDEL_IMPORT_2
strudel.setLevel(logging.INFO) # STRUDEL_IMPORT_3
def generate(params, img_file, filename_prefix, props):
    # validate the params, specifically for the Stability API
    if not validate_params(params, props):
        strudel.info(f' Return False because validate_params(params, props) is False ') #  # STRUDEL_IF_LOG_1
        return False

    # map the generic params to the specific ones for the Stability API
    mapped_params = map_params(params)

    # create the headers
    headers = create_headers()

    # prepare the URL (specifically setting the engine id)
    api_url = f"{config.STABILITY_API_V1_URL}{props.sd_model}/image-to-image"

    # prepare the file input
    files = {
        "init_image": img_file,
    }

    # send the API request
    try:
        response = requests.post(
            api_url,
            headers=headers,
            files=files,
            data=mapped_params,
            timeout=request_timeout(),
        )
        img_file.close()
    except requests.exceptions.ReadTimeout:
        img_file.close()
        # return operators.handle_error(
        #     f"The server timed out. Try again in a moment, or get help. [Get help with timeouts]({config.HELP_WITH_TIMEOUTS_URL})",
        #     "timeout",
        # )

    # print log info for debugging
    # debug_log(response)

    # handle the response
    if response.status_code == 200:
        strudel.info(f' Return handle_success(response, filename_prefix) because response.status_code == 200') #  # STRUDEL_IF_LOG_1
        return handle_success(response, filename_prefix)
    else:
        strudel.info(f' Return handle_error(response) because response.status_code == 200') #  # STRUDEL_IF_LOG_ELSE_2
        return handle_error(response)


def upscale(img_file, filename_prefix, props):
    # create the headers
    headers = create_headers()

    # prepare the URL
    api_url = f"{config.STABILITY_API_V2_URL}upscale/fast"

    # prepare the file input
    files = {
        "image": img_file,
    }

    # prepare the params
    data = {"output_format": get_image_format().lower()}

    # send the API request
    try:
        response = requests.post(
            api_url, headers=headers, files=files, data=data, timeout=request_timeout()
        )
        img_file.close()
    except requests.exceptions.ReadTimeout:
        img_file.close()
        # return operators.handle_error(
        #     f"The server timed out during upscaling. Try again in a moment, or turn off upscaling.",
        #     "timeout",
        # )

    # print log info for debugging
    # debug_log(response)

    # handle the response
    if response.status_code == 200:
        strudel.info(f' Return handle_success(response, filename_prefix) because response.status_code == 200') #  # STRUDEL_IF_LOG_1
        return handle_success(response, filename_prefix)
    else:
        strudel.info(f' Return handle_error(response) because response.status_code == 200') #  # STRUDEL_IF_LOG_ELSE_2
        return handle_error(response)


def handle_success(response, filename_prefix):
    try:
        data = response.json()
        output_file = utils.create_temp_file(filename_prefix + "-")
    except:
        return operators.handle_error(
            f"Couldn't create a temp file to save image", "temp_file"
        )

    try:
        if "image" in data:
            strudel.info(' "image" in data') #  # STRUDEL_IF_LOG_0
            with open(output_file, "wb") as file:
                file.write(base64.b64decode(data["image"]))
        elif "artifacts" in data:
            strudel.info(' "artifacts" in data') #  # STRUDEL_IF_LOG_0
            for i, image in enumerate(data["artifacts"]):
                with open(output_file, "wb") as file:
                    file.write(base64.b64decode(image["base64"]))
        else:
            strudel.info(f' Return operators.handle_error(DreamStudio returned an unexpected response  . . ., "unexpected_response") because "artifacts" not in data') #  # STRUDEL_IF_LOG_ELSE_1
            return operators.handle_error(
                f"DreamStudio returned an unexpected response", "unexpected_response"
            )

        return output_file
    except:
        return operators.handle_error(
            f"DreamStudio returned an unexpected response", "unexpected_response"
        )


def handle_error(response):
    import json

    error_key = ""

    try:
        # convert the response to JSON (hopefully)
        response_obj = response.json()

        # get the message key from the response, if it exists
        message = response_obj.get("message", str(response.content))

        # handle the different types of errors
        if response_obj.get("timeout", False):
            strudel.info(' response_obj.get("timeout", False)') #  # STRUDEL_IF_LOG_0
            error_message = f"The server timed out. Try again in a moment, or get help. [Get help with timeouts]({config.HELP_WITH_TIMEOUTS_URL})"
            error_key = "timeout"
        else:
            strudel.info(' Assign tuple of length 2.=parse_message_for_error(message) because response_obj.get("timeout", False) is False ') #  # STRUDEL_IF_LOG_ELSE_1
            error_message, error_key = parse_message_for_error(message)
    except:
        error_message = f"(Server Error) An unknown error occurred in the Stability API. Full server response: {str(response.content)}"
        error_key = "unknown_error_response"

    strudel.info('Return operators.handle_error(error_message, error_key)') #  # STRUDEL_RETURN_TRACE_0
    return operators.handle_error(error_message, error_key)


# PRIVATE SUPPORT FUNCTIONS:


def create_headers():
    strudel.info('Method "create_headers" returns') #  # STRUDEL_RETURN_TRACE_0
    return {
        "User-Agent": f"Blender/{bpy.app.version_string}",
        "Accept": "application/json",
        "Authorization": f"Bearer {utils.get_dream_studio_api_key()}",
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
        strudel.info(' params["negative_prompt"]') #  # STRUDEL_IF_LOG_0
        mapped_params["text_prompts[1][text]"] = params["negative_prompt"]
        mapped_params["text_prompts[1][weight]"] = -1.0

    strudel.info('Method "map_params" returns "mapped_params"') #  # STRUDEL_RETURN_TRACE_0
    return mapped_params


def validate_params(params, props):
    # validate the dimensions (the sdxl 1024 model only supports a few specific image sizes)
    if props.sd_model.startswith(
        "stable-diffusion-xl-1024"
    ) and not utils.are_sdxl_1024_dimensions_valid(params["width"], params["height"]):
        strudel.info(' single-pass because props.sd_model.startswith("stable-diffusion-xl-1024") AND utils.are_sdxl_1024_dimensions_valid(params["width"], params["height"]) is False ') #  # STRUDEL_IF_LOG_1
        pass
        # return operators.handle_error(
        #     f"The SDXL model only supports these image sizes: {', '.join(utils.sdxl_1024_valid_dimensions)}. Please change your image size and try again.",
        #     "invalid_dimensions",
        # )
    elif params["steps"] < 10:
        strudel.info(f' Return operators.handle_error("Steps must be set to at least 10.", "steps_too_small") because params["steps"] < 10') #  # STRUDEL_IF_LOG_1
        return operators.handle_error(
            "Steps must be set to at least 10.", "steps_too_small"
        )
    else:
        strudel.info(f' Return True because params["steps"] < 10') #  # STRUDEL_IF_LOG_ELSE_2
        return True


def parse_message_for_error(message):
    if '"Authorization" is missing' in message:
        strudel.info(f' Return tuple of length 2. because "Authorization is missing" in message') #  # STRUDEL_IF_LOG_1
        return "Your DreamStudio API key is missing. Please enter it above.", "api_key"
    elif (
        "Incorrect API key" in message
        or "Unauthenticated" in message
        or "Unable to find corresponding account" in message
    ):
        strudel.info(' single-pass because "Incorrect API key" in message OR "Unauthenticated" in message OR "Unable to find corresponding account" in message') #  # STRUDEL_IF_LOG_1
        pass
        # return (
        #     f"Your DreamStudio API key is incorrect. Please find it on the DreamStudio website, and re-enter it above. [DreamStudio website]({config.DREAM_STUDIO_URL})",
        #     "api_key",
        # )
    elif "not have enough balance" in message:
        strudel.info(f' Return tuple of length 2. because "not have enough balance" in message') #  # STRUDEL_IF_LOG_1
        return (
            f"You don't have enough DreamStudio credits. Please purchase credits on the DreamStudio website or switch to a different backend in the AI Render add-on preferences. [DreamStudio website]({config.DREAM_STUDIO_URL})",
            "credits",
        )
    elif "invalid_prompts" in message:
        strudel.info(f' Return tuple of length 2. because "invalid_prompts" in message') #  # STRUDEL_IF_LOG_1
        return (
            "Invalid prompt. Your prompt includes filtered words. Please change your prompt and try again.",
            "prompt",
        )
    elif "image too large" in message:
        strudel.info(f' Return tuple of length 2. because "image too large" in message') #  # STRUDEL_IF_LOG_1
        return (
            "Image size is too large. Please decrease width/height.",
            "dimensions_too_large",
        )
    elif "invalid_height_or_width" in message:
        strudel.info(f' Return tuple of length 2. because "invalid_height_or_width" in message') #  # STRUDEL_IF_LOG_1
        return (
            "Invalid width or height. They must be in the range 128-2048 in multiples of 64.",
            "invalid_dimensions",
        )
    elif "body.sampler must be" in message:
        strudel.info(f' Return tuple of length 2. because "body.sampler must be" in message') #  # STRUDEL_IF_LOG_1
        return (
            "Invalid sampler. Please choose a new Sampler under 'Advanced Options'.",
            "sampler",
        )
    elif "body.cfg_scale must be" in message:
        strudel.info(f' Return tuple of length 2. because "body.cfg_scale must be" in message') #  # STRUDEL_IF_LOG_1
        return (
            "Invalid prompt strength. 'Prompt Strength' must be in the range 0-35.",
            "prompt_strength",
        )
    elif "body.seed must be" in message:
        strudel.info(f' Return tuple of length 2. because "body.seed must be" in message') #  # STRUDEL_IF_LOG_1
        return "Invalid seed value. Please choose a new 'Seed'.", "seed"
    elif "body.steps must be" in message:
        strudel.info(f' Return tuple of length 2. because "body.steps must be" in message') #  # STRUDEL_IF_LOG_1
        return "Invalid number of steps. 'Steps' must be in the range 10-150.", "steps"
    strudel.info('Method "parse_message_for_error" returns') #  # STRUDEL_RETURN_TRACE_0
    return (
        f"(Server Error) An error occurred in the Stability API. Full server response: {message}",
        "unknown_error",
    )


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
    strudel.info('Method "get_samplers" returns') #  # STRUDEL_RETURN_TRACE_0
    return [
        ("k_euler", "Euler", "", 10),
        ("k_euler_ancestral", "Euler a", "", 20),
        ("k_heun", "Heun", "", 30),
        ("k_dpm_2", "DPM2", "", 40),
        ("k_dpm_2_ancestral", "DPM2 a", "", 50),
        ("k_lms", "LMS", "", 60),
        ("K_DPMPP_2S_ANCESTRAL", "DPM++ 2S a", "", 110),
        ("K_DPMPP_2M", "DPM++ 2M", "", 120),
        ("ddim", "DDIM", "", 210),
        ("ddpm", "DDPM", "", 220),
    ]


def default_sampler():
    strudel.info('Return "K_DPMPP_2M"') #  # STRUDEL_RETURN_TRACE_0
    return "K_DPMPP_2M"


def get_upscaler_models(context):
    strudel.info('Method "get_upscaler_models" returns') #  # STRUDEL_RETURN_TRACE_0
    return [
        ("fast", "fast", ""),
    ]


def is_upscaler_model_list_loaded(context=None):
    strudel.info('Return True') #  # STRUDEL_RETURN_TRACE_0
    return True


def default_upscaler_model():
    strudel.info('Return "fast"') #  # STRUDEL_RETURN_TRACE_0
    return "fast"


def request_timeout():
    strudel.info('Return 55') #  # STRUDEL_RETURN_TRACE_0
    return 55


def get_image_format():
    strudel.info('Return "PNG"') #  # STRUDEL_RETURN_TRACE_0
    return "PNG"


def supports_negative_prompts():
    strudel.info('Return True') #  # STRUDEL_RETURN_TRACE_0
    return True


def supports_choosing_model():
    strudel.info('Return True') #  # STRUDEL_RETURN_TRACE_0
    return True


def supports_upscaling():
    strudel.info('Return True') #  # STRUDEL_RETURN_TRACE_0
    return True


def supports_choosing_upscaler_model():
    strudel.info('Return False') #  # STRUDEL_RETURN_TRACE_0
    return False


def supports_reloading_upscaler_models():
    strudel.info('Return False') #  # STRUDEL_RETURN_TRACE_0
    return False


def supports_choosing_upscale_factor():
    strudel.info('Return False') #  # STRUDEL_RETURN_TRACE_0
    return False


def fixed_upscale_factor():
    strudel.info('Return 4.0') #  # STRUDEL_RETURN_TRACE_0
    return 4.0


def supports_inpainting():
    strudel.info('Return False') #  # STRUDEL_RETURN_TRACE_0
    return False


def supports_outpainting():
    strudel.info('Return False') #  # STRUDEL_RETURN_TRACE_0
    return False


def min_image_size():
    strudel.info('Method "min_image_size" returns') #  # STRUDEL_RETURN_TRACE_0
    return 640 * 1536


def max_image_size():
    strudel.info('Method "max_image_size" returns') #  # STRUDEL_RETURN_TRACE_0
    return 1024 * 1024


def max_upscaled_image_size():
    strudel.info('Method "max_upscaled_image_size" returns') #  # STRUDEL_RETURN_TRACE_0
    return 4096 * 4096


def is_using_sdxl_1024_model(props):
    strudel.info('Return props.sd_model.startswith("stable-diffusion-xl-1024")') #  # STRUDEL_RETURN_TRACE_0
    return props.sd_model.startswith("stable-diffusion-xl-1024")

