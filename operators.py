import bpy
from bpy.app.handlers import persistent
import requests
import time
from . import (
    defer_error,
    utils,
)
from .config import API_URL


def update_compositor_node_with_image(img):
    compositor_nodes = bpy.context.scene.node_tree.nodes
    image_node = compositor_nodes.get('SDR_image_node')
    image_node.image = img


def send_to_api():
    context = bpy.context
    props = context.scene.sdr_props

    api_key = props.api_key
    prompt = props.prompt_text

    tmp_path = context.preferences.filepaths.temporary_directory.rstrip('/')
    if tmp_path == '': tmp_path = '/tmp'

    tmp_filename = f"{tmp_path}/sdr-{int(time.time())}.png"

    headers = {
        "User-Agent": "Blender/" + bpy.app.version_string,
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Dream-Studio-Api-Key": api_key,
    }

    params = {
        "prompt": prompt,
    }

    # send an API request
    response = requests.get(API_URL, params=params, headers=headers)

    # handle a successful response
    if response.status_code == 200:

        # save the image
        with open(tmp_filename, 'wb') as file:
            for chunk in response:
                file.write(chunk)
            file.close()
        
        # load the image into the compositor
        img = bpy.data.images.load(tmp_filename, check_existing=True)
        update_compositor_node_with_image(img)

        # create a texture to be used as a preview image
        # TODO: Finish or remove the preview
        texture = bpy.data.textures.new(name="previewTexture", type="IMAGE")
        texture.image = img
        tex = bpy.data.textures['previewTexture']
        tex.extension = 'CLIP'

    # handle 404
    elif response.status_code in [403, 404]:
        defer_error.show_error_when_ready("It looks like the web server this plugin relies on is missing. It's possible this is temporary, and you can try again later.")

    # handle all other errors
    else:
        if 'application/json' in response.headers.get('Content-Type'):
            import json
            response_obj = response.json()
            if response_obj.get('Message', '') in ['Forbidden', None]:
                error_message = "It looks like the web server this plugin relies on is missing. It's possible this is temporary, and you can try again later."
            else:
                error_message = response_obj.get('error', f"An unknown error occurred in the DreamStudio API. Full server response: {json.dumps(response_obj)}")
        else:
            error_message = f"An unknown error occurred in the DreamStudio API. Full server response: {str(response.content)}"
        
        defer_error.show_error_when_ready(error_message)

    return {'FINISHED'}



def ensure_compositor_nodes():
    context = bpy.context
    context.scene.use_nodes = True
    compositor_nodes = context.scene.node_tree.nodes
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
    create_link = context.scene.node_tree.links.new

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



# TODO: Remove this or change it to the manual trigger
class SDR_OT_send_to_api(bpy.types.Operator):
    "Send our prompt, params and/or image to the API"
    bl_idname = "sdr.send_to_api"
    bl_label = "Test AI" 

    def execute(self, context):
        return send_to_api()


# TODO: Remove this
class SDR_OT_ensure_compositor_nodes(bpy.types.Operator):
    "Ensure that the Stable Diffusion Render compositor nodes are created and working"
    bl_idname = "sdr.ensure_compositor_nodes"
    bl_label = "Ensure Compositor Nodes"

    def execute(self, context):
        return ensure_compositor_nodes()


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


def clear_error(self, context):
    context.scene.sdr_props.error_message = ''


@persistent
def render_pre_handler(scene):
    # when the render is starting, ensure we have the right compositor nodes
    ensure_compositor_nodes()


@persistent
def render_post_handler(scene):
    # when the render is ready:

    # check to see if we have a render result
    is_img_ready = bpy.data.images['Render Result'].has_data

    # if it's ready, post to the api
    if is_img_ready:
        send_to_api()
    else:
        print("Rendered image is not ready")


classes = [
    SDR_OT_send_to_api,
    SDR_OT_ensure_compositor_nodes,
    SDR_OT_show_error_popup,
]


def register_operators():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_operators():
    for cls in classes:
        bpy.utils.unregister_class(cls)
