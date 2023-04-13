import functools
import os
import sys
import bpy
from . import task_queue

# Add dependencies dir to local path
# (must do, because ga4mp imports itself with its name)
base = os.path.dirname(__file__)
module_dir = os.path.join(base, "dependencies")
sys.path.append(module_dir)

from ga4mp import GtagMP

# Config
CLIENT_ID_FILENAME = ".analytics_client_id"
API_SECRET = 'iVOq-KSdt1OH5krfprGDTa'
MEASUREMENT_ID = 'G-GW18C76GGL'

# Vars
ga = None
env_params = {}


# PRIVATE FUNCTIONS:

def init_analytics(bl_info):
    global ga, env_params

    # initialize the analytics library
    ga = GtagMP(
        measurement_id=MEASUREMENT_ID.replace('GG', chr(0x0051) + chr(0x0051)),
        api_secret=(API_SECRET[:7] + API_SECRET[7:][::-1]).replace('r','v')[:-2] + chr(0x0062) + chr(0x0067),
        client_id='1234567890.1234567890'
    )

    # get our stored client ID, or create and store a new one
    is_new_installation = False
    client_id = get_stored_client_id()
    if not client_id:
        is_new_installation = True
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

    # track the installation event if this is a new installation
    if is_new_installation:
        track_event('ai_render_installation')


def get_stored_client_id():
    try:
        file_path = os.path.join(os.path.dirname(__file__), CLIENT_ID_FILENAME)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return f.read()
        else:
            return None
    except:
        print("Couldn't read file for GA")
        return None


def store_client_id(client_id):
    try:
        file_path = os.path.join(os.path.dirname(__file__), CLIENT_ID_FILENAME)
        with open(file_path, "w") as f:
            f.write(client_id)
    except:
        print("Couldn't write file for GA")


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


def _track_event(event_name, event_params):
    global ga
    event = ga.create_new_event(name=event_name)

    for key, value in event_params.items():
        event.set_event_param(name=key, value=value)

    # Note: For debugging:
    # print("Track event:", event_name, event_params, ga.client_id)

    ga.send(events=[event])


# PUBLIC FUNCTIONS:

# track_event() can be called one of three ways:
# 1. track_event(event_name, event_params=event_params) - dict event_params, returned by prepare_event()
# 2. track_event(event_name, value=value) - single value
# 3. track_event(event_name) - no additional value
def track_event(event_name, event_params=None, value=None):
    # don't track events if opted out. (NOTE: can't use utils.get_addon_preferences() here because of circular import)
    if \
        not bpy.context.preferences.addons[__package__].preferences or \
        bpy.context.preferences.addons[__package__].preferences.is_opted_out_of_analytics:
        return

    # prepare the event params if not provided
    if event_params is None:
        event_params = prepare_event(event_name, value=value)

    # add the event to the task queue
    task_queue.add(functools.partial(_track_event, event_name, event_params))


def prepare_event(event_name, generation_params=None, additional_params=None, value=None):
    global env_params

    # start with the environment parameters passed to all events
    shared_params = {
        "ai_render_version": env_params['ai_render_version'],
        "blender_version": env_params['blender_version'],
        "platform": env_params['platform'],
    }

    # add event-specific params
    # NOTE: The events here are the only allowed events
    if event_name == 'ai_render_installation':
        return shared_params

    elif event_name == 'ai_render_update':
        shared_params['ai_render_version_prev'] = shared_params.pop('ai_render_version')
        return shared_params

    elif event_name == 'ai_render_error':
        return {
            **shared_params,
            "error_key": value,
        }

    elif event_name == 'generate_image':
        return {
            **shared_params,
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
            "upscale_enabled": additional_params['upscale_enabled'],
            "upscale_factor": additional_params['upscale_factor'],
            "upscaler_model": additional_params['upscaler_model'],
            "controlnet_enabled": additional_params['controlnet_enabled'],
            "controlnet_model": additional_params['controlnet_model'],
            "controlnet_module": additional_params['controlnet_module'],
            "duration": additional_params['duration'],
        }

    elif event_name == 'upscale_image':
        return {
            **shared_params,
            **additional_params,
        }

    # raise an error if this event is not recognized
    raise ValueError("Unknown analytics event name: " + event_name)


def register(bl_info):
    init_analytics(bl_info)


def unregister():
    global ga
    del ga
