import subprocess
import re
import sys
import platform
import time

def get_cuda_version():
    # nvidia-smi prints the header (containing "CUDA Version") immediately, then
    # can hang while enumerating the process table on some drivers. Stream its
    # output and stop as soon as we find the version, so we neither hang nor wait
    # out a fixed timeout.
    try:
        proc = subprocess.Popen(
            ['nvidia-smi'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except FileNotFoundError:
        print("nvidia-smi command not found. Is the NVIDIA driver installed?", file=sys.stderr)
        return None

    version = None
    try:
        deadline = time.monotonic() + 15
        for line in proc.stdout:
            match = re.search(r' CUDA Version: \s*([\d.]+)', line)
            if match:
                version = match.group(1)
                break
            if time.monotonic() > deadline:
                break
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    if version is None:
        print("CUDA version not found. Is CUDA Toolkit installed?", file=sys.stderr)
    return version

def has_mps_support():
    """Check if Apple Silicon MPS is available."""
    if sys.platform != 'darwin':
        return False

    # Check if running on Apple Silicon (arm64)
    if platform.machine() != 'arm64':
        return False

    # Verify macOS version supports MPS (macOS 12.3+)
    try:
        mac_version = platform.mac_ver()[0]
        if mac_version:
            major, minor = map(int, mac_version.split('.')[:2])
            # MPS requires macOS 12.3 or later
            if major > 12 or (major == 12 and minor >= 3):
                return True
    except (ValueError, AttributeError):
        pass

    return False

if __name__ == "__main__":
    # First check for MPS on macOS
    if has_mps_support():
        print("mps", end="")
    else:
        # Check for CUDA
        cuda_version = get_cuda_version()
        if not cuda_version is None:
            cuda_version = int(float(cuda_version))
            if cuda_version >= 12:
                print("cu126",end="")
            elif cuda_version == 11:
                print("cu118",end="")
            else:
                print("cpu",end="")
        else:
            print("cpu",end="")
