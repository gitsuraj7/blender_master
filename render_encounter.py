import bpy, math, os

def exec_script_without_render(filepath):
    with open(filepath, 'r') as f:
        code = f.read()
    # Disable render calls
    code = code.replace("bpy.ops.render.render", "pass #")
    exec_globals = {"bpy": bpy, "math": math, "os": os, "random": __import__("random")}
    exec(code, exec_globals)

# 1. Clean and build base environment
env_file = "e:/blender master/build_neon_maze_env_v2.py"
refine_file = "e:/blender master/refine_maze_v3.py"
fix_file = "e:/blender master/fix_phase2.py"

print("Building environment...")
exec_script_without_render(env_file)
print("Refining environment...")
exec_script_without_render(refine_file)
print("Applying phase 2 fixes...")
exec_script_without_render(fix_file)

# 2. Add Encounter Entity (Option A: 2 glowing eyes + faint silhouette in fog)
# The inner right corner is at x=1.5, y=10.
# Camera is at (0, -1.0, 1.6) looking +Y. 
# We place the entity mostly behind the corner (x=1.6) but peeking out (x=1.4).
print("Adding encounter entity...")

# Silhouette base (mostly hidden behind x=1.5, y=10 corner)
bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=1.6, location=(1.6, 10.4, 0.8))
entity = bpy.context.active_object
entity.name = "Hidden_Entity_Silhouette"

mat_sil = bpy.data.materials.new("Entity_Silhouette")
mat_sil.use_nodes = True
b = mat_sil.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (0.005, 0.005, 0.005, 1) # Pure dark
b.inputs['Roughness'].default_value = 0.9
b.inputs['Metallic'].default_value = 0.5
entity.data.materials.append(mat_sil)

# Glowing eyes (peeking around the corner)
mat_eyes = bpy.data.materials.new("Entity_Eyes")
mat_eyes.use_nodes = True
mat_eyes.node_tree.nodes.remove(mat_eyes.node_tree.nodes['Principled BSDF'])
emis = mat_eyes.node_tree.nodes.new('ShaderNodeEmission')
emis.inputs['Color'].default_value = (1.0, 0.02, 0.1, 1) # Menacing red/magenta
emis.inputs['Strength'].default_value = 50.0 # Bright enough to pierce fog
out = mat_eyes.node_tree.nodes.new('ShaderNodeOutputMaterial')
mat_eyes.node_tree.links.new(emis.outputs[0], out.inputs[0])

# Eye 1 (Left eye, peeking out)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.015, location=(1.45, 10.3, 1.45))
eye1 = bpy.context.active_object
eye1.name = "Entity_Eye_L"
eye1.data.materials.append(mat_eyes)

# Eye 2 (Right eye, closer to corner)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.015, location=(1.52, 10.33, 1.45))
eye2 = bpy.context.active_object
eye2.name = "Entity_Eye_R"
eye2.data.materials.append(mat_eyes)

# 3. Render settings for the final elite frame
scn = bpy.context.scene
scn.cycles.samples = 64 # Good enough with denoising, much faster
scn.render.resolution_x = 1920
scn.render.resolution_y = 1080

out_dir = "e:/blender master/output"
if not os.path.exists(out_dir):
    os.makedirs(out_dir)
scn.render.filepath = os.path.join(out_dir, "encounter_frame.png")

print("Rendering encounter frame...")
bpy.ops.render.render(write_still=True)
print("Elite encounter frame completed: encounter_frame.png")
