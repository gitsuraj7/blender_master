import bpy
import math
import os

def build_neon_maze_p1():
    # 1. CLEANUP
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 2. RENDER SETTINGS (CYCLES, AGX, PITCH BLACK WORLD)
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 32
    scn.cycles.use_denoising = True
    scn.view_settings.view_transform = 'AgX'
    scn.view_settings.look = 'AgX - High Contrast'
    
    # Pitch Black World
    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0, 0, 0, 1)
    bg.inputs['Strength'].default_value = 0.0
    
    # 3. MATERIALS
    # Wet Floor
    mat_floor = bpy.data.materials.new(name="Wet_Floor")
    mat_floor.use_nodes = True
    ns = mat_floor.node_tree.nodes
    bsdf = ns['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.08
    
    # Bump Noise for Floor
    n_noise = ns.new('ShaderNodeTexNoise')
    n_noise.inputs['Scale'].default_value = 50.0
    n_noise.inputs['Detail'].default_value = 15.0
    n_bump = ns.new('ShaderNodeBump')
    n_bump.inputs['Strength'].default_value = 0.05
    n_bump.inputs['Distance'].default_value = 0.1
    mat_floor.node_tree.links.new(n_noise.outputs['Color'], n_bump.inputs['Height'])
    mat_floor.node_tree.links.new(n_bump.outputs['Normal'], bsdf.inputs['Normal'])
    
    # Dark Wall
    mat_wall = bpy.data.materials.new(name="Dark_Wall")
    mat_wall.use_nodes = True
    w_bsdf = mat_wall.node_tree.nodes['Principled BSDF']
    w_bsdf.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1)
    w_bsdf.inputs['Roughness'].default_value = 0.95 # Swallow light
    
    # 4. GEOMETRY (L-Shape Corridor: W 2.5m, H 3m)
    # Origin is center. Width 2.5 means X spans -1.25 to 1.25.
    
    def add_block(name, loc, scale, mat):
        bpy.ops.mesh.primitive_cube_add(location=loc)
        obj = bpy.context.active_object
        obj.name = name
        obj.scale = scale
        obj.data.materials.append(mat)
        return obj

    # Floors
    add_block("Floor_Straight", (0, 5, -0.1), (1.25, 5, 0.1), mat_floor)
    add_block("Floor_Turn", (5, 11.25, -0.1), (5, 1.25, 0.1), mat_floor)
    
    # Ceilings
    add_block("Ceil_Straight", (0, 5, 3.1), (1.25, 5, 0.1), mat_wall)
    add_block("Ceil_Turn", (5, 11.25, 3.1), (5, 1.25, 0.1), mat_wall)

    # Walls
    # Left Wall straight
    add_block("Wall_L_Straight", (-1.35, 5, 1.5), (0.1, 5, 1.5), mat_wall)
    # Right Wall straight (ends at Y=10 to allow turn)
    add_block("Wall_R_Straight", (1.35, 5, 1.5), (0.1, 5, 1.5), mat_wall)
    
    # The wall straight ahead when looking down corridor (at corner)
    add_block("Wall_Corner_Ahead", (0, 12.6, 1.5), (1.45, 0.1, 1.5), mat_wall)
    
    # Back wall of the turn
    add_block("Wall_Turn_Back", (5, 12.6, 1.5), (5, 0.1, 1.5), mat_wall)
    # Front wall of the turn
    add_block("Wall_Turn_Front", (5, 9.9, 1.5), (3.75, 0.1, 1.5), mat_wall)
    # End of turn wall
    add_block("Wall_Turn_End", (10.1, 11.25, 1.5), (0.1, 1.25, 1.5), mat_wall)

    # 5. CAMERA (Player View)
    bpy.ops.object.camera_add(location=(0, -2, 1.6))
    cam = bpy.context.active_object
    cam.data.lens = 30 # Wide angle
    # Rotation: look straight down Y, slight tilt (roll)
    cam.rotation_euler = (math.radians(90), math.radians(3), 0)
    bpy.context.scene.camera = cam
    
    # 6. LIGHTING
    # Cyan Fill (Soft, wide, overhead/side)
    bpy.ops.object.light_add(type='AREA', location=(-1.2, 4, 2.5))
    l_cyan = bpy.context.active_object
    l_cyan.data.shape = 'RECTANGLE'
    l_cyan.data.size = 0.5
    l_cyan.data.size_y = 6
    l_cyan.data.color = (0.0, 1.0, 0.8)
    l_cyan.data.energy = 50
    l_cyan.rotation_euler = (math.radians(45), 0, math.radians(-90)) # Pointing inwards to the right floor
    
    # Magenta Accent (Hard, directional, coming from the turn)
    bpy.ops.object.light_add(type='AREA', location=(2, 11.25, 1.0))
    l_mag = bpy.context.active_object
    l_mag.data.shape = 'RECTANGLE'
    l_mag.data.size = 0.2
    l_mag.data.size_y = 2
    l_mag.data.color = (1.0, 0.0, 0.5)
    l_mag.data.energy = 800 # High contrast punch
    l_mag.data.spread = math.radians(45) # Focused
    l_mag.rotation_euler = (math.radians(90), 0, math.radians(90)) # Pointing towards -X (into the main corridor)

    # 7. FOG (Only at the corner)
    bpy.ops.mesh.primitive_cube_add(location=(0, 11.25, 1.5))
    fog = bpy.context.active_object
    fog.scale = (1.25, 1.25, 1.5)
    
    mat_fog = bpy.data.materials.new(name="Fog_Corner")
    mat_fog.use_nodes = True
    fns = mat_fog.node_tree.nodes
    fns.remove(fns['Principled BSDF'])
    v = fns.new('ShaderNodeVolumePrincipled')
    v.inputs['Density'].default_value = 0.08
    v.inputs['Anisotropy'].default_value = 0.6 # Light scatters forward
    f_out = fns['Material Output']
    mat_fog.node_tree.links.new(v.outputs[0], f_out.inputs[1])
    fog.data.materials.append(mat_fog)
    fog.display_type = 'WIRE'
    
    # 8. RENDER TO FILE
    out_dir = "e:/blender master/output"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    scn.render.filepath = os.path.join(out_dir, "maze_p1_test.png")
    scn.render.resolution_x = 1280
    scn.render.resolution_y = 720
    bpy.ops.render.render(write_still=True)

build_neon_maze_p1()
print("Phase 1 Environment Built and Rendered.")
