import bpy
import requests
import functools
import random
from . import (
    config,
    task_queue,
    utils,
)


def mute_compositor_mix_node(scene):
    compositor_nodes = scene.node_tree.nodes
    compositor_nodes.get('SDR_mix_node').mute = True


def unmute_compositor_mix_node(scene):
    compositor_nodes = scene.node_tree.nodes
    compositor_nodes.get('SDR_mix_node').mute = False


def update_compositor_node_with_image(scene, img):
    compositor_nodes = scene.node_tree.nodes
    image_node = compositor_nodes.get('SDR_image_node')
    image_node.image = img


def ensure_compositor_nodes(scene):
    """Ensure that the compositor nodes are created"""
    scene.use_nodes = True
    compositor_nodes = scene.node_tree.nodes
    composite_node = compositor_nodes.get('Composite')

    # if our image node already exists, just quit
    if 'SDR_image_node' in compositor_nodes:
        return {'FINISHED'}

    # othewise, create a new image node and mix rgb node
    image_node = compositor_nodes.new(type='CompositorNodeImage')
    image_node.name = 'SDR_image_node'
    image_node.location = (300, 400)
    image_node.label = 'Stable Diffusion Render'

    mix_node = compositor_nodes.new(type='CompositorNodeMixRGB')
    mix_node.name = 'SDR_mix_node'
    mix_node.location = (550, 500)
    
    # get a reference to the new link function, for convenience
    create_link = scene.node_tree.links.new

    # link the image node to the mix node
    create_link(image_node.outputs.get('Image'), mix_node.inputs[2])

    # get the socket that's currently linked to the compositor, or as a 
    # fallback, get the rendered image output
    if composite_node.inputs.get('Image').is_linked:
        original_socket = composite_node.inputs.get('Image').links[0].from_socket
    else:
        original_socket = compositor_nodes['Render Layers'].outputs.get('Image')
    
    # link the original socket to the input of the mix node
    create_link(original_socket, mix_node.inputs[1])

    # link the mix node to the compositor node
    create_link(mix_node.outputs.get('Image'), composite_node.inputs.get('Image'))

    return {'FINISHED'}


def ensure_sdr_workspace():
    """Ensure we have a compositor window and an image viewer"""
    workspace_id = "Stable Diffusion Render"

    # if the workspace isn't in our file, add it from our own included blend file
    if workspace_id not in bpy.data.workspaces:
        
        original_workspace = utils.get_current_workspace()

        bpy.ops.workspace.append_activate(
            idname=workspace_id,
            filepath=utils.get_workspace_blend_file_filepath()
        )

        utils.activate_workspace(workspace=original_workspace)


def activate_sdr_workspace():
    """Activate the special compositor workspace, and make sure it's viewing the render result"""
    workspace_id = "Stable Diffusion Render"
    try:
        utils.activate_workspace(workspace_id=workspace_id)
        utils.view_render_result_in_sdr_image_editor()
    except:
        handle_error("Couldn't find the Stable Diffusion Render workspace. Please reload this blend file, or deactivate Stable Diffusion Render.")


def handle_error(msg, error_key = ''):
    """Show an error popup, and set the error message to be displayed in the ui"""
    print("Stable Diffusion Error: ", msg)
    task_queue.add(functools.partial(bpy.ops.sdr.show_error_popup, 'INVOKE_DEFAULT', error_message=msg, error_key=error_key))


def clear_error(scene):
    """Clear the error message in the ui"""
    scene.sdr_props.error_message = ''
    scene.sdr_props.error_key = ''


def clear_error_handler(self, context):
    clear_error(context.scene)


def generate_new_random_seed(scene):
    props = scene.sdr_props
    if (props.use_random_seed):
        props.seed = random.randint(1000000000, 2147483647)


def save_render_to_file(scene):
    tmp_filename = utils.get_temp_render_filename()

    orig_render_file_format = scene.render.image_settings.file_format
    bpy.data.images['Render Result'].save_render(tmp_filename)
    scene.render.image_settings.file_format = orig_render_file_format

    return tmp_filename


def do_pre_render_setup(scene, do_mute_mix_node = True):
    # Lock the user interface when rendering, so that we can change
    # compositor nodes in the render_pre handler without causing a crash!
    # See: https://docs.blender.org/api/current/bpy.app.handlers.html#note-on-altering-data
    scene.render.use_lock_interface = True

    # clear any previous errors
    clear_error(scene)

    # when the render is starting, ensure we have the right compositor nodes
    ensure_compositor_nodes(scene)

    # then mute the mix node, so we get the result of the original render,
    # if that's what we want
    if do_mute_mix_node:
        mute_compositor_mix_node(scene)


def do_pre_api_setup():
    # switch the workspace to our sdr compositor, so the new rendered image will actually appear
    activate_sdr_workspace()


def send_to_api(scene):
    """Post to the API and process the resulting image"""
    props = scene.sdr_props

    if not bpy.data.images['Render Result'].has_data:
        handle_error("In order to generate an image, you'll need to render something first. Even just a blank scene is ok.")
        return

    # generate a new seed, if we want a random one
    generate_new_random_seed(scene)

    # prepare data for the API request
    headers = {
        "User-Agent": "Blender/" + bpy.app.version_string,
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Dream-Studio-Api-Key": bpy.context.preferences.addons[__package__].preferences.dream_studio_api_key,
    }

    params = {
        "prompt": props.prompt_text,
        "width": round(scene.render.resolution_x * scene.render.resolution_percentage / 100),
        "height": round(scene.render.resolution_y * scene.render.resolution_percentage / 100),
        "image_similarity": props.image_similarity,
        "seed": props.seed,
        "cfg_scale": props.cfg_scale,
        "steps": props.steps,
        "sampler": props.sampler,
    }

    # save the rendered image and then read it back in
    tmp_filename = save_render_to_file(scene)
    img_file = open(tmp_filename, 'rb')
    files = {"file": img_file}

    # send the API request
    response = requests.post(config.API_URL, params=params, headers=headers, files=files)

    # close the image file
    img_file.close()

    # TODO: REMOVE DEBUGGING CODE...
    # print("request body:")
    # print(response.request.body)
    # print("\n")
    # print("response body:")
    # print(response.content)
    # try:
    #     print(response.json())
    # except:
    #     print("body not json")

    # handle a successful response
    if response.status_code == 200:

        # save the image
        tmp_filename = utils.get_temp_output_filename()

        with open(tmp_filename, 'wb') as file:
            for chunk in response:
                file.write(chunk)
        
        # load the image into the compositor
        img = bpy.data.images.load(tmp_filename, check_existing=True)
        update_compositor_node_with_image(scene, img)

        # unmute the mix node
        unmute_compositor_mix_node(scene)

    # handle 404
    elif response.status_code in [403, 404]:
        handle_error("It looks like the web server this plugin relies on is missing. It's possible this is temporary, and you can try again later.")
        return False

    # handle 500
    elif response.status_code == 500:
        handle_error(f"An unknown error occurred in the DreamStudio API. Full server response: {str(response.content)}")
        return False

    # handle all other errors
    else:
        import json
        error_key = ''

        try:
            response_obj = response.json()
            if response_obj.get('Message', '') in ['Forbidden', None]:
                error_message = "It looks like the web server this plugin relies on is missing. It's possible this is temporary, and you can try again later."
            else:
                error_message = response_obj.get('error', f"An unknown error occurred in the DreamStudio API. Full server response: {json.dumps(response_obj)}")
                error_key = response_obj.get('error_key', '')
        except:
            error_message = f"An unknown error occurred in the DreamStudio API. Full server response: {str(response.content)}"

        handle_error(error_message, error_key)
        return False

    return True


class SDR_OT_set_valid_render_dimensions(bpy.types.Operator):
    "Set render width and height to 512 x 512"
    bl_idname = "sdr.set_valid_render_dimensions"
    bl_label = "Set Image Size to 512x512"

    def execute(self, context):
        context.scene.render.resolution_x = 512
        context.scene.render.resolution_y = 512
        context.scene.render.resolution_percentage = 100
        return {'FINISHED'}


class SDR_OT_show_other_dimension_options(bpy.types.Operator):
    "Other options for image size"
    bl_idname = "sdr.show_other_dimension_options"
    bl_label = "Image Size Options"
    bl_options = {'REGISTER', 'UNDO'}

    panel_width = 250
    valid_dimensions = utils.valid_dimensions_tuple_list()

    width: bpy.props.EnumProperty(
        name="Image Width",
        default="512",
        items=valid_dimensions,
        description="Image Width"
    )
    height: bpy.props.EnumProperty(
        name="Image Height",
        default="512",
        items=valid_dimensions,
        description="Image Height"
    )

    def draw(self, context):
        layout = self.layout
        utils.label_multiline(layout, text="Choose dimensions that Stable Diffusion can work with. (Anything larger than 512x512 may take a long time)", width=self.panel_width)
        
        layout.separator()

        row = layout.row()
        col = row.column()
        col.label(text="Width:")
        col = row.column()
        col.prop(self, "width", text="")

        row = layout.row()
        col = row.column()
        col.label(text="Height:")
        col = row.column()
        col.prop(self, "height", text="")

        layout.separator()

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=self.panel_width)

    def execute(self, context):
        context.scene.render.resolution_x = int(self.width)
        context.scene.render.resolution_y = int(self.height)
        context.scene.render.resolution_percentage = 100
        return {'FINISHED'}


class SDR_OT_generate_new_image_from_render(bpy.types.Operator):
    "Generate a new Stable Diffusion image (from the rendered image)"
    bl_idname = "sdr.generate_new_image_from_render"
    bl_label = "Generate New Image From Render"

    def execute(self, context):
        do_pre_render_setup(context.scene)
        do_pre_api_setup()

        # post to the api (on a different thread, outside the operator)
        task_queue.add(functools.partial(send_to_api, context.scene))
        
        return {'FINISHED'}


class SDR_OT_generate_new_image_from_current(bpy.types.Operator):
    "Generate a new Stable Diffusion image (from the current Stable Diffusion image)"
    bl_idname = "sdr.generate_new_image_from_current"
    bl_label = "Generate New Image From Current"

    def execute(self, context):
        do_pre_render_setup(context.scene, False)
        do_pre_api_setup()
        
        # post to the api (on a different thread, outside the operator)
        task_queue.add(functools.partial(send_to_api, context.scene))

        return {'FINISHED'}


class SDR_OT_setup_instructions_popup(bpy.types.Operator):
    "Show the setup instructions in a popup dialog"
    bl_idname = "sdr.show_setup_instructions_popup"
    bl_label = "Stable Diffusion Render Setup"

    width = 350

    message: bpy.props.StringProperty(
        name="message",
        description="Message to display"
    )

    def draw(self, context):
        utils.label_multiline(self.layout, text=self.message, icon="HELP", width=self.width)
        row = self.layout.row()
        row.operator("wm.url_open", text="Sign Up For DreamStudio (free)", icon="URL").url = config.DREAM_STUDIO_URL

    def invoke(self, context, event):
        self.message = "The Stable Diffusion Renderer uses a service called DreamStudio. You will need to create a DreamStudio account, and get your own API KEY from them. You will get free credits, which will be used when you render. After using your free credits, you will need to sign up for a membership. DreamStudio is unaffiliated with this Blender Plugin. It's just a great and easy to use option!"
        return context.window_manager.invoke_props_dialog(self, width=self.width)

    def execute(self, context):
        return {'FINISHED'}


class SDR_OT_show_error_popup(bpy.types.Operator):
    "Show an error message in a popup dialog"
    bl_idname = "sdr.show_error_popup"
    bl_label = "Stable Diffusion Render Error"

    width = 350

    error_key: bpy.props.StringProperty(
        name="error_key",
        default="",
        description="Error key code related to specific api param that had an error"
    )

    error_message: bpy.props.StringProperty(
        name="error_message",
        description="Error Message to display"
    )

    def draw(self, context):
        utils.label_multiline(self.layout, text=self.error_message, icon="ERROR", width=self.width)

    def invoke(self, context, event):
        # store the error key and message in the main SDR props
        context.scene.sdr_props.error_key = self.error_key
        context.scene.sdr_props.error_message = self.error_message

        # show a popup
        return context.window_manager.invoke_props_dialog(self, width=self.width)

    def execute(self, context):
        # report the error, for the status bar
        self.report({'ERROR'}, self.error_message)
        return {'FINISHED'}



classes = [
    SDR_OT_set_valid_render_dimensions,
    SDR_OT_show_other_dimension_options,
    SDR_OT_generate_new_image_from_render,
    SDR_OT_generate_new_image_from_current,
    SDR_OT_setup_instructions_popup,
    SDR_OT_show_error_popup,
]


def register_operators():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_operators():
    for cls in classes:
        bpy.utils.unregister_class(cls)
