import os
import sys
import bpy

# Add dependencies dir to local path (must do, because ga4mp does self-importing)
base = os.path.dirname(__file__)
module_dir = os.path.join(base, "dependencies")
sys.path.append(module_dir)

from ga4mp import GtagMP

CLIENT_ID_FILENAME = ".analytics_client_id"
API_SECRET = 'iVOq-KSaTDGvpfvk5HO1bg'
MEASUREMENT_ID = 'G-GW18C76QQL'

ga = None
env_params = {}


# PRIVATE FUNCTIONS:

def init_analytics(bl_info):
    global ga, env_params

    # initialize the analytics library
    ga = GtagMP(measurement_id=MEASUREMENT_ID, api_secret=API_SECRET, client_id='1234567890.1234567890')

    # get our stored client ID, or create and store a new one
    client_id = get_stored_client_id()
    if not client_id:
        client_id = create_random_client_id()
        store_client_id(client_id)

    # set the client ID
    ga.client_id = client_id

    # set the environment parameters
    env_params = {
        'ai_render_version': '-'.join(map(str, bl_info['version'])),
        'blender_version': bpy.app.version_string,
        'platform': sys.platform,
    }


def get_stored_client_id():
    file_path = os.path.join(os.path.dirname(__file__), CLIENT_ID_FILENAME)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return f.read()
    else:
        return None


def store_client_id(client_id):
    file_path = os.path.join(os.path.dirname(__file__), CLIENT_ID_FILENAME)
    with open(file_path, "w") as f:
        f.write(client_id)


def create_random_client_id():
    global ga
    return ga.random_client_id()


def count_words(text):
    # convert punctuation to spaces
    for char in '-.,\n':
        text=text.replace(char, ' ')

    # split words by spaces and count
    return len(text.split())


def get_first_words(text, num_words):
    words = text.split()
    return ' '.join(words[:num_words])


# PUBLIC FUNCTIONS:

def track_event(event_name, event_params):
    global ga
    event = ga.create_new_event(name=event_name)

    for key, value in event_params.items():
        event.set_event_param(name=key, value=value)

    # print("Track event:", event_name, event_params, ga.client_id)

    ga.send(events=[event])


def prepare_event(event_name, generation_params=None, additional_params=None):
    global env_params

    if event_name == 'generate_image':
        return {
            "ai_render_version": env_params['ai_render_version'],
            "blender_version": env_params['blender_version'],
            "platform": env_params['platform'],
            "backend": additional_params['backend'],
            "width": generation_params['width'],
            "height": generation_params['height'],
            "model": additional_params['model'],
            "prompt_length": count_words(generation_params['prompt']) - count_words(additional_params['preset_style']),
            "has_negative_prompt": "yes" if generation_params['negative_prompt'] else "no",
            "preset_style": get_first_words(additional_params['preset_style'], 3),
            "image_similarity": round(generation_params['image_similarity'], 2),
            "sampler": generation_params['sampler'],
            "is_animation_frame": additional_params['is_animation_frame'],
            "has_animated_prompt": additional_params['has_animated_prompt'],
            "duration": additional_params['duration'],
        }
    raise ValueError("Unknown analytics event name: " + event_name)


def register(bl_info):
    init_analytics(bl_info)


def unregister():
    global ga
    del ga
