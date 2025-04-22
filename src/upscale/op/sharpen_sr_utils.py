import math
from realesrgan import RealESRGANer
import torch

from upscale.lib.util import Observable
from torch.nn import functional as F


# Ported from realesrgan.RealESRGANer
class TiledSRProcessor(RealESRGANer):
    def __init__(self, scale, model_path, model, tile=0, tile_pad=10, pre_pad=0, half=False, device=None, pad_to_window_size=0):
        self.scale = scale
        self.tile_size = tile
        self.tile_pad = tile_pad
        self.pre_pad = pre_pad
        self.mod_scale = None
        self.half = False if device == 'cpu' else half
        self.half = False

        self.device = device
        model.load_state_dict(torch.load(model_path)['params'], strict=True)

        model.eval()
        self.model = model.to(self.device)
        if self.half:
            self.model = self.model.half()

        self.pad_to_window_size = pad_to_window_size
        self.observer = None

    def setObserver(self, observer: Observable):
        self.observer = observer

    # Some models require tile size is a multiple of windows size.
    def padToMultipleOfWindowSize(sel, img, window_size):
        # pad input image to be a multiple of window_size
        mod_pad_h, mod_pad_w = 0, 0
        _, _, h, w = img.size()
        if h % window_size != 0:
            mod_pad_h = window_size - h % window_size
        if w % window_size != 0:
            mod_pad_w = window_size - w % window_size
        img = F.pad(img, (0, mod_pad_w, 0, mod_pad_h), 'reflect')
        return img

    # @Override
    def tile_process(self):

        batch, channel, height, width = self.img.shape
        output_height = height * self.scale
        output_width = width * self.scale
        output_shape = (batch, channel, output_height, output_width)

        # start with black image
        self.output = self.img.new_zeros(output_shape)
        tiles_x = math.ceil(width / self.tile_size)
        tiles_y = math.ceil(height / self.tile_size)

        self.observer.startJob(tiles_x * tiles_y)

        # loop over all tiles
        for y in range(tiles_y):
            for x in range(tiles_x):
                # extract tile from input image
                ofs_x = x * self.tile_size
                ofs_y = y * self.tile_size
                # input tile area on total image
                input_start_x = ofs_x
                input_end_x = min(ofs_x + self.tile_size, width)
                input_start_y = ofs_y
                input_end_y = min(ofs_y + self.tile_size, height)

                # input tile area on total image with padding
                input_start_x_pad = max(input_start_x - self.tile_pad, 0)
                input_end_x_pad = min(input_end_x + self.tile_pad, width)
                input_start_y_pad = max(input_start_y - self.tile_pad, 0)
                input_end_y_pad = min(input_end_y + self.tile_pad, height)

                # input tile dimensions
                input_tile_width = input_end_x - input_start_x
                input_tile_height = input_end_y - input_start_y
                tile_idx = y * tiles_x + x + 1
                input_tile = self.img[:, :, input_start_y_pad:input_end_y_pad, input_start_x_pad:input_end_x_pad]

                # upscale tile
                try:
                    with torch.no_grad():
                        if self.pad_to_window_size > 0:
                            input_tile = self.padToMultipleOfWindowSize(input_tile, self.pad_to_window_size)
                        output_tile = self.model(input_tile)
                except RuntimeError as error:
                    print('Error', error)

                # output tile area on total image
                output_start_x = input_start_x * self.scale
                output_end_x = input_end_x * self.scale
                output_start_y = input_start_y * self.scale
                output_end_y = input_end_y * self.scale

                # output tile area without padding
                output_start_x_tile = (input_start_x - input_start_x_pad) * self.scale
                output_end_x_tile = output_start_x_tile + input_tile_width * self.scale
                output_start_y_tile = (input_start_y - input_start_y_pad) * self.scale
                output_end_y_tile = output_start_y_tile + input_tile_height * self.scale

                try:
                    # put tile into output image
                    self.output[:, :, output_start_y:output_end_y,
                                output_start_x:output_end_x] = output_tile[:, :, output_start_y_tile:output_end_y_tile,
                                                                           output_start_x_tile:output_end_x_tile]
                except Exception as error:
                    print('Error', error)

                if self.observer is not None:
                    self.observer.updateJob(1)

    def process(self):
        super().process()

    def pre_process(self, img):
        super().pre_process(img)
