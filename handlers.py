import bpy
from bpy.app.handlers import persistent
import functools
from . import (
    operators,
    task_queue,
)


@persistent
def load_post_handler(context):
    """Handle new blender file load (and new scene load)"""

    # register the task queue (because app timers get stopped
    # when loading a new blender file)
    task_queue.register_task_queue()

    # switch the workspace to compositor, so the new rendered image will actually appear
    operators.ensure_sdr_workspace()


@persistent
def render_pre_handler(scene):
    """Handle render about to start"""

    # Lock the user interface when rendering, so that we can change
    # compositor nodes in the render_pre handler without causing a crash!
    # See: https://docs.blender.org/api/current/bpy.app.handlers.html#note-on-altering-data
    scene.render.use_lock_interface = True

    # clear any previous errors
    operators.clear_error(scene)

    # when the render is starting, ensure we have the right compositor nodes
    operators.ensure_compositor_nodes(scene)

    # then mute the mix node, so we get the result of the original render
    operators.mute_compositor_mix_node(scene)


@persistent
def render_complete_handler(scene):
    """Handle render completed (this is where the api and stable diffusion start)"""

    # check to see if we have a render result
    is_img_ready = bpy.data.images['Render Result'].has_data

    # if it's ready, post to the api
    if is_img_ready:

        # switch the workspace to our sdr compositor, so the new rendered image will actually appear
        operators.activate_sdr_workspace()

        # post to the api (on a different thread, outside the handler)
        task_queue.add(functools.partial(operators.send_to_api, scene))
    else:
        print("Rendered image is not ready")


def register_handlers():
    bpy.app.handlers.load_post.append(load_post_handler)
    bpy.app.handlers.render_pre.append(render_pre_handler)
    bpy.app.handlers.render_complete.append(render_complete_handler)


def unregister_handlers():
    bpy.app.handlers.load_post.remove(load_post_handler)
    bpy.app.handlers.render_pre.remove(render_pre_handler)
    bpy.app.handlers.render_complete.remove(render_complete_handler)
