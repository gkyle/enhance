import torch
import pynvml
import psutil
from typing import Tuple

try:
    import intel_extension_for_pytorch as ipex
    IPEX_AVAILABLE = True
except ImportError:
    IPEX_AVAILABLE = False

class GPUInfo:

    def __init__(self):
        try:
            self.cudaAvailable = torch.cuda.is_available()
        except Exception as e:
            self.cudaAvailable = False

        try:
            self.mpsAvailable = torch.backends.mps.is_available()
        except Exception as e:
            self.mpsAvailable = False

        try:
            # Check for Intel XPU support
            self.xpuAvailable = IPEX_AVAILABLE and hasattr(torch, 'xpu') and torch.xpu.is_available()
        except (AttributeError, Exception) as e:
            self.xpuAvailable = False

        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                self.useNVML = True
                self.nvmlHandle = pynvml.nvmlDeviceGetHandleByIndex(0)
            else:
                self.useNVML = False
                self.nvmlHandle = None
        except Exception as e:
            self.useNVML = False
            self.nvmlHandle = None

    def getGpuNames(self):
        try:
            if self.mpsAvailable:
                return [["mps", "Apple Silicon GPU (MPS)"]]
            if self.xpuAvailable:
                return [
                    [f"xpu:{i}", torch.xpu.get_device_name(i)]
                    for i in range(torch.xpu.device_count())
                ]
            if self.cudaAvailable:
                return [
                    [f"cuda:{i}", torch.cuda.get_device_name(i)]
                    for i in range(torch.cuda.device_count())
                ]
        except Exception as e:
            pass
        return []

    def getGpuPresent(self):
        return self.cudaAvailable or self.mpsAvailable or self.xpuAvailable

    def getGpuMemory(self) -> Tuple[float, float]:  # Return (total GB, available GB)
        try:
            if self.mpsAvailable:
                total_bytes = psutil.virtual_memory().total
                free_bytes = psutil.virtual_memory().available
                return float(toGB(total_bytes)), float(toGB(free_bytes))
            if self.xpuAvailable:
                free_bytes, total_bytes = torch.xpu.mem_get_info()
                return float(toGB(total_bytes)), float(toGB(free_bytes))
            if self.cudaAvailable:
                free_bytes, total_bytes = torch.cuda.mem_get_info()
                return float(toGB(total_bytes)), float(toGB(free_bytes))
        except Exception as e:
            pass
        return None
    
    def getGpuMemeoryTotal(self) -> float:
        try:
            if self.mpsAvailable:
                total_bytes = psutil.virtual_memory().total
                return float(toGB(total_bytes))
            if self.xpuAvailable:
                free_bytes, total_bytes = torch.xpu.mem_get_info()
                return float(toGB(total_bytes))
            if self.cudaAvailable:
                free_bytes, total_bytes = torch.cuda.mem_get_info()
                return float(toGB(total_bytes))
        except Exception as e:
            pass
        return None
    
    def getGpuMemoryAvailable(self) -> float:
        try:
            if self.mpsAvailable:
                free_bytes = psutil.virtual_memory().available
                return float(toGB(free_bytes))
            if self.xpuAvailable:
                free_bytes, total_bytes = torch.xpu.mem_get_info()
                return float(toGB(free_bytes))
            if self.cudaAvailable:
                free_bytes, total_bytes = torch.cuda.mem_get_info()
                return float(toGB(free_bytes))
        except Exception as e:
            pass
        return None

    def getGpuUtilization(self) -> float:
        try:
            if self.mpsAvailable:
                return None
            if self.xpuAvailable and IPEX_AVAILABLE:
                try:
                    xpu_utilization = ipex.xpu.get_device_utilization(0) / 100.0
                    return xpu_utilization
                except Exception as e:
                    pass
                return None
            if self.cudaAvailable and self.nvmlHandle:
                gpu_utilization = pynvml.nvmlDeviceGetUtilizationRates(self.nvmlHandle).gpu / 100.0
                return gpu_utilization
        except Exception as e:
            pass
        return None

def toGB(bytes):
    return bytes / (1024 * 1024 * 1024)
