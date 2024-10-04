# AI Render ComfyUI Support

## Branch: comfyui-support

ComfyUI support for AI Render is not included in the main branch of the AI-Render repository, but there is a ComfyUI branch for it

> It works on **Blender 4.2.0 LTS** and above. This branch is a work in progress, so expect bugs and missing features. I used to create our latest Projection Mapping Show [Infinite Loop - AI Endless Exploration](https://www.blendingpixels.com/projects/medimex-2024), so the code has been written with the production time constraint and the need to operate as quickly as possible.

## Installation of the Addon

0. Install Blender 4.2.0 LTS (or later). Uninstall any previous version of AI Render Addon.

1. Switch to the comfyui-support branch at:  
   [https://github.com/benrugg/AI-Render/tree/comfyui-support](https://github.com/benrugg/AI-Render/tree/comfyui-support)

2. Download ZIP from Github.  
  [https://github.com/user-attachments/assets/69c2b9b0-73c5-43d2-b53c-a61218c4b731](https://github.com/user-attachments/assets/69c2b9b0-73c5-43d2-b53c-a61218c4b731)

3. Open Blender 4.2.x and go to Edit > Preferences > Add-ons > Add-ons settings dropdown > Install from Disk.  
  [https://github.com/user-attachments/assets/169055e8-06dc-4453-832c-39998ab02460](https://github.com/user-attachments/assets/169055e8-06dc-4453-832c-39998ab02460)

4. In the Addons preferences, unfold ```AI Render ComfyUI Support``` and check all the settings:

![Addons Preferences](https://i.imgur.com/LSjbraU.png)

You should already have ```ComfyUI Local``` selected as a backend. For typical ComfyUI installations, the default Server URL is the usual ```http://localhost:8188```.

You only need to:

- Set the ```ComfyUI Path``` to the path of your ComfyUI installation.
- Check if the ```Workflow Path``` is correct (It should auto-fill with the Addon folder ```./sd_backends/comfyui/workflows_api/```)

## Core concept

The core concept is simple. The **"CG 2 AI"** idea is to bring all the 3d information, like the depth pass, the normal pass, the open-pose skeleton, etc., from Blender Compositor into ComfyUI and use the ControlNets to influence the AI generation, using the diffusion process like a render engine.

You need some ComfyUI and Blender skills to make the most of this implementation.

## The ComfyUI Example Workflow

If you are confident with ComfyUI, you can use the ```example.json``` file in the ```./sd_backends/comfyui/workflows_api/``` folder as a starting point to create your workflows.

![ComfyUI](https://i.imgur.com/xCy2kYj_d.webp?maxwidth=1520&fidelity=grand)

> Be sure to open the ```example.json``` file in the ```./sd_backends/comfyui/```.  
> **DO NOT** open the ```example_api.json``` in the ```./sd_backends/comfyui/workflows_api/``` folder, which is used by the addon

To get the example work, you'll need the following custom nodes:

- [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack.git)
- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes.git)
- [comfyui_controlnet_aux](https://github.com/Fannovel16/comfyui_controlnet_aux.git)

Must have:

- [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager.git)
- [rgthree-comfy](https://github.com/rgthree/rgthree-comfy.git)

To make the example work, install all the models I'm using for the checkpoint and the controllers, or use your own and create your own workflow.

After you create your workflow, you can save it in the ```./sd_backends/comfyui/workflows_api/``` folder with the DEV option enabled in ComfyUI.

Then, you can use it in Blender. The Addon will look into the ```workflows_api/``` folder and list the items in the dropdown.

## How to create a workflow that the Addon can use

The node mapping works in 2 ways:

1. The ***PARAM_TO_WORKFLOW*** dictionary was the first approach I took. It maps the Blender parameter names to the ComfyUI nodes and tries to reuse the same Blender UI panel of the original AI Render Addon, integrating as best as it can into the original code structure.

1. The ***SUPPORTED NODES***  list accommodates the needs of ComfyUI and its complexity. It's an automatic mapping for a predefined set of ComfyUI nodes

  > During the production, I needed to bring some other nodes from ComfyUI to Blender, so I created a new panel in the AI Render Addon to handle them.

### 1. PARAM_TO_WORKFLOW

Some nodes must have the title (meta_title) of the node with the exact name so the Addon can identify them. They are mapped in the ```PARAM_TO_WORKFLOW``` dictionary.

```json
{
    "prompt": {
        "class_type": "CLIPTextEncode",
        "input_key": "text",
        "meta_title": "positive"
    },
    "negative_prompt": {
        "class_type": "CLIPTextEncode",
        "input_key": "text",
        "meta_title": "negative"
    },
    "color_image": {
        "class_type": "LoadImage",
        "input_key": "image",
        "meta_title": "color"
    },
    "depth_image": {
        "class_type": "LoadImage",
        "input_key": "image",
        "meta_title": "depth"
    },
    "normal_image": {
        "class_type": "LoadImage",
        "input_key": "image",
        "meta_title": "normal"
    }
}
```

So, the ```positive``` and the ```negative``` prompts are CLIPTextEncode nodes, and are mapped to the corresponding parameter of the AI Render UI panel.

The ```color_image```, ```depth_image```, and ```normal_image``` are LoadImage nodes connected to the corresponding controlnet nodes.

> The provided ```example.json``` serves as a template, allowing you to customize and adapt it to your specific needs. After creating your personal workflow, you can open it in the Blender interface and animate, tweak, and experiment with all the parameters of the supported nodes.

![Blender](https://i.imgur.com/Aw1uff0_d.webp?maxwidth=1520&fidelity=grand)

### 2. The ***SUPPORTED NODES***

There is also a set of nodes that are automatically supported. By adding them to your ComfyUI workflow, the Addon will recognize them and make them available in the ```ComfyUI``` Blender UI panel.

At the moment, the supported nodes are:

- CheckpointLoaderSimple
- KSampler*
- LoraLoader
- ControlNetApplyAdvanced
- ACN_AdvancedControlNetApply
- SelfAttentionGuidance
- UpscaleModelLoader
- CLIPSetLastLayer

Feel free to ask for specific nodes to be added. It's very quick to add them.

> *The Ksampler with the title `main_sampler` will also be mapped to the original Sampler panel of the AI Render Addon. I suggest having a unique `main_sampler` at the end of the chain and all the other samplers before so they can be tweaked from the new ComfyUI panel.

## Installation of ComfyUI

### 1. Install [Python](https://www.python.org/ftp/python/3.11.9/)

### 2. Install [Miniconda](https://docs.anaconda.com/miniconda/#quick-command-line-install)

### 3. Create a Conda 3.11 Environment

Open the Terminal and run

```shell
conda create --name comfy python=3.11.9 --yes
```

### [4. Install and Test ComfyUI](https://github.com/comfyanonymous/ComfyUI)

 Navigate to the location where you want ComfyUI and clone the repo

 ```shell
git clone https://github.com/comfyanonymous/ComfyUI.git
```

Enter the directory

```shell
 cd ComfyUI
 ```

Run the `conda install` command specified in the [ComfyUI documentation](https://docs.comfy.org/get_started/manual_install#nvidia:install-nightly)

```shell
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
```

Install the dependencies

 ```shell
pip install -r requirements.txt
```

Test the ComfyUI installation

```shell
python main.py
```

 If everything is set up correctly, you should see the ComfyUI server running.
 Open your browser at `http://127.0.0.1:8188` and check the Comfy UI.

If you don't have any checkpoint SD model, download.

### 5. Install the checkpoint models

 You can download the desired checkpoint models from the [official repositories](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5) or [community sources](https://civitai.com/models), then place them in the designated `models/checkpoints` folder within the ComfyUI directory.

To start simple you can download 1.5 SD models only.
![Civit AI Screenshot](media/Pasted%20image%2020241004124041.png)

Alternatively you can set an `extra_model_paths.yaml` and place into the root of the ComfyUI repository. Here's mine, I have a MODELS folder outside my main COMFY folder, in which I have all my different ComfyUI installations.

```yaml
comfyui:
    base_path: ../../MODELS/
    checkpoints: checkpoints/
    clip: clip/
    clip_vision: clip_vision/
    configs: configs/
    controlnet: controlnet/
    embeddings: embeddings/
    animatediff_models: |
        animatediff/
        animatediff_models/
    animatediff_motion_lora: animatediff_motion_lora/
    loras: |
        Lora/
        loras/
    upscale_models: |
        ESRGAN/
        RealESRGAN/
        SwinIR/
        upscale_models/
    vae: |
        VAE/
        vae/
    ipadapter: ipadapter/
    unet: unet/
```

### 6. Install the required custom nodes

To get the example work, you'll need the following custom nodes:

- [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack.git)
- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes.git)
- [comfyui_controlnet_aux](https://github.com/Fannovel16/comfyui_controlnet_aux.git)

Must have:

- [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager.git)
- [rgthree-comfy](https://github.com/rgthree/rgthree-comfy.git)

### 7. Open the example and download the missing models

After completing the installations, you can now open the provided example workflow in ComfyUI and download any missing models as prompted.
