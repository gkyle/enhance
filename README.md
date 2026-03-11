## Overview

Enhance AI is a desktop application for photographers that sharpens, denoises, and upscales photographs using community-contributed image enhancement models. It can be used standalone or integrated into a Lightroom workflow.

Most general-purpose AI image enhancers try to work for *every kind of image*. But in practice, enhancement models often perform best when trained on very specific subjects.

The core idea behind **Enhance AI** is: **Use specialized image enhancement models for specific subjects.**

For example:
- Birds
- Insects
- Flowers
- Aircraft
- Architecture

When a model is trained on a narrow subject domain, it can learn the textures, edges, and structures that are typical for that subject. This often produces significantly better results than a general-purpose model. Good results can often be achieved with a few thousand training images and a consumer GPU. This makes it possible for the community to build high-quality models for many specific domains.

Enhance AI focuses on model discovery, management, and inference, making it easy to apply these models to your images.

<img width="1812" height="1505" alt="Screenshot 2025-08-29 140627" src="https://github.com/user-attachments/assets/b459cced-266e-48d8-8871-eed1fa5bdcfa" />

## Supported Platforms

Windows, MacOS, Linux

The application will work with discrete GPUs or on CPU. Model performance is significantly improved when running with a discrete GPU.

TODO: Validate hardware support for Intel and AMD GPUs.

## Installation and Usage
Clone this repository or [download the zip](https://github.com/gkyle/enhance/archive/refs/heads/main.zip) and uncompress on your system.

Navigate to the download location and run the appropriate command for your operating system.

On Linux and macOS:

`run.sh`

On Windows:

`run.bat`

Setup will create a sandboxed virtual Python environment and download required packages. It will attempt to determine if a compatible GPU is available on your system. For NVidia users, the CUDA Toolkit must be installed. If drivers or CUDA toolkit installation change after install, changes will be detected the next time the command is run.

## Lightroom Integration (Optional)

Install and run the application from the install location once. This is needed to capture and store the install location for Lightroom.
Open Lightroom. Navigate to File > Plug-in Manager.
Click Add.

Navigate to the install location and select the “enhanceAI.lrdevplugin” folder.

After the plug-in is installed, it can be accessed from:
- File > Plug-in Extras > Enhance with Enhance AI

## Features
### Model Manager
On the right-hand panel, select Model Manager.

<img width="1654" height="1082" alt="Screenshot 2025-08-29 144136" src="https://github.com/user-attachments/assets/4731bdce-1d79-4adb-b5bd-e7d4d11a7664" />

If this is the first time running or if you’d like to check for new models, click “Refresh Models”.

Click “Install” for any models that you want.

### Running Models
On the right-hand panel, select Sharpen, Denoise, or Upscale.

Choose one or more models that you’d like to execute. Press Okay.

A new image will be generated for each chosen model.

If multiple models are chosen, they will execute in sequence. You can view the task queue by selecting the down arrow on the top bar.

<img width="1059" height="875" alt="Screenshot 2025-08-29 144204" src="https://github.com/user-attachments/assets/facaebd6-e4a8-4365-ab26-8e718b49b5c3" />

When execution completes, the view automatically switches to “Side-by-side Compare”.

### Compare Images
Enhance AI supports these views:
- Single image
- Side-by-side compare
- 4-way compare

In all views:
- You can pan by left-pressing and moving the mouse.
- You can zoom using the scroll wheel.

In Side-by-side Compare, you can move the divider by right-pressing the mouse in the desired location.

When viewing upscaled images, the scale is referenced to the original image.

<img width="1812" height="1505" alt="Screenshot 2025-08-29 152023" src="https://github.com/user-attachments/assets/225dda4b-9689-46a8-a575-ad9ef077eaf1" />

### Post Processing
Blend Original Image: Soften the impact of the model on the generated image, by blending with the original. The percentage indicates the amount of the original image included in the blend.

## Supported Models
Enhance AI uses [Spandrel](https://github.com/chaiNNer-org/spandrel) to load models. [Supported model architectures are listed here](https://github.com/chaiNNer-org/spandrel?tab=readme-ov-file#model-architecture-support).

Additional model sources:
- [Open Model DB](https://openmodeldb.info/)
- [Phhofm Github](https://github.com/Phhofm/models/releases)
- [neosr github](https://github.com/neosr-project/neosr) and [discord](https://discord.gg/NN2HGtJ3d6)

### Training and contributing models

TODO
