import bpy
import math
import random
import os

def reset_context():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def create_moss_stone_material():
    mat = bpy.data.materials.new(name="MossyStone")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for n in nodes: nodes.remove(n)

    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_bsdf.inputs['Roughness'].default_value = 0.8
    links.new(node_bsdf.outputs[0], node_out.inputs[0])

    node_stone_noise = nodes.new(type='ShaderNodeTexNoise')
    node_stone_noise.inputs['Scale'].default_value = 10.0
    node_stone_noise.inputs['Detail'].default_value = 15.0
    
    node_stone_ramp = nodes.new(type='ShaderNodeValToRGB')
    node_stone_ramp.color_ramp.elements[0].color = (0.05, 0.05, 0.05, 1)
    node_stone_ramp.color_ramp.elements[1].color = (0.25, 0.25, 0.25, 1)
    links.new(node_stone_noise.outputs[0], node_stone_ramp.inputs[0])

    node_moss_color = nodes.new(type='ShaderNodeRGB')
    node_moss_color.outputs[0].default_value = (0.02, 0.12, 0.02, 1)

    node_geo = nodes.new(type='ShaderNodeNewGeometry')
    node_sep = nodes.new(type='ShaderNodeSeparateXYZ')
    links.new(node_geo.outputs['Normal'], node_sep.inputs[0])
    
    node_moss_ramp = nodes.new(type='ShaderNodeValToRGB')
    node_moss_ramp.color_ramp.elements[0].position = 0.6
    node_moss_ramp.color_ramp.elements[0].color = (0,0,0,1)
    node_moss_ramp.color_ramp.elements[1].position = 0.85
    node_moss_ramp.color_ramp.elements[1].color = (1,1,1,1)
    links.new(node_sep.outputs[2], node_moss_ramp.inputs[0])

    node_mix = nodes.new(type='ShaderNodeMixRGB')
    links.new(node_moss_ramp.outputs[0], node_mix.inputs[0]) 
    links.new(node_stone_ramp.outputs[0], node_mix.inputs[1])
    links.new(node_moss_color.outputs[0], node_mix.inputs[2])
    
    # Water Stains
    node_streak_noise = nodes.new(type='ShaderNodeTexNoise')
    node_streak_noise.inputs['Scale'].default_value = 4.0
    
    node_mapping = nodes.new(type='ShaderNodeMapping')
    node_mapping.inputs['Scale'].default_value = (1.0, 1.0, 0.05) 
    node_tc = nodes.new(type='ShaderNodeTexCoord')
    links.new(node_tc.outputs['Object'], node_mapping.inputs[0])
    links.new(node_mapping.outputs[0], node_streak_noise.inputs['Vector'])

    node_streak_ramp = nodes.new(type='ShaderNodeValToRGB')
    node_streak_ramp.color_ramp.elements[0].position = 0.4
    node_streak_ramp.color_ramp.elements[0].color = (1,1,1,1)
    node_streak_ramp.color_ramp.elements[1].position = 0.6
    node_streak_ramp.color_ramp.elements[1].color = (0,0,0,1)
    links.new(node_streak_noise.outputs[0], node_streak_ramp.inputs[0])
    
    node_stain_mix = nodes.new(type='ShaderNodeMixRGB')
    node_stain_mix.blend_type = 'MULTIPLY'
    node_stain_mix.inputs[2].default_value = (0.02, 0.02, 0.02, 1) 
    links.new(node_streak_ramp.outputs[0], node_stain_mix.inputs[0])
    links.new(node_mix.outputs[0], node_stain_mix.inputs[1])
    links.new(node_stain_mix.outputs[0], node_bsdf.inputs['Base Color'])

    node_bump = nodes.new(type='ShaderNodeBump')
    node_bump.inputs['Strength'].default_value = 0.5
    links.new(node_stone_noise.outputs[0], node_bump.inputs['Height'])
    links.new(node_bump.outputs[0], node_bsdf.inputs['Normal'])

    return mat

def create_water_material():
    mat = bpy.data.materials.new(name="WaterReflective")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for n in nodes: nodes.remove(n)

    node_out = nodes.new(type='ShaderNodeOutputMaterial')
    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_bsdf.inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1)
    node_bsdf.inputs['Roughness'].default_value = 0.05
    node_bsdf.inputs['Transmission Weight'].default_value = 0.9
    node_bsdf.inputs['IOR'].default_value = 1.33
    links.new(node_bsdf.outputs[0], node_out.inputs[0])

    node_noise = nodes.new(type='ShaderNodeTexNoise')
    node_noise.inputs['Scale'].default_value = 60.0
    node_bump = nodes.new(type='ShaderNodeBump')
    node_bump.inputs['Strength'].default_value = 0.015
    links.new(node_noise.outputs[0], node_bump.inputs['Height'])
    links.new(node_bump.outputs[0], node_bsdf.inputs['Normal'])

    return mat

def ancient_scene_build():
    moss_mat = create_moss_stone_material()
    water_mat = create_water_material()

    bpy.ops.mesh.primitive_plane_add(size=60)
    floor = bpy.context.active_object
    floor.data.materials.append(moss_mat)
    mod = floor.modifiers.new(name="Displace", type='DISPLACE')
    tex = bpy.data.textures.new("FloorDisp", type='CLOUDS')
    tex.noise_scale = 4.0
    mod.texture = tex
    mod.strength = 0.6
    bpy.ops.object.shade_smooth()

    bpy.ops.mesh.primitive_plane_add(size=60, location=(0,0,0.3))
    water = bpy.context.active_object
    water.data.materials.append(water_mat)

    bpy.ops.mesh.primitive_cube_add(location=(0, 6, 0.5))
    plat1 = bpy.context.active_object
    plat1.scale = (8, 4, 0.8)
    plat1.data.materials.append(moss_mat)

    bpy.ops.mesh.primitive_cube_add(location=(0, 8, 1.5))
    plat2 = bpy.context.active_object
    plat2.scale = (5, 3, 0.8)
    plat2.data.materials.append(moss_mat)

    bpy.ops.mesh.primitive_monkey_add(location=(0, 10, 4), rotation=(math.radians(20), 0, 0))
    head = bpy.context.active_object
    head.name = "MassiveHead"
    head.scale = (5, 5, 5) 
    head.data.materials.append(moss_mat)
    mod_sub = head.modifiers.new(name="Subsurf", type='SUBSURF')
    mod_sub.levels = 3
    mod_disp = head.modifiers.new(name="Displace", type='DISPLACE')
    tex_head = bpy.data.textures.new("HeadDisp", type='CLOUDS')
    tex_head.noise_scale = 1.0
    mod_disp.texture = tex_head
    mod_disp.strength = 0.4
    bpy.ops.object.shade_smooth()

    for i in range(35):
        x = random.uniform(-15, 15)
        y = random.uniform(-5, 18)
        if abs(x) < 4 and 4 < y < 14: continue 
        bpy.ops.mesh.primitive_cube_add(location=(x, y, 0.5))
        rock = bpy.context.active_object
        rock.scale = (random.uniform(0.3, 2.0), random.uniform(0.3, 2.0), random.uniform(0.2, 0.8))
        rock.rotation_euler = (random.uniform(0,3.14), random.uniform(0,3.14), random.uniform(0,3.14))
        rock.data.materials.append(moss_mat)
        mod_bev = rock.modifiers.new(name="Bevel", type='BEVEL')
        mod_bev.width = 0.1

    for i in [-10, -5, 5, 10]:
        for j in [0, 6, 12]:
            bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=1, location=(i, j, 5))
            col = bpy.context.active_object
            h = random.uniform(9, 13)
            col.scale = (1, 1, h)
            col.location.z = h / 2
            col.data.materials.append(moss_mat)
            col.name = f"Column_{i}_{j}"

    bpy.ops.object.light_add(type='SUN', location=(10, -10, 20))
    sun = bpy.context.active_object
    sun.name = "SunLight"
    sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(45))
    sun.data.energy = 2.0
    sun.data.color = (1.0, 0.9, 0.8)

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,10))
    fog = bpy.context.active_object
    fog.scale = (40, 40, 20)
    mat_fog = bpy.data.materials.new(name="VolumetricFog")
    mat_fog.use_nodes = True
    for n in mat_fog.node_tree.nodes: mat_fog.node_tree.nodes.remove(n)
    n_vol = mat_fog.node_tree.nodes.new(type='ShaderNodeVolumePrincipled')
    n_vol.inputs['Density'].default_value = 0.03
    n_vol.inputs['Anisotropy'].default_value = 0.8
    n_out = mat_fog.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    mat_fog.node_tree.links.new(n_vol.outputs[0], n_out.inputs[1])
    fog.data.materials.append(mat_fog)

    bpy.ops.object.camera_add(location=(0, -6, 2.0), rotation=(math.radians(85), 0, 0))
    cam = bpy.context.active_object
    cam.name = "MainCamera"
    bpy.context.scene.camera = cam

def human_element():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=1.7, location=(1.2, -2, 1.15))
    human = bpy.context.active_object
    human.name = "HumanSilhouette"
    
    mat_human = bpy.data.materials.new(name="BlackSilhouette")
    mat_human.use_nodes = True
    node_bsdf = mat_human.node_tree.nodes.get("Principled BSDF")
    if node_bsdf:
        node_bsdf.inputs['Base Color'].default_value = (0,0,0,1)
        node_bsdf.inputs['Roughness'].default_value = 1.0
        node_bsdf.inputs['Specular IOR Level'].default_value = 0.0
    human.data.materials.append(mat_human)

def polish_pass():
    for obj in bpy.data.objects:
        if obj.name.startswith("Column_"):
            obj.rotation_euler[0] += random.uniform(-0.04, 0.04)
            obj.rotation_euler[1] += random.uniform(-0.04, 0.04)
            mod = obj.modifiers.new(name="Bevel", type='BEVEL')
            mod.segments = 3
            mod.width = 0.1
            
    bpy.ops.object.light_add(type='SPOT', location=(0, 5, 22))
    spot = bpy.context.active_object
    spot.rotation_euler = (0, math.radians(-10), 0)
    spot.data.energy = 5000000.0 
    spot.data.spot_size = math.radians(40)
    spot.data.spot_blend = 0.5
    spot.data.color = (1.0, 0.95, 0.85)

    bpy.context.scene.render.engine = 'CYCLES'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        bpy.context.scene.cycles.device = 'GPU'
    except:
        pass
        
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.cycles.use_denoising = True
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.resolution_percentage = 100

    out_dir = "e:/blender master/output"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    out_path = os.path.join(out_dir, "ancient_ruin_render.png")
    bpy.context.scene.render.filepath = out_path
    print("Starting render...")
    bpy.ops.render.render(write_still=True)
    print("Render complete! Saved to", out_path)

if __name__ == "__main__":
    reset_context()
    ancient_scene_build()
    human_element()
    polish_pass()
