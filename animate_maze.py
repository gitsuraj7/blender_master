import bpy
import math
import random
import os

def prepare_animation():
    # 1. Read and execute the environment builder
    env_file = "e:/blender master/build_neon_maze_env_v2.py"
    with open(env_file, 'r') as f:
        env_code = f.read()
    # Strip out the still render call so we don't waste time rendering an image
    env_code = env_code.replace("bpy.ops.render.render(write_still=True)", "pass")
    
    # 2. Read and execute the refiner script
    refine_file = "e:/blender master/refine_maze_v3.py"
    with open(refine_file, 'r') as f:
        refine_code = f.read()
    refine_code = refine_code.replace("bpy.ops.render.render(write_still=True)", "pass")
    
    # Execute both in a controlled namespace
    exec_globals = {"bpy": bpy, "math": math, "random": random, "os": os}
    exec(env_code, exec_globals)
    exec(refine_code, exec_globals)

    # 3. Animate the Camera
    cam = bpy.context.scene.camera
    if cam:
        # Initial frame (Start further back)
        cam.location = (0, -1.0, 1.6)
        cam.keyframe_insert(data_path="location", frame=1)
        
        # End frame (Move towards the turning corner with the magenta neon)
        cam.location = (0, 7.5, 1.6)
        cam.keyframe_insert(data_path="location", frame=150)
        
        # Make the movement linear for a steady walking/approaching feel
        if cam.animation_data and cam.animation_data.action:
            for fcurve in cam.animation_data.action.fcurves:
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'LINEAR'
                    
    # 4. Light Flicker Animation (Cyan Neon)
    cyan_light = None
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT' and obj.data.color[1] > 0.5: # cyan
            cyan_light = obj
            break
            
    if cyan_light:
        cyan_light.data.energy = 20
        cyan_light.data.keyframe_insert(data_path="energy", frame=1)
        # Add noise modifier to the fcurve to simulate a broken neon tube
        if cyan_light.data.animation_data and cyan_light.data.animation_data.action:
            fcurve = cyan_light.data.animation_data.action.fcurves.find('energy')
            if fcurve:
                noise = fcurve.modifiers.new('NOISE')
                noise.scale = 2.0
                noise.strength = 15.0
                noise.offset = 0.0

    # 5. Render Settings for Video
    scn = bpy.context.scene
    scn.frame_start = 1
    scn.frame_end = 150
    scn.render.fps = 24
    
    # Maintain AAA quality (64 samples with denoising is good for video)
    scn.cycles.samples = 64
    scn.render.resolution_x = 1920
    scn.render.resolution_y = 1080
    
    # Output to MP4
    out_dir = "e:/blender master/output"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    scn.render.filepath = os.path.join(out_dir, "neon_maze_cinematic.mp4")
    scn.render.image_settings.file_format = 'FFMPEG'
    scn.render.ffmpeg.format = 'MPEG4'
    scn.render.ffmpeg.codec = 'H264'
    scn.render.ffmpeg.constant_rate_factor = 'HIGH'
    
    # Render Animation
    print("--------------------------------------------------")
    print("Starting Video Render: 150 frames at 1080p, 64 samples")
    print("--------------------------------------------------")
    bpy.ops.render.render(animation=True)
    print("Animation Render Complete. Saved to output/neon_maze_cinematic.mp4")

if __name__ == "__main__":
    prepare_animation()
