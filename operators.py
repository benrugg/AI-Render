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
            # "prompt": prompt,
        }

        response = requests.get(API_URL, params=params, headers=headers)

        if response.status_code == 200:
            self.report({'INFO'}, "success")
            with open(tmp_filename, 'wb') as file:
                for chunk in response:
                    file.write(chunk)
                file.close()

        elif response.status_code == 404:
            self.report({'ERROR'}, "It looks like the web server this plugin relies on is missing. It's possible this is temporary, and you can try again later.")

        else:
            if 'application/json' in response.headers.get('Content-Type'):
                import json
                response_obj = response.json()
                error_message = response_obj.get('error', f"An unknown error occurred in the DreamStudio API. Full server response: {json.dumps(response_obj)}")
            else:
                error_message = f"An unknown error occurred in the DreamStudio API. Full server response: {str(response.content)}"
            
            self.report({'ERROR'}, error_message)

        return {'FINISHED'}