bl_info = {
    "name": "Stable Diffusion Render",
    "description": "Use the Stable Diffusion AI algorithm to create a new image based on your render and a text prompt",
    "author": "Ben Rugg",
    "version": (0, 0, 1),
    "blender": (3, 3, 0),
    "location": "3D View > Sidebar  &  Render Properties > Stable Diffusion Render",
    "warning": "",
    "tracker_url": "",
    "category": "Render",
}


if "bpy" in locals():
    import imp
    imp.reload(colors)
    imp.reload(defer_error)
    imp.reload(operators)
    imp.reload(properties)
    imp.reload(ui_bgl)
    imp.reload(ui_messages)
    imp.reload(ui)
    imp.reload(utils)
else:
    from . import (
        colors,
        defer_error,
        operators,
        properties,
        ui_bgl,
        ui_messages,
        ui,
        utils,
    )

import bpy


def register():
    operators.register_operators()
    properties.register_properties()
    ui_messages.register_ui_messages()
    ui.register_ui()

    bpy.types.Scene.sdr_props = bpy.props.PointerProperty(type=properties.SDRProperties)

    bpy.app.handlers.render_pre.append(operators.render_pre_handler)
    bpy.app.handlers.render_post.append(operators.render_post_handler)


def unregister():
    operators.unregister_operators()
    properties.unregister_properties()
    ui_messages.unregister_ui_messages()
    ui.unregister_ui()

    del bpy.types.Scene.sdr_props

    bpy.app.handlers.render_pre.remove(operators.render_pre_handler)
    bpy.app.handlers.render_post.remove(operators.render_post_handler)


if __name__ == "__main__":
    register()
