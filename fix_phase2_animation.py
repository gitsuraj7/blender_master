import bpy, math, random

# -----------------------
# Settings
# -----------------------
frame_start = 1
frame_end = 120  # 5 seconds @ 24 fps
fps = 24
out_dir = r"e:/blender master/output"
video_path = out_dir + "/maze_flicker.mp4"

# Ensure output folder exists
import os
if not os.path.isdir(out_dir):
    os.makedirs(out_dir)

# -----------------------
# Helper functions
# -----------------------

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
        # Noise texture (drives flicker)
        noise = nodes.new(type='ShaderNodeTexNoise')
        noise.location = (-300, 0)
        noise.inputs['Scale'].default_value = 5.0
        noise.inputs['Detail'].default_value = 2.0
        # Math node to convert noise (0‑1) to strength range
        math_node = nodes.new(type='ShaderNodeMath')
        math_node.operation = 'MULTIPLY'
        math_node.location = (-100, 0)
        # Base strength constant
        const = nodes.new(type='ShaderNodeValue')
        const.location = (-200, -100)
        const.outputs[0].default_value = base_strength
        # Multiply constant * noise
        links.new(const.outputs[0], math_node.inputs[0])
        links.new(noise.outputs['Fac'], math_node.inputs[1])
        # Connect to emission strength
        links.new(math_node.outputs[0], emis.inputs['Strength'])
        # Output
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (200, 0)
        links.new(emis.outputs[0], output.inputs['Surface'])
    return mat

# -----------------------
# 1. Flickering wire material
# -----------------------
wire_obj = get_obj('Hanging_Cable')
if wire_obj:
    # Use a warm, damaged metal colour
    wire_mat = create_emission_material('Wire_Flicker', (0.7, 0.02, 0.2), 200.0)
    if wire_mat.name not in wire_obj.data.materials:
        wire_obj.data.materials.append(wire_mat)
    else:
        # replace existing material
        for i, m in enumerate(wire_obj.data.materials):
            if m.name == wire_mat.name:
                wire_obj.data.materials[i] = wire_mat
                break

# -----------------------
# 2. Post‑war dust volume (simple cube with noisy density)
# -----------------------
if not get_obj('Dust_Volume'):
    bpy.ops.mesh.primitive_cube_add(size=8, location=(0, 8, 1.5))
    dust = bpy.context.active_object
    dust.name = 'Dust_Volume'
    dust.scale = (4, 4, 2)
    # Material for volume
    dust_mat = bpy.data.materials.new('Dust_Volume_Mat')
    dust_mat.use_nodes = True
    nodes = dust_mat.node_tree.nodes
    links = dust_mat.node_tree.links
    nodes.clear()
    princ = nodes.new(type='ShaderNodeVolumePrincipled')
    princ.location = (0, 0)
    princ.inputs['Density'].default_value = 0.02
    # Noise to modulate density
    noise = nodes.new(type='ShaderNodeTexNoise')
    noise.location = (-300, 0)
    noise.inputs['Scale'].default_value = 2.0
    noise.inputs['Detail'].default_value = 4.0
    # Multiply base density by noise
    math = nodes.new(type='ShaderNodeMath')
    math.operation = 'MULTIPLY'
    math.location = (-100, 0)
    const = nodes.new(type='ShaderNodeValue')
    const.location = (-200, -100)
    const.outputs[0].default_value = 0.02
    links.new(const.outputs[0], math.inputs[0])
    links.new(noise.outputs['Fac'], math.inputs[1])
    links.new(math.outputs[0], princ.inputs['Density'])
    # Volume Output
    out = nodes.new(type='ShaderNodeOutputMaterial')
    out.location = (200, 0)
    links.new(princ.outputs['Volume'], out.inputs['Volume'])
    dust.data.materials.append(dust_mat)

# -----------------------
# 3. Animation settings
# -----------------------
scene = bpy.context.scene
scene.frame_start = frame_start
scene.frame_end = frame_end
scene.render.fps = fps
# Set video output if supported
# Use PNG sequence for animation (fallback when FFMPEG unavailable)
# Set render to PNG sequence
scene.render.image_settings.file_format = 'PNG'
# Blender will append frame number automatically
scene.render.filepath = os.path.join(out_dir, 'frame_')
# After rendering, combine to MP4 using ffmpeg (outside Blender)
scene.render.use_file_extension = True
scene.render.filepath = video_path
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.cycles.samples = 64

# Ensure the emission node uses the driver (noise already animated via its internal fractal over time)
# No explicit driver needed – the Noise texture will vary per frame automatically.

# -----------------------
# 4. Render animation
# -----------------------
print('Starting render...')
bpy.ops.render.render(animation=True)
print('RENDER_DONE')
