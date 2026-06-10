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
        # Precomputed tile occupancy map (True = tile has mask pixels)
        self.tile_occupancy = None

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
            # Precompute tile occupancy map to avoid per-tile reductions
            self._compute_tile_occupancy()

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

    def _compute_tile_occupancy(self):
        """Precompute which tiles contain mask pixels (single device sync)."""
        if self.mask_tensor is None:
            return

        actual_tile_size = self.tileSize - (self.tilePad * 2)
        _, _, h, w = self.mask_tensor.shape
        xtiles = math.ceil(w / actual_tile_size)
        ytiles = math.ceil(h / actual_tile_size)

        # Build occupancy grid on device, then transfer once
        occupancy = torch.zeros((ytiles, xtiles), dtype=torch.bool, device=self.device)
        for y in range(ytiles):
            for x in range(xtiles):
                y1 = y * actual_tile_size
                y2 = min((y + 1) * actual_tile_size, h)
                x1 = x * actual_tile_size
                x2 = min((x + 1) * actual_tile_size, w)
                occupancy[y, x] = (self.mask_tensor[:, :, y1:y2, x1:x2] > 0).any()

        # Single device sync: transfer to CPU
        self.tile_occupancy = occupancy.cpu().numpy()

    def _tile_has_mask_pixels(self, y: int, x: int) -> bool:
        """Check if a tile contains any mask pixels using precomputed occupancy map."""
        if self.tile_occupancy is None:
            return True  # No mask means process all tiles
        return bool(self.tile_occupancy[y, x])

    def _blend_ramp_1d(self, pre: int, core: int, post: int) -> torch.Tensor:
        """Build a 1D blend weight that ramps up over `pre` samples, stays at 1.0
        across the `core`, then ramps down over `post` samples.

        The ramps span the tile overlap so that adjacent tiles cross-fade instead
        of meeting at a hard seam. Endpoints are kept slightly above 0 to avoid
        zero-weight pixels during normalization.
        """
        parts = []
        if pre > 0:
            parts.append(
                torch.linspace(1.0 / (pre + 1), pre / (pre + 1), pre, device=self.device)
            )
        parts.append(torch.ones(core, device=self.device))
        if post > 0:
            parts.append(
                torch.linspace(post / (post + 1), 1.0 / (post + 1), post, device=self.device)
            )
        return torch.cat(parts)

    @torch.no_grad()
    def process_tiles(self):
        actual_tile_size = self.tileSize - (self.tilePad * 2)
        scaled_tile_size = actual_tile_size * self.scale
        scaled_tile_pad = self.tilePad * self.scale
        b, c, h, w = self.img_tensor.shape
        out_h, out_w = h * self.scale, w * self.scale
        xtiles = math.ceil(w / actual_tile_size)
        ytiles = math.ceil(h / actual_tile_size)
        if not self.observer is None:
            self.observer.startJob(xtiles * ytiles)

        # Accumulation buffers for weighted (feathered) tile blending.
        output_accum = torch.zeros((1, 3, out_h, out_w), dtype=torch.float32, device=self.device)
        weight_accum = torch.zeros((1, 1, out_h, out_w), dtype=torch.float32, device=self.device)

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

                is_skip = not self._tile_has_mask_pixels(y, x)

                # Extend the kept region into the overlap on sides that have a
                # neighbour, so tiles can be cross-faded together. Sides on the
                # image border stop at the tile core (the pad there is only
                # reflected padding, not real image data).
                left_ext = scaled_tile_pad if x > 0 else 0
                right_ext = scaled_tile_pad if x < xtiles - 1 else 0
                top_ext = scaled_tile_pad if y > 0 else 0
                bottom_ext = scaled_tile_pad if y < ytiles - 1 else 0

                # Core placement in the output image.
                px_core = x * scaled_tile_size
                py_core = y * scaled_tile_size

                # Destination region in the output image (core + overlap).
                dst_x0 = px_core - left_ext
                dst_x1 = px_core + scaled_tile_size + right_ext
                dst_y0 = py_core - top_ext
                dst_y1 = py_core + scaled_tile_size + bottom_ext

                # Clamp to the output bounds (last row/column may overhang).
                cx0, cx1 = max(dst_x0, 0), min(dst_x1, out_w)
                cy0, cy1 = max(dst_y0, 0), min(dst_y1, out_h)

                # Blend weight window for the (unclamped) kept region.
                wx = self._blend_ramp_1d(left_ext, scaled_tile_size, right_ext)
                wy = self._blend_ramp_1d(top_ext, scaled_tile_size, bottom_ext)
                # Crop the weight window to match the clamped destination.
                wx = wx[(cx0 - dst_x0):wx.shape[0] - (dst_x1 - cx1)]
                wy = wy[(cy0 - dst_y0):wy.shape[0] - (dst_y1 - cy1)]
                weight2d = wy[:, None] * wx[None, :]

                if is_skip:
                    # Non-masked tile: contribute the upscaled original so the
                    # buffers stay fully covered; the final mask blend restores
                    # exact original pixels for these regions.
                    source_region = original_scaled[:, :, cy0:cy1, cx0:cx1]
                else:
                    # Get tile, padded to tile_size + tile_pad
                    tile = self.preprocess_tile(y, x)
                    processed_tile = self.model(tile)
                    # Slice the kept region (core + overlap) from the processed
                    # tile, in processed-tile coordinates.
                    src_x0 = scaled_tile_pad - left_ext + (cx0 - dst_x0)
                    src_y0 = scaled_tile_pad - top_ext + (cy0 - dst_y0)
                    source_region = processed_tile[
                        :, :,
                        src_y0:src_y0 + (cy1 - cy0),
                        src_x0:src_x0 + (cx1 - cx0),
                    ]

                output_accum[:, :, cy0:cy1, cx0:cx1] += source_region * weight2d
                weight_accum[:, :, cy0:cy1, cx0:cx1] += weight2d

                if self.observer is not None:
                    self.observer.updateJob(1)

        # Normalize the accumulated, feathered tiles.
        output_tensor = output_accum / weight_accum.clamp_min(1e-8)

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
