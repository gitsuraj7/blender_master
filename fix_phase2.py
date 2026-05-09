import bpy, random, math

# Utility functions

def get_obj(name):
    return bpy.data.objects.get(name)

def get_or_create_mat(name, base_color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        principled = nodes.get('Principled BSDF')
        if principled:
            principled.inputs['Base Color'].default_value = (*base_color[:3], 1)
            principled.inputs['Roughness'].default_value = roughness
            principled.inputs['Metallic'].default_value = metallic
    return mat

def delete_area_lights():
    for obj in list(bpy.data.objects):
        if obj.type == 'LIGHT' and obj.data.type == 'AREA':
            bpy.data.objects.remove(obj, do_unlink=True)

def set_emission(obj_name, strength):
    obj = get_obj(obj_name)
    if not obj: return
    mat = obj.active_material
    if not mat: return
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            node.inputs['Strength'].default_value = strength

def set_color(obj_name, rgb):
    obj = get_obj(obj_name)
    if not obj: return
    mat = obj.active_material
    if not mat: return
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            node.inputs['Color'].default_value = (*rgb, 1)

def set_color_management():
    view = bpy.context.scene.view_settings
    view.view_transform = 'Filmic'
    view.look = 'High Contrast'
    bpy.context.scene.cycles.sample_clamp_indirect = 2.0

def adjust_fog():
    fog = get_obj('Fog_Volume')
    if not fog: return
    mat = fog.active_material
    if not mat: return
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    # Find Principled Volume node
    principled = None
    for n in nodes:
        if n.type == 'VOLUME_PRINCIPLED':
            principled = n
            break
    if not principled:
        return
    # Noise texture
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 3.0
    noise.inputs['Detail'].default_value = 5.0
    noise.location = (-300, 0)
    # ColorRamp to map noise to 0.08‑0.2 range
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (-100, 0)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    # Multiply base density (0.15) with ramp output
    math = nodes.new('ShaderNodeMath')
    math.operation = 'MULTIPLY'
    math.inputs[1].default_value = 0.15
    math.location = (100, 0)
    # Links
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], math.inputs[0])
    links.new(math.outputs['Value'], principled.inputs['Density'])

def adjust_materials():
    # Walls: add procedural noise to roughness and a subtle normal map
    for obj in bpy.data.objects:
        if obj.name.startswith('Wall_'):
            mat = obj.active_material
            if not mat:
                continue
            nt = mat.node_tree
            nodes = nt.nodes
            links = nt.links
            # Noise for roughness variation
            noise = nodes.new('ShaderNodeTexNoise')
            noise.inputs['Scale'].default_value = 15.0
            noise.location = (-300, 200)
            # Mix with base roughness (0.8) – multiply
            mix = nodes.new('ShaderNodeMixRGB')
            mix.blend_type = 'MULTIPLY'
            mix.inputs['Fac'].default_value = 1.0
            mix.location = (-100, 200)
            # Find Principled BSDF
            principled = None
            for n in nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    principled = n
                    break
            if not principled:
                continue
            # Connect base roughness to Mix input 1
            roughness_in = principled.inputs['Roughness']
            if roughness_in.is_linked:
                links.new(roughness_in.links[0].from_socket, mix.inputs[1])
            else:
                val = roughness_in.default_value
                mix.inputs[1].default_value = (val, val, val, 1.0)
            # Connect noise to Mix input 2
            links.new(noise.outputs['Fac'], mix.inputs[2])
            # Output back to Principled roughness
            links.new(mix.outputs['Color'], principled.inputs['Roughness'])
            # Normal map strength
            for n in nodes:
                if n.type == 'NORMAL_MAP':
                    n.inputs['Strength'].default_value = 0.1
    # Floor normal map strength increase
    floor = get_obj('Floor_Straight') or get_obj('Floor_Turn')
    if floor and floor.active_material:
        nt = floor.active_material.node_tree
        for n in nt.nodes:
            if n.type == 'NORMAL_MAP':
                n.inputs['Strength'].default_value = 0.08

def adjust_geometry():
    # Increase wall panel rotation randomness
    for obj in bpy.data.objects:
        if obj.name.startswith('Wall_'):
            delta = math.radians(random.uniform(-0.5, 0.5))
            obj.rotation_euler[2] += delta
    # Add 2 additional hanging cables (cylinders)
    for i in range(2):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=2.2)
        cab = bpy.context.active_object
        cab.name = f'Hanging_Cable_{i+2}'
        cab.location = (random.uniform(-0.5, 0.5), random.uniform(6, 12), random.uniform(2, 3))
        cab.rotation_euler = (math.radians(random.uniform(5, 15)), math.radians(random.uniform(0, 10)), math.radians(random.uniform(-5, 5)))
        mat = get_or_create_mat('Cable_Dark', (0.02, 0.02, 0.02, 1), roughness=0.6, metallic=0.7)
        cab.data.materials.append(mat)
    # Add one ceiling pipe (torus)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.4, minor_radius=0.02)
    pipe = bpy.context.active_object
    pipe.name = 'Ceiling_Pipe'
    pipe.location = (0, 8, 3.0)
    pipe.rotation_euler = (math.radians(90), 0, 0)
    mat_pipe = get_or_create_mat('Pipe_Metal', (0.1, 0.1, 0.1, 1), roughness=0.3, metallic=1.0)
    pipe.data.materials.append(mat_pipe)
    # Adjust foreground pillar
    pillar = get_obj('FG_Shadow_Pillar')
    if pillar:
        pillar.scale[0] *= 1.2
        pillar.scale[1] *= 1.2
        pillar.location[1] = 0.5
    # Ensure one wall receives no direct light (set emission to 0)
    wall = get_obj('Wall_R_0')
    if wall and wall.active_material:
        nt = wall.active_material.node_tree
        for n in nt.nodes:
            if n.type == 'EMISSION':
                n.inputs['Strength'].default_value = 0.0

# Apply corrections
delete_area_lights()
set_emission('Neon_Tube_Mag', 300.0)
set_emission('Neon_Tube_Cyan', 60.0)
set_color('Neon_Tube_Mag', (0.7, 0.02, 0.2))
set_color('Neon_Tube_Cyan', (0.05, 0.6, 0.7))
set_color_management()
adjust_fog()
adjust_materials()
adjust_geometry()

# Render preview for verification
scene = bpy.context.scene
scene.cycles.samples = 64
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
out_dir = "e:/blender master/output"
import os
if not os.path.isdir(out_dir):
    os.makedirs(out_dir)
scene.render.filepath = os.path.join(out_dir, "maze_phase2_fixed.png")
bpy.ops.render.render(write_still=True)
print('RENDER_DONE')
