# Doric Column Visualization Task

Create a 3D visualization of a classical Doric column using the bpwf MCP server tools.

## Architectural Requirements

Create a historically accurate Doric column with the following components:

### 1. Column Shaft
- **Height**: 6.0 units
- **Base diameter**: 1.0 unit
- **Top diameter**: 0.85 units (tapered)
- **Position**: Centered at origin (0, 0, 0) with base at z=0
- **Color**: Marble white (#F5F5DC)
- **Fluting**: 20 vertical grooves around the circumference
  - Each flute should be a semi-circular groove
  - Depth: 0.05 units
  - Use boolean subtraction to create the grooves

### 2. Capital (Top Section)

#### Echinus (Curved Section)
- **Shape**: Truncated cone
- **Base diameter**: 0.85 units (matches shaft top)
- **Top diameter**: 1.1 units
- **Height**: 0.3 units
- **Position**: Directly on top of shaft (z=6.0)
- **Color**: Same marble white (#F5F5DC)

#### Abacus (Square Top)
- **Shape**: Rectangular box (slightly rounded if possible)
- **Dimensions**: 1.2 x 1.2 x 0.15 units
- **Position**: On top of echinus (z=6.3)
- **Color**: Same marble white (#F5F5DC)

### 3. Base Platform (Stylobate)
- **Shape**: Cylinder
- **Diameter**: 1.3 units
- **Height**: 0.2 units
- **Position**: z=-0.2 to z=0
- **Color**: Slightly darker stone (#E8E8D0)

## Lighting Setup

Use a three-point lighting setup to highlight the architectural details:

1. **Key Light**: Sun light with strength 2.0
2. **Fill Light**: Point light at position (3, -3, 4) with strength 500
3. **Rim Light**: Point light at position (-3, 3, 5) with strength 300

## Camera and Rendering

- **Camera Position**: (5, -5, 4)
- **Look At**: (0, 0, 3) - middle of the column
- **Samples**: 256 for high quality
- **Resolution**: 1920x1080
- **Output**: Save to `assets/08_doric_column.png`
- **Background**: Transparent or light gradient

## Implementation Steps

1. Create a new scene with ID "doric_column"
2. Create the base platform cylinder
3. Create the main shaft as a tapered cylinder
4. Create 20 small cylinders positioned radially around the shaft for fluting grooves
5. Use boolean subtraction to subtract each flute from the shaft
6. Create the echinus (capital curved section) as a cone
7. Create the abacus (square top) as a cube
8. Add the three-point lighting setup
9. Position the camera for an attractive 3/4 view
10. Render the scene with high quality settings

## Expected Output

A photorealistic rendering of a classical Doric column showing:
- Clear fluting detail on the shaft
- Proper proportions and taper
- Well-defined capital with echinus and abacus
- Professional lighting that emphasizes the 3D form
- Clean, publication-quality image suitable for architectural documentation

## Notes

- Use the bpwf MCP server tools (create_scene, add_cylinder, add_cone, add_cube, boolean_operation, add_sun_light, add_point_light, render_scene)
- Ensure all boolean operations complete before rendering
- The column should follow classical Doric proportions (height ≈ 6-7 times the base diameter)
- Pay attention to the taper - Doric columns are wider at the base for visual stability
