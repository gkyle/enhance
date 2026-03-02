from sam2.build_sam import build_sam2_hf
from sam2.sam2_image_predictor import SAM2ImagePredictor
from huggingface_hub import try_to_load_from_cache

import numpy as np

SAM_FILENAME = "sam2.1_hiera_large.pt"
SAM_TYPE = "facebook/" + SAM_FILENAME.replace(".pt", "").replace("_", "-")


def _is_model_cached(repo_id):
    """Check if a HuggingFace model is already downloaded in the local cache."""
    result = try_to_load_from_cache(repo_id, SAM_FILENAME)
    return isinstance(result, str)


class GenerateMasks:
    def __init__(self, device, observable=None):
        self.device = device
        self.observable = observable

    def run(self, image, input_boxes, labels):
        if self.observable:
            if not _is_model_cached(SAM_TYPE):
                self.observable.set_status("Downloading SAM2 model (first run)")
        sam2_model = build_sam2_hf(SAM_TYPE, device=self.device)
        sam2_predictor = SAM2ImagePredictor(sam2_model)
        if self.observable:
            self.observable.set_status(None)

        masks = []
        scores = []

        for input_box in input_boxes:
            sam2_predictor.set_image(np.array(image))
            mask, score, _ = sam2_predictor.predict(
                point_coords=None,
                point_labels=None,
                box=input_box,
                multimask_output=False,
            )
            if mask is None or score is None or len(mask) == 0 or len(score) == 0:
                masks.append(None)
                scores.append(None)
            else:
                masks.append(mask[0])
                scores.append(score[0])

        return {
            "masks": masks,
            "scores": scores,
            "bboxes": input_boxes,
            "labels": labels
        }
