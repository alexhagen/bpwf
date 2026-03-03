"""
VDB file utilities for bpwf - handles saving 3D arrays to OpenVDB format.

This module provides functionality to save 3D data (as Python lists, numpy arrays,
or torch tensors) to VDB files. It automatically detects if pyopenvdb is available,
and falls back to using Docker with the aswf/ci-vfxall image if needed.
"""

import os
import sys
import tempfile
import shutil
from typing import Union, Optional, Tuple, List
from pathlib import Path

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


def check_openvdb_available() -> Tuple[bool, str]:
    """
    Check if pyopenvdb can be imported and can write VDB files.
    
    Returns:
        tuple: (success: bool, message: str)
            - success: True if pyopenvdb is available and functional
            - message: Description of the status or error
    """
    try:
        import pyopenvdb as vdb
    except ImportError:
        return False, "pyopenvdb is not installed. Install with: pip install pyopenvdb"
    
    # Test if we can create a FloatGrid
    try:
        grid = vdb.FloatGrid()
        grid.name = "test"
    except Exception as e:
        return False, f"pyopenvdb is installed but cannot create FloatGrid: {str(e)}"
    
    # Test if we can write to a file
    try:
        with tempfile.NamedTemporaryFile(suffix='.vdb', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            vdb.write(tmp_path, grids=[grid])
            # Verify file was created
            if not os.path.exists(tmp_path):
                return False, "pyopenvdb write succeeded but file was not created"
            return True, "pyopenvdb is available and functional"
        finally:
            # Clean up test file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except Exception as e:
        return False, f"pyopenvdb cannot write VDB files: {str(e)}"


def check_docker_available() -> Tuple[bool, str]:
    """
    Check if Docker is available on the system.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        import subprocess
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, f"Docker is available: {result.stdout.strip()}"
        else:
            return False, "Docker command failed"
    except FileNotFoundError:
        return False, "Docker is not installed or not in PATH"
    except Exception as e:
        return False, f"Error checking Docker: {str(e)}"


def _normalize_to_numpy(data: Union[List, 'np.ndarray', 'torch.Tensor']) -> 'np.ndarray':
    """
    Convert input data to numpy array.
    
    Args:
        data: Input data as list of lists, numpy array, or torch tensor
        
    Returns:
        numpy.ndarray: 3D numpy array
        
    Raises:
        ValueError: If data cannot be converted or is not 3D
        ImportError: If numpy is not available
    """
    if not HAS_NUMPY:
        raise ImportError("numpy is required for VDB operations. Install with: pip install numpy")
    
    # Convert torch tensor to numpy
    if HAS_TORCH and isinstance(data, torch.Tensor):
        data = data.detach().cpu().numpy()
    
    # Convert list to numpy
    elif isinstance(data, (list, tuple)):
        data = np.array(data, dtype=np.float32)
    
    # Already numpy array
    elif isinstance(data, np.ndarray):
        data = data.astype(np.float32)
    
    else:
        raise ValueError(f"Unsupported data type: {type(data)}. Expected list, numpy.ndarray, or torch.Tensor")
    
    # Validate 3D
    if data.ndim != 3:
        raise ValueError(f"Data must be 3D, got shape {data.shape}")
    
    return data


def _save_vdb_native(
    data: 'np.ndarray',
    filepath: str,
    voxel_size: float = 1.0,
    transform: Optional[dict] = None
) -> bool:
    """
    Save VDB file using native pyopenvdb.
    
    Args:
        data: 3D numpy array
        filepath: Output VDB file path
        voxel_size: Size of each voxel
        transform: Optional transform parameters
        
    Returns:
        bool: True if successful
        
    Raises:
        ImportError: If pyopenvdb is not available
        Exception: If writing fails
    """
    try:
        import pyopenvdb as vdb
    except ImportError:
        raise ImportError("pyopenvdb is not installed. Install with: pip install pyopenvdb")
    
    # Create FloatGrid
    grid = vdb.FloatGrid()
    grid.name = "density"
    
    # Copy data from array
    grid.copyFromArray(data)
    
    # Set transform
    if transform:
        # Custom transform from dict
        # This is a placeholder - actual implementation depends on transform format
        pass
    else:
        # Simple linear transform with voxel size
        grid.transform = vdb.createLinearTransform(voxel_size)
    
    # Write to file
    vdb.write(filepath, grids=[grid])
    
    return True


def _save_vdb_docker(
    data: 'np.ndarray',
    filepath: str,
    voxel_size: float = 1.0,
    transform: Optional[dict] = None
) -> bool:
    """
    Save VDB file using Docker container with aswf/ci-vfxall image.
    
    Args:
        data: 3D numpy array
        filepath: Output VDB file path
        voxel_size: Size of each voxel
        transform: Optional transform parameters
        
    Returns:
        bool: True if successful
        
    Raises:
        ImportError: If docker-py is not available
        Exception: If Docker operations fail
    """
    try:
        import docker
    except ImportError:
        raise ImportError(
            "docker-py is required for Docker fallback. Install with: pip install docker"
        )
    
    # Create Docker client
    try:
        client = docker.from_env()
    except Exception as e:
        raise RuntimeError(f"Cannot connect to Docker: {str(e)}")
    
    # Create temporary directory for data exchange
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Save numpy array to temporary file
        data_file = tmpdir_path / "data.npy"
        np.save(str(data_file), data)
        
        # Save parameters
        params_file = tmpdir_path / "params.npy"
        np.save(str(params_file), np.array([voxel_size]))
        
        # Output file path in container
        output_file = tmpdir_path / "output.vdb"
        
        # Create Python script to run in container
        script = f"""
import numpy as np
import pyopenvdb as vdb

# Load data
data = np.load('/data/data.npy')
params = np.load('/data/params.npy')
voxel_size = float(params[0])

# Create VDB grid
grid = vdb.FloatGrid()
grid.name = "density"
grid.copyFromArray(data)

# Set transform
grid.transform = vdb.createLinearTransform(voxel_size)

# Write file
vdb.write('/data/output.vdb', grids=[grid])
print("VDB file written successfully")
"""
        
        script_file = tmpdir_path / "write_vdb.py"
        script_file.write_text(script)
        
        # Pull image if not available
        image_name = "aswf/ci-vfxall:latest"
        try:
            client.images.get(image_name)
        except docker.errors.ImageNotFound:
            print(f"Pulling Docker image {image_name}... This may take a while.")
            client.images.pull(image_name)
        
        # Run container
        try:
            container = client.containers.run(
                image_name,
                command=f"python3 /data/write_vdb.py",
                volumes={str(tmpdir_path): {'bind': '/data', 'mode': 'rw'}},
                remove=True,
                detach=False,
                stdout=True,
                stderr=True
            )
            
            print(f"Docker output: {container.decode('utf-8')}")
            
        except Exception as e:
            raise RuntimeError(f"Docker container execution failed: {str(e)}")
        
        # Check if output file was created
        if not output_file.exists():
            raise RuntimeError("Docker container did not create output VDB file")
        
        # Copy output file to target location
        shutil.copy(str(output_file), filepath)
    
    return True


def save_vdb(
    data: Union[List, 'np.ndarray', 'torch.Tensor'],
    filepath: str,
    voxel_size: float = 1.0,
    transform: Optional[dict] = None,
    force_docker: bool = False
) -> bool:
    """
    Save 3D array data to OpenVDB file format.
    
    This function accepts 3D data in various formats (Python lists, numpy arrays,
    or torch tensors) and saves it as a VDB file. It automatically detects if
    pyopenvdb is available and falls back to using Docker if needed.
    
    Args:
        data: 3D data as:
            - Python list of lists of lists
            - numpy.ndarray (3D)
            - torch.Tensor (3D)
        filepath: Output VDB file path
        voxel_size: Size of each voxel (default: 1.0)
        transform: Optional transform parameters (dict)
        force_docker: Force use of Docker even if pyopenvdb is available
        
    Returns:
        bool: True if successful
        
    Raises:
        ValueError: If data is invalid
        ImportError: If required dependencies are missing
        RuntimeError: If both native and Docker methods fail
        
    Examples:
        >>> import numpy as np
        >>> data = np.random.rand(100, 100, 100)
        >>> save_vdb(data, "output.vdb", voxel_size=0.1)
        True
        
        >>> # Works with lists
        >>> data_list = [[[1.0]*10 for _ in range(10)] for _ in range(10)]
        >>> save_vdb(data_list, "output2.vdb")
        True
        
        >>> # Works with torch tensors
        >>> import torch
        >>> data_torch = torch.rand(50, 50, 50)
        >>> save_vdb(data_torch, "output3.vdb")
        True
    """
    # Normalize input to numpy array
    try:
        data_np = _normalize_to_numpy(data)
    except Exception as e:
        raise ValueError(f"Failed to normalize input data: {str(e)}")
    
    print(f"Saving VDB file with shape {data_np.shape} to {filepath}")
    
    # Try native pyopenvdb first (unless forced to use Docker)
    if not force_docker:
        openvdb_available, openvdb_msg = check_openvdb_available()
        
        if openvdb_available:
            print("Using native pyopenvdb...")
            try:
                _save_vdb_native(data_np, filepath, voxel_size, transform)
                print(f"Successfully saved VDB file: {filepath}")
                return True
            except Exception as e:
                print(f"Native pyopenvdb failed: {str(e)}")
                print("Falling back to Docker...")
        else:
            print(f"pyopenvdb not available: {openvdb_msg}")
            print("Attempting Docker fallback...")
    else:
        print("Forcing Docker method...")
    
    # Fall back to Docker
    docker_available, docker_msg = check_docker_available()
    
    if not docker_available:
        raise RuntimeError(
            f"Cannot save VDB file: pyopenvdb is not available and Docker is not available.\n"
            f"pyopenvdb: {openvdb_msg}\n"
            f"Docker: {docker_msg}\n"
            f"Please install pyopenvdb (pip install pyopenvdb) or Docker."
        )
    
    print(f"Docker is available: {docker_msg}")
    
    try:
        _save_vdb_docker(data_np, filepath, voxel_size, transform)
        print(f"Successfully saved VDB file using Docker: {filepath}")
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to save VDB file using Docker: {str(e)}")


# Convenience function for loading VDB files (if pyopenvdb is available)
def load_vdb(filepath: str) -> Optional['np.ndarray']:
    """
    Load VDB file to numpy array (requires pyopenvdb).
    
    Args:
        filepath: Path to VDB file
        
    Returns:
        numpy.ndarray: 3D array of data, or None if loading fails
        
    Note:
        This function requires pyopenvdb to be installed.
        Docker fallback is not supported for loading.
    """
    try:
        import pyopenvdb as vdb
    except ImportError:
        print("Warning: pyopenvdb is not installed. Cannot load VDB files.")
        return None
    
    if not HAS_NUMPY:
        print("Warning: numpy is not installed. Cannot load VDB files.")
        return None
    
    try:
        grids = vdb.readAllGridMetadata(filepath)
        if not grids:
            print(f"No grids found in {filepath}")
            return None
        
        # Read the first grid
        grid = vdb.read(filepath, grids[0].name)
        
        # Convert to numpy array
        data = grid.copyToArray()
        
        return data
    except Exception as e:
        print(f"Error loading VDB file: {str(e)}")
        return None
