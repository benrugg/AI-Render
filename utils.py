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
import tempfile
from . import config


valid_dimensions = [384, 448, 512, 576, 640, 704, 768, 832, 896, 960, 1024]
file_formats = {"JPEG": "jpg", "BMP": "bmp", "IRIS": "rgb", "PNG": "png", "JPEG2000": "jp2", "TARGA": "tga", "TARGA_RAW": "tga", "CINEON": "cin", "DPX": "dpx", "OPEN_EXR_MULTILAYER": "exr", "OPEN_EXR": "exr", "HDR": "hdr", "TIFF": "tif", "WEBP": "webp"}


def get_addon_preferences(context):
    return context.preferences.addons[__package__].preferences


def create_temp_file(prefix, suffix=".png"):
    return tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix).name


def join_path(path, subpath):
    return os.path.join(path, subpath)


def get_filepath_in_package(path, filename = ""):
    script_path = os.path.dirname(os.path.realpath(__file__))
    subpath = path + os.sep + filename
    return os.path.join(script_path, subpath)


def copy_file(src, dest):
    shutil.copy2(src, dest)


def get_workspace_blend_file_filepath():
    return get_filepath_in_package("blendfiles", "air_workspace.blend")


def get_preset_style_thumnails_filepath():
    return get_filepath_in_package("style_thumbnails")


def get_extension_from_file_format(file_format):
    if file_format in file_formats:
        return file_formats[file_format]
    else:
        return ""


def get_current_workspace(context = None):
    if not context:
        context = bpy.context

    if context.window and context.window.workspace:
        return context.window.workspace
    else:
        return None


def activate_workspace(context = None, workspace = None, workspace_id = None):
    if not workspace:
        workspace = bpy.data.workspaces[workspace_id]

    if context and context.window:
        context.window.workspace = workspace
    else:
        bpy.data.window_managers[0].windows[0].workspace = workspace


def view_render_result_in_air_image_editor():
    image_editor_area = None
    areas = bpy.data.workspaces[config.workspace_id].screens[0].areas

    for area in areas:
        if area.type == 'IMAGE_EDITOR':
            image_editor_area = area
            break

    if image_editor_area:
        image_editor_area.spaces.active.image = bpy.data.images['Render Result']


def get_api_key(context = None):
    if not context:
        context = bpy.context
    return get_addon_preferences(context).dream_studio_api_key


def get_output_width(scene):
    return round(scene.render.resolution_x * scene.render.resolution_percentage / 100)


def get_output_height(scene):
    return round(scene.render.resolution_y * scene.render.resolution_percentage / 100)


def are_dimensions_valid(scene):
    return (
        get_output_width(scene) in valid_dimensions and
        get_output_height(scene) in valid_dimensions
    )


def are_dimensions_too_large(scene):
    return get_output_width(scene) * get_output_height(scene) > config.max_image_px_area


def generate_valid_dimensions_tuple_list():
    return_tuple = lambda num: (str(num), str(num) + " px", str(num))
    return list(map(return_tuple, valid_dimensions))


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


def is_installation_valid():
    return __package__ == config.package_name


def show_invalid_installation_message(layout, width):
    box = layout.box()
    box.label(text="Installation Error:")

    label_multiline(box, text=f"It looks like this add-on wasn't installed correctly. Please remove it and get a new copy. [Get AI Render]({config.ADDON_DOWNLOAD_URL})", icon="ERROR", alert=True, width=width)
