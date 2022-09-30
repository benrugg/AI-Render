# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
# import logging
import time
from . import colors, ui_bgl, utils

# bk_logger = logging.getLogger(__name__)

messages = []
draw_handler_ref = None


# check for same messages and just make them longer by the timeout.
def add_message(text='', timeout=5, color=colors.GREEN):
    """
    Add message to GUI. Function checks for same messages and make them longer by the timeout.
    It also logs the message into the console with levels: Red=Error, other=info.
    """
    global messages

    # if color == colors.RED:
    #     bk_logger.error(text)
    # else:
    #     bk_logger.info(text)

    # check for same messages and just make them longer by the timeout.
    for old_message in messages:
        if old_message.text == text:
            old_message.timeout = old_message.age + timeout
            return
    message = UIMessage(text=text, timeout=timeout, color=color)
    messages.append(message)


class UIMessage():
    def __init__(self, text='', timeout=10, color=(.5, 1, .5, 1)):
        self.text = text
        self.timeout = timeout
        self.start_time = time.time()
        self.color = color
        self.draw_color = color
        self.age = 0
        w, a, r = utils.get_largest_area(area_type='VIEW_3D')
        self.active_area_pointer = a.as_pointer()

    def fade(self):
        fade_time = 1
        self.age = time.time() - self.start_time
        if self.age + fade_time > self.timeout:
            alpha_multiplier = (self.timeout - self.age) / fade_time
            self.draw_color = (self.color[0], self.color[1], self.color[2], self.color[3] * alpha_multiplier)
            if self.age > self.timeout:
                global messages
                try:
                    messages.remove(self)
                except Exception as e:
                    pass

    def draw(self, x, y):
        if (bpy.context.area is not None and bpy.context.area.as_pointer() == self.active_area_pointer):
            ui_bgl.draw_text(self.text, x, y + 8, 24, self.draw_color)


def draw_handler(self, context):
    global messages

    if not utils.guard_from_crash():
        return
    
    for message in messages:
        message.draw(50, 50)
        message.fade()


def register_ui_messages():
    global draw_handler_ref

    args = (None, bpy.context)
    draw_handler_ref = bpy.types.SpaceView3D.draw_handler_add(draw_handler, args, 'WINDOW', 'POST_PIXEL')


def unregister_ui_messages():
    global draw_handler_ref

    bpy.types.SpaceView3D.draw_handler_remove(draw_handler_ref, 'WINDOW')