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


import logging # STRUDEL_IMPORT_0
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
    automatic1111_api,
    stability_api,
    stablehorde_api,
    shark_api,
)

strudel = logging.getLogger(__name__) # STRUDEL_IMPORT_1
strudel.addHandler(logging.StreamHandler()) # STRUDEL_IMPORT_2
strudel.setLevel(logging.INFO) # STRUDEL_IMPORT_3
min_dimension_size = 128
max_dimension_size = 2048
valid_dimension_step_size = 64
sdxl_1024_valid_dimensions = [
    "1024x1024",
    "1152x896",
    "896x1152",
    "1216x832",
    "832x1216",
    "1344x768",
    "768x1344",
    "1536x640",
    "640x1536",
]

example_dimensions = [512, 640, 768, 896, 960, 1024, 1280, 1344, 1600, 1920, 2048]
file_formats = {
    "JPEG": "jpg",
    "BMP": "bmp",
    "IRIS": "rgb",
    "PNG": "png",
    "JPEG2000": "jp2",
    "TARGA": "tga",
    "TARGA_RAW": "tga",
    "CINEON": "cin",
    "DPX": "dpx",
    "OPEN_EXR_MULTILAYER": "exr",
    "OPEN_EXR": "exr",
    "HDR": "hdr",
    "TIFF": "tif",
    "WEBP": "webp",
}

max_filename_length = 128 if platform.system() == "Windows" else 230


def get_addon_preferences(context=None):
    if not context:
        strudel.info(' Assign context=bpy.context because "context" is evaluated to False') #  # STRUDEL_IF_LOG_1
        context = bpy.context
    strudel.info('Method "get_addon_preferences" returns') #  # STRUDEL_RETURN_TRACE_0
    return context.preferences.addons[__package__].preferences


def create_temp_file(prefix, suffix=".png"):
    strudel.info('Method "create_temp_file" returns') #  # STRUDEL_RETURN_TRACE_0
    return tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix).name


def sanitize_filename(filename, extra_length=0):
    # remove any characters that aren't alphanumeric, space, underscore, dash, period, comma or parentheses
    filename = re.sub(r"[^\w \-_\.(),]", "_", filename)
    # remove any double underscores, dashes, periods
    filename = re.sub(r"([-_\.]){2,}", r"\1", filename)
    # limit to max filename length
    filename = filename[: (max_filename_length - extra_length)]
    strudel.info('Method "sanitize_filename" returns "filename"') #  # STRUDEL_RETURN_TRACE_0
    return filename


def sanitize_filename_template(template):
    # remove any {vars} that aren't in the list of allowed vars
    strudel.info('Return re.sub("((.*?))", Lambda in If condition., template)') #  # STRUDEL_RETURN_TRACE_0
    return re.sub(
        r"{(.*?)}",
        lambda match: (
            match.group(0)
            if match.group(1) in config.filename_template_allowed_vars
            else ""
        ),
        template,
    )


def get_image_filename(scene, prompt, negative_prompt, suffix=""):
    props = scene.air_props
    timestamp = int(time.time())
    template = props.image_filename_template
    if not template:
        strudel.info(' Assign template=config.default_image_filename_template because "template" is evaluated to False') #  # STRUDEL_IF_LOG_1
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
    strudel.info('Method "get_image_filename" returns') #  # STRUDEL_RETURN_TRACE_0
    return sanitized_filename + suffix


def get_image_format(to_lower=True):
    image_format = get_active_backend().get_image_format()
    strudel.info('Method "get_image_format" returns') #  # STRUDEL_RETURN_TRACE_0
    return image_format.lower() if to_lower else image_format


def should_autosave_after_image(props):
    # return true to signify we should autosave the after image, if that setting is on,
    # and the path is valid, and we're not rendering an animation
    strudel.info('Method "should_autosave_after_image" returns') #  # STRUDEL_RETURN_TRACE_0
    return (
        props.do_autosave_after_images
        and props.autosave_image_path
        and not props.is_rendering_animation
        and not props.is_rendering_animation_manually
    )


def get_filepath_in_package(path, filename="", starting_dir=__file__):
    """Convert a relative path in the add-on package to an absolute path"""
    script_path = os.path.dirname(os.path.realpath(starting_dir))
    subpath = path + os.sep + filename if path else filename
    strudel.info('Return os.path.join(script_path, subpath)') #  # STRUDEL_RETURN_TRACE_0
    return os.path.join(script_path, subpath)


def get_absolute_path_for_output_file(path, filename):
    """Convert a relative path in the blend file to an absolute path"""
    strudel.info('Return os.path.join(os.path.abspath(bpy.path.abspath(path)), filename)') #  # STRUDEL_RETURN_TRACE_0
    return os.path.join(os.path.abspath(bpy.path.abspath(path)), filename)


def does_path_exist(path):
    strudel.info('Return os.path.exists(os.path.abspath(bpy.path.abspath(path)))') #  # STRUDEL_RETURN_TRACE_0
    return os.path.exists(os.path.abspath(bpy.path.abspath(path)))


def get_filename_from_path(file_path, include_extension=True):
    filename_and_extension = os.path.splitext(os.path.basename(file_path))
    if include_extension:
        strudel.info(f' Return filename_and_extension[0] + filename_and_extension[1] because include_extension') #  # STRUDEL_IF_LOG_1
        return filename_and_extension[0] + filename_and_extension[1]
    else:
        strudel.info(f' Return filename_and_extension[0] because "include_extension" is evaluated to False') #  # STRUDEL_IF_LOG_ELSE_2
        return filename_and_extension[0]


def copy_file(src, dest):
    shutil.copy2(src, dest)


def get_preset_style_thumnails_filepath():
    strudel.info('Return get_filepath_in_package("style_thumbnails")') #  # STRUDEL_RETURN_TRACE_0
    return get_filepath_in_package("style_thumbnails")


def get_extension_from_file_format(file_format):
    if file_format in file_formats:
        strudel.info(f' Return file_formats[file_format] because file_format in file_formats') #  # STRUDEL_IF_LOG_1
        return file_formats[file_format]
    else:
        strudel.info(f' Return "" because file_format not in file_formats') #  # STRUDEL_IF_LOG_ELSE_2
        return ""


def activate_workspace(context=None, workspace=None, workspace_id=None):
    if not workspace:
        strudel.info(' "workspace" is evaluated to False') #  # STRUDEL_IF_LOG_0
        workspace = bpy.data.workspaces.get(workspace_id)
        if not workspace:
            strudel.info(f' Return None because "workspace" is evaluated to False') #  # STRUDEL_IF_LOG_1
            return

    if context and context.window:
        strudel.info(' Assign context.window.workspace=workspace because context AND context.window') #  # STRUDEL_IF_LOG_1
        context.window.workspace = workspace
    else:
        strudel.info(' Assign bpy.data.window_managers[0].windows[0].workspace=workspace because Condition: not (context AND context.window)') #  # STRUDEL_IF_LOG_ELSE_2
        bpy.data.window_managers[0].windows[0].workspace = workspace


def get_areas_by_type(area_type, scene=None, context=None, workspace_id=None):
    if not scene:
        strudel.info(' Assign scene=context.scene because "scene" is evaluated to False') #  # STRUDEL_IF_LOG_1
        scene = context.scene
    if not context:
        strudel.info(' Assign context=bpy.context because "context" is evaluated to False') #  # STRUDEL_IF_LOG_1
        context = bpy.context

    results = []

    # get an area from our desired workspace, if we have one
    if workspace_id:
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
    areas = get_areas_by_type("IMAGE_EDITOR", scene, context, workspace_id)
    potential_area = None

    # loop through all areas, prioritizing the render result area, but returning
    # any image editor area as a backup
    for area in areas:
        active_image = area.spaces.active.image
        if active_image is not None:
            if active_image.type == "RENDER_RESULT":
                return area
            else:
                potential_area = area

    strudel.info('Method "find_area_showing_render_result" returns "potential_area"') #  # STRUDEL_RETURN_TRACE_0
    return potential_area


def split_area(context, area, direction="HORIZONTAL", factor=0.5):
    if bpy.app.version >= (3, 2, 0):
        strudel.info(' bpy.app.version >= tuple of length 3.') #  # STRUDEL_IF_LOG_0
        with context.temp_override(area=area):
            bpy.ops.screen.area_split(direction=direction, factor=factor)
    else:
        override = context.copy()
        override["area"] = area
        bpy.ops.screen.area_split(override, direction=direction, factor=factor)


def view_sd_in_render_view(img, scene=None, context=None):
    # get the render result area, if it's open
    image_editor_area = find_area_showing_render_result(scene, context)

    # if it's not open, try to switch to the render workspace and then get the area
    if not image_editor_area:
        strudel.info(' "image_editor_area" is evaluated to False') #  # STRUDEL_IF_LOG_0
        activate_workspace(workspace_id="Rendering")
        image_editor_area = find_area_showing_render_result(scene, context, "Rendering")

    # if we have an area, set the image
    if image_editor_area:
        strudel.info(' Assign image_editor_area.spaces.active.image=img because image_editor_area') #  # STRUDEL_IF_LOG_1
        image_editor_area.spaces.active.image = img


def get_animated_prompt_text_data_block():
    if config.animated_prompts_text_name in bpy.data.texts:
        strudel.info(f' Return bpy.data.texts[config.animated_prompts_text_name] because config.animated_prompts_text_name in bpy.data.texts') #  # STRUDEL_IF_LOG_1
        return bpy.data.texts[config.animated_prompts_text_name]
    else:
        strudel.info(f' Return None because config.animated_prompts_text_name not in bpy.data.texts') #  # STRUDEL_IF_LOG_ELSE_2
        return None


def get_dream_studio_api_key(context=None):
    strudel.info('Method "get_dream_studio_api_key" returns') #  # STRUDEL_RETURN_TRACE_0
    return get_addon_preferences(context).dream_studio_api_key


def get_stable_horde_api_key(context=None):
    strudel.info('Method "get_stable_horde_api_key" returns') #  # STRUDEL_RETURN_TRACE_0
    return get_addon_preferences(context).stable_horde_api_key


def sd_backend(context=None):
    strudel.info('Method "sd_backend" returns') #  # STRUDEL_RETURN_TRACE_0
    return get_addon_preferences(context).sd_backend


def sd_backend_formatted_name(context=None):
    backend = sd_backend(context)

    if backend == "dreamstudio":
        strudel.info(f' Return "DreamStudio" because backend({backend}) == "dreamstudio"') #  # STRUDEL_IF_LOG_1
        return "DreamStudio"
    elif backend == "stablehorde":
        strudel.info(f' Return "Stable Horde" because backend({backend}) == "stablehorde"') #  # STRUDEL_IF_LOG_1
        return "Stable Horde"
    elif backend == "automatic1111":
        strudel.info(f' Return "Automatic1111" because backend({backend}) == "automatic1111"') #  # STRUDEL_IF_LOG_1
        return "Automatic1111"
    elif backend == "shark":
        strudel.info(f' Return "SHARK by nod.ai" because backend({backend}) == "shark"') #  # STRUDEL_IF_LOG_1
        return "SHARK by nod.ai"


def local_sd_url(context=None):
    strudel.info('Method "local_sd_url" returns') #  # STRUDEL_RETURN_TRACE_0
    return get_addon_preferences(context).local_sd_url


def local_sd_timeout(context=None):
    strudel.info('Method "local_sd_timeout" returns') #  # STRUDEL_RETURN_TRACE_0
    return get_addon_preferences(context).local_sd_timeout


def get_output_width(scene):
    strudel.info('Return round(scene.render.resolution_x * scene.render.resolution_percentage / 100)') #  # STRUDEL_RETURN_TRACE_0
    return round(scene.render.resolution_x * scene.render.resolution_percentage / 100)


def get_output_height(scene):
    strudel.info('Return round(scene.render.resolution_y * scene.render.resolution_percentage / 100)') #  # STRUDEL_RETURN_TRACE_0
    return round(scene.render.resolution_y * scene.render.resolution_percentage / 100)


def get_upscaled_width(scene):
    if not scene:
        strudel.info(' Assign scene=bpy.context.scene because "scene" is evaluated to False') #  # STRUDEL_IF_LOG_1
        scene = bpy.context.scene

    upscale_factor = scene.air_props.upscale_factor
    strudel.info('Return round(get_output_width(scene) * upscale_factor({upscale_factor}))') #  # STRUDEL_RETURN_TRACE_0
    return round(get_output_width(scene) * upscale_factor)


def get_upscaled_height(scene):
    if not scene:
        strudel.info(' Assign scene=bpy.context.scene because "scene" is evaluated to False') #  # STRUDEL_IF_LOG_1
        scene = bpy.context.scene

    upscale_factor = scene.air_props.upscale_factor
    strudel.info('Return round(get_output_height(scene) * upscale_factor({upscale_factor}))') #  # STRUDEL_RETURN_TRACE_0
    return round(get_output_height(scene) * upscale_factor)


def sanitized_upscaled_width(max_upscaled_image_size, scene=None):
    if not scene:
        strudel.info(' Assign scene=bpy.context.scene because "scene" is evaluated to False') #  # STRUDEL_IF_LOG_1
        scene = bpy.context.scene

    upscaled_width = get_upscaled_width(scene)
    upscaled_height = get_upscaled_height(scene)

    if upscaled_width * upscaled_height > max_upscaled_image_size:
        strudel.info(f' Return round(math.sqrt(max_upscaled_image_size({max_upscaled_image_size}) * upscaled_width({upscaled_width}) / upscaled_height({upscaled_height}))) because upscaled_width({upscaled_width}) * upscaled_height({upscaled_height}) > max_upscaled_image_size') #  # STRUDEL_IF_LOG_1
        return round(
            math.sqrt(max_upscaled_image_size * (upscaled_width / upscaled_height))
        )
    else:
        strudel.info(f' Return upscaled_width because upscaled_width({upscaled_width}) * upscaled_height({upscaled_height}) > max_upscaled_image_size') #  # STRUDEL_IF_LOG_ELSE_2
        return upscaled_width


def sanitized_upscaled_height(max_upscaled_image_size, scene=None):
    if not scene:
        strudel.info(' Assign scene=bpy.context.scene because "scene" is evaluated to False') #  # STRUDEL_IF_LOG_1
        scene = bpy.context.scene

    upscaled_width = get_upscaled_width(scene)
    upscaled_height = get_upscaled_height(scene)

    if upscaled_width * upscaled_height > max_upscaled_image_size:
        strudel.info(f' Return round(math.sqrt(max_upscaled_image_size({max_upscaled_image_size}) * upscaled_height({upscaled_height}) / upscaled_width({upscaled_width}))) because upscaled_width({upscaled_width}) * upscaled_height({upscaled_height}) > max_upscaled_image_size') #  # STRUDEL_IF_LOG_1
        return round(
            math.sqrt(max_upscaled_image_size * (upscaled_height / upscaled_width))
        )
    else:
        strudel.info(f' Return upscaled_height because upscaled_width({upscaled_width}) * upscaled_height({upscaled_height}) > max_upscaled_image_size') #  # STRUDEL_IF_LOG_ELSE_2
        return upscaled_height


def are_dimensions_valid(scene):
    if is_using_sdxl_1024_model(scene):
        strudel.info(f' Return are_sdxl_1024_dimensions_valid(get_output_width(scene), get_output_height(scene)) because is_using_sdxl_1024_model(scene)') #  # STRUDEL_IF_LOG_1
        return are_sdxl_1024_dimensions_valid(
            get_output_width(scene), get_output_height(scene)
        )
    else:
        strudel.info(f' Return get_output_width(scene) in range(min_dimension_size, max_dimension_size({max_dimension_size}) + valid_dimension_step_size({valid_dimension_step_size}), valid_dimension_step_size) AND get_output_height(scene) in range(min_dimension_size, max_dimension_size({max_dimension_size}) + valid_dimension_step_size({valid_dimension_step_size}), valid_dimension_step_size) because is_using_sdxl_1024_model(scene) is False ') #  # STRUDEL_IF_LOG_ELSE_2
        return get_output_width(scene) in range(
            min_dimension_size,
            max_dimension_size
            + valid_dimension_step_size,  # range is exclusive of the last value
            valid_dimension_step_size,
        ) and get_output_height(scene) in range(
            min_dimension_size,
            max_dimension_size
            + valid_dimension_step_size,  # range is exclusive of the last value
            valid_dimension_step_size,
        )


def are_sdxl_1024_dimensions_valid(width, height):
    dimensions = f"{width}x{height}"
    strudel.info('Method "are_sdxl_1024_dimensions_valid" returns') #  # STRUDEL_RETURN_TRACE_0
    return dimensions in sdxl_1024_valid_dimensions


def are_dimensions_too_large(scene):
    strudel.info('Method "are_dimensions_too_large" returns') #  # STRUDEL_RETURN_TRACE_0
    return (
        get_output_width(scene) * get_output_height(scene)
        > get_active_backend().max_image_size()
    )


def are_dimensions_too_small(scene):
    strudel.info('Method "are_dimensions_too_small" returns') #  # STRUDEL_RETURN_TRACE_0
    return (
        get_output_width(scene) * get_output_height(scene)
        < get_active_backend().min_image_size()
    )


def are_upscaled_dimensions_too_large(scene):
    strudel.info('Method "are_upscaled_dimensions_too_large" returns') #  # STRUDEL_RETURN_TRACE_0
    return (
        get_upscaled_width(scene) * get_upscaled_height(scene)
        > get_active_backend().max_upscaled_image_size()
    )


def generate_example_dimensions_tuple_list():
    return_tuple = lambda num: (str(num), str(num) + " px", str(num))
    strudel.info('Return list(map(return_tuple, example_dimensions))') #  # STRUDEL_RETURN_TRACE_0
    return list(map(return_tuple, example_dimensions))


def generate_sdxl_1024_dimensions_tuple_list():
    return_tuple = lambda dimension: (
        dimension,
        " x ".join(dimension.split("x")),
        dimension,
    )
    strudel.info('Return list(map(return_tuple, sdxl_1024_valid_dimensions))') #  # STRUDEL_RETURN_TRACE_0
    return list(map(return_tuple, sdxl_1024_valid_dimensions))


def is_using_sdxl_1024_model(scene):
    strudel.info('Return get_active_backend().is_using_sdxl_1024_model(scene.air_props)') #  # STRUDEL_RETURN_TRACE_0
    return get_active_backend().is_using_sdxl_1024_model(scene.air_props)


def has_url(text, strict_match_protocol=False):
    # remove markdown *
    text = text.replace("*", "")

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
                text.replace(ch, "")

    # # if none found, look for url without markup
    # else:
    #     if strict_match_protocol:
    #         bare_url_regex = r"(https{0,1}:\/\/[A-Za-z0-9\-\._~:\/\?#\[\]@!\$&'\(\)\*\+\,;%=]+)"
    #     else:
    #         bare_url_regex = r"(?:[a-z]{3,9}:\/\/?[\-;:&=\+\$,\w]+?[a-z0-9\.\-]+|[\/a-z0-9]+\.|[\-;:&=\+\$,\w]+@)[a-z0-9\.\-]+(?:(?:\/[\+~%\/\.\w\-_]*)?\??[\-\+=&;%@\.\w_]*#?[\.\!\/\\\w]*)?"
    #
    #     urls = re.findall(bare_url_regex, text, re.IGNORECASE)
    #
    #     for i, url in enumerate(urls):
    #         urls[i] = [url, url]

    # # return what was found (could be just text)
    strudel.info('Method "has_url" returns') #  # STRUDEL_RETURN_TRACE_0
    return urls, text


#
def label_multiline(
    layout,
    text="",
    icon="NONE",
    width=-1,
    max_lines=12,
    use_urls=True,
    alignment="LEFT",
    alert=False,
):
    """
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
    """
    rows = []
    if text.strip() == "":
        strudel.info(f' Return list of length 1. because text.strip() == ""') #  # STRUDEL_IF_LOG_1
        return [layout.row()]

    text = text.replace("\r\n", "\n")

    if use_urls:
        strudel.info(' Assign tuple of length 2.=has_url(text) because use_urls') #  # STRUDEL_IF_LOG_1
        urls, text = has_url(text, strict_match_protocol=True)
    else:
        strudel.info(' Assign urls=list of length 0. because "use_urls" is evaluated to False') #  # STRUDEL_IF_LOG_ELSE_2
        urls = []

    lines = text.split("\n")

    if width > 0:
        strudel.info(' Assign char_threshold=int(width({width}) / 5.7) because width({width}) > 0') #  # STRUDEL_IF_LOG_1
        char_threshold = int(width / 5.7)
    else:
        strudel.info(' Assign char_threshold=35 because width({width}) <= 0') #  # STRUDEL_IF_LOG_ELSE_2
        char_threshold = 35

    line_index = 0
    for line in lines:

        line_index += 1
        while len(line) > char_threshold:
            # find line split close to the end of line
            i = line.rfind(" ", 0, char_threshold)
            # split long words
            if i < 1:
                i = char_threshold
            l1 = line[:i]

            row = layout.row()
            if alert:
                row.alert = True
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
        if alert:
            row.alert = True
        row.alignment = alignment
        row.label(text=line, icon=icon)
        rows.append(row)

        # set the icon to none after the first row
        icon = "NONE"

    # if we have urls, include them as buttons at the end
    if use_urls:
        strudel.info(' use_urls') #  # STRUDEL_IF_LOG_0
        for url in urls:
            row = layout.row()
            row.operator("wm.url_open", text=url[0], icon="URL").url = url[1]

    # return the resulting rows
    strudel.info('Method "label_multiline" returns "rows"') #  # STRUDEL_RETURN_TRACE_0
    return rows


def get_active_backend():
    backend = sd_backend()

    if backend == "dreamstudio":
        strudel.info(f' Return stability_api because backend({backend}) == "dreamstudio"') #  # STRUDEL_IF_LOG_1
        return stability_api
    elif backend == "stablehorde":
        strudel.info(f' Return stablehorde_api because backend({backend}) == "stablehorde"') #  # STRUDEL_IF_LOG_1
        return stablehorde_api
    elif backend == "automatic1111":
        strudel.info(f' Return automatic1111_api because backend({backend}) == "automatic1111"') #  # STRUDEL_IF_LOG_1
        return automatic1111_api
    elif backend == "shark":
        strudel.info(f' Return shark_api because backend({backend}) == "shark"') #  # STRUDEL_IF_LOG_1
        return shark_api


def is_installation_valid():
    strudel.info('Method "is_installation_valid" returns') #  # STRUDEL_RETURN_TRACE_0
    return __package__ == config.package_name


def show_invalid_installation_message(layout, width):
    box = layout.box()
    box.label(text="Installation Error:")

    label_multiline(
        box,
        text=f"It looks like this add-on wasn't installed correctly. Please remove it and get a new copy. [Get AI Render]({config.ADDON_DOWNLOAD_URL})",
        icon="ERROR",
        alert=True,
        width=width,
    )


#

