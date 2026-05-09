import bpy, math, os

def exec_script_without_render(filepath):
    with open(filepath, 'r') as f:
        code = f.read()
    code = code.replace("bpy.ops.render.render", "pass #")
    exec_globals = {"bpy": bpy, "math": math, "os": os, "random": __import__("random")}
    exec(code, exec_globals)

env_file = "e:/blender master/build_neon_maze_env_v2.py"
refine_file = "e:/blender master/refine_maze_v3.py"
fix_file = "e:/blender master/fix_phase2.py"

print("Building base environment...")
exec_script_without_render(env_file)
exec_script_without_render(refine_file)
# exec_script_without_render(fix_file) # Skipping this as it deletes area lights needed for EEVEE

# Manually apply essential fixes from fix_file without deleting lights
print("Setting up EEVEE materials...")
def set_em(name, color, strength):
    obj = bpy.data.objects.get(name)
    if obj and obj.active_material:
        nodes = obj.active_material.node_tree.nodes
        for n in nodes:
            if n.type == 'EMISSION':
                n.inputs['Color'].default_value = (*color, 1)
                n.inputs['Strength'].default_value = strength

set_em('Neon_Tube_Mag', (0.7, 0.02, 0.2), 300.0)
set_em('Neon_Tube_Cyan', (0.05, 0.6, 0.7), 60.0)

print("Injecting encounter entity...")
# Silhouette base
bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=1.6, location=(1.6, 10.4, 0.8))
entity = bpy.context.active_object
entity.name = "Hidden_Entity_Silhouette"
mat_sil = bpy.data.materials.new("Entity_Silhouette")
mat_sil.use_nodes = True
b = mat_sil.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (0.005, 0.005, 0.005, 1)
b.inputs['Roughness'].default_value = 0.9
b.inputs['Metallic'].default_value = 0.5
entity.data.materials.append(mat_sil)

# Glowing eyes
mat_eyes = bpy.data.materials.new("Entity_Eyes")
mat_eyes.use_nodes = True
mat_eyes.node_tree.nodes.remove(mat_eyes.node_tree.nodes['Principled BSDF'])
emis = mat_eyes.node_tree.nodes.new('ShaderNodeEmission')
emis.inputs['Color'].default_value = (1.0, 0.02, 0.1, 1)
emis.inputs['Strength'].default_value = 50.0
out = mat_eyes.node_tree.nodes.new('ShaderNodeOutputMaterial')
mat_eyes.node_tree.links.new(emis.outputs[0], out.inputs[0])

# Eye L
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.015, location=(1.45, 10.3, 1.45))
bpy.context.active_object.name = "Entity_Eye_L"
bpy.context.active_object.data.materials.append(mat_eyes)

# Eye R
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.015, location=(1.52, 10.33, 1.45))
bpy.context.active_object.name = "Entity_Eye_R"
bpy.context.active_object.data.materials.append(mat_eyes)

print("Setting up camera animation...")
cam = bpy.context.scene.camera
if cam:
    cam.location = (0, -1.0, 1.6)
    cam.keyframe_insert(data_path="location", frame=1)
    
    # Move slowly down the corridor, building tension
    cam.location = (0, 5.0, 1.6)
    cam.keyframe_insert(data_path="location", frame=120)
    
    if cam.animation_data and cam.animation_data.action:
        for fcurve in cam.animation_data.action.fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'LINEAR'

print("Configuring render settings...")
scn = bpy.context.scene
scn.frame_start = 1
scn.frame_end = 120
scn.render.fps = 24

# Use EEVEE NEXT settings for rapid cinematic render
scn.render.engine = 'BLENDER_EEVEE_NEXT'
scn.eevee.use_bloom = True
scn.eevee.bloom_intensity = 0.05
scn.eevee.use_raytracing = True # Crucial for lighting surfaces with emissives
scn.eevee.taa_render_samples = 16

# Ensure Area Lights exist and are bright enough
if 'Area_Mag' not in bpy.data.objects:
    bpy.ops.object.light_add(type='AREA', location=(1.1, 12.2, 1.5))
    l_mag = bpy.context.active_object
    l_mag.name = 'Area_Mag'
    l_mag.data.color = (1.0, 0.0, 0.5)
    l_mag.data.energy = 50
    l_mag.rotation_euler = (math.radians(90), 0, math.radians(135))

if 'Area_Cyan' not in bpy.data.objects:
    bpy.ops.object.light_add(type='AREA', location=(-1.1, 6, 2.0))
    l_cyan = bpy.context.active_object
    l_cyan.name = 'Area_Cyan'
    l_cyan.data.color = (0.0, 1.0, 0.8)
    l_cyan.data.energy = 20
    l_cyan.rotation_euler = (math.radians(90), 0, math.radians(-90))

scn.render.resolution_x = 1280
scn.render.resolution_y = 720
scn.render.resolution_percentage = 100

out_dir = "e:/blender master/output"
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

# Render direct to MP4
scn.render.filepath = os.path.join(out_dir, "encounter_cinematic.mp4")
scn.render.image_settings.file_format = 'FFMPEG'
scn.render.ffmpeg.format = 'MPEG4'
scn.render.ffmpeg.codec = 'H264'
scn.render.ffmpeg.constant_rate_factor = 'HIGH'

print("==================================================")
print("Starting Cinematic Video Render: 120 frames at 720p, 32 samples")
print("==================================================")
bpy.ops.render.render(animation=True)
print("Animation Render Complete. Saved to output/encounter_cinematic.mp4")
