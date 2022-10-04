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


def get_workspace_blend_file_filepath():
    script_path = os.path.dirname(os.path.realpath(__file__))
    subpath = "blendfiles" + os.sep + "compositor_workspace.blend"
    return os.path.join(script_path, subpath)


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


def view_render_result_in_sdr_image_editor():
    image_editor_area = None
    areas = bpy.data.workspaces['Stable Diffusion Render'].screens[0].areas

    for area in areas:
        if area.type == 'IMAGE_EDITOR':
            image_editor_area = area
            break
    
    if image_editor_area:
        image_editor_area.spaces.active.image = bpy.data.images['Render Result']


def has_url(text):
    #first remove markdown *
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
        bare_url_regex = r"(?:[a-z]{3,9}:\/\/?[\-;:&=\+\$,\w]+?[a-z0-9\.\-]+|[\/a-z0-9]+\.|[\-;:&=\+\$,\w]+@)[a-z0-9\.\-]+(?:(?:\/[\+~%\/\.\w\-_]*)?\??[\-\+=&;%@\.\w_]*#?[\.\!\/\\\w]*)?"
        urls = re.findall(bare_url_regex, text, re.IGNORECASE)

        for i, url in enumerate(urls):
            urls[i] = [url, url]
    
    # return what was found (could be just text)
    return urls, text


def label_multiline(layout, text='', icon='NONE', width=-1, max_lines=10, use_urls=True):
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
        urls, text = has_url(text)
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