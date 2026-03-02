from PIL import Image

from enhance.lib.file import File, Mask
from enhance.lib.util import Observable

import enhance.op.florence as florence
import enhance.op.sam as sam


class GenerateMasks(Observable):
    def __init__(self, device):
        super().__init__()

        self.device = device

    def run(self, inFile: File):
        self.startJob(2)

        img = Image.open(inFile.path).convert("RGB")

        gen_labels = florence.GenerateLabels(self.device, observable=self)
        label_results = gen_labels.run(img)
        self.updateJob(1)

        if len(label_results['bboxes']) == 0:
            return False

        gen_masks = sam.GenerateMasks(self.device, observable=self)
        mask_results = gen_masks.run(img, label_results['bboxes'], label_results['labels'])

        if len(mask_results['masks']) > 0:
            inFile.masks = []
            for i in range(len(mask_results['masks'])):
                mask = Mask(
                    score=mask_results['scores'][i],
                    label=mask_results['labels'][i],
                    mask=mask_results['masks'][i],
                    box=mask_results['bboxes'][i]
                )
                inFile.addMask(mask)

        self.updateJob(1)
        return len(mask_results['masks']) > 0
