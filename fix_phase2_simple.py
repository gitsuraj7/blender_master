import bpy, random, math

def delete_area_lights():
    for obj in list(bpy.data.objects):
        if obj.type == 'LIGHT' and obj.data.type == 'AREA':
            bpy.data.objects.remove(obj, do_unlink=True)

def set_emission(obj_name, strength):
    obj = bpy.data.objects.get(obj_name)
    if not obj or not obj.active_material:
        return
    for node in obj.active_material.node_tree.nodes:
        if node.type == 'EMISSION':
            node.inputs['Strength'].default_value = strength

def set_color(obj_name, rgb):
    obj = bpy.data.objects.get(obj_name)
    if not obj or not obj.active_material:
        return
    for node in obj.active_material.node_tree.nodes:
        if node.type == 'EMISSION':
            node.inputs['Color'].default_value = (*rgb, 1)

def set_color_management():
    view = bpy.context.scene.view_settings
    view.view_transform = 'Filmic'
    view.look = 'High Contrast'
    bpy.context.scene.cycles.sample_clamp_indirect = 2.0

def adjust_fog():
    fog = bpy.data.objects.get('Fog_Volume')
    if not fog or not fog.active_material:
        return
    mat = fog.active_material
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    # Find Principled Volume node
    principled = next((n for n in nodes if n.type == 'VOLUME_PRINCIPLED'), None)
    if not principled:
        return
    # Create Noise texture
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 3.0
    noise.inputs['Detail'].default_value = 5.0
    # ColorRamp to map 0-1 to 0.08-0.2
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0,0,0,1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (1,1,1,1)
    # Multiply base density
    math = nodes.new('ShaderNodeMath')
    math.operation = 'MULTIPLY'
    math.inputs[1].default_value = 0.15
    # Links
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], math.inputs[0])
    links.new(math.outputs['Value'], principled.inputs['Density'])

def add_cables(count=2):
    for i in range(count):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=2.2)
        cab = bpy.context.active_object
        cab.name = f'Hanging_Cable_{i+2}'
        cab.location = (random.uniform(-0.5,0.5), random.uniform(6,12), random.uniform(2,3))
        cab.rotation_euler = (math.radians(random.uniform(5,15)), math.radians(random.uniform(0,10)), math.radians(random.uniform(-5,5)))
        mat = bpy.data.materials.get('Cable_Dark')
        if not mat:
            mat = bpy.data.materials.new('Cable_Dark')
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get('Principled BSDF')
            if bsdf:
                bsdf.inputs['Base Color'].default_value = (0.02,0.02,0.02,1)
                bsdf.inputs['Roughness'].default_value = 0.6
                bsdf.inputs['Metallic'].default_value = 0.7
        cab.data.materials.append(mat)

def adjust_pillar():
    pillar = bpy.data.objects.get('FG_Shadow_Pillar')
    if pillar:
        pillar.scale[0] *= 1.2
        pillar.scale[1] *= 1.2
        pillar.location[1] = 0.5

def ensure_dark_wall():
    wall = bpy.data.objects.get('Wall_R_0')
    if wall and wall.active_material:
        for node in wall.active_material.node_tree.nodes:
            if node.type == 'EMISSION':
                node.inputs['Strength'].default_value = 0.0

def main():
    delete_area_lights()
    set_emission('Neon_Tube_Mag', 300.0)
    set_emission('Neon_Tube_Cyan', 60.0)
    set_color('Neon_Tube_Mag', (0.7, 0.02, 0.2))
    set_color('Neon_Tube_Cyan', (0.05, 0.6, 0.7))
    set_color_management()
    adjust_fog()
    add_cables(2)
    adjust_pillar()
    ensure_dark_wall()
    # Low‑res render for verification
    sc = bpy.context.scene
    sc.cycles.samples = 64
    sc.render.resolution_x = 1280
    sc.render.resolution_y = 720
    out = "e:/blender master/output"
    import os
    if not os.path.isdir(out):
        os.makedirs(out)
    sc.render.filepath = os.path.join(out, "maze_phase2_fixed_simple.png")
    bpy.ops.render.render(write_still=True)
    print('RENDER_DONE')

if __name__ == '__main__':
    main()
