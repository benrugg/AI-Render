import bpy
import os
from .. import utils


preview_collection = None
img_dir = utils.get_preset_style_thumnails_filepath()

preset_styles = [
    ("Digital Portrait", "beautiful portrait, 8k resolution concept art portrait, hyperdetailed, intricately detailed, trending on Artstation, triadic colors, volumetric lighting, soft focus, dynamic lighting", "digital-portrait.jpg"),
    ("B&W Portrait", "b&w photography, close up portrait, ambient light, depth of field, intricately detailed, Nikon 15mm, photograph by Annie Leibovitz", "bw-portrait.jpg"),
    ("Photorealistic", "stunning photograph, natural light, megapixel, pro canon 50mm lens", "photorealistic.jpg"),
    ("Impressionist", "impressionist painting by Claude Monet, impressionism, visible brushstrokes, beautiful light", "impressionist.jpg"),
    ("Expressionist", "expressionist painting by Edvard Munch, subjective perspective, emotionally evocative painting", "expressionist.jpg"),
    ("3D Game", "unreal engine 5, 3d shading, shadow depth", "3d-game.jpg"),
    ("Infrared Photograph", "infrared photograph, unsplash", "infrared-photograph.jpg"),
    ("Low Poly", "low poly colorful", "low-poly.jpg"),
    ("Pencil Drawing", "pencil drawing, hyperdetailed, intricate details, 8k, high contrast pencil lines, dynamic lighting and shadow, realistic", "pencil-drawing.jpg"),
    ("Pop Art", "pop art vivid colors", "pop-art.jpg"),
    ("Cyberpunk", "cyberpunk, contemporary cyber art, blade runner, neon", "cyberpunk.jpg"),
    ("Steampunk", "steampunk brass wood steel, hyperdetailed illustration, complex machinery", "steampunk.jpg"),
    ("Solarpunk", "solarpunk, epic scale, hyperdetailed, trending on Artstation", "solarpunk.jpg"),
    ("Sci-Fi Concept", "sci-fi concept art, hyperdetailed, 8k, trending on Artstation", "sci-fi-concept.jpg"),
    ("Vaporwave", "vaporwave art", "vaporwave.jpg"),
    ("Charcoal Sketch", "charcoal art, hyperdetailed, 8k, trending on artstation", "charcoal-sketch.jpg"),
    ("Anime", "anime scene, cel-shaded anime illustration", "anime.jpg"),
    ("Abstract", "stunning abstract art acrylic paint", "abstract.jpg"),
    ("Iridescent", "ethereal heavenly expansive iridescent lens flare psychedelic, trending on Artstation", "iridescent.jpg"),
    ("Cubist", "cubism, cubist art", "cubist.jpg"),
    ("Hudson River School", "landscape, Hudson River School art, intricate details, matte painting", "hudson-river-school.jpg"),
    ("Caspar David Friedrich", "landscape painting by Caspar David Friedrich", "caspar-david-friedrich.jpg"),
    ("Canaletto", "Canaletto matte painting", "canaletto.jpg"),
    ("Surreal", "surrealism, surreal art by Salvador Dali, matte painting", "surreal.jpg"),
    ("Shin Hanga", "eldritch, shin hanga, detailed matte painting, 8k resolution concept art, volume lighting", "shin-hanga.jpg"),
    ("Wadim Kashin", "by Wadim Kashin", "wadim-kashin.jpg"),
    ("Leonid Afremov", "by Leonid Afremov", "leonid-afremov.jpg"),
    ("Victo Ngai", "intricate digital art by Victo Ngai", "victo-ngai.jpg"),
    ("Dan Mumford", "dark fantasy art by Dan Mumford", "dan-mumford.jpg"),
    ("Product shot", "striking product shot, muted colors, soft lighting, softbox, depth of field", "product-shot.jpg"),
    ("UI/UX interface", "ui ux interface dribbble", "ui-ux-interface.jpg"),
    ("Crayon Drawing", "crayon drawing", "crayon-drawing.jpg"),
    ("Anaglyph", "anaglyph filter, anaglyph 3d effect", "anaglyph.jpg"),
    ("Cartoon", "saturday morning cartoon illustration, colorful cartoon", "cartoon.jpg"),
    ("Noir Line Art", "portrait, noir line art, trending on Artstation", "noir-line-art.jpg"),
    ("Bauhaus", "bauhaus art, bauhaus style painting", "bauhaus.jpg"),
    ("Bone Carving", "bone carving", "bone-carving.jpg"),
    ("Stipple", "stipple", "stipple.jpg"),
    ("Wild Rainbow", "intricate, yellow green red, Scenic, Hyperdetailed, rainbow splash, symbolic, Bagshaw, Chevrier, Ferri, Kaluta, spinning, Pixiv, Mucha, Cina, Cinematic, WLOP, 8K, smooth sharp focus, rutkowski, detailed eyes, Artgerm, Giger, glowing fractal edges, cel-shaded", "wild-rainbow.jpg"),
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
