bl_info = {
    "name": "AI Render - Stable Diffusion in Blender",
    "description": "Create amazing images using Stable Diffusion AI",
    "author": "Ben Rugg",
    "version": (0, 2, 2),
    "blender": (3, 0, 0),
    "location": "Render Properties > AI Render",
    "warning": "",
    "tracker_url": "https://github.com/benrugg/AI-Render/issues",
    "category": "Render",
}


if "bpy" in locals():
    import imp
    imp.reload(addon_updater_ops)
    imp.reload(config)
    imp.reload(handlers)
    imp.reload(operators)
    imp.reload(preferences)
    imp.reload(properties)
    imp.reload(task_queue)
    imp.reload(ui_panels)
    imp.reload(ui_preset_styles)
    imp.reload(utils)
else:
    from . import (
        addon_updater_ops,
        config,
        handlers,
        operators,
        preferences,
        properties,
        task_queue,
        utils,
    )
    from .ui import (
        ui_panels,
        ui_preset_styles,
    )

import bpy


def register():
    addon_updater_ops.register(bl_info)
    handlers.register()
    operators.register()
    preferences.register()
    properties.register()
    task_queue.register()
    ui_panels.register()
    ui_preset_styles.register()


def unregister():
    addon_updater_ops.unregister()
    handlers.unregister()
    operators.unregister()
    preferences.unregister()
    properties.unregister()
    task_queue.unregister()
    ui_panels.unregister()
    ui_preset_styles.unregister()


if __name__ == "__main__":
    register()
