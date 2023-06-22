import bpy
from . import (
    addon_updater_ops,
    config,
    operators,
    properties,
    utils,
)


class AIRPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    # AIR Preferences
    dream_studio_api_key: bpy.props.StringProperty(
        name="API Key",
        description="Your DreamStudio API KEY",
    )

    stable_horde_api_key: bpy.props.StringProperty(
        name="API Key",
        description="Your Stable Horde API KEY (optional)",
    )

    is_valid_installation: bpy.props.BoolProperty(
        name="Add-on installed correctly",
        description="If this is False, the add-on hasn't been installed correctly",
        default=True,
    )

    is_local_sd_enabled: bpy.props.BoolProperty(
        name="Enable Rendering with Local Stable Diffusion",
        description="NOTE: This is now legacy, but is used to set sd_backend for anyone who was previously using Automatic1111",
        default=False,
        update=properties.ensure_properties,
    )

    sd_backend: bpy.props.EnumProperty(
        name="Stable Diffusion Backend",
        default="dreamstudio",
        items=[
            ('dreamstudio', 'DreamStudio (cloud)', ''),
            ('stablehorde', 'Stable Horde (cloud)', ''),
            ('automatic1111', 'Automatic1111 (local)', ''),
            ('shark', 'SHARK by nod.ai (local)', ''),
        ],
        update=properties.ensure_properties,
        description="Choose a Stable Diffusion backend to use. DreamStudio is the default, and is the quickest to run. Stable Horde is a community-run backend that is completely free. Automatic1111 is a local installation of Stable Diffusion.",
    )

    local_sd_url: bpy.props.StringProperty(
        name="URL of the Stable Diffusion Web Server",
        description="The location of the web server that is currently running on your local machine",
        default="http://127.0.0.1:7860",
    )

    local_sd_timeout: bpy.props.IntProperty(
        name="Timeout (in seconds)",
        description="How long to wait for your local Stable Diffusion installation to run (in seconds, per image)",
        default=360,
        min=10,
        max=3600,
    )

    is_opted_out_of_analytics: bpy.props.BoolProperty(
        name="Opt out of analytics",
        description="If this is checked, the add-on will not send or store any analytics data",
        default=False,
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
            col = row.column()
            col.label(text="Stable Diffusion Backend:")
            col = row.column()
            col.prop(self, "sd_backend", text="")

            if self.sd_backend == "dreamstudio":
                box.separator()

                row = box.row()
                row.operator("wm.url_open", text="Sign Up For DreamStudio (free)", icon="URL").url = config.DREAM_STUDIO_URL

                row = box.row()
                row.prop(self, "dream_studio_api_key")

            if self.sd_backend == "stablehorde":
                box.separator()

                row = box.row()
                row.operator("wm.url_open", text="Get a Stable Horde API key (free / not required)", icon="URL").url \
                    = config.STABLE_HORDE_URL

                row = box.row()
                row.prop(self, "stable_horde_api_key")

            # Local Installation with Automatic1111
            if self.sd_backend == "automatic1111":
                box = layout.box()
                row = box.row()
                row.label(text="Local Installation with Automatic1111:", icon="INFO")

                utils.label_multiline(box, text="Instead of running in the cloud with DreamStudio, AI Render can hook into an existing local installation of Stable Diffusion. This allows for unlimited, free rendering on your own machine. It requires some advanced setup steps.", width=width_guess)

                box.separator()

                row = box.row()
                col = row.column()
                col.label(text="Local Web Server URL:")
                col = row.column()
                col.prop(self, "local_sd_url", text="")

                row = box.row()
                col = row.column()
                col.label(text="Timeout (in seconds):")
                col = row.column()
                col.prop(self, "local_sd_timeout", text="")

                box.separator()
                utils.label_multiline(box, text=f"AI Render will use your local Stable Diffusion installation. Please make sure the Web UI is launched and running in a terminal.", icon="KEYTYPE_BREAKDOWN_VEC", width=width_guess)

                box.separator()
                row = box.row()
                row.operator("wm.url_open", text="Help with local installation", icon="URL").url \
                    = config.HELP_WITH_LOCAL_INSTALLATION_URL
            
            # Local Installation with SHARK
            if self.sd_backend == "shark":
                box = layout.box()
                row = box.row()
                row.label(text="Local Installation with SHARK", icon="INFO")

                utils.label_multiline(box, text="Instead of running in the cloud with DreamStudio, AI Render can hook into an existing local installation of Stable Diffusion. This allows for unlimited, free rendering on your own machine. It requires some advanced setup steps.", width=width_guess)

                box.separator()

                row = box.row()
                col = row.column()
                col.label(text="Local Web Server URL:")
                col = row.column()
                col.prop(self, "local_sd_url", text="")

                row = box.row()
                col = row.column()
                col.label(text="Timeout (in seconds):")
                col = row.column()
                col.prop(self, "local_sd_timeout", text="")

                box.separator()
                utils.label_multiline(box, text=f"AI Render will use your local Stable Diffusion installation. Please make sure the Web UI is launched and running in a terminal.", icon="KEYTYPE_BREAKDOWN_VEC", width=width_guess)

                box.separator()
                row = box.row()
                row.operator("wm.url_open", text="Help with local installation", icon="URL").url \
                    = config.HELP_WITH_SHARK_INSTALLATION_URL
            
            # Notes
            box = layout.box()
            box.label(text="Note:")

            utils.label_multiline(box, text="AI image generation is an incredible technology, and it's only in its infancy. Please use it responsibly and ethically.", width=width_guess)

            box = layout.box()
            box.label(text="Analytics:")
            utils.label_multiline(box, text="AI Render sends anonymous meta information to Google Analytics, to help improve the add-on. No prompt text or images are sent or stored in any way.", width=width_guess)
            row = box.row()
            row.prop(self, "is_opted_out_of_analytics")

            # Add-on Updater
            box = layout.box()
            addon_updater_ops.update_settings_ui_condensed(self, context, box)


def update_sd_backend_from_previous_installation(context):
    preferences = utils.get_addon_preferences(context)
    if preferences.is_local_sd_enabled:
        preferences.sd_backend = "automatic1111"
        preferences.is_local_sd_enabled = False


classes = [
    AIRPreferences,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
