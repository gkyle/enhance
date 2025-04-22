from enum import Enum
import os
import time

import cv2


class RenderMode(Enum):
    Single = 1
    Split = 2
    Grid = 3


class ZoomLevel(Enum):
    FIT = 1
    FIT_WIDTH = 2
    FIT_HEIGHT = 3


def saveToCache(img, baseName, pathExtra: str = ""):
    base, ext = os.path.splitext(baseName)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    rootPath = os.getcwd() + "/.cache/"
    if not os.path.exists(rootPath):
        os.makedirs(rootPath)
    outpath = os.path.join(rootPath,
                           base + "_sharpened" + pathExtra + "_" + timestamp + ext)
    cv2.imwrite(outpath, img, [cv2.IMWRITE_JPEG_QUALITY, 100])
    return outpath
