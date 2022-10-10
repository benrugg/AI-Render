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
    if not context:
        context = bpy.context

    # if SDR has been enabled in this file, do the enable steps
    # right now, to ensure everything is running and in place
    if context.scene.sdr_props.is_enabled:
        operators.enable_sdr(context.scene)


@persistent
def render_pre_handler(scene):
    """Handle render about to start"""

    # if SDR isn't enabled, or we don't want to run automatically, quit here
    if not scene.sdr_props.is_enabled or not scene.sdr_props.auto_run:
        return

    # otherwise, do the pre-render setup
    operators.do_pre_render_setup(scene)


@persistent
def render_complete_handler(scene):
    """Handle render completed (this is where the api and stable diffusion start)"""

    # if SDR isn't enabled, or we don't want to run automatically, quit here
    if not scene.sdr_props.is_enabled or not scene.sdr_props.auto_run:
        return

    # check to see if we have a render result
    is_img_ready = bpy.data.images['Render Result'].has_data

    # if it's ready, post to the api
    if is_img_ready:

        # do pre-api setup
        operators.do_pre_api_setup()

        # post to the api (on a different thread, outside the handler)
        task_queue.add(functools.partial(operators.send_to_api, scene))
    else:
        operators.handle_error("Rendered image is not ready. Try generating a new image manually under Stable Diffusion Render > Operation")


def register():
    bpy.app.handlers.load_post.append(load_post_handler)
    bpy.app.handlers.render_pre.append(render_pre_handler)
    bpy.app.handlers.render_complete.append(render_complete_handler)


def unregister():
    bpy.app.handlers.load_post.remove(load_post_handler)
    bpy.app.handlers.render_pre.remove(render_pre_handler)
    bpy.app.handlers.render_complete.remove(render_complete_handler)
