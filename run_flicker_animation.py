import bpy, os, random, math, subprocess

# ------------------------------------------------
# Configuration
# ------------------------------------------------
frame_start = 1
frame_end = 120  # 5 seconds @ 24 fps
fps = 24
out_dir = r"e:/blender master/output"
video_mp4 = os.path.join(out_dir, "maze_flicker.mp4")

# Ensure output directory exists
if not os.path.isdir(out_dir):
    os.makedirs(out_dir)

# ------------------------------------------------
# Helper utilities
# ------------------------------------------------
def get_obj(name):
    return bpy.data.objects.get(name)

def create_emission_material(name, base_color, base_strength):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        # Emission node
        emis = nodes.new(type='ShaderNodeEmission')
        emis.location = (0, 0)
        emis.inputs['Color'].default_value = (*base_color, 1)
        # Noise texture drives flicker
        noise = nodes.new(type='ShaderNodeTexNoise')
        noise.location = (-300, 0)
        noise.inputs['Scale'].default_value = 8.0
        noise.inputs['Detail'].default_value = 2.0
        # Math node multiplies base strength by noise
        mult = nodes.new(type='ShaderNodeMath')
        mult.operation = 'MULTIPLY'
        mult.location = (-100, 0)
        const = nodes.new(type='ShaderNodeValue')
        const.location = (-200, -100)
        const.outputs[0].default_value = base_strength
        # Links
        links.new(const.outputs[0], mult.inputs[0])
        links.new(noise.outputs['Fac'], mult.inputs[1])
        links.new(mult.outputs[0], emis.inputs['Strength'])
        # Output
        out = nodes.new(type='ShaderNodeOutputMaterial')
        out.location = (200, 0)
        links.new(emis.outputs[0], out.inputs['Surface'])
    return mat

# ------------------------------------------------
# 1. Ensure wire has flickering emission material
# ------------------------------------------------
wire = get_obj('Hanging_Cable')
if wire:
    mat = create_emission_material('Wire_Flicker', (0.7, 0.02, 0.2), 250.0)
    if mat.name not in wire.data.materials:
        wire.data.materials.clear()
        wire.data.materials.append(mat)

# ------------------------------------------------
# 2. Add post‑war dust volume (if not already present)
# ------------------------------------------------
if not get_obj('Dust_Volume'):
    bpy.ops.mesh.primitive_cube_add(size=8, location=(0, 8, 1.5))
    dust = bpy.context.active_object
    dust.name = 'Dust_Volume'
    dust.scale = (4, 4, 2)
    # Volume material
    mat = bpy.data.materials.new('Dust_Volume_Mat')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    vol = nodes.new(type='ShaderNodeVolumePrincipled')
    vol.location = (0, 0)
    vol.inputs['Density'].default_value = 0.02
    # Noise texture to vary density
    noise = nodes.new(type='ShaderNodeTexNoise')
    noise.location = (-300, 0)
    noise.inputs['Scale'].default_value = 2.0
    noise.inputs['Detail'].default_value = 4.0
    mult = nodes.new(type='ShaderNodeMath')
    mult.operation = 'MULTIPLY'
    mult.location = (-100, 0)
    const = nodes.new(type='ShaderNodeValue')
    const.location = (-200, -100)
    const.outputs[0].default_value = 0.02
    # Links
    links.new(const.outputs[0], mult.inputs[0])
    links.new(noise.outputs['Fac'], mult.inputs[1])
    links.new(mult.outputs[0], vol.inputs['Density'])
    out = nodes.new(type='ShaderNodeOutputMaterial')
    out.location = (200, 0)
    links.new(vol.outputs['Volume'], out.inputs['Volume'])
    dust.data.materials.append(mat)

# ------------------------------------------------
# 3. Animation / render settings (PNG sequence)
# ------------------------------------------------
scene = bpy.context.scene
scene.frame_start = frame_start
scene.frame_end = frame_end
scene.render.fps = fps
scene.render.image_settings.file_format = 'PNG'
# Blender appends frame number automatically
scene.render.filepath = os.path.join(out_dir, 'frame_')
scene.render.use_file_extension = True
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.cycles.samples = 64

# ------------------------------------------------
# 4. Render animation
# ------------------------------------------------
print('Rendering PNG sequence...')
bpy.ops.render.render(animation=True)
print('Render finished')

# ------------------------------------------------
# 5. Convert PNG sequence to MP4 using ffmpeg (external)
# ------------------------------------------------
# Build ffmpeg command (expects frames named frame_0001.png etc.)
ffmpeg_cmd = [
    'ffmpeg', '-y',
    '-framerate', str(fps),
    '-i', os.path.join(out_dir, 'frame_%04d.png'),
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    video_mp4
]
print('Running ffmpeg...')
subprocess.run(ffmpeg_cmd, check=True)
print('MP4 created at', video_mp4)
