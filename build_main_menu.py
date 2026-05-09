import bpy
import math

def build_main_menu():
    # 1. CLEANUP
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 2. PRO RENDER SETTINGS
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 64
    bpy.context.scene.cycles.use_denoising = True
    
    # Enable AgX or Filmic
    bpy.context.scene.view_settings.view_transform = 'AgX'
    
    # 3. MATERIALS
    def create_emissive(name, color, strength=10.0):
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        ns = mat.node_tree.nodes
        ns.remove(ns.get('Principled BSDF'))
        emit = ns.new('ShaderNodeEmission')
        emit.inputs['Color'].default_value = color
        emit.inputs['Strength'].default_value = strength
        out = ns.new('ShaderNodeOutputMaterial')
        mat.node_tree.links.new(emit.outputs[0], out.inputs[0])
        return mat
        
    mat_cyan = create_emissive("UI_Cyan", (0.0, 1.0, 0.8, 1.0), 5.0)
    mat_magenta = create_emissive("UI_Magenta", (1.0, 0.0, 0.5, 1.0), 10.0)
    mat_white = create_emissive("UI_White", (1.0, 1.0, 1.0, 1.0), 3.0)
    
    mat_dark = bpy.data.materials.new(name="Dark_Metal")
    mat_dark.use_nodes = True
    mat_dark.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1)
    mat_dark.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0.8
    mat_dark.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.2

    mat_floor = bpy.data.materials.new(name="Reflective_Floor")
    mat_floor.use_nodes = True
    mat_floor.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1)
    mat_floor.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.05
    mat_floor.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = 0.5

    # 4. ENVIRONMENT & CAMERA
    # Floor
    bpy.ops.mesh.primitive_plane_add(size=20)
    bpy.context.active_object.data.materials.append(mat_floor)
    
    # Back wall
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 5, 0), rotation=(math.radians(90), 0, 0))
    bpy.context.active_object.data.materials.append(mat_dark)
    
    # Camera
    bpy.ops.object.camera_add(location=(0, -8, 1.5), rotation=(math.radians(90), 0, 0))
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam

    # 5. THE BOT (Right Side)
    # Torso
    bpy.ops.mesh.primitive_cube_add(size=2, location=(3, 0, 1.5))
    torso = bpy.context.active_object
    torso.scale = (0.4, 0.3, 0.4)
    torso.data.materials.append(mat_dark)
    
    # Eye
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.1, location=(3, -0.3, 1.5), rotation=(math.radians(90), 0, 0))
    eye = bpy.context.active_object
    eye.data.materials.append(mat_cyan)
    
    # Legs
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.5, location=(2.8, 0, 0.75))
    bpy.context.active_object.data.materials.append(mat_dark)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.5, location=(3.2, 0, 0.75))
    bpy.context.active_object.data.materials.append(mat_dark)
    
    # 6. UI TEXT (Left Side)
    def create_text(text_str, loc, size, mat):
        bpy.ops.object.text_add(location=loc, rotation=(math.radians(90), 0, 0))
        t = bpy.context.active_object
        t.data.body = text_str
        t.data.size = size
        t.data.align_x = 'LEFT'
        t.data.extrude = 0.02
        t.data.bevel_depth = 0.005
        t.data.materials.append(mat)
        return t

    create_text("CYBER CITY", (-4.5, 0, 3.0), 1.5, mat_magenta)
    create_text("> START GAME", (-4.5, 0, 1.5), 0.6, mat_cyan)
    create_text("  OPTIONS", (-4.5, 0, 0.8), 0.6, mat_white)
    create_text("  QUIT", (-4.5, 0, 0.1), 0.6, mat_white)

    # 7. LIGHTING & VOLUMETRICS
    # Rim Light for Bot
    bpy.ops.object.light_add(type='AREA', location=(5, 1, 2), rotation=(math.radians(90), math.radians(45), math.radians(135)))
    rim = bpy.context.active_object
    rim.data.energy = 1000
    rim.data.color = (0.0, 1.0, 0.8) # Cyan rim
    rim.data.shape = 'RECTANGLE'
    rim.data.size = 2
    rim.data.size_y = 4
    
    # General ambient light
    bpy.ops.object.light_add(type='AREA', location=(0, 0, 5), rotation=(0, 0, 0))
    amb = bpy.context.active_object
    amb.data.energy = 100
    amb.data.size = 10
    
    # Volumetric Cube
    bpy.ops.mesh.primitive_cube_add(size=20, location=(0, 0, 5))
    vol = bpy.context.active_object
    mat_vol = bpy.data.materials.new(name="Volumetric_Fog")
    mat_vol.use_nodes = True
    ns = mat_vol.node_tree.nodes
    ns.remove(ns.get('Principled BSDF'))
    v = ns.new('ShaderNodeVolumePrincipled')
    v.inputs['Density'].default_value = 0.01
    v.inputs['Emission Strength'].default_value = 0.001
    v.inputs['Emission Color'].default_value = (0.1, 0.0, 0.1, 1) # Purple ambient
    out = ns.new('ShaderNodeOutputMaterial')
    mat_vol.node_tree.links.new(v.outputs[0], out.inputs[1])
    vol.data.materials.append(mat_vol)
    vol.display_type = 'WIRE' # Don't block viewport view

build_main_menu()
print("Main Menu Built Successfully!")
