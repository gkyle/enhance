import math
import numpy as np
import torch
from torch.nn import functional as F

from enhance.lib.util import Observable


class TileProcessor:

    def __init__(
        self,
        model,
        tileSize,
        tilePad,
        scale,
        device=None,
        observer: Observable = None,
        mask: np.ndarray = None,
    ):
        self.model = model
        self.tileSize = tileSize
        self.tilePad = tilePad

        self.device = "cpu" if device is None else device
        self.model.to(self.device)
        self.model.eval()

        self.dtype = None
        self.img_tensor = None
        self.imgXPad = 0
        self.imgYPad = 0

        self.scale = scale

        self.observer: Observable = observer

        # Combined mask (binary: 1 = process, 0 = skip)
        self.mask = mask
        self.mask_tensor = None

    def preprocess_img(self):
        # img size should be a multiple of tile size
        # pad image with reflection
        b, c, h, w = self.img_tensor.shape
        self.imgXPad = (self.tileSize - (w % self.tileSize)) % self.tileSize
        self.imgYPad = (self.tileSize - (h % self.tileSize)) % self.tileSize
        x1 = self.imgXPad // 2
        x2 = self.imgXPad - x1
        y1 = self.imgYPad // 2
        y2 = self.imgYPad - y1

        self.img_tensor = F.pad(self.img_tensor, (x1, x2, y1, y2), 'reflect')

        # Also pad the mask if it exists
        if self.mask is not None:
            # Convert mask to tensor and add batch/channel dimensions, move to device
            mask_t = (
                torch.from_numpy(self.mask.astype(np.float32))
                .unsqueeze(0)
                .unsqueeze(0)
                .to(self.device)
            )
            self.mask_tensor = F.pad(mask_t, (x1, x2, y1, y2), "constant", 0)

    def postprocess_result(self, img_tensor):
        # remove padding
        b, c, h, w = img_tensor.shape

        x1 = (self.imgXPad // 2) * self.scale
        x2 = self.imgXPad * self.scale - x1
        y1 = (self.imgYPad // 2) * self.scale
        y2 = self.imgYPad * self.scale - y1

        result = img_tensor[:, :, y1:h - y2, x1:w - x2]

        return result

    def preprocess_tile(self, y, x):
        actualTileSize = self.tileSize - (self.tilePad * 2)

        y1 = max(y * actualTileSize - self.tilePad, 0)
        y2 = (y + 1) * actualTileSize + self.tilePad
        x1 = max(x * actualTileSize - self.tilePad, 0)
        x2 = (x + 1) * actualTileSize + self.tilePad

        tile = self.img_tensor[:, :, y1:y2, x1:x2]

        # Pad tiles to match tile_size
        tile_padY1 = 0
        tile_padY2 = 0
        tile_padX1 = 0
        tile_padX2 = 0

        # Shape is B, C, H, W
        if tile.shape[2] < self.tileSize:
            if y1 == 0:
                tile_padY1 = self.tileSize-tile.shape[2]
            else:
                tile_padY2 = self.tileSize-tile.shape[2]
                if tile_padY2 > tile.shape[2]:
                    tile_padY2 = tile.shape[2]-1

        if tile.shape[3] < self.tileSize:
            if x1 == 0:
                tile_padX1 = self.tileSize-tile.shape[3]
            else:
                tile_padX2 = self.tileSize-tile.shape[3]
                if tile_padX2 > tile.shape[3]:
                    tile_padX2 = tile.shape[3]-1

        tile = F.pad(tile, (tile_padX1, tile_padX2, tile_padY1, tile_padY2), 'reflect')

        # Padding with 'reflect' fails when the padding size exceeds the tile size on a given dimension. So when padding size would be too large, pad the maximum size with relfection, then pad the rest with 'constant'.
        # Applies to remainder at right at bottom edges.
        if tile.shape[2] < self.tileSize or tile.shape[3] < self.tileSize:
            tile_padY1 = 0
            tile_padX1 = 0
            tile_padY2 = self.tileSize-tile.shape[2]
            tile_padX2 = self.tileSize-tile.shape[3]
            tile = F.pad(tile, (tile_padX1, tile_padX2, tile_padY1, tile_padY2), 'constant')

        return tile

    def process_image(self, img):
        self.dtype = img.dtype
        self.img_tensor = self.img2tensor(img).to(self.device)

        self.preprocess_img()
        out_tensor = self.process_tiles()
        if out_tensor is None:
            return None
        out_tensor = self.postprocess_result(out_tensor)
        output_img = self.tensor2img(out_tensor)

        return output_img

    def _tile_has_mask_pixels(self, y: int, x: int) -> bool:
        """Check if a tile contains any mask pixels (optimization to skip empty tiles)."""
        if self.mask_tensor is None:
            return True  # No mask means process all tiles

        actual_tile_size = self.tileSize - (self.tilePad * 2)
        y1 = y * actual_tile_size
        y2 = (y + 1) * actual_tile_size
        x1 = x * actual_tile_size
        x2 = (x + 1) * actual_tile_size

        # Get the mask region for this tile (without padding)
        mask_region = self.mask_tensor[:, :, y1:y2, x1:x2]
        return mask_region.sum() > 0

    @torch.no_grad()
    def process_tiles(self):
        actual_tile_size = self.tileSize - (self.tilePad * 2)
        scaled_tile_size = actual_tile_size * self.scale
        scaled_tile_pad = self.tilePad * self.scale
        b, c, h, w = self.img_tensor.shape
        xtiles = math.ceil(w / actual_tile_size)
        ytiles = math.ceil(h / actual_tile_size)
        if not self.observer is None:
            self.observer.startJob(xtiles * ytiles)

        output_tensor = torch.zeros((1, 3, h*self.scale, w*self.scale), dtype=torch.float32).to(self.device)

        # If we have a mask, also keep a copy of the original scaled up for non-masked regions
        if self.mask_tensor is not None:
            # Scale up input tensor to output size for blending non-masked regions
            original_scaled = F.interpolate(
                self.img_tensor,
                scale_factor=self.scale,
                mode="bicubic",
                align_corners=False,
            )
            # Also scale up the mask
            mask_scaled = F.interpolate(
                self.mask_tensor, scale_factor=self.scale, mode="nearest"
            )

        for y in range(ytiles):
            for x in range(xtiles):
                if self.observer is not None and self.observer.shouldInterrupt():
                    return None

                # Skip tiles with no mask pixels (optimization)
                if not self._tile_has_mask_pixels(y, x):
                    # Copy original pixels for this tile region
                    if self.mask_tensor is not None:
                        px = x * scaled_tile_size
                        py = y * scaled_tile_size
                        trimmed_x = min(scaled_tile_size, output_tensor.shape[3] - px)
                        trimmed_y = min(scaled_tile_size, output_tensor.shape[2] - py)
                        output_tensor[
                            :, :, py : py + trimmed_y, px : px + trimmed_x
                        ] = original_scaled[
                            :, :, py : py + trimmed_y, px : px + trimmed_x
                        ]
                    if self.observer is not None:
                        self.observer.updateJob(1)
                    continue

                # Get tile, padded to tile_size + tile_pad
                tile = self.preprocess_tile(y, x)
                processed_tile = self.model(tile)
                # Remove tile padding
                processed_tile = processed_tile[:, :,
                                                scaled_tile_pad:scaled_tile_pad+scaled_tile_size,
                                                scaled_tile_pad:scaled_tile_pad+scaled_tile_size]

                px = x * scaled_tile_size
                py = y * scaled_tile_size

                # Trim tiles that exceed the image boundary (right and bottom edges)
                trimmed_scaled_tile_size_x = scaled_tile_size
                trimmed_scaled_tile_size_y = scaled_tile_size
                if px + scaled_tile_size > output_tensor.shape[3]:
                    trimmed_scaled_tile_size_x = output_tensor.shape[3] - px
                if py + scaled_tile_size > output_tensor.shape[2]:
                    trimmed_scaled_tile_size_y = output_tensor.shape[2] - py
                output_tensor[:, :, py:py+trimmed_scaled_tile_size_y, px:px+trimmed_scaled_tile_size_x] = \
                    processed_tile[:, :, 0:trimmed_scaled_tile_size_y, 0:trimmed_scaled_tile_size_x]

                if self.observer is not None:
                    self.observer.updateJob(1)

        # Apply mask blending: only keep model output within masked regions
        if self.mask_tensor is not None:
            # Blend: output = mask * model_output + (1 - mask) * original
            output_tensor = (
                mask_scaled * output_tensor + (1 - mask_scaled) * original_scaled
            )

        return output_tensor

    def img2tensor(self, img):
        if self.dtype == np.uint16:
            tensor = torch.from_numpy(img).float() / 65535.0
        else:
            tensor = torch.from_numpy(img).float() / 255.0
        tensor = tensor.permute(2, 0, 1).unsqueeze(0)
        return tensor

    def tensor2img(self, tensor):
        img = tensor.cpu().detach().squeeze(0).permute(1, 2, 0).numpy()
        if self.dtype == np.uint16:
            img = (img * 65535.0).clip(0, 65535).astype(self.dtype)
        elif self.dtype == np.uint8:
            img = (img * 255.0).clip(0, 255).astype(self.dtype)
        return img
