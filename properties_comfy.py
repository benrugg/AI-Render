import os
import bpy
from . import utils
from .sd_backends import comfyui_api

from pprint import pprint

WORKFLOW_JSON = {
    "3": {
        "inputs": {
            "seed": 925732691918506,
            "steps": 5,
            "cfg": 2,
            "sampler_name": "dpmpp_sde_gpu",
            "scheduler": "karras",
            "denoise": 1,
            "model": [
                "4",
                0
            ],
            "positive": [
                "13",
                0
            ],
            "negative": [
                "16",
                1
            ],
            "latent_image": [
                "10",
                0
            ]
        },
        "class_type": "KSampler",
        "_meta": {
            "title": "KSampler"
        }
    },
    "4": {
        "inputs": {
            "ckpt_name": "SD15\\28DSTABLEBESTVERSION_v6.safetensors"
        },
        "class_type": "CheckpointLoaderSimple",
        "_meta": {
            "title": "Load Checkpoint"
        }
    },
    "6": {
        "inputs": {
            "text": "positive",
            "clip": [
                "4",
                1
            ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
            "title": "positive"
        }
    },
    "7": {
        "inputs": {
            "text": "negative",
            "clip": [
                "4",
                1
            ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
            "title": "negative"
        }
    },
    "8": {
        "inputs": {
            "samples": [
                "3",
                0
            ],
            "vae": [
                "11",
                0
            ]
        },
        "class_type": "VAEDecode",
        "_meta": {
            "title": "VAE Decode"
        }
    },
    "9": {
        "inputs": {
            "filename_prefix": "ComfyUI",
            "images": [
                "8",
                0
            ]
        },
        "class_type": "SaveImage",
        "_meta": {
            "title": "Save Image"
        }
    },
    "10": {
        "inputs": {
            "pixels": [
                "12",
                0
            ],
            "vae": [
                "11",
                0
            ]
        },
        "class_type": "VAEEncode",
        "_meta": {
            "title": "VAE Encode"
        }
    },
    "11": {
        "inputs": {
            "vae_name": "vae-ft-mse-840000-ema-pruned.safetensors"
        },
        "class_type": "VAELoader",
        "_meta": {
            "title": "Load VAE"
        }
    },
    "12": {
        "inputs": {
            "image": "castel-3dscan-color.png",
            "upload": "image"
        },
        "class_type": "LoadImage",
        "_meta": {
            "title": "color"
        }
    },
    "13": {
        "inputs": {
            "strength": 1,
            "start_percent": 0,
            "end_percent": 1,
            "positive": [
                "6",
                0
            ],
            "negative": [
                "7",
                0
            ],
            "control_net": [
                "14",
                0
            ],
            "image": [
                "15",
                0
            ]
        },
        "class_type": "ControlNetApplyAdvanced",
        "_meta": {
            "title": "Apply ControlNet (Advanced)"
        }
    },
    "14": {
        "inputs": {
            "control_net_name": "SD15\\control_v11\\control_v11f1p_sd15_depth.pth"
        },
        "class_type": "ControlNetLoader",
        "_meta": {
            "title": "Load ControlNet Model"
        }
    },
    "15": {
        "inputs": {
            "image": "castle-3dmodel-depth.png",
            "upload": "image"
        },
        "class_type": "LoadImage",
        "_meta": {
            "title": "depth"
        }
    },
    "16": {
        "inputs": {
            "strength": 1,
            "start_percent": 0,
            "end_percent": 1,
            "positive": [
                "13",
                0
            ],
            "negative": [
                "13",
                1
            ],
            "control_net": [
                "17",
                0
            ],
            "image": [
                "18",
                0
            ]
        },
        "class_type": "ControlNetApplyAdvanced",
        "_meta": {
            "title": "Apply ControlNet (Advanced)"
        }
    },
    "17": {
        "inputs": {
            "control_net_name": "SD15\\control_v11\\control_v11p_sd15_normalbae.pth"
        },
        "class_type": "ControlNetLoader",
        "_meta": {
            "title": "Load ControlNet Model"
        }
    },
    "18": {
        "inputs": {
            "image": "castle-3dmodel-normal.png",
            "upload": "image"
        },
        "class_type": "LoadImage",
        "_meta": {
            "title": "normal"
        }
    },
    "22": {
        "inputs": {
            "resolution": 512,
            "image": [
                "12",
                0
            ]
        },
        "class_type": "BAE-NormalMapPreprocessor",
        "_meta": {
            "title": "BAE Normal Map"
        }
    },
    "25": {
        "inputs": {
            "images": [
                "22",
                0
            ]
        },
        "class_type": "PreviewImage",
        "_meta": {
            "title": "Preview Image"
        }
    }
}


def get_available_workflows(self, context):
    if utils.sd_backend() == "comfyui":
        return comfyui_api.get_workflows()
    else:
        return [("none", "None", "", 0)]


def set_active_workflow(self, context):
    if utils.sd_backend() == "comfyui":
        comfyui_api.set_active_workflow(context, self.comfyui_workflows)
    else:
        return


class AIRPropertiesComfyUI(bpy.types.PropertyGroup):
    comfyui_workflows: bpy.props.EnumProperty(
        name="ComfyUI Workflows",
        default=1,
        items=get_available_workflows,
        description="A list of the available workflows in the path specified in the addon preferences",
        update=set_active_workflow,
    )
    comfyui_active_workflow: bpy.props.StringProperty(
        name="Active Workflow",
        default="",
        description="The active workflow",

    )


def get_filename_from_path(path):
    # Extracts the filename without extension from a given path
    return os.path.splitext(os.path.basename(path))[0]


def create_class(class_name, properties):
    # Create a class with the given properties
    class_dict = {name: prop for name, prop in properties.items()}
    new_class = type(class_name, (bpy.types.PropertyGroup,), class_dict)
    return new_class


def create_property_group_classes(json_data):
    classes = {}
    controls = {}

    for key, val in json_data.items():
        if val["class_type"] == "ControlNetLoader":
            controls[key] = get_filename_from_path(val["inputs"]["control_net_name"])

    for key, val in json_data.items():
        if val["class_type"] == "ControlNetApplyAdvanced" and "control_net" in val["inputs"]:
            control_net_key = val["inputs"]["control_net"][0]
            class_name = controls.get(control_net_key)

            if class_name:
                annotations = {
                    "strength": bpy.props.FloatProperty(
                        name="Strength",
                        default=1.0,
                        soft_min=0.0,
                        soft_max=1.0,
                        min=0.0,
                        max=10.0,
                        description="Strength"
                    ),
                    "start_percent": bpy.props.FloatProperty(
                        name="Start Percent",
                        default=0.0,
                        soft_min=0.0,
                        soft_max=1.0,
                        min=0.0,
                        max=1.0,
                        description="Start Percent"
                    ),
                    "end_percent": bpy.props.FloatProperty(
                        name="End Percent",
                        default=1.0,
                        soft_min=0.0,
                        soft_max=1.0,
                        min=0.0,
                        max=1.0,
                        description="End Percent"
                    )
                }

                new_class_dict = {"__annotations__": annotations}
                new_class = type(class_name, (bpy.types.PropertyGroup,), new_class_dict)
                classes[class_name] = new_class
                # pprint(f"Created class {class_name} with properties: {new_class.__annotations__}")

    return classes

def register_generated_classes(generated_classes):
    for cls_name, cl in generated_classes.items():
        if not hasattr(bpy.types, cls_name):
            bpy.utils.register_class(cl)
            setattr(bpy.types, cls_name, cl)
            # Create a PointerProperty for the class
            prop_name = cls_name.lower()
            setattr(AIRPropertiesComfyUI, prop_name, bpy.props.PointerProperty(type=cl))

def unregister_generated_classes(generated_classes):
    for cls_name, cl in generated_classes.items():
        if hasattr(bpy.types, cls_name):
            # Remove PointerProperty from AIRPropertiesComfyUI
            prop_name = cls_name.lower()
            delattr(AIRPropertiesComfyUI, prop_name)
            # Unregister the class
            bpy.utils.unregister_class(cl)
            delattr(bpy.types, cls_name)

generated_classes = create_property_group_classes(WORKFLOW_JSON)


def register():
    bpy.utils.register_class(AIRPropertiesComfyUI)
    bpy.types.Scene.comfyui_props = bpy.props.PointerProperty(type=AIRPropertiesComfyUI)
    register_generated_classes(generated_classes)


def unregister():
    unregister_generated_classes(generated_classes)
    bpy.utils.unregister_class(AIRPropertiesComfyUI)
    del bpy.types.Scene.comfyui_props
