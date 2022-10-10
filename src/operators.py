import bpy
import requests
import functools
import random
import time

from . import (
    config,
    task_queue,
    utils,
)


valid_dimensions_tuple_list = utils.generate_valid_dimensions_tuple_list()


def enable_sdr(scene):
    # register the task queue (this also needs to be done post-load,
    # because app timers get stopped when loading a new blender file)
    task_queue.register()

    # ensure that we have our SDR workspace with a compositor and image viewer,
    # so the new rendered image will actually appear
    ensure_sdr_workspace()

    # create the sdr compositor nodes
    ensure_compositor_node_group(scene)

    # clear any possible past errors in the file (this would happen if sdr
    # was enabled in a file that we just opened, and it had been saved with
    # an error from a past render)
    clear_error(scene)


def mute_compositor_node_group(scene):
    compositor_nodes = scene.node_tree.nodes
    compositor_nodes.get('SDR').mute = True


def unmute_compositor_node_group(scene):
    compositor_nodes = scene.node_tree.nodes
    compositor_nodes.get('SDR').mute = False


def update_compositor_node_with_image(scene, img):
    compositor_nodes = scene.node_tree.nodes
    image_node = compositor_nodes.get('SDR').node_tree.nodes.get('SDR_image_node')
    image_node.image = img


def ensure_compositor_node_group(scene):
    """Ensure that the compositor node group is created"""
    scene.use_nodes = True
    compositor_nodes = scene.node_tree.nodes
    composite_node = compositor_nodes.get('Composite')

    # if our image node already exists, just quit
    if 'SDR' in compositor_nodes:
        return {'FINISHED'}

    # otherwise, create a new node group
    node_tree = bpy.data.node_groups.new('SDR_node_group_v1', 'CompositorNodeTree')

    node_group = compositor_nodes.new('CompositorNodeGroup')
    node_group.node_tree = node_tree
    node_group.location = (400, 500)
    node_group.name = 'SDR'
    node_group.label = 'Stable Diffusion Render'

    group_input = node_tree.nodes.new(type='NodeGroupInput')
    group_input.location = (0, 30)

    group_output = node_tree.nodes.new(type='NodeGroupOutput')
    group_output.location = (620, 0)

    # create a new image node and mix rgb node in the group
    image_node = node_tree.nodes.new(type='CompositorNodeImage')
    image_node.name = 'SDR_image_node'
    image_node.location = (60, -100)
    image_node.label = 'Stable Diffusion Result'

    mix_node = node_tree.nodes.new(type='CompositorNodeMixRGB')
    mix_node.name = 'SDR_mix_node'
    mix_node.location = (350, 75)

    # get a reference to the new link functions, for convenience
    create_link_in_group = node_tree.links.new
    create_link_in_compositor = scene.node_tree.links.new

    # create all the links within the group (group input node and image node to
    # the mix node, and mix node to the group output node)
    create_link_in_group(group_input.outputs[0], mix_node.inputs[1])
    create_link_in_group(image_node.outputs.get('Image'), mix_node.inputs[2])
    create_link_in_group(mix_node.outputs.get('Image'), group_output.inputs[0])

    # get the socket that's currently linked to the compositor, or as a
    # fallback, get the rendered image output
    if composite_node.inputs.get('Image').is_linked:
        original_socket = composite_node.inputs.get('Image').links[0].from_socket
    else:
        original_socket = compositor_nodes['Render Layers'].outputs.get('Image')

    # link the original socket to the input of the group
    create_link_in_compositor(original_socket, node_group.inputs[0])

    # link the output of the group to the compositor node
    create_link_in_compositor(node_group.outputs[0], composite_node.inputs.get('Image'))

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


def set_image_dimensions(context, width, height):
    context.scene.render.resolution_x = width
    context.scene.render.resolution_y = height
    context.scene.render.resolution_percentage = 100

    clear_error(context.scene)


def handle_error(msg, error_key = ''):
    """Show an error popup, and set the error message to be displayed in the ui"""
    print("Stable Diffusion Error: ", msg)
    task_queue.add(functools.partial(bpy.ops.sdr.show_error_popup, 'INVOKE_DEFAULT', error_message=msg, error_key=error_key))
    return False


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


def save_render_to_file(scene, timestamp):
    try:
        tmp_filename = utils.get_temp_render_filename(timestamp)
    except:
        return handle_error("Couldn't create temp directory for images")

    try:
        orig_render_file_format = scene.render.image_settings.file_format
        bpy.data.images['Render Result'].save_render(tmp_filename)
        scene.render.image_settings.file_format = orig_render_file_format
    except:
        return handle_error("Couldn't save rendered image. Please render or try again.")

    return tmp_filename


def do_pre_render_setup(scene, do_mute_node_group=True):
    # Lock the user interface when rendering, so that we can change
    # compositor nodes in the render_pre handler without causing a crash!
    # See: https://docs.blender.org/api/current/bpy.app.handlers.html#note-on-altering-data
    scene.render.use_lock_interface = True

    # clear any previous errors
    clear_error(scene)

    # when the render is starting, ensure we have the right compositor nodes
    ensure_compositor_node_group(scene)

    # then mute the compositor node group, so we get the result of the original render,
    # if that's what we want
    if do_mute_node_group:
        mute_compositor_node_group(scene)
    else:
        unmute_compositor_node_group(scene)


def do_pre_api_setup():
    # switch the workspace to our sdr compositor, so the new rendered image will actually appear
    activate_sdr_workspace()


def validate_params(scene):
    props = scene.sdr_props
    if utils.get_api_key().strip() == "":
        return handle_error("You must enter an API Key to render with Stable Diffusion", "api_key")
    if not utils.are_dimensions_valid(scene):
        return handle_error("Please set width and height to valid values", "dimensions")
    if get_full_prompt(scene) == "":
        return handle_error("Please enter a prompt for Stable Diffusion", "prompt")
    return True


def get_full_prompt(scene):
    props = scene.sdr_props
    prompt = props.prompt_text.strip()
    if prompt == config.default_prompt_text:
        prompt = ""
    if props.use_preset:
        if prompt == "":
            prompt = props.preset_style
        else:
            prompt = prompt + f", {props.preset_style}"
    return prompt


def send_to_api(scene):
    """Post to the API and process the resulting image"""
    props = scene.sdr_props

    # validate the parameters we will send
    if not validate_params(scene):
        return False

    # generate a new seed, if we want a random one
    generate_new_random_seed(scene)

    # prepare a timestamp for the filenames
    timestamp = int(time.time())

    # prepare data for the API request
    headers = {
        "User-Agent": "Blender/" + bpy.app.version_string,
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Dream-Studio-Api-Key": utils.get_api_key(),
    }

    params = {
        "prompt": get_full_prompt(scene),
        "width": utils.get_output_width(scene),
        "height": utils.get_output_height(scene),
        "image_similarity": props.image_similarity,
        "seed": props.seed,
        "cfg_scale": props.cfg_scale,
        "steps": props.steps,
        "sampler": props.sampler,
    }

    # save the rendered image and then read it back in
    tmp_filename = save_render_to_file(scene, timestamp)
    if not tmp_filename:
        return False
    img_file = open(tmp_filename, 'rb')
    files = {"file": img_file}

    # send the API request
    try:
        response = requests.post(config.API_URL, params=params, headers=headers, files=files, timeout=config.request_timeout)
    except requests.exceptions.ReadTimeout:
        img_file.close()
        return handle_error(f"The server timed out. Try again in a moment, or get help. [Get help with timeouts]({config.HELP_WITH_TIMEOUTS_URL})")

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
        tmp_filename = utils.get_temp_output_filename(timestamp)

        with open(tmp_filename, 'wb') as file:
            for chunk in response:
                file.write(chunk)

        # load the image into the compositor
        img = bpy.data.images.load(tmp_filename, check_existing=True)
        update_compositor_node_with_image(scene, img)

        # unmute the compositor node group
        unmute_compositor_node_group(scene)

    # handle 404
    elif response.status_code in [403, 404]:
        return handle_error("It looks like the web server this plugin relies on is missing. It's possible this is temporary, and you can try again later.")

    # handle 500
    elif response.status_code == 500:
        return handle_error(f"An unknown error occurred in the DreamStudio API. Full server response: {str(response.content)}")

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

        return handle_error(error_message, error_key)

    return True


class SDR_OT_enable(bpy.types.Operator):
    "Enable Stable Diffusion Render in this scene"
    bl_idname = "sdr.enable"
    bl_label = "Enable Stable Diffusion Render"

    def execute(self, context):
        enable_sdr(context.scene)
        context.scene.sdr_props.is_enabled = True
        return {'FINISHED'}


class SDR_OT_set_valid_render_dimensions(bpy.types.Operator):
    "Set render width and height to 512 x 512"
    bl_idname = "sdr.set_valid_render_dimensions"
    bl_label = "Set Image Size to 512x512"

    def execute(self, context):
        set_image_dimensions(context, 512, 512)
        return {'FINISHED'}


class SDR_OT_show_other_dimension_options(bpy.types.Operator):
    "Other options for image size"
    bl_idname = "sdr.show_other_dimension_options"
    bl_label = "Image Size Options"
    bl_options = {'REGISTER', 'UNDO'}

    panel_width = 250

    width: bpy.props.EnumProperty(
        name="Image Width",
        default="512",
        items=valid_dimensions_tuple_list,
        description="Image Width"
    )
    height: bpy.props.EnumProperty(
        name="Image Height",
        default="512",
        items=valid_dimensions_tuple_list,
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
        set_image_dimensions(context, int(self.width), int(self.height))
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
        do_pre_render_setup(context.scene, do_mute_node_group=False)
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
    SDR_OT_enable,
    SDR_OT_set_valid_render_dimensions,
    SDR_OT_show_other_dimension_options,
    SDR_OT_generate_new_image_from_render,
    SDR_OT_generate_new_image_from_current,
    SDR_OT_setup_instructions_popup,
    SDR_OT_show_error_popup,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
