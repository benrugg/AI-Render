import bpy
import requests
from .. import (
    config,
    operators,
    utils,
)


# CORE FUNCTIONS:

def send_to_api(params, img_file, filename_prefix):

    # create the headers
    headers = {
        "User-Agent": "Blender/" + bpy.app.version_string,
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Dream-Studio-Api-Key": utils.get_dream_studio_api_key(),
    }

    # prepare the file input
    files = {"file": img_file}

    # send the API request
    try:
        response = requests.post(config.API_URL, params=params, headers=headers, files=files, timeout=request_timeout())
        img_file.close()
    except requests.exceptions.ReadTimeout:
        img_file.close()
        return operators.handle_error(f"The server timed out. Try again in a moment, or get help. [Get help with timeouts]({config.HELP_WITH_TIMEOUTS_URL})")

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
        return operators.handle_error(f"Couldn't create a temp file to save image")


def handle_api_error(response):
    # handle 404
    if response.status_code in [403, 404]:
        return operators.handle_error("It looks like the web server this add-on relies on is missing. It's possible this is temporary, and you can try again later.")

    # handle 500
    elif response.status_code == 500:
        return operators.handle_error(f"An unknown error occurred in the DreamStudio API. Full server response: {str(response.content)}")

    # handle all other errors
    else:
        import json
        error_key = ''

        try:
            response_obj = response.json()
            if response_obj.get('Message', '') in ['Forbidden', None]:
                error_message = "It looks like the web server this add-on relies on is missing. It's possible this is temporary, and you can try again later."
            else:
                error_message = "(Server Error) " + response_obj.get('error', f"An unknown error occurred in the DreamStudio API. Full server response: {json.dumps(response_obj)}")
                error_key = response_obj.get('error_key', '')
        except:
            error_message = f"An unknown error occurred in the DreamStudio API. Full server response: {str(response.content)}"

        return operators.handle_error(error_message, error_key)


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
        ('plms', 'PLMS', '', 200),
        ('ddim', 'DDIM', '', 210),
    ]


def default_sampler():
    return 'k_lms'


def request_timeout():
    return 18 # until this is using DreamStudio's REST API, this has to stay low to avoid timeouts on our Lambda function


def get_image_format():
    return 'PNG'


def max_image_size():
    return 458752 # 896 x 512 or 960 x 448 (anything larger than this risks a timeout)
