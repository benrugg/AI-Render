import bpy
import os
from .. import utils


preview_collection = None
img_dir = utils.get_preset_style_thumnails_filepath()

preset_styles = [
    ("Anime", "anime, digital art, trending on artstation", "temp-anime.png"),
    ("Portrait", "artistic digital painted portrait", "temp-portrait.png"),
    ("B&W Portrait", "b&w photograph, detailed, depth of field", "temp-bw-portrait.png"),
    ("Animated", "cg character, pixar character", "temp-cg-character.png"),
]


def enum_thumbnail_icons(self, context):
    """EnumProperty callback"""
    global preview_collection
    enum_items = []

    if context is None:
        return enum_items

    if preview_collection.get("preset_styles_thumbnail_icons"):
        return preview_collection.preset_styles_thumbnail_icons

    for i, style in enumerate(preset_styles):
        label, prompt, img_filename = style
        full_filename = os.path.join(img_dir, img_filename)
        icon = preview_collection.get(label)

        if not icon:
            thumb = preview_collection.load(label, full_filename, 'IMAGE')
        else:
            thumb = preview_collection[label]

        enum_items.append((prompt, label, "", thumb.icon_id, i))

    # dynamically make list from directory:
    # if os.path.exists(img_dir):
    #     image_paths = []
    #     for fn in os.listdir(img_dir):
    #         if fn.lower().endswith(".png"):
    #             image_paths.append(fn)

    #     for i, name in enumerate(image_paths):
    #         # generate a thumbnail preview for a file
    #         filepath = os.path.join(img_dir, name)
    #         icon = preview_collection.get(name)

    #         if not icon:
    #             thumb = preview_collection.load(name, filepath, 'IMAGE')
    #         else:
    #             thumb = preview_collection[name]

    #         enum_items.append(("val " + name, "label " + name, "", thumb.icon_id, i))

    # else: 
    #     print("Error loading preset style thumbnails for Stable Diffusion Render. Directory doesn't exist: ", img_dir)

    preview_collection.preset_styles_thumbnail_icons = enum_items
    return preview_collection.preset_styles_thumbnail_icons


def register_ui_preset_styles():
    import bpy.utils.previews

    global preview_collection

    preview_collection = bpy.utils.previews.new()
    preview_collection.preset_styles_thumbnail_icons = []


def unregister_ui_preset_styles():
    global preview_collection

    bpy.utils.previews.remove(preview_collection)
    preview_collection = None