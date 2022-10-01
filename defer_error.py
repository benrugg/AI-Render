import bpy
import queue
import functools


execution_queue = queue.Queue()


def run_in_main_thread(function):
    execution_queue.put(function)


def execute_queued_functions():
    while not execution_queue.empty():
        function = execution_queue.get()
        function()
    return 1.0


# public method:
def show_error_when_ready(msg):
    run_in_main_thread(functools.partial(bpy.ops.sdr.show_error_popup, 'INVOKE_DEFAULT', error_message=msg))


def register_defer_error():
    bpy.app.timers.register(execute_queued_functions)


def unregister_defer_error():
    bpy.app.timers.unregister(execute_queued_functions)
