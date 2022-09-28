import bpy

class SDR_OT_test(bpy.types.Operator):
    "Test"
    bl_idname = "sdr.test"
    bl_label = "Test AI"

    def execute(self, context):
        import requests
        import time
        from .config import API_URL

        sdr_props = context.scene.sdr_props

        api_key = sdr_props.api_key
        prompt = sdr_props.prompt_text

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

            with open(tmp_filename, 'wb') as file:
                for chunk in response:
                    file.write(chunk)
                file.close()
            
            img = bpy.data.images.load(tmp_filename, check_existing=True)
            texture = bpy.data.textures.new(name="previewTexture", type="IMAGE")
            texture.image = img
            tex = bpy.data.textures['previewTexture']
            tex.extension = 'CLIP'

            self.report({'INFO'}, "success")

        # handle 404
        elif response.status_code == 404:
            self.report({'ERROR'}, "It looks like the web server this plugin relies on is missing. It's possible this is temporary, and you can try again later.")

        # handle all other errors
        else:
            if 'application/json' in response.headers.get('Content-Type'):
                import json
                response_obj = response.json()
                if response_obj.get('Message', '') == None:
                    error_message = "It looks like the web server this plugin relies on is missing. It's possible this is temporary, and you can try again later."
                else:
                    error_message = response_obj.get('error', f"An unknown error occurred in the DreamStudio API. Full server response: {json.dumps(response_obj)}")
            else:
                error_message = f"An unknown error occurred in the DreamStudio API. Full server response: {str(response.content)}"
            
            self.report({'ERROR'}, error_message)

        return {'FINISHED'}


class SDR_OT_ensure_compositor_nodes(bpy.types.Operator):
    "Ensure that the Stable Diffusion Render compositor nodes are created and working"
    bl_idname = "sdr.ensure_compositor_nodes"
    bl_label = "Ensure Compositor Nodes"

    def execute(self, context):
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

