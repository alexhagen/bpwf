# bpwf - Blender for Publication-Worthy Figures

[![PyPI version](https://badge.fury.io/py/bpwf.svg)](https://badge.fury.io/py/bpwf)
[![Python Versions](https://img.shields.io/pypi/pyversions/bpwf.svg)](https://pypi.org/project/bpwf/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/alexhagen/pyb/actions/workflows/test.yml/badge.svg)](https://github.com/alexhagen/pyb/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/coverage-11%25-red.svg)](htmlcov/index.html)
[![Downloads](https://pepy.tech/badge/bpwf/month)](https://pepy.tech/project/bpwf)

A Python package for programmatic 3D scene creation and rendering using Blender's `bpy` module. Write Python code to generate complex 3D visualizations without manually operating Blender's GUI.

## Overview

bpwf (Blender for Publication-Worthy Figures) provides a high-level Python interface to Blender's `bpy` module, allowing you to create 3D scenes, apply materials, set up lighting, and render images entirely through Python code. This is particularly useful for:

- Automated visualization pipelines in CI/CD environments
- Batch rendering of procedurally generated scenes
- Scientific visualization and data representation
- Reproducible 3D graphics generation for publications

Unlike the old approach of generating scripts and executing Blender externally, bpwf uses the official `bpy` package from PyPI to interact with Blender directly within your Python environment.

## Features

- **Primitive Geometry**: Create cubes, spheres, cylinders, cones, and planes
- **Boolean Operations**: Union, intersection, and difference operations on meshes
- **Materials**: Flat colors, emissive materials, transparent surfaces, PBR shaders, and SEM-style materials
- **Lighting**: Point lights and sun lamps with customizable intensity
- **Camera Control**: Flexible camera positioning and targeting
- **Volume Rendering**: Save 3D arrays to OpenVDB format for volume rendering
- **Direct bpy Integration**: Uses official Blender Python module for seamless integration
- **Multi-Scene Support**: Create and manage multiple independent scenes
- **MCP Server**: Model Context Protocol server for AI-assisted scene creation

## Installation

### Install bpwf

```bash
pip install bpwf
```

### Install bpy (Required Dependency)

The official Blender Python module is required:

```bash
pip install bpy
```

**Note**: `bpy` is a large package (~200MB) as it includes the full Blender application. Installation may take a few minutes.

### Optional Dependencies

```bash
# For volume rendering support
pip install bpwf[volume]

# For development
pip install bpwf[dev]
```

## Quick Start

```python
from bpwf import bpwf

# Create a new scene
scene = bpwf()

# Add a sphere
scene.sph(c=[0, 0, 0], r=1.0, name="sphere", color="#FF5733")

# Add a light source
scene.point(location=[5, 5, 5], strength=1000.0)

# Render the scene
scene.render(
    camera_location=[4, -4, 3],
    c=[0, 0, 0],
    l=[2, 2, 2],
    samples=128,
    res=[1920, 1080]
)

# Display the result (in Jupyter) or save
scene.show()
```

![Quick Start Example](assets/01_quick_start.png)

## Basic Examples

### Creating Primitives

```python
scene = bpwf()

# Rectangular parallelepiped (box)
scene.rpp(x1=-1, x2=1, y1=-1, y2=1, z1=0, z2=2, 
          name="box", color="#3498DB")

# Cylinder
scene.rcc(c=[0, 0, 0], r=0.5, h=2.0, 
          direction='z', name="cylinder", color="#E74C3C")

# Cone
scene.cone(c=[0, 0, 0], r1=1.0, r2=0.0, h=2.0,
           name="cone", color="#2ECC71")
```

![Creating Primitives Example](assets/02_creating_primitives.png)

### Boolean Operations

```python
scene = bpwf()

# Create two overlapping spheres
scene.sph(c=[0, 0, 0], r=1.0, name="sphere1", color="#3498DB")
scene.sph(c=[0.5, 0, 0], r=1.0, name="sphere2", color="#E74C3C")

# Subtract sphere2 from sphere1
scene.subtract("sphere1", "sphere2")
```

![Boolean Operations Example](assets/03_boolean_operations.png)

### Materials and Lighting

```python
scene = bpwf()

# Emissive material (glowing)
scene.sph(c=[0, 0, 0], r=1.0, name="light_sphere", 
          color="#FFFF00", emis=True, emittance=5.0)

# Transparent material
scene.sph(c=[2, 0, 0], r=1.0, name="glass_sphere",
          color="#FFFFFF", alpha=0.3)

# Add sun lamp
scene.sun(strength=1.0)
```

![Materials and Lighting Example](assets/04_materials_lighting.png)

### Using Principled BSDF Materials

```python
from bpwf import bpwf, PrincipledBSDF

scene = bpwf()

# Create a custom material
metal = PrincipledBSDF(
    name="metal",
    color="#C0C0C0",
    specular=1.0,
    roughness=0.2
)

# Create object with custom material
scene.sph(c=[0, 0, 0], r=1.0, name="metal_sphere")
scene.set_matl(obj="metal_sphere", matl="metal")
```

![Principled BSDF Materials Example](assets/05_principled_bsdf.png)

## Multi-Scene Support

Create and manage multiple independent scenes:

```python
from bpwf import bpwf

# Create first scene
scene1 = bpwf(scene_name="Scene1")
scene1.sph(c=[0, 0, 0], r=1.0, name="sphere1", color="#FF0000")

# Create second scene
scene2 = bpwf(scene_name="Scene2")
scene2.rpp(c=[0, 0, 0], l=[2, 2, 2], name="box1", color="#0000FF")

# Render both scenes
scene1.render(camera_location=[4, -4, 3])
scene2.render(camera_location=[4, -4, 3])
```

**Scene 1 (Red Sphere):**

![Multi-Scene Example 1](assets/06_multi_scene_1.png)

**Scene 2 (Blue Box):**

![Multi-Scene Example 2](assets/06_multi_scene_2.png)

## Volume Rendering with VDB

bpwf includes utilities for saving 3D arrays to OpenVDB format for volume rendering in Blender:

```python
import numpy as np
from bpwf import save_vdb, load_vdb

# Create 3D data (e.g., a sphere)
size = 50
center = size // 2
radius = 15

x, y, z = np.ogrid[:size, :size, :size]
distance = np.sqrt((x - center)**2 + (y - center)**2 + (z - center)**2)
data = np.where(distance <= radius, 1.0, 0.0).astype(np.float32)

# Save to VDB format
save_vdb(data, "sphere.vdb", voxel_size=0.1)

# Load VDB file back to numpy array
loaded_data = load_vdb("sphere.vdb")
```

The VDB utilities support:
- **Multiple input formats**: Python lists, numpy arrays, or PyTorch tensors
- **Automatic fallback**: Uses pyopenvdb if available, falls back to Docker if not
- **Easy integration**: Generated VDB files can be loaded directly in Blender for volume rendering

See `examples/07_vdb_volume.py` for more examples.

## MCP Server

bpwf includes a Model Context Protocol server for AI-assisted 3D scene creation:

```bash
# Start the MCP server
bpwf-mcp
```

The server provides tools for:
- Creating and managing scenes
- Adding primitives and lights
- Applying materials
- Rendering with various parameters

## API Overview

### Primitives

- `sph(c, r, name, color, alpha, emis, layer, subd)` - Create a sphere
- `rpp(x1, x2, y1, y2, z1, z2, c, l, name, color, alpha)` - Create a box
- `rcc(c, r, h, name, color, direction, alpha, emis)` - Create a cylinder
- `cone(c, r1, r2, h, name, color, direction, alpha)` - Create a cone
- `plane(x1, x2, y1, y2, z1, z2, c, l, name, color)` - Create a plane

### Boolean Operations

- `subtract(left, right, unlink)` - Boolean subtraction
- `union(left, right, unlink)` - Boolean union
- `intersect(left, right, unlink)` - Boolean intersection

### Materials

- `flat(name, color, alpha)` - Flat diffuse material
- `emis(name, color, alpha, emittance)` - Emissive material
- `trans(name, color)` - Transparent material
- `sem(name, e_color, bsdf_color, lw_value)` - SEM-style material
- `image(name, fname, alpha)` - Image texture material
- `set_matl(obj, matl)` - Assign material to object

### Lighting

- `sun(strength)` - Create sun lamp
- `point(location, strength, name, color)` - Create point light

### Rendering

- `render(camera_location, c, l, samples, res, draft, freestyle, perspective, transparent)` - Set up and render scene
- `run(filename, block, **kwargs)` - Execute rendering (compatibility method)
- `show()` - Display rendered image

### Utilities

- `delete(name)` - Delete object
- `unlink(name)` - Unlink object from scene
- `draft(i)` - Enable draft mode
- `split_scene(filename)` - Create scene copy with new filename

## Differences from pyb

bpwf is a modernized version of pyb with several key improvements:

1. **Direct bpy Integration**: Uses the official `bpy` package instead of generating scripts
2. **No External Dependencies**: No need for Docker or local Blender installation
3. **Simpler Architecture**: Direct API calls instead of string generation
4. **Multi-Scene Support**: Create and manage multiple independent scenes
5. **Better Performance**: No subprocess overhead or file I/O for scripts

## Migration from pyb

If you're migrating from pyb, the API is largely compatible:

```python
# Old (pyb)
from pyb import pyb
scene = pyb()

# New (bpwf)
from bpwf import bpwf
scene = bpwf()
```

Most method calls remain the same. The main differences:
- No more Docker/Blender detection
- `bpy` must be installed as a dependency
- Rendering happens in-process instead of via subprocess

## System Requirements

- Python 3.10 or higher
- ~200MB disk space for `bpy` package
- Sufficient RAM for Blender operations (4GB+ recommended)

## Contributing

Contributions are welcome! Please see the [GitHub repository](https://github.com/alexhagen/pyb) for:
- Issue tracking
- Feature requests
- Pull request guidelines

## License

MIT License - see LICENSE file for details

## Citation

If you use bpwf in academic work, please cite:

```
Hagen, A. (2026). bpwf: Blender for Publication-Worthy Figures.
https://github.com/alexhagen/pyb
```

## Acknowledgments

Built on top of [Blender](https://www.blender.org/) and the official [bpy](https://pypi.org/project/bpy/) package.
