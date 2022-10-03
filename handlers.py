import bpy
from bpy.app.handlers import persistent
import functools
from . import (
    operators,
    task_queue,
)


@persistent
def render_pre_handler(scene):
    # clear any previous errors
    # operators.clear_error(scene)

    # when the render is starting, ensure we have the right compositor nodes
    operators.ensure_compositor_nodes(scene)

    # then mute the mix node, so we get the result of the original render
    operators.mute_compositor_mix_node(scene)



@persistent
def render_complete_handler(scene):
    # when the render is ready:

    # check to see if we have a render result
    is_img_ready = bpy.data.images['Render Result'].has_data

    # if it's ready, post to the api
    if is_img_ready:
        task_queue.add(functools.partial(operators.send_to_api, scene))
    else:
        print("Rendered image is not ready")


def register_handlers():
    bpy.app.handlers.render_pre.append(render_pre_handler)
    bpy.app.handlers.render_complete.append(render_complete_handler)


def unregister_handlers():
    bpy.app.handlers.render_pre.remove(render_pre_handler)
    bpy.app.handlers.render_complete.remove(render_complete_handler)
