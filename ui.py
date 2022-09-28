import bpy
from . import operators

class SDR_PT_main(bpy.types.Panel):
    bl_label = "Stable Diffusion Render"
    bl_idname = "SDR_PT_main"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_order = 0


    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdr_props


class SDR_PT_setup(bpy.types.Panel):
    bl_label = "Setup"
    bl_idname = "SDR_PT_setup"
    bl_parent_id = "SDR_PT_main"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdr_props

        layout.label(text="The Stable Diffusion Renderer uses a service called DreamStudio. You will need to create a DreamStudio account, and get your own API KEY from them. You will get free credits, which will be used when you render. After using your free credits, you would need to sign up for a membership. DreamStudio is unafiliated with this Blender Plugin. It's just a great and easy to use option!")

        row = layout.row()
        row.operator("wm.url_open", text="Sign Up For DreamStudio (free)", icon="URL").url = "https://beta.dreamstudio.ai/"
        
        row = layout.row()
        row.prop(props, 'api_key')


class SDR_PT_prompt(bpy.types.Panel):
    bl_label = "Prompt"
    bl_idname = "SDR_PT_prompt"
    bl_parent_id = "SDR_PT_main"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdr_props

        # Prompt
        row = layout.row()
        row.scale_y = 1.8
        row.prop(props, 'prompt_text')

        row = layout.row()
        sub = row.column()
        sub.label(text="Prompt Strength")
        sub = row.column()
        sub.prop(props, 'prompt_strength', text="", slider=False)

        row = layout.row()
        sub = row.column()
        sub.label(text="Image Strength")
        sub = row.column()
        sub.prop(props, 'image_strength', text="", slider=False)


class SDR_PT_seed(bpy.types.Panel):
    bl_label = "Seed"
    bl_idname = "SDR_PT_seed"
    bl_parent_id = "SDR_PT_main"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdr_props

        # Seed
        row = layout.row()
        sub = row.column()
        sub.prop(props, 'use_random_seed')

        sub = row.column()
        sub.prop(props, 'seed')
        sub.enabled = not props.use_random_seed


class SDR_PT_test(bpy.types.Panel):
    bl_label = "Test"
    bl_idname = "SDR_PT_test"
    bl_parent_id = "SDR_PT_main"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdr_props

        # Test
        row = layout.row()
        row.operator(operators.SDR_OT_test.bl_idname)