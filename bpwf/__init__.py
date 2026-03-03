"""
bpwf - Blender for Publication-Worthy Figures
Programmatic 3D scene creation and rendering using Blender's bpy module.
"""

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import main classes
from .bpwf import bpwf, FileStringStream, PrincipledBSDF

# Import VDB utilities (optional - only if needed)
try:
    from .vdb_utils import save_vdb, load_vdb, check_openvdb_available, check_docker_available
    __all__ = ["bpwf", "FileStringStream", "PrincipledBSDF", "save_vdb", "load_vdb", 
               "check_openvdb_available", "check_docker_available"]
except ImportError as e:
    logger.warning(f"VDB utilities not available: {e}")
    __all__ = ["bpwf", "FileStringStream", "PrincipledBSDF"]

__version__ = "3.0.0"

# Log initialization
logger.info("bpwf initialized with direct bpy integration")
