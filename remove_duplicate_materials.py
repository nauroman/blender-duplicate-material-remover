bl_info = {
    "name": "Remove Duplicate Materials",
    "author": "Roman Naumov",
    "version": (1, 0, 0),
    "blender": (4, 4, 0),
    "location": "3D Viewport > Object Mode > Object Menu",
    "description": "Remove duplicate materials from selected meshes",
    "category": "Material",
}

import bpy
import bmesh
from mathutils import Vector, Color


def compare_material_properties(mat1, mat2):
    """
    Compare two materials to check if they are identical in all properties except name.
    Returns True if materials are identical (duplicates).
    """
    print(f"DEBUG: Comparing materials '{mat1.name if mat1 else 'None'}' and '{mat2.name if mat2 else 'None'}'")
    
    if mat1 is None or mat2 is None:
        print("DEBUG: One or both materials are None")
        return False
    
    if mat1 == mat2:  # Same material object
        print("DEBUG: Same material object - not duplicates")
        return False
    
    # Compare basic material properties that exist in Blender 4.4
    try:
        if mat1.use_nodes != mat2.use_nodes:
            print(f"DEBUG: use_nodes differ: {mat1.use_nodes} vs {mat2.use_nodes}")
            return False
        if mat1.blend_method != mat2.blend_method:
            print(f"DEBUG: blend_method differ: {mat1.blend_method} vs {mat2.blend_method}")
            return False
        if abs(mat1.alpha_threshold - mat2.alpha_threshold) > 0.001:
            print(f"DEBUG: alpha_threshold differ: {mat1.alpha_threshold} vs {mat2.alpha_threshold}")
            return False
        if mat1.show_transparent_back != mat2.show_transparent_back:
            print(f"DEBUG: show_transparent_back differ: {mat1.show_transparent_back} vs {mat2.show_transparent_back}")
            return False
        if mat1.use_backface_culling != mat2.use_backface_culling:
            print(f"DEBUG: use_backface_culling differ: {mat1.use_backface_culling} vs {mat2.use_backface_culling}")
            return False
    except AttributeError as e:
        print(f"DEBUG: AttributeError in basic properties: {e}")
        # Some properties might not exist in all Blender versions
        pass
    
    # Compare surface properties
    try:
        # Compare diffuse_color by converting to lists for proper comparison
        diffuse1 = list(mat1.diffuse_color) if hasattr(mat1.diffuse_color, '__iter__') else [mat1.diffuse_color]
        diffuse2 = list(mat2.diffuse_color) if hasattr(mat2.diffuse_color, '__iter__') else [mat2.diffuse_color]
        
        # Compare with small tolerance for floating point differences
        if len(diffuse1) != len(diffuse2):
            print(f"DEBUG: diffuse_color length differ: {len(diffuse1)} vs {len(diffuse2)}")
            return False
        
        for i, (d1, d2) in enumerate(zip(diffuse1, diffuse2)):
            if abs(d1 - d2) > 0.001:
                print(f"DEBUG: diffuse_color[{i}] differ: {d1} vs {d2}")
                return False
        
        # Handle metallic property safely
        if hasattr(mat1, 'metallic') and hasattr(mat2, 'metallic'):
            if abs(mat1.metallic - mat2.metallic) > 0.001:
                print(f"DEBUG: metallic differ: {mat1.metallic} vs {mat2.metallic}")
                return False
        
        # Handle specular property safely (may not exist in newer Blender versions)
        if hasattr(mat1, 'specular') and hasattr(mat2, 'specular'):
            if abs(mat1.specular - mat2.specular) > 0.001:
                print(f"DEBUG: specular differ: {mat1.specular} vs {mat2.specular}")
                return False
        elif hasattr(mat1, 'specular') != hasattr(mat2, 'specular'):
            print(f"DEBUG: Only one material has specular property")
            return False
        
        # Handle roughness property safely
        if hasattr(mat1, 'roughness') and hasattr(mat2, 'roughness'):
            if abs(mat1.roughness - mat2.roughness) > 0.001:
                print(f"DEBUG: roughness differ: {mat1.roughness} vs {mat2.roughness}")
                return False
        
    except AttributeError as e:
        print(f"DEBUG: AttributeError in surface properties: {e}")
        # Continue with comparison even if some properties are missing
        pass
    
    # If materials use nodes, compare node trees with a more lenient approach
    if mat1.use_nodes and mat2.use_nodes:
        if mat1.node_tree is None or mat2.node_tree is None:
            print("DEBUG: One material has use_nodes=True but no node_tree")
            return mat1.node_tree == mat2.node_tree
        
        # Use a simpler node tree comparison for now
        nodes_match = len(mat1.node_tree.nodes) == len(mat2.node_tree.nodes)
        links_match = len(mat1.node_tree.links) == len(mat2.node_tree.links)
        
        print(f"DEBUG: Node count match: {nodes_match} ({len(mat1.node_tree.nodes)} vs {len(mat2.node_tree.nodes)})")
        print(f"DEBUG: Link count match: {links_match} ({len(mat1.node_tree.links)} vs {len(mat2.node_tree.links)})")
        
        if not (nodes_match and links_match):
            return False
        
        # For now, if they have the same number of nodes and links, consider them similar
        # This is a simplified comparison - we could enhance this later
        print("DEBUG: Node trees considered similar (simplified comparison)")
    elif mat1.use_nodes != mat2.use_nodes:
        print("DEBUG: One material uses nodes, the other doesn't")
        return False
    
    print(f"DEBUG: Materials '{mat1.name}' and '{mat2.name}' are considered DUPLICATES!")
    return True


def compare_node_trees(tree1, tree2):
    """
    Compare two node trees to check if they are identical.
    Returns True if node trees are identical.
    """
    if tree1 is None or tree2 is None:
        return tree1 == tree2
    
    # Compare number of nodes
    if len(tree1.nodes) != len(tree2.nodes):
        return False
    
    # Compare number of links
    if len(tree1.links) != len(tree2.links):
        return False
    
    # Create mappings of nodes by type and location for comparison
    nodes1 = {}
    nodes2 = {}
    
    for node in tree1.nodes:
        key = (node.type, tuple(node.location), node.name if hasattr(node, 'name') else '')
        if key in nodes1:
            return False  # Duplicate nodes at same location
        nodes1[key] = node
    
    for node in tree2.nodes:
        key = (node.type, tuple(node.location), node.name if hasattr(node, 'name') else '')
        if key in nodes2:
            return False  # Duplicate nodes at same location
        nodes2[key] = node
    
    # Check if all nodes from tree1 exist in tree2
    for key, node1 in nodes1.items():
        if key not in nodes2:
            return False
        
        node2 = nodes2[key]
        
        # Compare node-specific properties
        if not compare_node_properties(node1, node2):
            return False
    
    # Compare links (connections between nodes)
    links1 = set()
    links2 = set()
    
    for link in tree1.links:
        link_key = (
            (link.from_node.type, tuple(link.from_node.location), link.from_socket.name),
            (link.to_node.type, tuple(link.to_node.location), link.to_socket.name)
        )
        links1.add(link_key)
    
    for link in tree2.links:
        link_key = (
            (link.from_node.type, tuple(link.from_node.location), link.from_socket.name),
            (link.to_node.type, tuple(link.to_node.location), link.to_socket.name)
        )
        links2.add(link_key)
    
    return links1 == links2


def compare_node_properties(node1, node2):
    """
    Compare properties of two nodes to check if they are identical.
    Returns True if nodes are identical.
    """
    if node1.type != node2.type:
        return False
    
    # Compare common properties based on node type
    if hasattr(node1, 'color') and hasattr(node2, 'color'):
        if node1.color != node2.color:
            return False
    
    if hasattr(node1, 'hide') and hasattr(node2, 'hide'):
        if node1.hide != node2.hide:
            return False
    
    # Compare specific properties for different node types
    if node1.type == 'BSDF_PRINCIPLED':
        # Compare input default values
        for input1, input2 in zip(node1.inputs, node2.inputs):
            if hasattr(input1, 'default_value') and hasattr(input2, 'default_value'):
                if input1.default_value != input2.default_value:
                    return False
    
    elif node1.type == 'TEX_IMAGE':
        if hasattr(node1, 'image') and hasattr(node2, 'image'):
            if node1.image != node2.image:
                return False
        if hasattr(node1, 'interpolation') and hasattr(node2, 'interpolation'):
            if node1.interpolation != node2.interpolation:
                return False
    
    # Add more node type comparisons as needed
    
    return True


def find_duplicate_materials(materials):
    """
    Find groups of duplicate materials.
    Returns a dictionary where keys are original materials and values are lists of duplicates.
    """
    print(f"DEBUG: find_duplicate_materials called with {len(materials)} materials:")
    for i, mat in enumerate(materials):
        print(f"DEBUG:   [{i}] {mat.name if mat else 'None'}")
    
    duplicates = {}
    processed = set()
    
    for i, mat1 in enumerate(materials):
        if mat1 in processed:
            print(f"DEBUG: Material '{mat1.name}' already processed, skipping")
            continue
        
        mat_duplicates = []
        
        for j, mat2 in enumerate(materials[i+1:], i+1):
            if mat2 in processed:
                print(f"DEBUG: Material '{mat2.name}' already processed, skipping")
                continue
            
            print(f"DEBUG: Comparing materials {i} and {j}")
            if compare_material_properties(mat1, mat2):
                print(f"DEBUG: Found duplicate! '{mat2.name}' is duplicate of '{mat1.name}'")
                mat_duplicates.append(mat2)
                processed.add(mat2)
        
        if mat_duplicates:
            print(f"DEBUG: Adding '{mat1.name}' to duplicates with {len(mat_duplicates)} duplicates")
            duplicates[mat1] = mat_duplicates
            processed.add(mat1)
    
    print(f"DEBUG: Found {len(duplicates)} groups of duplicates")
    return duplicates


class OBJECT_OT_test_simple(bpy.types.Operator):
    """Simple test operator"""
    bl_idname = "object.test_simple"
    bl_label = "Test Simple"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        print("TEST: Simple operator executed successfully!")
        self.report({'INFO'}, "Test operator worked!")
        return {'FINISHED'}


class OBJECT_OT_remove_duplicate_materials(bpy.types.Operator):
    """Remove duplicate materials from selected meshes"""
    bl_idname = "object.remove_duplicate_materials"
    bl_label = "Remove Duplicate Materials"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        print(f"POLL DEBUG: Selected objects: {len(context.selected_objects)}")
        print(f"POLL DEBUG: Selected object names: {[obj.name for obj in context.selected_objects]}")
        result = len(context.selected_objects) > 0
        print(f"POLL DEBUG: Returning {result}")
        return result
    
    def execute(self, context):
        print("=" * 50)
        print("DEBUG: SCRIPT EXECUTION STARTED")
        print("=" * 50)
        
        removed_count = 0
        processed_objects = 0
        
        print(f"DEBUG: Selected objects count: {len(context.selected_objects)}")
        
        # Check basic conditions first
        if not context.selected_objects:
            print("DEBUG: No objects selected!")
            self.report({'ERROR'}, "No objects selected!")
            return {'CANCELLED'}
        
        # Check if any selected objects are mesh objects
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not mesh_objects:
            print("DEBUG: No mesh objects selected!")
            return {'CANCELLED'}
        
        print(f"DEBUG: Found {len(mesh_objects)} mesh objects to process")
        
        # Process all selected mesh objects
        for obj in context.selected_objects:
            print(f"DEBUG: Processing object '{obj.name}' of type '{obj.type}'")
            if obj.type != 'MESH':
                print(f"DEBUG: Skipping non-mesh object '{obj.name}'")
                continue
            
            processed_objects += 1
            mesh = obj.data
            print(f"DEBUG: Processing mesh '{mesh.name}'")
            
            if not mesh.materials:
                print(f"DEBUG: Mesh '{mesh.name}' has no materials")
                continue
            
            # Get all materials from the mesh
            materials = [mat for mat in mesh.materials if mat is not None]
            print(f"DEBUG: Found {len(materials)} non-None materials in mesh '{mesh.name}'")
            print(f"DEBUG: Total material slots: {len(mesh.materials)}")
            
            # List all materials for debugging
            for i, mat in enumerate(mesh.materials):
                if mat:
                    print(f"DEBUG: Material slot {i}: '{mat.name}'")
                else:
                    print(f"DEBUG: Material slot {i}: None")
            
            if len(materials) < 2:
                print(f"DEBUG: Mesh '{mesh.name}' has less than 2 materials, skipping")
                continue
            
            # Find duplicate materials
            print(f"DEBUG: Calling find_duplicate_materials for mesh '{mesh.name}'")
            duplicates = find_duplicate_materials(materials)
            
            if not duplicates:
                print(f"DEBUG: No duplicates found for mesh '{mesh.name}'")
                continue
            
            print(f"DEBUG: Found duplicates for mesh '{mesh.name}': {len(duplicates)} groups")
            
            # Create material index mapping (duplicate -> original)
            material_mapping = {}
            materials_to_remove = set()
            
            for original, dupe_list in duplicates.items():
                original_idx = None
                for i, mat in enumerate(mesh.materials):
                    if mat == original:
                        original_idx = i
                        break
                
                if original_idx is None:
                    print(f"DEBUG: Could not find original material '{original.name}' in mesh material slots")
                    continue
                
                for duplicate in dupe_list:
                    duplicate_idx = None
                    for i, mat in enumerate(mesh.materials):
                        if mat == duplicate:
                            duplicate_idx = i
                            break
                    
                    if duplicate_idx is not None:
                        material_mapping[duplicate_idx] = original_idx
                        materials_to_remove.add(duplicate_idx)
            
            if not material_mapping:
                print("DEBUG: No material mapping created, continuing to next object")
                continue
            
            # Enter edit mode to access polygon data
            context.view_layer.objects.active = obj
            bpy.context.view_layer.update()
            
            # Switch to edit mode
            bpy.ops.object.mode_set(mode='EDIT')
            
            # Get bmesh representation
            bm = bmesh.from_edit_mesh(mesh)
            
            # Reassign materials for faces
            for face in bm.faces:
                if face.material_index in material_mapping:
                    face.material_index = material_mapping[face.material_index]
            
            # Update mesh
            bmesh.update_edit_mesh(mesh)
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # Remove duplicate material slots (from highest index to lowest)
            material_indices_to_remove = sorted(materials_to_remove, reverse=True)
            for idx in material_indices_to_remove:
                if idx < len(mesh.materials):
                    mesh.materials.pop(index=idx)
                    removed_count += 1
        
        if removed_count > 0:
            print(f"Removed {removed_count} duplicate materials from {processed_objects} objects")
        else:
            print("No duplicate materials found")
        
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(OBJECT_OT_remove_duplicate_materials.bl_idname)
    self.layout.operator(OBJECT_OT_test_simple.bl_idname)


def register():
    bpy.utils.register_class(OBJECT_OT_remove_duplicate_materials)
    bpy.utils.register_class(OBJECT_OT_test_simple)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_remove_duplicate_materials)
    bpy.utils.unregister_class(OBJECT_OT_test_simple)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == "__main__":
    register()
