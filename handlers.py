import bpy
from bpy.app.handlers import persistent
from . import operators


@persistent
def render_pre_handler(scene):
    # when the render is starting, ensure we have the right compositor nodes
    operators.ensure_compositor_nodes()


@persistent
def render_post_handler(scene):
    # when the render is ready:

    # check to see if we have a render result
    is_img_ready = bpy.data.images['Render Result'].has_data

    # if it's ready, post to the api
    if is_img_ready:
        operators.send_to_api()
    else:
        print("Rendered image is not ready")


def register_handlers():
    bpy.app.handlers.render_pre.append(render_pre_handler)
    bpy.app.handlers.render_post.append(render_post_handler)


def unregister_handlers():
    bpy.app.handlers.render_pre.remove(render_pre_handler)
    bpy.app.handlers.render_post.remove(render_post_handler)
