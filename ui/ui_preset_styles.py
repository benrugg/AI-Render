import bpy
import os
from .. import utils


preview_collection = None
img_dir = utils.get_preset_style_thumnails_filepath()

preset_styles = [
    ("Digital Portrait", "Beautiful portrait of {prompt} . concept art portrait, intricate details, soft focus, dynamic lighting", "digital-portrait.jpg"),
    ("B&W Portrait", "Black and white photo of {prompt} . close up portrait, ambient light, depth of field, intricate details", "bw-portrait.jpg"),
    ("Photorealistic", "Stunning photograph of {prompt} . natural light, highly detailed, lifelike, precise, accurate", "photorealistic.jpg"),
    ("Impressionist", "Impressionist style {prompt} . loose brushwork, light and color, ordinary subjects, highly detailed", "impressionist.jpg"),
    ("Expressionist", "Expressionist style {prompt} . emotional, distorted, individual perspective, highly detailed", "expressionist.jpg"),
    ("3D Game", "Professional 3d model {prompt} . octane render, highly detailed, volumetric, dramatic lighting", "3d-game.jpg"),
    ("Infrared Photograph", "Infrared photograph of {prompt}", "infrared-photograph.jpg"),
    ("Low Poly", "low-poly style {prompt} . low-poly game art, polygon mesh, jagged, blocky, wireframe edges, centered composition", "low-poly.jpg"),
    ("Pencil Drawing", "pencil drawing of {prompt} . intricate details, high contrast pencil lines, dynamic lighting and shadow, realistic", "pencil-drawing.jpg"),
    ("Pop Art", "pop art {prompt} . vibrant, mass culture, comic style, bold lines, ironic", "pop-art.jpg"),
    ("Cyberpunk", "cyberpunk style {prompt} . contemporary cyber art, blade runner, neon", "cyberpunk.jpg"),
    ("Steampunk", "steampunk style {prompt} . retro, mechanical, detailed, Victorian", "steampunk.jpg"),
    ("Solarpunk", "solarpunk style {prompt} . epic scale, hyperdetailed", "solarpunk.jpg"),
    ("Sci-Fi Concept", "sci-fi concept art style {prompt} . unique, interesting", "sci-fi-concept.jpg"),
    ("Vaporwave", "vaporwave style {prompt} . retro, neon, pixelated, nostalgic", "vaporwave.jpg"),
    ("Charcoal Sketch", "charcoal sketch of {prompt} . dark, grainy, high contrast, loose, dramatic", "charcoal-sketch.jpg"),
    ("Anime", "anime style animation {prompt} . Japanese style, hand-drawn or digital, vibrant, unique character designs, highly detailed", "anime.jpg"),
    ("Abstract", "abstract {prompt} . imaginative, surreal, non-representational, dream-like", "abstract.jpg"),
    ("Iridescent", "{prompt} . ethereal, heavenly, expansive, iridescent, lens flare, psychedelic", "iridescent.jpg"),
    ("Cubist", "Cubist style {prompt} . geometric, multi-perspective, fragmented, highly detailed", "cubist.jpg"),
    ("Hudson River School", "Hudson River School style {prompt} . landscape painting", "hudson-river-school.jpg"),
    ("Caspar David Friedrich", "landscape painting of {prompt} . in the style of Caspar David Friedrich", "caspar-david-friedrich.jpg"),
    ("Canaletto", "{prompt} . in the style of Canaletto, matte painting", "canaletto.jpg"),
    ("Surreal", "Surrealist style {prompt} . dreamlike, irrational, unexpected juxtapositions, highly detailed", "surreal.jpg"),
    ("Shin Hanga", "{prompt} . in Shin Hanga style, eldritch", "shin-hanga.jpg"),
    ("Wadim Kashin", "{prompt} . in the style of Wadim Kashin", "wadim-kashin.jpg"),
    ("Leonid Afremov", "{prompt} . in the style of Leonid Afremov", "leonid-afremov.jpg"),
    ("Victo Ngai", "{prompt} . in the style of Victo Ngai, intricate digital art", "victo-ngai.jpg"),
    ("Dan Mumford", "{prompt} . in the style of Dan Mumford, dark fantasy art", "dan-mumford.jpg"),
    ("Product shot", "product shot of {prompt} . striking, muted colors, soft lighting, softbox, depth of field", "product-shot.jpg"),
    ("UI/UX interface", "{prompt} . as a ui ux user interface, dribbble, graphic design", "ui-ux-interface.jpg"),
    ("Crayon Drawing", "crayon drawing of {prompt} . simple, colorful", "crayon-drawing.jpg"),
    ("Anaglyph", "anaglyph filter photo of {prompt} . anaglyph 3d effect", "anaglyph.jpg"),
    ("Cartoon", "cartoon modern {prompt} . mid-century modern aesthetic, stylized, geometric shapes, flat colors, highly detailed", "cartoon.jpg"),
    ("Noir Line Art", "noir line art of {prompt} . black and white, hand-drawn, high contrast", "noir-line-art.jpg"),
    ("Bauhaus", "bauhaus style {prompt} . functional, geometric, minimal, detailed", "bauhaus.jpg"),
    ("Bone Carving", "bone carving of {prompt}", "bone-carving.jpg"),
    ("Stipple", "stippled technique on {prompt} . dotted, texture, detailed, graphic, intricate", "stipple.jpg"),
    ("Wild Rainbow", "{prompt} . intricate, yellow green red, Scenic, Hyperdetailed, rainbow splash, symbolic, Bagshaw, Chevrier, Ferri, Kaluta, spinning, Pixiv, Mucha, Cina, Cinematic, Rutkowski, Artgerm, Giger, glowing fractal edges, cel-shaded", "wild-rainbow.jpg"),
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
    #     print("Error loading preset style thumbnails for AI Render. Directory doesn't exist: ", img_dir)

    preview_collection.preset_styles_thumbnail_icons = enum_items
    return preview_collection.preset_styles_thumbnail_icons


def register():
    import bpy.utils.previews

    global preview_collection

    preview_collection = bpy.utils.previews.new()
    preview_collection.preset_styles_thumbnail_icons = []


def unregister():
    global preview_collection

    bpy.utils.previews.remove(preview_collection)
    preview_collection.preset_styles_thumbnail_icons.clear()
    preview_collection = None
