import bpy
from bpy.app.handlers import persistent
from . import (
    operators,
    task_queue,
)


@persistent
def render_pre_handler(scene):
    # when the render is starting, ensure we have the right compositor nodes
    operators.ensure_compositor_nodes()


@persistent
def render_complete_handler(scene):
    # when the render is ready:

    # check to see if we have a render result
    is_img_ready = bpy.data.images['Render Result'].has_data

    # if it's ready, post to the api
    if is_img_ready:
        task_queue.add(operators.send_to_api)
    else:
        print("Rendered image is not ready")


def register_handlers():
    bpy.app.handlers.render_pre.append(render_pre_handler)
    bpy.app.handlers.render_complete.append(render_complete_handler)


def unregister_handlers():
    bpy.app.handlers.render_pre.remove(render_pre_handler)
    bpy.app.handlers.render_complete.remove(render_complete_handler)
