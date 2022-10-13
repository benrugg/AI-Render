import bpy
from . import (
    addon_updater_ops,
    config,
    operators,
    utils,
)


class AIRPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    # AIR Preferences
    dream_studio_api_key: bpy.props.StringProperty(
        name="API Key",
        description="Your DreamStudio API KEY",
    )

    is_valid_installation: bpy.props.BoolProperty(
        name="Add-on installed correctly",
        description="If this is False, the add-on hasn't been installed correctly",
        default=True
    )

    # Add-on Updater Preferences
    updater_expanded_in_preferences_panel: bpy.props.BoolProperty(
        name="Show the updater preferences",
        description="Updater preferences twirled down when True, twirled up when False",
        default=False)

    auto_check_update: bpy.props.BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=True)

    updater_interval_months: bpy.props.IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0)

    updater_interval_days: bpy.props.IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=1,
        min=0,
        max=31)

    updater_interval_hours: bpy.props.IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23)

    updater_interval_minutes: bpy.props.IntProperty(
        name='Minutes',
        description="Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59)


    def draw(self, context):
        layout = self.layout

        width_guess = 460

        # Invalid Installation Warning
        if not utils.is_installation_valid():
            utils.show_invalid_installation_message(layout, width_guess)

        else:

            # Setup
            box = layout.box()
            box.label(text="Setup:")

            row = box.row()
            col = row.column()
            col.label(text="Setup is quick and easy!")
            col = row.column()
            col.operator(operators.AIR_OT_setup_instructions_popup.bl_idname, text="Setup Instructions", icon="HELP")
            col = row.column()
            col.operator("wm.url_open", text="Watch Tutorial", icon="HELP").url = config.VIDEO_TUTORIAL_URL

            row = box.row()
            row.operator("wm.url_open", text="Sign Up For DreamStudio (free)", icon="URL").url = config.DREAM_STUDIO_URL

            row = box.row()
            row.prop(self, "dream_studio_api_key")

            # Notes
            box = layout.box()
            box.label(text="Note:")

            utils.label_multiline(box, text="AI image generation is an incredible technology, and it's only in its infancy. Please use it responsibly and ethically.", width=width_guess)

            # Add-on Updater
            box = layout.box()
            addon_updater_ops.update_settings_ui_condensed(self, context, box)


classes = [
    AIRPreferences,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
