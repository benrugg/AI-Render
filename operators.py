import bpy
import functools
import random
import time

from . import (
    config,
    progress_bar,
    task_queue,
    utils,
)

from .sd_backends.dreamstudio import dreamstudio_api
from .sd_backends.automatic1111 import automatic1111_api




def enable_air(scene):
    # register the task queue (this also needs to be done post-load,
    # because app timers get stopped when loading a new blender file)
    task_queue.register()

    # ensure that we have our AI Render workspace with a compositor and image viewer,
    # so the new rendered image will actually appear
    ensure_air_workspace()

    # create the ai render compositor nodes
    ensure_compositor_node_group(scene)

    # clear any possible past errors in the file (this would happen if ai render
    # was enabled in a file that we just opened, and it had been saved with
    # an error from a past render)
    clear_error(scene)


def mute_compositor_node_group(scene):
    compositor_nodes = scene.node_tree.nodes
    compositor_nodes.get('AIR').mute = True


def unmute_compositor_node_group(scene):
    compositor_nodes = scene.node_tree.nodes
    compositor_nodes.get('AIR').mute = False


def update_compositor_node_with_image(scene, img):
    compositor_nodes = scene.node_tree.nodes
    image_node = compositor_nodes.get('AIR').node_tree.nodes.get('AIR_image_node')
    image_node.image = img


def get_or_create_composite_node(compositor_nodes):
    """Get the existing Composite node, or create one"""
    if compositor_nodes.get('Composite'):
        return compositor_nodes.get('Composite')

    for node in compositor_nodes:
        if node.type == 'COMPOSITE':
            return node

    return compositor_nodes.new('CompositorNodeComposite')


def get_or_create_render_layers_node(compositor_nodes):
    """Get the existing Render Layers node, or create one"""
    if compositor_nodes.get('Render Layers'):
        return compositor_nodes.get('Render Layers')

    for node in compositor_nodes:
        if node.type == 'R_LAYERS':
            return node

    return compositor_nodes.new('CompositorNodeRLayers')


def ensure_compositor_node_group(scene):
    """Ensure that the compositor node group is created"""
    scene.use_nodes = True
    compositor_nodes = scene.node_tree.nodes

    # if our image node already exists, just quit
    if 'AIR' in compositor_nodes:
        return {'FINISHED'}

    # otherwise, create a new node group
    node_tree = bpy.data.node_groups.new('AIR_node_group_v1', 'CompositorNodeTree')

    node_group = compositor_nodes.new('CompositorNodeGroup')
    node_group.node_tree = node_tree
    node_group.location = (400, 500)
    node_group.name = 'AIR'
    node_group.label = 'AI Render'

    group_input = node_tree.nodes.new(type='NodeGroupInput')
    group_input.location = (0, 30)

    group_output = node_tree.nodes.new(type='NodeGroupOutput')
    group_output.location = (620, 0)

    # create a new image node and mix rgb node in the group
    image_node = node_tree.nodes.new(type='CompositorNodeImage')
    image_node.name = 'AIR_image_node'
    image_node.location = (60, -100)
    image_node.label = 'AI Render Result'

    mix_node = node_tree.nodes.new(type='CompositorNodeMixRGB')
    mix_node.name = 'AIR_mix_node'
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
    composite_node = get_or_create_composite_node(compositor_nodes)
    render_layers_node = get_or_create_render_layers_node(compositor_nodes)

    if composite_node.inputs.get('Image').is_linked:
        original_socket = composite_node.inputs.get('Image').links[0].from_socket
    else:
        original_socket = render_layers_node.outputs.get('Image')

    # link the original socket to the input of the group
    create_link_in_compositor(original_socket, node_group.inputs[0])

    # link the output of the group to the compositor node
    create_link_in_compositor(node_group.outputs[0], composite_node.inputs.get('Image'))

    return {'FINISHED'}


def ensure_air_workspace():
    """Ensure we have a compositor window and an image viewer"""

    # if the workspace isn't in our file, add it from our own included blend file
    if config.workspace_id not in bpy.data.workspaces:

        original_workspace = utils.get_current_workspace()

        bpy.ops.workspace.append_activate(
            idname=config.workspace_id,
            filepath=utils.get_workspace_blend_file_filepath()
        )

        utils.activate_workspace(workspace=original_workspace)


def activate_air_workspace(scene):
    """Activate the special compositor workspace, and make sure it's viewing the render result"""
    try:
        utils.activate_workspace(workspace_id=config.workspace_id)
        utils.view_render_result_in_air_image_editor()
    except:
        scene.air_props.is_enabled = False
        handle_error("Couldn't find the AI Render workspace. Please re-enable AI Render, or deactivate the AI Render add-on.")


def set_image_dimensions(context, width, height):
    context.scene.render.resolution_x = width
    context.scene.render.resolution_y = height
    context.scene.render.resolution_percentage = 100

    clear_error(context.scene)


def handle_error(msg, error_key = ''):
    """Show an error popup, and set the error message to be displayed in the ui"""
    print("AI Render Error: ", msg)
    task_queue.add(functools.partial(bpy.ops.ai_render.show_error_popup, 'INVOKE_DEFAULT', error_message=msg, error_key=error_key))
    return False


def set_silent_error(scene, msg, error_key = ''):
    """Set the error message to be displayed in the ui, but don't show a popup"""
    print("AI Render Error: ", msg)
    scene.air_props.error_message = msg
    scene.air_props.error_key = error_key


def clear_error(scene):
    """Clear the error message in the ui"""
    scene.air_props.error_message = ''
    scene.air_props.error_key = ''


def clear_error_handler(self, context):
    clear_error(context.scene)


def generate_new_random_seed(scene):
    props = scene.air_props
    if (props.use_random_seed):
        props.seed = random.randint(1000000000, 2147483647)


def render_frame(context, current_frame):
    """Render the current frame as part of an animation"""
    # set the frame
    context.scene.frame_set(current_frame)

    # render the frame
    bpy.ops.render.render()

    # post to the api
    return send_to_api(context.scene)


def save_render_to_file(scene, filename_prefix):
    try:
        temp_file = utils.create_temp_file(filename_prefix + "-")
    except:
        return handle_error("Couldn't create temp file for image")

    try:
        orig_render_file_format = scene.render.image_settings.file_format
        orig_render_color_mode = scene.render.image_settings.color_mode
        orig_render_color_depth = scene.render.image_settings.color_depth

        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGBA'
        scene.render.image_settings.color_depth = '8'

        bpy.data.images['Render Result'].save_render(temp_file)

        scene.render.image_settings.file_format = orig_render_file_format
        scene.render.image_settings.color_mode = orig_render_color_mode
        scene.render.image_settings.color_depth = orig_render_color_depth
    except:
        return handle_error("Couldn't save rendered image")

    return temp_file


def save_before_image(scene, filename_prefix):
    ext = utils.get_extension_from_file_format(scene.render.image_settings.file_format)
    if ext:
        ext = f".{ext}"
    filename = f"{filename_prefix}{ext}"
    full_path_and_filename = utils.get_absolute_path_for_output_file(scene.air_props.autosave_image_path, filename)
    try:
        bpy.data.images['Render Result'].save_render(bpy.path.abspath(full_path_and_filename))
    except:
        return handle_error(f"Couldn't save 'before' image to {bpy.path.abspath(full_path_and_filename)}")


def save_after_image(scene, filename_prefix, img_file):
    filename = f"{filename_prefix}.png"
    full_path_and_filename = utils.get_absolute_path_for_output_file(scene.air_props.autosave_image_path, filename)
    try:
        utils.copy_file(img_file, full_path_and_filename)
        return full_path_and_filename
    except:
        return handle_error(f"Couldn't save 'after' image to {bpy.path.abspath(full_path_and_filename)}")


def save_animation_image(scene, filename_prefix, img_file):
    filename = f"{filename_prefix}{str(scene.frame_current).zfill(4)}.png"
    full_path_and_filename = utils.get_absolute_path_for_output_file(scene.air_props.animation_output_path, filename)
    try:
        utils.copy_file(img_file, full_path_and_filename)
        return full_path_and_filename
    except:
        return handle_error(f"Couldn't save animation image to {bpy.path.abspath(full_path_and_filename)}")


def do_pre_render_setup(scene, do_mute_node_group=True):
    # Lock the user interface when rendering, so that we can change
    # compositor nodes in the render_init handler without causing a crash!
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


def do_pre_api_setup(scene):
    # switch the workspace to our ai render compositor, so the new rendered image will actually appear
    activate_air_workspace(scene)


def validate_params(scene):
    if utils.get_api_key().strip() == "" and not utils.do_use_local_sd():
        return handle_error("You must enter an API Key to render with Stable Diffusion", "api_key")
    if not utils.are_dimensions_valid(scene):
        return handle_error("Please set width and height to valid values", "dimensions")
    if utils.are_dimensions_too_large(scene):
        return handle_error("Image dimensions are too large. Please decrease width and/or height", "dimensions")
    if get_full_prompt(scene) == "":
        return handle_error("Please enter a prompt for Stable Diffusion", "prompt")
    return True

def validate_resolution(self,context):
    print(self)

def validate_animation_output_path(scene):
    props = scene.air_props
    if not utils.does_path_exist(props.animation_output_path):
        return handle_error("Animation output path does not exist")
    else:
        return True


def get_full_prompt(scene):
    props = scene.air_props
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
    props = scene.air_props

    # validate the parameters we will send
    if not validate_params(scene):
        return False

    # generate a new seed, if we want a random one
    generate_new_random_seed(scene)

    # prepare the output filenames
    timestamp = int(time.time())
    before_output_filename_prefix = f"ai-render-{timestamp}-1-before"
    after_output_filename_prefix = f"ai-render-{timestamp}-2-after"
    animation_output_filename_prefix = "ai-render-"

    # save the rendered image and then read it back in
    temp_input_file = save_render_to_file(scene, before_output_filename_prefix)
    if not temp_input_file:
        return False
    img_file = open(temp_input_file, 'rb')

    # autosave the before image, if we want that, and we're not rendering an animation
    if (
        props.do_autosave_before_images
        and props.autosave_image_path
        and not props.is_rendering_animation
        and not props.is_rendering_animation_manually
    ):
        save_before_image(scene, before_output_filename_prefix)

    # prepare data for the API request
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

    # send to whichever API we're using
    if utils.do_use_local_sd():
        if utils.local_sd_backend() == "automatic1111":
            output_file = automatic1111_api.send_to_api(params, img_file, after_output_filename_prefix)
        else:
            return handle_error(f"You are trying to use a local Stable Diffusion installation that isn't supported: {utils.local_sd_backend()}")
    else:
        output_file = dreamstudio_api.send_to_api(params, img_file, after_output_filename_prefix)

    # if we got a successful image created, handle it
    if output_file:

        # init var
        new_output_file = None

        # autosave the after image, if we want that, and we're not rendering an animation
        if (
            props.do_autosave_after_images
            and props.autosave_image_path
            and not props.is_rendering_animation
            and not props.is_rendering_animation_manually
        ):
            new_output_file = save_after_image(scene, after_output_filename_prefix, output_file)

        # if we're rendering an animation manually, save the image to the animation output path
        if props.is_rendering_animation_manually:
            new_output_file = save_animation_image(scene, animation_output_filename_prefix, output_file)

        # if we saved a new output image, use it
        if new_output_file:
            output_file = new_output_file

        # load the image into our scene
        try:
            img = bpy.data.images.load(output_file, check_existing=False)
        except:
            return handle_error("Couldn't load the image from Stable Diffusion")

        # load the image into the compositor
        try:
            update_compositor_node_with_image(scene, img)
        except:
            return handle_error("Couldn't load the image into the compositor")

        # unmute the compositor node group
        try:
            unmute_compositor_node_group(scene)
        except:
            return handle_error("Couldn't unmute the compositor node")

        # return success status
        return True

    # else, an error should have been created by the api function
    else:

        # return error status
        return False


class AIR_OT_enable(bpy.types.Operator):
    "Enable AI Render in this scene"
    bl_idname = "ai_render.enable"
    bl_label = "Enable AI Render"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        enable_air(context.scene)
        context.scene.air_props.is_enabled = True
        return {'FINISHED'}


class AIR_OT_set_valid_render_dimensions(bpy.types.Operator):
    "Set render width and height to 512 x 512"
    bl_idname = "ai_render.set_valid_render_dimensions"
    bl_label = "Set Image Size to 512x512"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        set_image_dimensions(context, 512, 512)
        return {'FINISHED'}


class AIR_OT_show_other_dimension_options(bpy.types.Operator):
    "Other options for image size"
    bl_idname = "ai_render.show_other_dimension_options"
    bl_label = "Image Size Options"
    bl_options = {'REGISTER', 'UNDO'}

    panel_width = 250

    width: bpy.props.FloatProperty(
        name="Image Width",
        default=512,
        step=6400,
        precision=0,
        min=384,
        description="Image Width",
        update= validate_resolution
    )
    height: bpy.props.FloatProperty(
        name="Image Height",
        default=512,
        step=6400,
        precision=0,
        min=384,
        description="Image Height",
        update= validate_resolution
    )

    def draw(self, context):
        layout = self.layout
        utils.label_multiline(layout, text="Choose dimensions that Stable Diffusion can work with. (Anything larger than 512x512 risks taking too long and timing out without results)", width=self.panel_width)

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


class AIR_OT_generate_new_image_from_render(bpy.types.Operator):
    "Generate a new Stable Diffusion image - without re-rendering - from the last rendered image"
    bl_idname = "ai_render.generate_new_image_from_render"
    bl_label = "New Image From Last Render"

    def execute(self, context):
        do_pre_render_setup(context.scene)
        do_pre_api_setup(context.scene)

        # post to the api (on a different thread, outside the operator)
        task_queue.add(functools.partial(send_to_api, context.scene))

        return {'FINISHED'}


class AIR_OT_generate_new_image_from_current(bpy.types.Operator):
    "Generate a new Stable Diffusion image - without re-rendering - using the latest Stable Diffusion image as the starting point"
    bl_idname = "ai_render.generate_new_image_from_current"
    bl_label = "New Image From Last AI Image"

    def execute(self, context):
        do_pre_render_setup(context.scene, do_mute_node_group=False)
        do_pre_api_setup(context.scene)

        # post to the api (on a different thread, outside the operator)
        task_queue.add(functools.partial(send_to_api, context.scene))

        return {'FINISHED'}


class AIR_OT_render_animation(bpy.types.Operator):
    "Render an animation using Stable Diffusion"
    bl_idname = "ai_render.render_animation"
    bl_label = "Render Animation"

    _timer = None
    _ticks_since_last_render = 0
    _finished = True
    _start_frame = 0
    _end_frame = 0
    _current_frame = 0
    _orig_current_frame = 0

    def _start_render(self, context):
        self._finished = False

        self._orig_current_frame = context.scene.frame_current
        self._start_frame = context.scene.frame_start
        self._end_frame = context.scene.frame_end
        self._current_frame = context.scene.frame_start
        context.scene.air_props.is_rendering_animation_manually = True

        context.scene.air_progress_status_message = ""
        context.scene.air_progress_label = self._get_label()
        context.scene.air_progress = 0

        self._ticks_since_last_render = 0
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)

    def _end_render(self, context, status_message):
        self._finished = True

        context.scene.frame_current = self._orig_current_frame
        context.scene.air_props.is_rendering_animation_manually = False

        context.scene.air_progress_status_message = status_message
        progress_bar.hide_progress_bar_after_delay()

        context.window_manager.event_timer_remove(self._timer)

    def _advance_frame(self, context):
        self._current_frame += 1
        if self._current_frame > context.scene.frame_end:
            self._end_render(context, "Animation Render Complete")

    def _report_complete(self):
        print("AI Render animation completed")
        self.report({'INFO'}, "AI Render animation completed")

    def _get_total_frames(self):
        return self._end_frame - self._start_frame + 1

    def _get_completed_frames(self):
        return self._current_frame - self._start_frame

    def _get_completed_percent(self):
        return round(self._get_completed_frames() / self._get_total_frames(), 2)

    def _get_label(self):
        return f"AI Render (Frame {self._get_completed_frames()}/{self._get_total_frames()})"

    def modal(self, context, event):
        if event.type == 'ESC':
            print("AI Render animation canceled")
            self.report({'INFO'}, "AI Render animation canceled")
            self._end_render(context, "Animation Render Canceled")
            return {'CANCELLED'}

        elif event.type == 'TIMER' and not self._finished:
            # after each render, wait a few ticks before starting the next one,
            # to give Blender time to update the UI
            if self._ticks_since_last_render < 2:
                self._ticks_since_last_render += 1
                return {'PASS_THROUGH'}
            else:
                self._ticks_since_last_render = 0

            # render the current frame
            was_successful = render_frame(context, self._current_frame)

            # if the render was successful, advance to the next frame.
            # otherwise, quit here with an error.
            if was_successful:
                self._advance_frame(context)
            else:
                print("AI Render animation ended with error")
                self.report({'INFO'}, "AI Render animation ended with error")
                self._end_render(context, "Animation Render Error")
                return {'CANCELLED'}

            # update the progress bar
            context.scene.air_progress_label = self._get_label()
            context.scene.air_progress = self._get_completed_percent() * 100

            # if we're done, report success and quit. otherwise, pass through
            if self._finished:
                self._report_complete()
                return {'FINISHED'}
            else:
                return {'PASS_THROUGH'}

        elif self._finished:
            self._report_complete()
            self._end_render(context, "Animation Render Complete")
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        scene = context.scene

        if validate_params(scene) and validate_animation_output_path(scene):
            do_pre_render_setup(scene)
            do_pre_api_setup(scene)
            self._start_render(context)
            return {'RUNNING_MODAL'}
        else:
            return {'CANCELLED'}


class AIR_OT_setup_instructions_popup(bpy.types.Operator):
    "Show the setup instructions in a popup dialog"
    bl_idname = "ai_render.show_setup_instructions_popup"
    bl_label = "Stable Diffusion Setup"

    width = 350

    message: bpy.props.StringProperty(
        name="message",
        description="Message to display"
    )

    def draw(self, context):
        utils.label_multiline(self.layout, text=self.message, icon="HELP", width=self.width-3, alignment="CENTER")
        row = self.layout.row()
        row.operator("wm.url_open", text="Sign Up For DreamStudio (free)", icon="URL").url = config.DREAM_STUDIO_URL

    def invoke(self, context, event):
        self.message = "This add-on uses a service called DreamStudio. You will need to create a DreamStudio account, and get your own API KEY from them. You will get free credits, which will be used when you render. After using your free credits, you will need to sign up for a membership. DreamStudio is unaffiliated with this Blender add-on. It's just a great and easy to use option!"
        return context.window_manager.invoke_props_dialog(self, width=self.width)

    def execute(self, context):
        return {'FINISHED'}


class AIR_OT_show_error_popup(bpy.types.Operator):
    "Show an error message in a popup dialog"
    bl_idname = "ai_render.show_error_popup"
    bl_label = "AI Render Error"

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
        # store the error key and message in the main AIR props
        context.scene.air_props.error_key = self.error_key
        context.scene.air_props.error_message = self.error_message

        # show a popup
        return context.window_manager.invoke_props_dialog(self, width=self.width)

    def cancel(self, context):
        # report the error, for the status bar
        self.report({'ERROR'}, self.error_message)

    def execute(self, context):
        # report the error, for the status bar
        self.report({'ERROR'}, self.error_message)
        return {'FINISHED'}



classes = [
    AIR_OT_enable,
    AIR_OT_set_valid_render_dimensions,
    AIR_OT_show_other_dimension_options,
    AIR_OT_generate_new_image_from_render,
    AIR_OT_generate_new_image_from_current,
    AIR_OT_render_animation,
    AIR_OT_setup_instructions_popup,
    AIR_OT_show_error_popup,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
