import bpy
import math
import random
import os

def build_neon_maze_elite():
    # 1. CLEANUP
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 2. RENDER SETTINGS
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 64
    scn.cycles.use_denoising = True
    scn.view_settings.view_transform = 'AgX'
    scn.view_settings.look = 'AgX - High Contrast'
    
    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0, 0, 0, 1)
    bg.inputs['Strength'].default_value = 0.0
    
    # 3. MATERIALS
    # Wet Floor (Puddles + Streaks)
    mat_floor = bpy.data.materials.new(name="Wet_Floor")
    mat_floor.use_nodes = True
    ns = mat_floor.node_tree.nodes
    bsdf = ns['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1)
    bsdf.inputs['Metallic'].default_value = 0.0
    
    tc = ns.new('ShaderNodeTexCoord')
    mapping = ns.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (1.0, 0.2, 1.0) # Stretch along Y (streaks)
    
    noise = ns.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 15.0
    noise.inputs['Detail'].default_value = 15.0
    noise.inputs['Roughness'].default_value = 0.6
    
    ramp = ns.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.4
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0) # Deep puddle
    ramp.color_ramp.elements[1].position = 0.6
    ramp.color_ramp.elements[1].color = (0.2, 0.2, 0.2, 1.0) # Damp concrete
    
    bump = ns.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.02
    bump.inputs['Distance'].default_value = 0.1
    
    links = mat_floor.node_tree.links
    links.new(tc.outputs['Object'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Roughness'])
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    
    # Dark Wall
    mat_wall = bpy.data.materials.new(name="Dark_Wall")
    mat_wall.use_nodes = True
    w_bsdf = mat_wall.node_tree.nodes['Principled BSDF']
    w_bsdf.inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1)
    w_bsdf.inputs['Roughness'].default_value = 0.8
    
    # Metal Pipe
    mat_pipe = bpy.data.materials.new(name="Metal_Pipe")
    mat_pipe.use_nodes = True
    p_bsdf = mat_pipe.node_tree.nodes['Principled BSDF']
    p_bsdf.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1)
    p_bsdf.inputs['Metallic'].default_value = 1.0
    p_bsdf.inputs['Roughness'].default_value = 0.4
    
    # Neons
    mat_cyan = bpy.data.materials.new(name="Neon_Cyan")
    mat_cyan.use_nodes = True
    c_ns = mat_cyan.node_tree.nodes
    c_ns.remove(c_ns['Principled BSDF'])
    c_em = c_ns.new('ShaderNodeEmission')
    c_em.inputs['Color'].default_value = (0.1, 0.9, 0.8, 1)
    c_em.inputs['Strength'].default_value = 100.0
    c_out = c_ns.get('Material Output')
    mat_cyan.node_tree.links.new(c_em.outputs[0], c_out.inputs[0])

    mat_mag = bpy.data.materials.new(name="Neon_Mag")
    mat_mag.use_nodes = True
    m_ns = mat_mag.node_tree.nodes
    m_ns.remove(m_ns['Principled BSDF'])
    m_em = m_ns.new('ShaderNodeEmission')
    m_em.inputs['Color'].default_value = (0.9, 0.05, 0.4, 1)
    m_em.inputs['Strength'].default_value = 150.0
    m_out = m_ns.get('Material Output')
    mat_mag.node_tree.links.new(m_em.outputs[0], m_out.inputs[0])

    # 4. GEOMETRY
    def add_mesh(type, name, loc, scale, rot, mat):
        if type == 'CUBE':
            bpy.ops.mesh.primitive_cube_add(location=loc, scale=scale)
        elif type == 'CYLINDER':
            bpy.ops.mesh.primitive_cylinder_add(location=loc, scale=scale)
        obj = bpy.context.active_object
        obj.name = name
        obj.rotation_euler = rot
        obj.data.materials.append(mat)
        return obj

    # Floors and Ceilings
    add_mesh('CUBE', "Floor_Straight", (0, 6, -0.1), (1.25, 6, 0.1), (0,0,0), mat_floor)
    add_mesh('CUBE', "Floor_Turn", (4, 13.25, -0.1), (5.25, 1.25, 0.1), (0,0,0), mat_floor)
    add_mesh('CUBE', "Ceil_Straight", (0, 6, 3.1), (1.25, 6, 0.1), (0,0,0), mat_wall)
    add_mesh('CUBE', "Ceil_Turn", (4, 13.25, 3.1), (5.25, 1.25, 0.1), (0,0,0), mat_wall)

    # Modular Walls with Damage/Offset
    for i in range(4):
        y_pos = 1.5 + i * 3
        # Left wall panels
        rot_z = random.uniform(-0.02, 0.02)
        off_x = random.uniform(-0.05, 0.0)
        wall_l = add_mesh('CUBE', f"Wall_L_{i}", (-1.35 + off_x, y_pos, 1.5), (0.1, 1.45, 1.5), (0, 0, rot_z), mat_wall)
        bpy.ops.object.modifier_add(type='BEVEL')
        wall_l.modifiers["Bevel"].width = 0.02
        
        # Right wall panels (only up to Y=12)
        if i < 3:
            rot_z = random.uniform(-0.02, 0.02)
            off_x = random.uniform(0.0, 0.05)
            wall_r = add_mesh('CUBE', f"Wall_R_{i}", (1.35 + off_x, y_pos, 1.5), (0.1, 1.45, 1.5), (0, 0, rot_z), mat_wall)
            bpy.ops.object.modifier_add(type='BEVEL')
            wall_r.modifiers["Bevel"].width = 0.02
        
        # Support Pillars (Shadow casters)
        add_mesh('CUBE', f"Pillar_L_{i}", (-1.2, y_pos - 1.45, 1.5), (0.1, 0.1, 1.5), (0,0,0), mat_wall)
        add_mesh('CUBE', f"Pillar_R_{i}", (1.2, y_pos - 1.45, 1.5), (0.1, 0.1, 1.5), (0,0,0), mat_wall)

    # Corner Walls
    wall_c_ahead = add_mesh('CUBE', "Wall_Corner_Ahead", (0, 14.6, 1.5), (1.45, 0.1, 1.5), (0,0,0), mat_wall)
    bpy.ops.object.modifier_add(type='BEVEL')
    wall_c_ahead.modifiers["Bevel"].width = 0.02
    
    wall_c_back = add_mesh('CUBE', "Wall_Turn_Back", (5, 14.6, 1.5), (5, 0.1, 1.5), (0,0,0), mat_wall)
    wall_c_front = add_mesh('CUBE', "Wall_Turn_Front", (5, 11.9, 1.5), (3.75, 0.1, 1.5), (0,0,0), mat_wall)

    # Imperfect Pipes
    for p in range(3):
        z_pos = 2.8 - (p * 0.15)
        rot_y = random.uniform(-0.02, 0.02)
        add_mesh('CYLINDER', f"Pipe_{p}", (-1.1, 6, z_pos), (0.03, 0.03, 6), (math.radians(90), rot_y, 0), mat_pipe)

    # 5. PHYSICAL NEON TUBES & LIGHTING
    # Focal Point: Magenta Vertical Tube at the inner corner (Y=12, X=1.3)
    add_mesh('CYLINDER', "Neon_Tube_Mag", (1.25, 12.1, 1.5), (0.03, 0.03, 1.0), (0,0,0), mat_mag)
    # Fill Point: Cyan Horizontal Tube on the left wall (Y=6, X=-1.25)
    add_mesh('CYLINDER', "Neon_Tube_Cyan", (-1.25, 6, 2.0), (0.03, 0.03, 2.0), (math.radians(90), 0, 0), mat_cyan)

    # To ensure Cycles bounces light beautifully from these small tubes, add supportive invisible lights
    bpy.ops.object.light_add(type='AREA', location=(1.1, 12.2, 1.5))
    l_mag = bpy.context.active_object
    l_mag.data.shape = 'RECTANGLE'
    l_mag.data.size = 0.1
    l_mag.data.size_y = 2.0
    l_mag.data.color = (1.0, 0.0, 0.5)
    l_mag.data.energy = 50
    l_mag.rotation_euler = (math.radians(90), 0, math.radians(135)) # Pointing towards corner and floor

    bpy.ops.object.light_add(type='AREA', location=(-1.1, 6, 2.0))
    l_cyan = bpy.context.active_object
    l_cyan.data.shape = 'RECTANGLE'
    l_cyan.data.size = 0.1
    l_cyan.data.size_y = 4.0
    l_cyan.data.color = (0.0, 1.0, 0.8)
    l_cyan.data.energy = 20
    l_cyan.rotation_euler = (math.radians(90), 0, math.radians(-90)) # Pointing right

    # 6. LOCALIZED FOG (Glowing Corner)
    fog = add_mesh('CUBE', "Fog_Volume", (1.0, 12.0, 1.5), (2.0, 2.0, 1.5), (0,0,0), mat_wall) # mat will be replaced
    mat_fog = bpy.data.materials.new(name="Fog_Corner")
    mat_fog.use_nodes = True
    fns = mat_fog.node_tree.nodes
    fns.remove(fns['Principled BSDF'])
    v = fns.new('ShaderNodeVolumePrincipled')
    v.inputs['Density'].default_value = 0.15
    v.inputs['Anisotropy'].default_value = 0.8 # Strong forward scattering toward camera
    f_out = fns.get('Material Output')
    mat_fog.node_tree.links.new(v.outputs[0], f_out.inputs[1])
    fog.data.materials[0] = mat_fog
    fog.display_type = 'WIRE'

    # 7. CAMERA
    bpy.ops.object.camera_add(location=(0, -1, 1.6))
    cam = bpy.context.active_object
    cam.data.lens = 28 # Wide lens for depth
    # Slight roll for tension
    cam.rotation_euler = (math.radians(90), math.radians(3), 0)
    bpy.context.scene.camera = cam

    # 8. RENDER
    out_dir = "e:/blender master/output"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    scn.render.filepath = os.path.join(out_dir, "maze_elite_test.png")
    scn.render.resolution_x = 1280
    scn.render.resolution_y = 720
    bpy.ops.render.render(write_still=True)

build_neon_maze_elite()
print("Elite Environment Built and Rendered.")
