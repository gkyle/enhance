import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from PIL import Image

from upscale.lib.file import InputFile
from upscale.lib.util import Observable

FLORENCE2_MODEL_ID = "microsoft/Florence-2-base"
TASK_PROMPT = "<OD>"


class GenerateLabels(Observable):
    def __init__(self, device):
        super().__init__()
        self.device = device

    def detect(self, inFile: InputFile):
        img = Image.open(inFile.path).convert("RGB")
        return self.run(img)

    def run(self, img):
        # FYI: Forcing revision=pr/27. https://github.com/huggingface/transformers/issues/37712
        florence2_model = AutoModelForCausalLM.from_pretrained(
            FLORENCE2_MODEL_ID, trust_remote_code=True, torch_dtype='auto',  revision="pr/27").eval().to(self.device)
        florence2_processor = AutoProcessor.from_pretrained(FLORENCE2_MODEL_ID, trust_remote_code=True)

        results = run_florence2(TASK_PROMPT, None, florence2_model, florence2_processor, img)
        return results[TASK_PROMPT]


def run_florence2(task_prompt, text_input, model, processor, image):
    device = model.device

    if text_input is None:
        prompt = task_prompt
    else:
        prompt = task_prompt + text_input

    inputs = processor(text=prompt, images=image, return_tensors="pt").to(device, torch.float16)
    generated_ids = model.generate(
        input_ids=inputs["input_ids"].to(device),
        pixel_values=inputs["pixel_values"].to(device),
        max_new_tokens=1024,
        early_stopping=False,
        do_sample=False,
        num_beams=3,
    )
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    parsed_answer = processor.post_process_generation(
        generated_text,
        task=task_prompt,
        image_size=(image.width, image.height)
    )
    return parsed_answer
