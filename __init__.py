bl_info = {
    "name": "AI Render - Stable Diffusion in Blender",
    "description": "Create amazing images using Stable Diffusion AI",
    "author": "Ben Rugg",
    "version": (1, 0, 1),
    "blender": (3, 0, 0),
    "location": "Render Properties > AI Render",
    "warning": "",
    "doc_url": "https://github.com/benrugg/AI-Render#readme",
    "tracker_url": "https://github.com/benrugg/AI-Render/issues",
    "category": "Render",
}


if "bpy" in locals():
    import imp

    imp.reload(addon_updater_ops)
    imp.reload(analytics)
    imp.reload(config)
    imp.reload(handlers)
    imp.reload(operators)
    imp.reload(preferences)
    imp.reload(progress_bar)
    imp.reload(properties)
    imp.reload(task_queue)
    imp.reload(ui_panels)
    imp.reload(ui_preset_styles)
    imp.reload(utils)
    imp.reload(comfyui_api)
    imp.reload(automatic1111_api)
    imp.reload(stability_api)
    imp.reload(stablehorde_api)
    imp.reload(properties_comfy)
    imp.reload(ui_panels_comfyui)
else:
    from . import (
        addon_updater_ops,
        analytics,
        config,
        handlers,
        operators,
        preferences,
        progress_bar,
        properties,
        task_queue,
        utils,
        properties_comfy,
    )
    from .ui import (
        ui_panels,
        ui_preset_styles,
        ui_panels_comfyui
    )
    from .sd_backends import (
        comfyui_api,
        automatic1111_api,
        stability_api,
        stablehorde_api,
    )

import bpy


def register():
    addon_updater_ops.register(bl_info)
    analytics.register(bl_info)
    handlers.register()
    operators.register()
    preferences.register()
    progress_bar.register()
    properties.register()
    task_queue.register()
    ui_panels.register()
    ui_preset_styles.register()
    properties_comfy.register()
    ui_panels_comfyui.register()


def unregister():
    addon_updater_ops.unregister()
    analytics.unregister()
    handlers.unregister()
    operators.unregister()
    preferences.unregister()
    progress_bar.unregister()
    properties.unregister()
    task_queue.unregister()
    ui_panels.unregister()
    ui_preset_styles.unregister()
    properties_comfy.unregister()
    ui_panels_comfyui.unregister()


if __name__ == "__main__":
    register()
