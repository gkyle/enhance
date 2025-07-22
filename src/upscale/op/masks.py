from PIL import Image

from upscale.lib.file import File, Mask
from upscale.lib.util import Observable

import upscale.op.florence as florence
import upscale.op.sam as sam


class GenerateMasks(Observable):
    def __init__(self, device):
        super().__init__()

        self.device = device

    def run(self, inFile: File):
        self.startJob(2)

        img = Image.open(inFile.path).convert("RGB")

        genLabels = florence.GenerateLabels(self.device)
        labelResults = genLabels.run(img)
        self.updateJob(1)

        if len(labelResults['bboxes']) == 0:
            return False

        genMasks = sam.GenerateMasks(self.device)
        maskResults = genMasks.run(img, labelResults['bboxes'], labelResults['labels'])

        if len(maskResults['masks']) > 0:
            inFile.masks = []
            for i in range(len(maskResults['masks'])):
                mask = Mask(
                    score=maskResults['scores'][i],
                    label=maskResults['labels'][i],
                    mask=maskResults['masks'][i],
                    box=maskResults['bboxes'][i]
                )
                inFile.masks.append(mask)

        self.updateJob(1)
        return len(maskResults['masks']) > 0
