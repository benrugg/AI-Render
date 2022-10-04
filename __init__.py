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
    imp.reload(config)
    imp.reload(handlers)
    imp.reload(operators)
    imp.reload(preferences)
    imp.reload(properties)
    imp.reload(task_queue)
    imp.reload(ui)
    imp.reload(utils)
else:
    from . import (
        config,
        handlers,
        operators,
        preferences,
        properties,
        task_queue,
        ui,
        utils,
    )

import bpy


def register():
    handlers.register_handlers()
    operators.register_operators()
    preferences.register_preferences()
    properties.register_properties()
    task_queue.register_task_queue()
    ui.register_ui()
    


def unregister():
    handlers.unregister_handlers()
    operators.unregister_operators()
    preferences.unregister_preferences()
    properties.unregister_properties()
    task_queue.unregister_task_queue()
    ui.unregister_ui()


if __name__ == "__main__":
    register()
