import bpy
import math
import random
import os

def prepare_animation():
    env_file = "e:/blender master/build_neon_maze_env_v2.py"
    with open(env_file, 'r') as f:
        env_code = f.read()
    env_code = env_code.replace("bpy.ops.render.render(write_still=True)", "pass")
    
    refine_file = "e:/blender master/refine_maze_v3.py"
    with open(refine_file, 'r') as f:
        refine_code = f.read()
    refine_code = refine_code.replace("bpy.ops.render.render(write_still=True)", "pass")
    
    exec_globals = {"bpy": bpy, "math": math, "random": random, "os": os}
    exec(env_code, exec_globals)
    exec(refine_code, exec_globals)

    # Animate the Camera
    cam = bpy.context.scene.camera
    if cam:
        cam.location = (0, -1.0, 1.6)
        cam.keyframe_insert(data_path="location", frame=1)
        cam.location = (0, 7.5, 1.6)
        cam.keyframe_insert(data_path="location", frame=150)
        
        if cam.animation_data and cam.animation_data.action:
            for fcurve in cam.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'LINEAR'
                    
    # Light Flicker Animation
    cyan_light = None
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT' and obj.data.color[1] > 0.5:
            cyan_light = obj
            break
            
    if cyan_light:
        cyan_light.data.energy = 20
        cyan_light.data.keyframe_insert(data_path="energy", frame=1)
        if cyan_light.data.animation_data and cyan_light.data.animation_data.action:
            fcurve = cyan_light.data.animation_data.action.fcurves.find('energy')
            if fcurve:
                noise = fcurve.modifiers.new('NOISE')
                noise.scale = 2.0
                noise.strength = 15.0
                noise.offset = 0.0

    # FAST PREVIEW RENDER SETTINGS (EEVEE)
    scn = bpy.context.scene
    scn.render.engine = 'BLENDER_EEVEE_NEXT' # Eevee Next in 4.2
    scn.eevee.use_bloom = True  # Enable bloom for neon glow
    scn.eevee.bloom_intensity = 0.05
    
    scn.frame_start = 1
    scn.frame_end = 150
    scn.render.fps = 24
    
    scn.render.resolution_x = 1280
    scn.render.resolution_y = 720
    scn.render.resolution_percentage = 50 # Render at 640x360 for extreme speed
    
    out_dir = "e:/blender master/output"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    scn.render.filepath = os.path.join(out_dir, "preview_neon_maze.mp4")
    scn.render.image_settings.file_format = 'FFMPEG'
    scn.render.ffmpeg.format = 'MPEG4'
    scn.render.ffmpeg.codec = 'H264'
    scn.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    
    print("Starting FAST EEVEE Preview Render...")
    bpy.ops.render.render(animation=True)
    print("Preview Complete!")

if __name__ == "__main__":
    prepare_animation()
