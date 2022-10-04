import bpy
import requests
import functools
import time
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


def handle_error(msg):
    """Show an error popup, and set the error message to be displayed in the ui"""
    task_queue.add(functools.partial(bpy.ops.sdr.show_error_popup, 'INVOKE_DEFAULT', error_message=msg))


def clear_error(scene):
    """Clear the error message in the ui"""
    scene.sdr_props.error_message = ''


def clear_error_handler(self, context):
    clear_error(context.scene)


def generate_new_random_seed(scene):
    props = scene.sdr_props
    if (props.use_random_seed):
        props.seed = random.randint(1000000000, 2147483647)


def get_temp_path():
    tmp_path = bpy.context.preferences.filepaths.temporary_directory.rstrip('/')
    if tmp_path == '': tmp_path = '/tmp'
    return tmp_path


def get_temp_render_filename():
    return f"{get_temp_path()}/sdr-temp-render.png"


def get_temp_output_filename():
    return f"{get_temp_path()}/sdr-{int(time.time())}.png"


def save_render_to_file(scene):
    if bpy.data.images['Render Result'].has_data:
        tmp_filename = get_temp_render_filename()

        orig_render_file_format = scene.render.image_settings.file_format
        bpy.data.images['Render Result'].save_render(tmp_filename)
        scene.render.image_settings.file_format = orig_render_file_format

        return tmp_filename
    
    return False


def send_to_api(scene):
    """Post to the API and process the resulting image"""
    props = scene.sdr_props

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
        "image_similarity": props.image_similarity,
        "seed": props.seed,
        "cfg_scale": props.cfg_scale,
        "steps": props.steps,
        "sampler": props.sampler,
    }

    # save the rendered image and then read it back in
    tmp_filename = save_render_to_file(scene)
    if not tmp_filename:
        print("Saving rendered image failed")
        return False

    img_file = open(tmp_filename, 'rb')
    files = {"file": img_file}

    # send an API request
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
        tmp_filename = get_temp_output_filename()

        with open(tmp_filename, 'wb') as file:
            for chunk in response:
                file.write(chunk)
        
        # load the image into the compositor
        img = bpy.data.images.load(tmp_filename, check_existing=True)
        update_compositor_node_with_image(scene, img)

        # unmute the mix node
        unmute_compositor_mix_node(scene)

        # create a texture to be used as a preview image
        # TODO: Finish or remove the preview
        texture = bpy.data.textures.new(name="previewTexture", type="IMAGE")
        texture.image = img
        tex = bpy.data.textures['previewTexture']
        tex.extension = 'CLIP'

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
        try:
            response_obj = response.json()
            if response_obj.get('Message', '') in ['Forbidden', None]:
                error_message = "It looks like the web server this plugin relies on is missing. It's possible this is temporary, and you can try again later."
            else:
                error_message = response_obj.get('error', f"An unknown error occurred in the DreamStudio API. Full server response: {json.dumps(response_obj)}")
        except:
            error_message = f"An unknown error occurred in the DreamStudio API. Full server response: {str(response.content)}"

        handle_error(error_message)
        return False

    return True



# TODO: Remove this or change it to the manual trigger
class SDR_OT_send_to_api(bpy.types.Operator):
    "Send to the API to generate a new image"
    bl_idname = "sdr.send_to_api"
    bl_label = "Generate New Image"

    def execute(self, context):
        send_to_api(context.scene)
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

    error_message: bpy.props.StringProperty(
        name="error_message",
        description="Error Message to display"
    )

    def draw(self, context):
        utils.label_multiline(self.layout, text=self.error_message, icon="ERROR", width=self.width)

    def invoke(self, context, event):
        context.scene.sdr_props.error_message = self.error_message
        return context.window_manager.invoke_props_dialog(self, width=self.width)

    def execute(self, context):
        return {'FINISHED'}



classes = [
    SDR_OT_send_to_api,
    SDR_OT_setup_instructions_popup,
    SDR_OT_show_error_popup,
]


def register_operators():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_operators():
    for cls in classes:
        bpy.utils.unregister_class(cls)
