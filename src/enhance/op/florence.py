import os

# Set environment variable to suppress trust_remote_code prompts
os.environ["HF_HUB_DISABLE_INTERACTIVE_TRUST_REMOTE_CODE"] = "1"

import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from PIL import Image

from enhance.lib.file import InputFile
from enhance.lib.util import Observable

FLORENCE2_MODEL_ID = "microsoft/Florence-2-base"
TASK_PROMPT = "<OD>"


class GenerateLabels(Observable):
    def __init__(self, device):
        super().__init__()
        self.device = device
        # Load model and processor once during initialization
        self.florence2_model = (
            AutoModelForCausalLM.from_pretrained(
                FLORENCE2_MODEL_ID,
                trust_remote_code=True,
                torch_dtype="auto",
                attn_implementation="eager",
            )
            .eval()
            .to(self.device)
        )
        self.florence2_processor = AutoProcessor.from_pretrained(
            FLORENCE2_MODEL_ID, trust_remote_code=True
        )

    def detect(self, inFile: InputFile):
        img = Image.open(inFile.path).convert("RGB")
        return self.run(img)

    def run(self, img):
        results = run_florence2(
            TASK_PROMPT, None, self.florence2_model, self.florence2_processor, img
        )
        return results[TASK_PROMPT]


def run_florence2(task_prompt, text_input, model, processor, image):
    device = model.device

    if text_input is None:
        prompt = task_prompt
    else:
        prompt = task_prompt + text_input

    # Convert numpy array to PIL Image if needed
    if hasattr(image, "shape"):  # numpy array
        from PIL import Image as PILImage

        pil_image = PILImage.fromarray(image)
        image_size = (pil_image.width, pil_image.height)
    else:  # already PIL Image
        pil_image = image
        image_size = (image.width, image.height)

    inputs = processor(text=prompt, images=pil_image, return_tensors="pt").to(
        device, torch.float16
    )
    generated_ids = model.generate(
        input_ids=inputs["input_ids"].to(device),
        pixel_values=inputs["pixel_values"].to(device),
        max_new_tokens=1024,
        do_sample=False,
        use_cache=False,  # Disable caching to avoid past_key_values issues
    )
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    parsed_answer = processor.post_process_generation(
        generated_text, task=task_prompt, image_size=image_size
    )
    return parsed_answer
