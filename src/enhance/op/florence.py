import os

# Set environment variable to suppress trust_remote_code prompts
os.environ["HF_HUB_DISABLE_INTERACTIVE_TRUST_REMOTE_CODE"] = "1"

import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from huggingface_hub import try_to_load_from_cache

FLORENCE2_MODEL_ID = "microsoft/Florence-2-base"
TASK_PROMPT = "<OD>"


def _is_model_cached(repo_id):
    """Check if a HuggingFace model is already downloaded in the local cache."""
    result = try_to_load_from_cache(repo_id, "config.json")
    return isinstance(result, str)


class GenerateLabels:
    def __init__(self, device, observable):
        self.device = device
        self.florence2_model = None
        self.florence2_processor = None
        self.observable = observable

    def _load_model(self):
        if self.florence2_model is not None:
            return
        if not _is_model_cached(FLORENCE2_MODEL_ID):
            self.observable.set_status("Downloading Florence-2 model (first run)")
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
        self.observable.set_status(None)

    def run(self, img):
        self._load_model()
        self.observable.set_status("Detecting subjects")
        results = _run_florence2(
            TASK_PROMPT, None, self.florence2_model, self.florence2_processor, img
        )
        self.observable.set_status(None)
        return results[TASK_PROMPT]


def _run_florence2(task_prompt, text_input, model, processor, image):
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
