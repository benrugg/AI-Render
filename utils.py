# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


import bpy
import re
import os
import shutil
import math
import platform
import time
import tempfile
from . import config
from .sd_backends import (
    comfyui_api,
    automatic1111_api,
    stability_api,
    stablehorde_api,
    shark_api,
)

# Colorama Placeholder
from . import Fore

min_dimension_size = 128
max_dimension_size = 2048
valid_dimension_step_size = 64
sdxl_1024_valid_dimensions = ['1024x1024', '1152x896', '896x1152', '1216x832', '832x1216', '1344x768', '768x1344', '1536x640', '640x1536']

example_dimensions = [512, 640, 768, 896, 960, 1024, 1280, 1344, 1600, 1920, 2048]
file_formats = {"JPEG": "jpg", "BMP": "bmp", "IRIS": "rgb", "PNG": "png", "JPEG2000": "jp2", "TARGA": "tga", "TARGA_RAW": "tga", "CINEON": "cin", "DPX": "dpx", "OPEN_EXR_MULTILAYER": "exr", "OPEN_EXR": "exr", "HDR": "hdr", "TIFF": "tif", "WEBP": "webp"}

max_filename_length = 128 if platform.system() == "Windows" else 230


def get_addon_preferences(context=None):
    if not context:
        context = bpy.context
    return context.preferences.addons[__package__].preferences


def create_temp_file(prefix, suffix=".png"):
    return tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix).name


def sanitize_filename(filename, extra_length=0):
    # remove any characters that aren't alphanumeric, space, underscore, dash, period, comma or parentheses
    filename = re.sub(r'[^\w \-_\.(),]', '_', filename)
    # remove any double underscores, dashes, periods
    filename = re.sub(r'([-_\.]){2,}', r'\1', filename)
    # limit to max filename length
    filename = filename[:(max_filename_length - extra_length)]
    return filename


def sanitize_filename_template(template):
    # remove any {vars} that aren't in the list of allowed vars
    return re.sub(r'{(.*?)}', lambda match: match.group(0) if match.group(1) in config.filename_template_allowed_vars else '', template)


def get_image_filename(scene, prompt, negative_prompt, suffix=""):
    props = scene.air_props
    timestamp = int(time.time())
    template = props.image_filename_template
    if not template:
        template = config.default_image_filename_template

    template = sanitize_filename_template(template)

    full_filename = f"{template}".format(
        timestamp=timestamp,
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=get_output_width(scene),
        height=get_output_height(scene),
        seed=props.seed,
        image_similarity=round(props.image_similarity, 2),
        prompt_strength=round(props.cfg_scale, 2),
        steps=props.steps,
    )

    sanitized_filename = sanitize_filename(full_filename, len(suffix))
    return sanitized_filename + suffix


def get_image_format(to_lower = True):
    image_format = get_active_backend().get_image_format()
    return image_format.lower() if to_lower else image_format


def should_autosave_after_image(props):
    # return true to signify we should autosave the after image, if that setting is on,
    # and the path is valid, and we're not rendering an animation
    return \
        props.do_autosave_after_images \
        and props.autosave_image_path \
        and not props.is_rendering_animation \
        and not props.is_rendering_animation_manually


def get_filepath_in_package(path, filename="", starting_dir=__file__):
    """Convert a relative path in the add-on package to an absolute path"""
    script_path = os.path.dirname(os.path.realpath(starting_dir))
    subpath = path + os.sep + filename if path else filename
    return os.path.join(script_path, subpath)


def get_absolute_path_for_output_file(path, filename):
    """Convert a relative path in the blend file to an absolute path"""
    return os.path.join(os.path.abspath(bpy.path.abspath(path)), filename)


def does_path_exist(path):
    return os.path.exists(os.path.abspath(bpy.path.abspath(path)))


def get_filename_from_path(file_path, include_extension=True):
    filename_and_extension = os.path.splitext(os.path.basename(file_path))
    if include_extension:
        return filename_and_extension[0] + filename_and_extension[1]
    else:
        return filename_and_extension[0]


def copy_file(src, dest):
    shutil.copy2(src, dest)


def get_preset_style_thumnails_filepath():
    return get_filepath_in_package("style_thumbnails")


def get_extension_from_file_format(file_format):
    if file_format in file_formats:
        return file_formats[file_format]
    else:
        return ""


def activate_workspace(context=None, workspace=None, workspace_id=None):
    if not workspace:
        workspace = bpy.data.workspaces.get(workspace_id)
        if not workspace:
            return

    if context and context.window:
        context.window.workspace = workspace
    else:
        bpy.data.window_managers[0].windows[0].workspace = workspace


def get_areas_by_type(area_type, scene=None, context=None, workspace_id=None):
    if not scene:
        scene = context.scene
    if not context:
        context = bpy.context

    results = []

    # get an area from our desired workspace, if we have one
    if (workspace_id):
        workspace = bpy.data.workspaces[workspace_id]
        for area in workspace.screens[0].areas:
            if area.type == area_type:
                results.append(area)
        return results
    else:
        # otherwise, get an area from the current screen in any open window
        for window in context.window_manager.windows:
            if window.scene != scene:
                continue

            for area in window.screen.areas:
                if area.type == area_type:
                    results.append(area)
        return results


def find_area_showing_render_result(scene=None, context=None, workspace_id=None):
    areas = get_areas_by_type('IMAGE_EDITOR', scene, context, workspace_id)
    potential_area = None

    # loop through all areas, prioritizing the render result area, but returning
    # any image editor area as a backup
    for area in areas:
        active_image = area.spaces.active.image
        if active_image is not None:
            if active_image.type == 'RENDER_RESULT':
                return area
            else:
                potential_area = area

    return potential_area


def split_area(context, area, direction='HORIZONTAL', factor=0.5):
    if bpy.app.version >= (3, 2, 0):
        with context.temp_override(area=area):
            bpy.ops.screen.area_split(direction=direction, factor=factor)
    else:
        override = context.copy()
        override['area'] = area
        bpy.ops.screen.area_split(override, direction=direction, factor=factor)


def view_sd_in_render_view(img, scene=None, context=None):
    # get the render result area, if it's open
    image_editor_area = find_area_showing_render_result(scene, context)

    # if it's not open, try to switch to the render workspace and then get the area
    if not image_editor_area:
        activate_workspace(workspace_id='Rendering')
        image_editor_area = find_area_showing_render_result(scene, context, 'Rendering')

    # if we have an area, set the image
    if image_editor_area:
        image_editor_area.spaces.active.image = img


def get_animated_prompt_text_data_block():
    if config.animated_prompts_text_name in bpy.data.texts:
        return bpy.data.texts[config.animated_prompts_text_name]
    else:
        return None


def get_dream_studio_api_key(context=None):
    return get_addon_preferences(context).dream_studio_api_key


def get_stable_horde_api_key(context=None):
    return get_addon_preferences(context).stable_horde_api_key


def sd_backend(context=None):
    active_sd_backend = get_addon_preferences(context).sd_backend
    return active_sd_backend


def sd_backend_formatted_name(context=None):
    backend = sd_backend(context)

    if backend == 'dreamstudio':
        return 'DreamStudio'
    elif backend == 'stablehorde':
        return 'Stable Horde'
    elif backend == 'automatic1111':
        return 'Automatic1111'
    elif backend == 'shark':
        return 'SHARK by nod.ai'
    elif backend == 'comfyui':
        return 'ComfyUI'


def local_sd_url(context=None):
    return get_addon_preferences(context).local_sd_url


def local_sd_timeout(context=None):
    return get_addon_preferences(context).local_sd_timeout


def get_output_width(scene):
    return round(scene.render.resolution_x * scene.render.resolution_percentage / 100)


def get_output_height(scene):
    return round(scene.render.resolution_y * scene.render.resolution_percentage / 100)


def get_upscaled_width(scene):
    if not scene:
        scene = bpy.context.scene

    upscale_factor = scene.air_props.upscale_factor
    return round(get_output_width(scene) * upscale_factor)


def get_upscaled_height(scene):
    if not scene:
        scene = bpy.context.scene

    upscale_factor = scene.air_props.upscale_factor
    return round(get_output_height(scene) * upscale_factor)


def sanitized_upscaled_width(max_upscaled_image_size, scene=None):
    if not scene:
        scene = bpy.context.scene

    upscaled_width = get_upscaled_width(scene)
    upscaled_height = get_upscaled_height(scene)

    if upscaled_width * upscaled_height > max_upscaled_image_size:
        return round(math.sqrt(max_upscaled_image_size * (upscaled_width / upscaled_height)))
    else:
        return upscaled_width


def sanitized_upscaled_height(max_upscaled_image_size, scene=None):
    if not scene:
        scene = bpy.context.scene

    upscaled_width = get_upscaled_width(scene)
    upscaled_height = get_upscaled_height(scene)

    if upscaled_width * upscaled_height > max_upscaled_image_size:
        return round(math.sqrt(max_upscaled_image_size * (upscaled_height / upscaled_width)))
    else:
        return upscaled_height


def are_dimensions_valid(scene):
    if is_using_sdxl_1024_model(scene):
        return are_sdxl_1024_dimensions_valid(get_output_width(scene), get_output_height(scene))
    else:
        return (
            get_output_width(scene) in range(
                min_dimension_size,
                max_dimension_size + valid_dimension_step_size, # range is exclusive of the last value
                valid_dimension_step_size
            ) and
            get_output_height(scene) in range(
                min_dimension_size,
                max_dimension_size + valid_dimension_step_size, # range is exclusive of the last value
                valid_dimension_step_size
            )
        )


def are_sdxl_1024_dimensions_valid(width, height):
    dimensions = f"{width}x{height}"
    return dimensions in sdxl_1024_valid_dimensions


def are_dimensions_too_large(scene):
    return get_output_width(scene) * get_output_height(scene) > get_active_backend().max_image_size()


def are_dimensions_too_small(scene):
    return get_output_width(scene) * get_output_height(scene) < get_active_backend().min_image_size()


def are_upscaled_dimensions_too_large(scene):
    return get_upscaled_width(scene) * get_upscaled_height(scene) > get_active_backend().max_upscaled_image_size()


def generate_example_dimensions_tuple_list():
    return_tuple = lambda num: (str(num), str(num) + " px", str(num))
    return list(map(return_tuple, example_dimensions))


def generate_sdxl_1024_dimensions_tuple_list():
    return_tuple = lambda dimension: (dimension, ' x '.join(dimension.split('x')), dimension)
    return list(map(return_tuple, sdxl_1024_valid_dimensions))


def is_using_sdxl_1024_model(scene):
    return get_active_backend().is_using_sdxl_1024_model(scene.air_props)


def has_url(text, strict_match_protocol=False):
    # remove markdown *
    text = text.replace('*','')

    # Anything that isn't a square closing bracket
    name_regex = "[^]]+"

    # http:// or https:// followed by anything but a closing paren
    url_in_markup_regex = "http[s]?://[^)]+"

    # first look for markup urls
    markup_regex = f"\[({name_regex})]\(\s*({url_in_markup_regex})\s*\)"

    urls = re.findall(markup_regex, text, re.IGNORECASE)

    if len(urls) > 0:
        replacechars = "[]()"

        for url in urls:
            text = re.sub(markup_regex, "", text)
            for ch in replacechars:
                text.replace(ch, '')

    # if none found, look for url without markup
    else:
        if strict_match_protocol:
            bare_url_regex = r"(https{0,1}:\/\/[A-Za-z0-9\-\._~:\/\?#\[\]@!\$&'\(\)\*\+\,;%=]+)"
        else:
            bare_url_regex = r"(?:[a-z]{3,9}:\/\/?[\-;:&=\+\$,\w]+?[a-z0-9\.\-]+|[\/a-z0-9]+\.|[\-;:&=\+\$,\w]+@)[a-z0-9\.\-]+(?:(?:\/[\+~%\/\.\w\-_]*)?\??[\-\+=&;%@\.\w_]*#?[\.\!\/\\\w]*)?"

        urls = re.findall(bare_url_regex, text, re.IGNORECASE)

        for i, url in enumerate(urls):
            urls[i] = [url, url]

    # return what was found (could be just text)
    return urls, text


def label_multiline(layout, text='', icon='NONE', width=-1, max_lines=12, use_urls=True, alignment="LEFT", alert=False):
    '''
     draw a ui label, but try to split it in multiple lines.

    Parameters
    ----------
    layout
    text
    icon
    width width to split by in px
    max_lines maximum lines to draw
    use_urls - automatically parse urls to buttons
    Returns
    -------
    rows of the text(to add extra elements)
    '''
    rows = []
    if text.strip() == '':
        return [layout.row()]

    text = text.replace("\r\n", "\n")

    if use_urls:
        urls, text = has_url(text, strict_match_protocol=True)
    else:
        urls = []

    lines = text.split("\n")

    if width > 0:
        char_threshold = int(width / 5.7)
    else:
        char_threshold = 35

    line_index = 0
    for line in lines:

        line_index += 1
        while len(line) > char_threshold:
            #find line split close to the end of line
            i = line.rfind(" ", 0, char_threshold)
            #split long words
            if i < 1:
                i = char_threshold
            l1 = line[:i]

            row = layout.row()
            if alert: row.alert = True
            row.alignment = alignment
            row.label(text=l1, icon=icon)
            rows.append(row)

            # set the icon to none after the first row
            icon = "NONE"

            line = line[i:].lstrip()
            line_index += 1
            if line_index > max_lines:
                break

        if line_index > max_lines:
            break

        row = layout.row()
        if alert: row.alert = True
        row.alignment = alignment
        row.label(text=line, icon=icon)
        rows.append(row)

        # set the icon to none after the first row
        icon = "NONE"

    # if we have urls, include them as buttons at the end
    if use_urls:
        for url in urls:
            row = layout.row()
            row.operator("wm.url_open", text=url[0], icon="URL").url = url[1]

    # return the resulting rows
    return rows


def get_active_backend():
    backend = sd_backend()

    if backend == "dreamstudio":
        return stability_api
    elif backend == "stablehorde":
        return stablehorde_api
    elif backend == "automatic1111":
        return automatic1111_api
    elif backend == "shark":
        return shark_api
    elif backend == "comfyui":
        return comfyui_api


def is_installation_valid():
    return __package__ == config.package_name


def show_invalid_installation_message(layout, width):
    box = layout.box()
    box.label(text="Installation Error:")

    label_multiline(box, text=f"It looks like this add-on wasn't installed correctly. Please remove it and get a new copy. [Get AI Render]({config.ADDON_DOWNLOAD_URL})", icon="ERROR", alert=True, width=width)
