import bpy
import queue
import functools
from . import ui_messages


execution_queue = queue.Queue()


def run_in_main_thread(function):
    execution_queue.put(function)


def execute_queued_functions():
    while not execution_queue.empty():
        function = execution_queue.get()
        function()
    return 1.0


if not bpy.app.timers.is_registered(execute_queued_functions):
    bpy.app.timers.register(execute_queued_functions)


def show_error_when_ready(msg):
    ui_messages.add_message(text=msg)
    run_in_main_thread(functools.partial(bpy.ops.sdr.show_error_popup, 'INVOKE_DEFAULT', error_message=msg))