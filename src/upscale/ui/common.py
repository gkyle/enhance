from enum import Enum
import cv2
from PIL import Image
import tifftools
import logging

logger = logging.getLogger(__name__)

exif_fields = [
    271,   # Make
    272,   # Model
    306,   # DateTime
    700,   # XMLPacket
    33723, # IPTC_NAA
    34853, # GPSInfo
    34858, # TimeZoneOffset
    36867, # DateTimeOriginal
    36868, # DateTimeDigitized
    36880, # OffsetTime
    36881, # OffsetTimeOriginal
    36882, # OffsetTimeDigitized
    37520, # SubSecTime
    37521, # SubSecTimeOriginal
    37522, # SubSecTimeDigitized
    42033, # TimeZoneOffset
    50971, # PreviewDateTime

    42034, # LensSpecification
    42035, # LensMake
    42036, # LensModel
    42037, # LensSerialNumber
    41989, # FocalLengthIn35mmFilm
    37386, # FocalLength
    37379, # BrightnessValue
    37380, # ExposureBiasValue
    37385, # Flash
    34867 # ISOSpeed
]

class RenderMode(Enum):
    Single = 1
    Split = 2
    Grid = 3


class ZoomLevel(Enum):
    FIT = 1
    FIT_WIDTH = 2
    FIT_HEIGHT = 3


# Use PIL to save image and EXIF data for 8bit JPEG and TIF images.
def writeFile(img, basePath, outpath):
    img = img[:, :, ::-1] # bgr2rgb
    dstImg = Image.fromarray(img)

    # Copy EXIF fields
    try:
        srcImg = Image.open(basePath)
        srcExif = srcImg.getexif()
        dstExif = Image.Exif()

        if srcExif:
            for tag, value in srcExif.items():
                if tag in exif_fields:
                    dstExif[tag] = value

    except Exception as e:
        logger.info(f"Unable to copy EXIF fields: {e}")

    dstImg.save(outpath, exif=dstExif, quality=100)


# Since PIL doesn't support 16bit RGB images, use OpenCV to save the file, the reopen, copy, and resave the file with EXIF data using tifftools.
# Also use this method for 8bit TIFF for EXIF handling.
def writeTiffFile(img, basePath, outpath):
    # Save 16bit image data
    cv2.imwrite(outpath, img)

    try:
        # Copy EXIF fields
        srcExif = tifftools.read_tiff(basePath)
        dstExif = tifftools.read_tiff(outpath)

        for tag in exif_fields:
            if tag in srcExif["ifds"][0]["tags"]:
                dstExif["ifds"][0]["tags"][tag] = srcExif["ifds"][0]["tags"][tag]

        # Save again with EXIF data
        tifftools.write_tiff(dstExif, outpath, allowExisting=True)
    except Exception as e:
        logger.warning(f"Unable to copy EXIF fields: {e}")
