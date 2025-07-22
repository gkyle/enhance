from sam2.build_sam import build_sam2_hf
from sam2.sam2_image_predictor import SAM2ImagePredictor

import numpy as np

SAM_TYPE = "facebook/sam2.1-hiera-large"


class GenerateMasks:
    def __init__(self, device):
        self.device = device

    def run(self, image, input_boxes, labels):
        sam2_model = build_sam2_hf(SAM_TYPE, device=self.device)
        sam2_predictor = SAM2ImagePredictor(sam2_model)

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
