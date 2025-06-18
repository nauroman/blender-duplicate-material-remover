# Blender 4.4 Add-on: Remove Duplicate Materials

This add-on removes duplicate materials from selected mesh objects in Blender 4.4. It identifies materials that are identical in all properties except their names, removes the duplicates, and reassigns polygons to use the original materials.

## Features

- **Smart Material Comparison**: Compares all material properties including:
  - Basic properties (blend method, alpha threshold, etc.)
  - Surface properties (diffuse color, metallic, specular, roughness)
  - Node trees (if using shader nodes)
  - Node properties and connections

- **Polygon Reassignment**: Automatically reassigns faces from duplicate materials to the original materials

- **Batch Processing**: Works on all selected mesh objects at once

- **Safe Operation**: Uses bmesh for reliable mesh editing and includes undo support

## Installation

1. Copy the `remove_duplicate_materials.py` file to your Blender add-ons directory:
   - **Windows**: `C:\Users\[username]\AppData\Roaming\Blender Foundation\Blender\4.4\scripts\addons\`
   - **macOS**: `/Users/[username]/Library/Application Support/Blender/4.4/scripts/addons/`
   - **Linux**: `~/.config/blender/4.4/scripts/addons/`

2. Open Blender 4.4

3. Go to **Edit** > **Preferences** > **Add-ons**

4. Search for "Remove Duplicate Materials"

5. Enable the add-on by checking the checkbox

## Usage

1. **Select mesh objects** in the 3D viewport that contain duplicate materials

2. **Access the tool** via:
   - **Object Menu**: Object > Remove Duplicate Materials
   - Or use the search function (F3) and type "Remove Duplicate Materials"

3. The add-on will:
   - Analyze all materials on selected meshes
   - Identify duplicates based on property comparison
   - Reassign polygons from duplicate materials to originals
   - Remove duplicate material slots
   - Display a report with the number of materials removed

## How It Works

### Material Comparison Process

The add-on compares materials using a comprehensive approach:

1. **Basic Properties**: Blend method, shadow method, alpha threshold, backface culling, etc.
2. **Surface Properties**: Diffuse color, metallic, specular, roughness values
3. **Node Trees**: If materials use nodes, it compares:
   - Node types and positions
   - Node properties and default values
   - Node connections (links)
   - Image textures and settings

### Polygon Reassignment

- Uses bmesh for safe mesh editing
- Switches to edit mode temporarily to access face data
- Updates material indices for affected faces
- Removes duplicate material slots after reassignment

## Example Scenario

Imagine you have a mesh with these materials:
- "Metal_001" (original)
- "Metal_002" (duplicate of Metal_001)
- "Glass_001" (original)
- "Metal_003" (duplicate of Metal_001)

After running the add-on:
- All polygons using "Metal_002" and "Metal_003" will be reassigned to "Metal_001"
- "Metal_002" and "Metal_003" material slots will be removed
- "Glass_001" remains unchanged (no duplicates found)

## Compatibility

- **Blender Version**: 4.4+
- **Object Types**: Mesh objects only
- **Material Types**: Works with both basic materials and shader node materials

## Troubleshooting

- **No duplicates found**: Materials may have subtle differences in properties or node setups
- **Operator not available**: Ensure you have mesh objects selected in Object mode
- **Unexpected results**: The add-on uses precise property comparison; materials that appear similar may have small differences

## Technical Details

The add-on uses several key functions:
- `compare_material_properties()`: Main material comparison logic
- `compare_node_trees()`: Compares shader node setups
- `find_duplicate_materials()`: Groups materials by similarity
- `OBJECT_OT_remove_duplicate_materials`: Main operator class

## License

This add-on is provided as-is for educational and practical use in Blender projects.
