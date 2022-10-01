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
    imp.reload(defer_error)
    imp.reload(handlers)
    imp.reload(operators)
    imp.reload(properties)
    imp.reload(ui)
    imp.reload(utils)
else:
    from . import (
        defer_error,
        handlers,
        operators,
        properties,
        ui,
        utils,
    )

import bpy


def register():
    defer_error.register_defer_error()
    handlers.register_handlers()
    operators.register_operators()
    properties.register_properties()
    ui.register_ui()


def unregister():
    defer_error.unregister_defer_error()
    handlers.unregister_handlers()
    operators.unregister_operators()
    properties.unregister_properties()
    ui.unregister_ui()


if __name__ == "__main__":
    register()
