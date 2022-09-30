bl_info = {
    "name": "Stable Diffusion Render",
    "description": "Use the Stable Diffusion AI algorithm to create a new image based on your render and a text prompt",
    "author": "Ben Rugg",
    "version": (0, 0, 1),
    "blender": (3, 0, 0),
    "location": "3D View > Sidebar  &  Render Properties > Stable Diffusion Render",
    "warning": "",
    "tracker_url": "",
    "category": "Render",
}


if "bpy" in locals():
    import imp
    imp.reload(properties)
    imp.reload(operators)
    imp.reload(ui)
else:
    from . import properties, operators, ui

import bpy
from . import operators
from . import ui
from .properties import SDRProperties


classes = [
    SDRProperties,
    operators.SDR_OT_send_to_api,
    operators.SDR_OT_ensure_compositor_nodes,
    operators.SDR_OT_show_error_popup,
    ui.SDR_PT_main,
    ui.SDR_PT_setup,
    ui.SDR_PT_prompt,
    ui.SDR_PT_seed,
    ui.SDR_PT_test,
    ui.SDR_PT_output,
]


def register():
    from bpy.utils import register_class
    
    for cls in classes:
        register_class(cls)
    
    bpy.types.Scene.sdr_props = bpy.props.PointerProperty(type=SDRProperties)
    bpy.app.handlers.render_pre.append(operators.render_pre_handler)
    bpy.app.handlers.render_post.append(operators.render_post_handler)


def unregister():
    from bpy.utils import unregister_class
    
    for cls in reversed(classes):
        unregister_class(cls)
    
    del bpy.types.Scene.sdr_props
    bpy.app.handlers.render_pre.remove(operators.render_pre_handler)
    bpy.app.handlers.render_post.remove(operators.render_post_handler)


if __name__ == "__main__":
    register()
