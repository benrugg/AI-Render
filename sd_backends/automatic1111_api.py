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

    # map the generic params to the specific ones for the Automatic1111 API
    map_params(params)

    # add a base 64 encoded image to the params
    params["init_images"] = ["data:image/png;base64," + base64.b64encode(img_file.read()).decode()]
    img_file.close()

    # add args for ControlNet if it's enabled
    if props.controlnet_is_enabled:
        controlnet_model = props.controlnet_model
        controlnet_module = props.controlnet_module
        controlnet_weight = props.controlnet_weight

        if not controlnet_model:
            return operators.handle_error(f"No ContolNet model selected. Either choose a new model or disable ControlNet. [Get help]({config.HELP_WITH_CONTROLNET_URL})", "controlnet_model_missing")

        params["alwayson_scripts"] = {
            "controlnet": {
                "args": [
                    {
                    "weight": controlnet_weight,
                    "module": controlnet_module,
                    "model": controlnet_model
                    }
                ]
            }
        }

    # prepare the server url
    try:
        server_url = get_server_url("/sdapi/v1/img2img")
    except:
        return operators.handle_error(f"You need to specify a location for the local Stable Diffusion server in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_url_missing")

    # send the API request
    response = do_post(server_url, params)

    if response == False:
        return False

    # handle the response
    if response.status_code == 200:
        return handle_success(response, filename_prefix)
    else:
        return handle_error(response)


def upscale(img_file, filename_prefix, props):

    # prepare the params
    data = {
        "resize_mode": 0,
        "show_extras_results": True,
        "gfpgan_visibility": 0,
        "codeformer_visibility": 0,
        "codeformer_weight": 0,
        "upscaling_resize": props.upscale_factor,
        "upscaling_resize_w": utils.sanitized_upscaled_width(max_upscaled_image_size()),
        "upscaling_resize_h": utils.sanitized_upscaled_height(max_upscaled_image_size()),
        "upscaling_crop": True,
        "upscaler_1": props.upscaler_model,
        "upscaler_2": "None",
        "extras_upscaler_2_visibility": 0,
        "upscale_first": True,
    }

    # add a base 64 encoded image to the params
    data["image"] = "data:image/png;base64," + base64.b64encode(img_file.read()).decode()
    img_file.close()

    # prepare the server url
    try:
        server_url = get_server_url("/sdapi/v1/extra-single-image")
    except:
        return operators.handle_error(f"You need to specify a location for the local Stable Diffusion server in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_url_missing")

    # send the API request
    response = do_post(server_url, data)

    # print log info for debugging
    # debug_log(response)

    if response == False:
        return False

    # handle the response
    if response.status_code == 200:
        return handle_success(response, filename_prefix)
    else:
        return handle_error(response)


def handle_success(response, filename_prefix):

    # ensure we have the type of response we are expecting
    try:
        response_obj = response.json()
        base64_img = response_obj.get("images", [False])[0] or response_obj.get("image")
    except:
        print("Automatic1111 response content: ")
        print(response.content)
        return operators.handle_error("Received an unexpected response from the Automatic1111 Stable Diffusion server.", "unexpected_response")

    # create a temp file
    try:
        output_file = utils.create_temp_file(filename_prefix + "-")
    except:
        return operators.handle_error("Couldn't create a temp file to save image.", "temp_file")

    # decode base64 image
    try:
        img_binary = base64.b64decode(base64_img.replace("data:image/png;base64,", ""))
    except:
        return operators.handle_error("Couldn't decode base64 image from the Automatic1111 Stable Diffusion server.", "base64_decode")

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
                return operators.handle_error(f"It looks like the Automatic1111 server is running, but it's not in API mode. [Get help]({config.HELP_WITH_AUTOMATIC1111_NOT_IN_API_MODE_URL})", "automatic1111_not_in_api_mode")
            elif response_obj.get('detail') and response_obj['detail'] == "Sampler not found":
                return operators.handle_error("The sampler you selected is not available on the Automatic1111 Stable Diffusion server. Please select a different sampler.", "invalid_sampler")
            else:
                return operators.handle_error(f"An error occurred in the Automatic1111 Stable Diffusion server. Full server response: {json.dumps(response_obj)}", "unknown_error")
        except:
            return operators.handle_error(f"It looks like the Automatic1111 server is running, but it's not in API mode. [Get help]({config.HELP_WITH_AUTOMATIC1111_NOT_IN_API_MODE_URL})", "automatic1111_not_in_api_mode")

    else:
        return operators.handle_error("An error occurred in the Automatic1111 Stable Diffusion server. Check the server logs for more info.", "unknown_error_response")


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


def map_params(params):
    params["denoising_strength"] = round(1 - params["image_similarity"], 2)
    params["sampler_index"] = params["sampler"]


def do_post(url, data):
    # send the API request
    try:
        return requests.post(url, json=data, headers=create_headers(), timeout=utils.local_sd_timeout())
    except requests.exceptions.ConnectionError:
        return operators.handle_error(f"The local Stable Diffusion server couldn't be found. It's either not running, or it's running at a different location than what you specified in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_not_found")
    except requests.exceptions.MissingSchema:
        return operators.handle_error(f"The url for your local Stable Diffusion server is invalid. Please set it correctly in the add-on preferences. [Get help]({config.HELP_WITH_LOCAL_INSTALLATION_URL})", "local_server_url_invalid")
    except requests.exceptions.ReadTimeout:
        return operators.handle_error("The local Stable Diffusion server timed out. Set a longer timeout in AI Render preferences, or use a smaller image size.", "timeout")


def debug_log(response):
    # print("request body:")
    # print(response.request.body)
    # print("\n")

    print("response body:")
    print(response.content)

    try:
        print(response.json())
    except:
        print("body not json")


# PUBLIC SUPPORT FUNCTIONS:

def get_samplers():
    # NOTE: Keep the number values (fourth item in the tuples) in sync with DreamStudio's
    # values (in stability_api.py). These act like an internal unique ID for Blender
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
        ('DPM++ SDE Karras', 'DPM++ SDE Karras', '', 105),
        ('DPM++ 2S a', 'DPM++ 2S a', '', 110),
        ('DPM++ 2M', 'DPM++ 2M', '', 120),
        ('DPM++ SDE', 'DPM++ SDE', '', 125),
        ('PLMS', 'PLMS', '', 200),
        ('DDIM', 'DDIM', '', 210),
    ]


def default_sampler():
    return 'LMS'


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
    return False


def supports_upscaling():
    return True


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


def get_available_controlnet_models(context):
    models = context.scene.air_props.controlnet_available_models

    if (not models):
        return []
    else:
        enum_list = []
        for item in models.split("||||"):
            enum_list.append((item, item, ""))
        return enum_list


def get_available_controlnet_modules(context):
    modules = context.scene.air_props.controlnet_available_modules

    if (not modules):
        return []
    else:
        enum_list = []
        for item in modules.split("||||"):
            enum_list.append((item, item, ""))
        return enum_list


def choose_controlnet_defaults(context):
    models = get_available_controlnet_models(context)
    modules = get_available_controlnet_modules(context)

    if (not models) or (not modules):
        return

    # priority order for models and modules
    priority_order = ['depth', 'openpose', 'normal', 'canny', 'scribble']

    # choose a matching model and module in the priority order:
    for item in priority_order:
        model_selection = None
        module_selection = None

        for model in models:
            if item in model[0]:
                model_selection = model[0]
                break

        for module in modules:
            if item in module[0]:
                module_selection = module[0]
                break

        if model_selection and module_selection:
            context.scene.air_props.controlnet_model = model_selection
            context.scene.air_props.controlnet_module = module_selection
            return


def load_upscaler_models(context):
    try:
        # set a flag to indicate whether the list of models has already been loaded
        was_already_loaded = is_upscaler_model_list_loaded(context)

        # get the list of available upscaler models from the Automatic1111 api
        server_url = get_server_url("/sdapi/v1/upscalers")
        headers = { "Accept": "application/json" }
        response = requests.get(server_url, headers=headers, timeout=5)
        response_obj = response.json()
        print("Upscaler models returned from Automatic1111 API:")
        print(response_obj)

        # store the list of models in the scene properties
        if not response_obj:
            return operators.handle_error(f"No upscaler models are installed in Automatic1111. [Get help]({config.HELP_WITH_AUTOMATIC1111_UPSCALING_URL})")
        else:
            # map the response object to a list of model names
            upscaler_models = []
            for model in response_obj:
                if (model["name"] != "None"):
                    upscaler_models.append(model["name"])
            context.scene.air_props.automatic1111_available_upscaler_models = "||||".join(upscaler_models)

            # if the list of models was not already loaded, set the default model
            if not was_already_loaded:
                context.scene.air_props.upscaler_model = default_upscaler_model()

            # return success
            return True
    except:
        return operators.handle_error(f"Couldn't get the list of available upscaler models from the Automatic1111 server. [Get help]({config.HELP_WITH_AUTOMATIC1111_UPSCALING_URL})")


def load_controlnet_models(context):
    try:
        # get the list of available controlnet models from the Automatic1111 api
        server_url = get_server_url("/controlnet/model_list")
        headers = { "Accept": "application/json" }
        response = requests.get(server_url, headers=headers, timeout=5)
        response_obj = response.json()
        print("ControlNet models returned from Automatic1111 API:")
        print(response_obj)

        # store the list of models in the scene properties
        models = response_obj["model_list"]
        if not models:
            return operators.handle_error(f"You don't have any ControlNet models installed. You will need to download them from Hugging Face. [Get help]({config.HELP_WITH_CONTROLNET_URL})")
        else:
            context.scene.air_props.controlnet_available_models = "||||".join(models)
            return True
    except:
        return operators.handle_error(f"Couldn't get the list of available ControlNet models from the Automatic1111 server. Make sure ControlNet is installed and activated. [Get help]({config.HELP_WITH_CONTROLNET_URL})")


def load_controlnet_modules(context):
    try:
        # get the list of available controlnet modules from the Automatic1111 api
        server_url = get_server_url("/controlnet/module_list")
        headers = { "Accept": "application/json" }
        response = requests.get(server_url, headers=headers, timeout=5)
        response_obj = response.json()
        print("ControlNet modules returned from Automatic1111 API:")
        print(response_obj)

        # store the list of modules in the scene properties
        modules = response_obj["module_list"]
        context.scene.air_props.controlnet_available_modules = "||||".join(modules)
        return True
    except:
        return operators.handle_error(f"Couldn't get the list of available ControlNet modules from the Automatic1111 server. Make sure ControlNet is installed and activated. [Get help]({config.HELP_WITH_CONTROLNET_URL})")
