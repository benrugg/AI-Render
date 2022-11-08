#  Original code by Michel Anders (@varkenvarken). Modified by Ben Rugg (@benrugg).
#
#  (c) 2017,2021 Michel Anders
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.


import bpy

# function to tag all info areas for redraw
def tag_image_editor_areas_for_redraw(self, context):
    areas = context.window.screen.areas
    for area in areas:
        if area.type == 'IMAGE_EDITOR':
            area.tag_redraw()

# a variable where we can store the original draw funtion
info_header_draw = lambda s,c: None


def register():
    # a value between [0, 100] will show the slider
    bpy.types.Scene.air_progress = bpy.props.FloatProperty(
        default=-1,
        subtype='PERCENTAGE',
        precision=0,
        min=-1,
        soft_min=0,
        soft_max=100,
        max=101,
        update=tag_image_editor_areas_for_redraw,
    )

    # the label in front of the slider can be configured
    bpy.types.Scene.air_progress_label = bpy.props.StringProperty(
        default="Progress",
        update=tag_image_editor_areas_for_redraw,
    )

    # save the original draw method of the Info header
    global info_header_draw
    info_header_draw = bpy.types.IMAGE_HT_tool_header.draw

    # create a new draw function
    def newdraw(self, context):
        global info_header_draw

        # first call the original stuff
        info_header_draw(self, context)

        # then add the prop that acts as a progress indicator
        if (
            context.scene.air_progress >= 0 and
            context.scene.air_progress <= 100
        ):
            self.layout.separator()
            text = context.scene.air_progress_label
            self.layout.prop(context.scene,
                                "air_progress",
                                text=text,
                                slider=True)

    # replace the draw function
    bpy.types.IMAGE_HT_tool_header.draw = newdraw


def unregister():
    global info_header_draw
    bpy.types.IMAGE_HT_tool_header.draw = info_header_draw

    del bpy.types.Scene.air_progress
    del bpy.types.Scene.air_progress_label
