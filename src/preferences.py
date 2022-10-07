import bpy
from . import (
    config,
    operators
)


class SDRPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    dream_studio_api_key: bpy.props.StringProperty(
        name="API Key",
        description="Your DreamStudio API KEY",
    )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        col = row.column()
        col.label(text="Setup is easy!")
        col = row.column()
        col.operator(operators.SDR_OT_setup_instructions_popup.bl_idname, text="Setup Instructions", icon="HELP")

        row = layout.row()
        row.operator("wm.url_open", text="Sign Up For DreamStudio (free)", icon="URL").url = config.DREAM_STUDIO_URL

        row = layout.row()
        row.prop(self, "dream_studio_api_key")


classes = [
    SDRPreferences,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
