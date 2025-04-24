from enum import Enum
import os


class Unpickle:
    # forces reinitialization of instance during unpickling so that fields that weren't present at pickling time are present at run time.
    def __getstate__(self):
        return super().__getstate__()

    def __setstate__(self, state: dict):
        self.__init__()
        self.__dict__.update(state)


class File(Unpickle):

    def __init__(self, path):
        super().__init__()
        self.basename = os.path.basename(path) if path else None
        self.path = path
        self.timestamp = 0

    def setPath(self, path):
        self.path = path
        self.basename = os.path.basename(path) if path else None


class InputFile(File):

    def __init__(self, path):
        super().__init__(path)


class PostProcessOperation(Enum):
    Blend = "Blend"
    Blur = "Blur"
    Downscale = "Downscale"


class PostProcess():
    def __init__(self, operation: PostProcessOperation, parameters: dict):
        self.operation = operation
        self.parameters = parameters


class OutputFile(File):

    def __init__(self, path, baseFile: File, operation=None, postprocess: dict = {}):
        super().__init__(path)

        self.baseFile = baseFile
        self.operation = operation

        if baseFile is not None:
            self.origPath = baseFile.path
        else:
            self.origPath = path
        self.postprocess = postprocess
