import bpy
import math
import random

def build_pro_indo_cyber():
    # 1. CLEANUP
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 2. PRO RENDER SETTINGS
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.cycles.use_denoising = True
    bpy.context.scene.render.film_transparent = True
    
    # 3. PROCEDURAL "TOKYO GRIME" MATERIAL
    def create_grime_material(name, color=(0.02, 0.02, 0.02, 1.0), is_windows=False):
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        for n in nodes: nodes.remove(n)
        
        # Principled BSDF
        node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        node_bsdf.inputs['Base Color'].default_value = color
        node_bsdf.inputs['Roughness'].default_value = 0.4
        
        # Noise for Grime
        node_noise = nodes.new(type='ShaderNodeTexNoise')
        node_noise.inputs['Scale'].default_value = 50.0
        node_noise.inputs['Detail'].default_value = 15.0
        
        node_ramp = nodes.new(type='ShaderNodeValToRGB')
        node_ramp.color_ramp.elements[0].position = 0.4
        node_ramp.color_ramp.elements[1].position = 0.6
        links.new(node_noise.outputs[0], node_ramp.inputs[0])
        links.new(node_ramp.outputs[0], node_bsdf.inputs['Roughness'])
        
        if is_windows:
            # Add glowing window patterns
            node_voronoi = nodes.new(type='ShaderNodeTexVoronoi')
            node_voronoi.feature = 'F1'
            node_voronoi.distance = 'CHEBYCHEV'
            node_voronoi.inputs['Scale'].default_value = 20.0
            
            node_win_ramp = nodes.new(type='ShaderNodeValToRGB')
            node_win_ramp.color_ramp.elements[0].position = 0.8
            node_win_ramp.color_ramp.elements[1].color = (1, 0.8, 0.2, 1) # Yellow light
            links.new(node_voronoi.outputs[0], node_win_ramp.inputs[0])
            
            node_mix = nodes.new(type='ShaderNodeMixShader')
            node_emit = nodes.new(type='ShaderNodeEmission')
            node_emit.inputs['Color'].default_value = (1, 0.8, 0.5, 1)
            node_emit.inputs['Strength'].default_value = 10.0
            
            links.new(node_win_ramp.outputs[0], node_mix.inputs[0])
            links.new(node_bsdf.outputs[0], node_mix.inputs[1])
            links.new(node_emit.outputs[0], node_mix.inputs[2])
            
            node_out = nodes.new(type='ShaderNodeOutputMaterial')
            links.new(node_mix.outputs[0], node_out.inputs[0])
        else:
            node_out = nodes.new(type='ShaderNodeOutputMaterial')
            links.new(node_bsdf.outputs[0], node_out.inputs[0])
        return mat

    mat_wall = create_grime_material("Pro_Wall", is_windows=True)
    mat_ground = create_grime_material("Pro_Ground", color=(0.01, 0.01, 0.01, 1.0))
    mat_ground.node_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0.05

    # 4. ARCHITECTURE
    # Ground
    bpy.ops.mesh.primitive_plane_add(size=20)
    ground = bpy.context.active_object
    ground.scale = (2, 5, 1)
    ground.data.materials.append(mat_ground)

    # Detailed Buildings
    for i in [-4, 4]:
        for j in range(3):
            bpy.ops.mesh.primitive_cube_add(size=2, location=(i, j*4-4, 5))
            bldg = bpy.context.active_object
            bldg.scale = (0.5, 1.8, 5)
            bldg.data.materials.append(mat_wall)
            # Add "Pipes"
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=10, location=(i-0.5 if i>0 else i+0.5, j*4-4, 5))
            pipe = bpy.context.active_object
            pipe.data.materials.append(create_grime_material(f"Pipe_{i}_{j}", color=(0.1, 0.1, 0.1, 1.0)))

    # 5. THE "SHAWL" CHARACTER (Using a cloth-like mesh)
    bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 1), rotation=(0, 0, math.radians(180)))
    hero = bpy.context.active_object
    
    # Procedural Indian Pattern Shader
    mat_shawl = bpy.data.materials.new(name="Pashmina_Shawl")
    mat_shawl.use_nodes = True
    ns = mat_shawl.node_tree.nodes
    ls = mat_shawl.node_tree.links
    for n in ns: ns.remove(n)
    
    n_wave = ns.new(type='ShaderNodeTexWave')
    n_wave.wave_type = 'RINGS'
    n_wave.inputs['Scale'].default_value = 20.0
    
    n_ramp = ns.new(type='ShaderNodeValToRGB')
    n_ramp.color_ramp.elements[0].color = (0.3, 0.02, 0.02, 1) # Deep Red
    n_ramp.color_ramp.elements[1].color = (0.8, 0.6, 0.1, 1) # Gold
    ls.new(n_wave.outputs[0], n_ramp.inputs[0])
    
    n_bsdf = ns.new(type='ShaderNodeBsdfPrincipled')
    ls.new(n_ramp.outputs[0], n_bsdf.inputs['Base Color'])
    
    n_out = ns.new(type='ShaderNodeOutputMaterial')
    ls.new(n_bsdf.outputs[0], n_out.inputs[0])
    hero.data.materials.append(mat_shawl)

    # 6. PRO LIGHTING & CAMERA
    # Menacing Spotlight
    bpy.ops.object.light_add(type='SPOT', location=(5, -10, 10))
    spot = bpy.context.active_object
    spot.data.energy = 50000
    spot.data.color = (1, 0.7, 0.2)
    spot.rotation_euler = (math.radians(45), 0, math.radians(-30))
    
    # Camera Dolly
    bpy.ops.object.camera_add(location=(0, -8, 1.5), rotation=(math.radians(88), 0, 0))
    bpy.context.scene.camera = bpy.context.active_object
    bpy.context.active_object.keyframe_insert(data_path="location", frame=1)
    bpy.context.active_object.location.y = -4
    bpy.context.active_object.keyframe_insert(data_path="location", frame=240)

    # 7. VOLUME ATMOSPHERE
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 5))
    fog = bpy.context.active_object
    fog.scale = (15, 20, 10)
    mat_fog = bpy.data.materials.new(name="Atmosphere_Pro")
    mat_fog.use_nodes = True
    for n in mat_fog.node_tree.nodes: mat_fog.node_tree.nodes.remove(n)
    n_vol = mat_fog.node_tree.nodes.new(type='ShaderNodeVolumePrincipled')
    n_vol.inputs['Density'].default_value = 0.05
    n_out_f = mat_fog.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    mat_fog.node_tree.links.new(n_vol.outputs[0], n_out_f.inputs[1])
    fog.data.materials.append(mat_fog)

build_pro_indo_cyber()
print("Pro Indo-Cyber Scene Built!")
