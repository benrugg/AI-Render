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

The core concept is simple. The "CG 2 AI" idea is to bring all the 3D information, like the depth pass, the normal pass, the open-pose skeleton, etc., from Blender Compositor into ComfyUI and use the ControlNets to influence the AI generation, using the diffusion process like a render engine.

You need some ComfyUI and Blender skills to make the most of this implementation.

## The ComfyUI Example Workflow

If you are confident with ComfyUI, you can use the ```example.json``` file in the ```./sd_backends/comfyui/workflows_api/``` folder as a starting point to create your workflows.

![ComfyUI](https://i.imgur.com/xCy2kYj_d.webp?maxwidth=1520&fidelity=grand)

> Be sure to open the ```example.json``` file in the ```./sd_backends/comfyui/```.  
> **DO NOT** open the ```example_api.json``` in the ```./sd_backends/comfyui/workflows_api/``` folder, which is used by the addon

To get the example work, you'll need the following custom nodes:

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

1. The ***PARAM_TO_WORKFLOW*** dictionary was the first approach I took. It maps the Blender parameter names to the ComfyUI nodes. It tries to reuse the same Blender UI panel as the original AI Render Addon, integrating it into the original code structure as best as possible.

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

So, the ```positive``` and the ```negative``` prompts are CLIPTextEncode nodes and are mapped to the corresponding parameter of the AI Render UI panel.

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

Feel free to ask for specific nodes to be added. It's very quick and easy to add them.

> *The Ksampler with the title `main_sampler` will also be mapped to the original Sampler panel of the AI Render Addon. I suggest having a unique `main_sampler` at the end of the chain and all the other samplers before so they can be tweaked from the new ComfyUI panel.

## Installation of ComfyUI

### 1. Install [Python](https://www.python.org/ftp/python/3.11.9/)

For developing reasons, I prefer to use the same Python version shipped with Blender.

### 2. Install [Miniconda](https://docs.anaconda.com/miniconda/#quick-command-line-install)

I prefer to use `conda` to manage Python environments.

### 3. Create a Conda 3.11 Environment

Open the Terminal and run

```shell
conda create --name comfy python=3.11.9 --yes
```

Activate the environment with

```shell
conda activate comfy
```

### [4. Install and Test ComfyUI](https://github.com/comfyanonymous/ComfyUI)

 **Navigate to the location** where you want ComfyUI and clone the repo

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

Test the ComfyUI installation.

```shell
python main.py
```

 You should see the ComfyUI server running if everything is set up correctly.
 Open your browser at `http://127.0.0.1:8188` and check the Comfy UI.

If you don't have any checkpoint SD model, download it.

### 5. Install the checkpoint models

 You can download the desired checkpoint models from the [official repositories](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5) or [community sources](https://civitai.com/models), then place them in the designated `models/checkpoints` folder within the ComfyUI directory.

To start simple, you can download 1.5 SD models only.
![Civit AI Screenshot](media/Pasted%20image%2020241004124041.png)

Alternatively, you can set an `extra_model_paths.yaml` and place it into the root of the ComfyUI repository. Here's mine. I have a `MODELS` folder outside my main `COMFY` folder, with all my ComfyUI installations. (Yep, I've more than one...)

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

- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes.git)
- [comfyui_controlnet_aux](https://github.com/Fannovel16/comfyui_controlnet_aux.git)

Must have:

- [ComfyUI-Manager](https://github.com/ltdrdata/ComfyUI-Manager.git)
- [rgthree-comfy](https://github.com/rgthree/rgthree-comfy.git)

### 7. Open the example and download the missing models

After completing the installations, you can open the provided example workflow in ComfyUI and download any missing models as prompted.

### 8. Run a test Render from Blender

Open Blender and activate the Addon. Launch a render with `F12` framing the default cube or any geometry. If you have any issues:

1. open the terminal in Blender from `Window > Toggle System Console`
2. Check the output in the terminal of the ComfyUI server

## Troubleshot

Check also the ComfyUI input folder. You should see the temp passes folders:  
![Screenshot 2024-09-13 at 00 05 35](https://private-user-images.githubusercontent.com/1170571/367073785-d3176980-c12f-49c0-bb40-794b6a42c4ee.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MjgwNTY3NDQsIm5iZiI6MTcyODA1NjQ0NCwicGF0aCI6Ii8xMTcwNTcxLzM2NzA3Mzc4NS1kMzE3Njk4MC1jMTJmLTQ5YzAtYmI0MC03OTRiNmE0MmM0ZWUucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI0MTAwNCUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNDEwMDRUMTU0MDQ0WiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9M2UzNzYyYzM1NGU3OWE3YTg4NmM4OTEwNmIzMmM2Njc4Y2U1M2JhZmUyNDM4OWMyZjE5NGFkMWEwNmRhMGNiZCZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.MinqWbE8NqHXsnhsp6kLed3X8Ja6TL-0VuCCDZN5AY8)

The `example_api.json` is just a workflow example. You can open the **non API version** which is located outside of the `./workflow_api folder`.  
[![Uploading Screenshot 2024-09-12 at 22.10.58.png…](https://github.com/benrugg/AI-Render/issues/146)](https://github.com/benrugg/AI-Render/issues/146)

Bypass the nodes of the Alpha trick I'm using if you want, and have a look:  
![Screenshot 2024-09-12 at 22 37 46](https://private-user-images.githubusercontent.com/1170571/367053599-e7a7dc98-f41c-4e46-b7d6-762cd9a79dd3.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MjgwNTY3NDQsIm5iZiI6MTcyODA1NjQ0NCwicGF0aCI6Ii8xMTcwNTcxLzM2NzA1MzU5OS1lN2E3ZGM5OC1mNDFjLTRlNDYtYjdkNi03NjJjZDlhNzlkZDMucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI0MTAwNCUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNDEwMDRUMTU0MDQ0WiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9ZmVmYzVhYmIxNGM0NDJkNWU3NDU4MzAzMmM5NTU2OTY0NTRkZDM5YTI3NGE1NDU4ODBlNDU4YzFjOGMyYmQxOCZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.sPbQVWStRe2_EAkvAbD8EfJVLogk1ajFOea2nK0VoJU)

Take your time to understand the dataflow and read the notes.

You can modify it as you need and create any workflow you want. You don't need to download the ckpt models or the Lora models I'm testing.

### The essential things are

1. Have a LoadImage node for the input image titled "color". This image is ignored if the denoise value of the KSampler is 1.  
    ![Screenshot 2024-09-12 at 22 43 01](https://private-user-images.githubusercontent.com/1170571/367055076-e4df72b4-f1ed-4e50-a899-b441ee8847bc.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MjgwNTY3NDQsIm5iZiI6MTcyODA1NjQ0NCwicGF0aCI6Ii8xMTcwNTcxLzM2NzA1NTA3Ni1lNGRmNzJiNC1mMWVkLTRlNTAtYTg5OS1iNDQxZWU4ODQ3YmMucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI0MTAwNCUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNDEwMDRUMTU0MDQ0WiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9MzBjNWYzMDliMTE1MGQ4MDUwYTdkYzY3ZmE4OTA4MjdiNTM3ZDhmOWMxMDcxMTZjMmE5MDVkOGJiOTI1NWE2MSZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.WvakVv8UEfM9AOV-KRJtXolGjpeq6z5wIz5E5L3vtvQ)

2. Have a SaveImage node for the output image with the title "output_image"  
    ![Screenshot 2024-09-12 at 22 46 15](https://private-user-images.githubusercontent.com/1170571/367055801-8d1b5b00-21e8-4674-97ab-be66f326195d.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MjgwNTY3NDQsIm5iZiI6MTcyODA1NjQ0NCwicGF0aCI6Ii8xMTcwNTcxLzM2NzA1NTgwMS04ZDFiNWIwMC0yMWU4LTQ2NzQtOTdhYi1iZTY2ZjMyNjE5NWQucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI0MTAwNCUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNDEwMDRUMTU0MDQ0WiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9ZWQzMzZlM2U4NjIzMDJmODU5ZmM0MjhlMmU5ZWZlNzNhYTZjYmNlMDc4NGYyOGVkODhlZjMwYmE3MzEyMDkyNCZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.ppjc7s3KzY6WNfIHgexLcB7A6WC9xAtfcuFmXmy8zP0)

If you want to drive the generation better, you can use controlnet models with the same logic:  
![Screenshot 2024-09-12 at 23 02 54](https://private-user-images.githubusercontent.com/1170571/367060525-96afa1dc-524c-4988-a541-7287062e4049.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MjgwNTY3NDQsIm5iZiI6MTcyODA1NjQ0NCwicGF0aCI6Ii8xMTcwNTcxLzM2NzA2MDUyNS05NmFmYTFkYy01MjRjLTQ5ODgtYTU0MS03Mjg3MDYyZTQwNDkucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI0MTAwNCUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNDEwMDRUMTU0MDQ0WiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9YzczZjM3ZTI1YzRhNzRiNGE0NGZiYjRiYjU4NDc1OWUyMDg3Y2YzODczZTEzYTg2YTc1MjA1M2Y0OWIzZmIyNiZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.vtohuec4A3hAHQKMVoUeGSNyL3TMM9Kf6ZzTx6k8G4M)
PS: The lineart is created from the "color" image.

Of course, you need a KSampler node "main_sampler", but you can create any pipeline you need. At the moment, the list of supported node classes that will appear in Blender UI are the following:

```json
[
    "CheckpointLoaderSimple",
    "KSampler",
    "LoraLoader",
    "ControlNetApplyAdvanced",
    "ACN_AdvancedControlNetApply",
    "SelfAttentionGuidance",
    "UpscaleModelLoader",
    "CLIPSetLastLayer"
]
```

If you need any other node inside Blender, just ask me.

To solve your issue, make sure to:

- Use Blender >= 4.2.0

- Check the ComfyUI Setup panel  
    ![Screenshot 2024-09-12 at 23 30 47](https://private-user-images.githubusercontent.com/1170571/367066734-b72c0840-6672-4886-b628-c7f75726b849.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MjgwNTY3NDQsIm5iZiI6MTcyODA1NjQ0NCwicGF0aCI6Ii8xMTcwNTcxLzM2NzA2NjczNC1iNzJjMDg0MC02NjcyLTQ4ODYtYjYyOC1jN2Y3NTcyNmI4NDkucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI0MTAwNCUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNDEwMDRUMTU0MDQ0WiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9NTBkNTIwNjhhOGFmZWNmM2EyNTU0YzAyYzQzYWM2ZTM5YTAyODFhNzM3NjljOTVjMTUyMjViN2M5NWVkNWE4NiZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.d2Yqg7fgvr4Ti9kpqNkon1_t26r984rUu6yGwqr-qYo)

- Leave the compositor open during the render and check what you're sending to comfy and where.  
    ![Screenshot 2024-09-12 at 23 27 02](https://private-user-images.githubusercontent.com/1170571/367066130-a1dcd70a-a50e-48f5-8942-1a07df8a7813.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MjgwNTY3NDQsIm5iZiI6MTcyODA1NjQ0NCwicGF0aCI6Ii8xMTcwNTcxLzM2NzA2NjEzMC1hMWRjZDcwYS1hNTBlLTQ4ZjUtODk0Mi0xYTA3ZGY4YTc4MTMucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI0MTAwNCUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNDEwMDRUMTU0MDQ0WiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9YzlmODRjM2VjMzYzYjVkZTc0OTE3OGVjYTk1Nzg4YzA1NDY5MWM2ZTYzY2I3ZTMzZDk0MjYzNmQ0MDY3MTZiZiZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.eAcCZdZfj2yZ2xkv_jAqmibwZ97LlxqrNkCg7jzd5tk)

- Check the mist pass: For the depth controlnet image, I'm sending the Mist pass, so enable the Mist Viewport Display for the active camera and set it up to match the clipping points of the scene. You can also clamp it in the compositor with the color ramp node; using the Viewer Node, you can preview the passes in the Image Editor  
    ![Screenshot 2024-09-12 at 23 43 52](https://private-user-images.githubusercontent.com/1170571/367070622-6f3859f8-7aa1-47c4-832d-3287b8c487f1.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MjgwNTY3NDQsIm5iZiI6MTcyODA1NjQ0NCwicGF0aCI6Ii8xMTcwNTcxLzM2NzA3MDYyMi02ZjM4NTlmOC03YWExLTQ3YzQtODMyZC0zMjg3YjhjNDg3ZjEucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI0MTAwNCUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNDEwMDRUMTU0MDQ0WiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9MDZjMWQ3Njg0MDA3ODA1MmMwM2E5Mjg3MzdhNDJiZmY1YmE5NjcyZjljNGM0ZTJmNjM1ZDU1OGMwODliYjhhOSZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ._76-SwQpd6WxA2mOAGxfrohyb9KdY0GFjnxhELQSru4)

- Leave the terminal where comfy is running and the Blender system console open to check what's happening during render, report any errors, etc.  
    ![Screenshot 2024-09-12 at 23 58 00](https://private-user-images.githubusercontent.com/1170571/367072358-dd18fb4d-b62a-46cd-b444-b2f2de2bc951.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MjgwNTY3NDQsIm5iZiI6MTcyODA1NjQ0NCwicGF0aCI6Ii8xMTcwNTcxLzM2NzA3MjM1OC1kZDE4ZmI0ZC1iNjJhLTQ2Y2QtYjQ0NC1iMmYyZGUyYmM5NTEucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI0MTAwNCUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNDEwMDRUMTU0MDQ0WiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9MTlhMzAwY2U2ZDA2NWUyYzI0OWJjNjg5MWU1OTNiNGNiMjJjMGNhNGM0NGUxYTg1M2IwYmZmMTYzMWIxMGUxNSZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.Ka_2d4Ytz-UmVGrZ6axlJTbYTh-vdTY3RIrbiK2YwNc)

- Enable Keep User Interface in the Temp Editors:  
    ![Screenshot 2024-09-13 at 00 00 19](https://private-user-images.githubusercontent.com/1170571/367072825-c3fb70b1-59be-4d1f-bab9-f01a5b1eb2df.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MjgwNTY3NDQsIm5iZiI6MTcyODA1NjQ0NCwicGF0aCI6Ii8xMTcwNTcxLzM2NzA3MjgyNS1jM2ZiNzBiMS01OWJlLTRkMWYtYmFiOS1mMDFhNWIxZWIyZGYucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI0MTAwNCUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNDEwMDRUMTU0MDQ0WiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9ODczNzM5MTRiY2ZjMDk5ZjNmNmRiMmVkNTlmY2U0ZjJjMzk1OTJiOWI3ZDhmMDEyNzZhNjFiNDdhN2JjYjViYiZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.kpeLBjjF5eiXECjfnMEIlvsTQlIQjt5OFO9j2vPkUTo)

I'm recording a comprehensive tutorial, but its taking soooooo much time...
