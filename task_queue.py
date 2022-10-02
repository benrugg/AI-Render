import bpy
import queue


# private
execution_queue = queue.Queue()

def execute_queued_functions():
    while not execution_queue.empty():
        function = execution_queue.get()
        function()
    return 0.2


# public method
def add(function):
    """Add a function to the task queue, to be executed in the main thread"""
    execution_queue.put(function)


def register_task_queue():
    bpy.app.timers.register(execute_queued_functions)


def unregister_task_queue():
    bpy.app.timers.unregister(execute_queued_functions)
