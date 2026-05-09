import bpy
import math
import random
import os
import mathutils

def prepare_fps_animation():
    # 1. Build environment
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

    cam = bpy.context.scene.camera
    
    # 2. Animate the Camera (Walking forward + Head bob)
    if cam:
        cam.location = (0, -1.0, 1.6)
        cam.keyframe_insert(data_path="location", frame=1)
        cam.location = (0, 7.5, 1.6)
        cam.keyframe_insert(data_path="location", frame=150)
        
        # Add head bobbing
        if cam.animation_data and cam.animation_data.action:
            for fcurve in cam.animation_data.action.fcurves:
                if fcurve.data_path == "location" and fcurve.array_index == 2: # Z axis (up/down)
                    noise = fcurve.modifiers.new('NOISE')
                    noise.scale = 3.0
                    noise.strength = 0.04
                    noise.offset = 0.0
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'LINEAR'
                    
    # 3. Light Flicker
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

    # 4. Import GLB and attach to camera (FPS POV)
    glb_path = "e:/blender master/Copilot3D-f8972524-c93f-4559-9872-1f6dd8511979.glb"
    if os.path.exists(glb_path):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.import_scene.gltf(filepath=glb_path)
        
        imported_objects = bpy.context.selected_objects
        
        if imported_objects:
            # Calculate size to normalize scale
            min_co = [float('inf'), float('inf'), float('inf')]
            max_co = [float('-inf'), float('-inf'), float('-inf')]
            has_mesh = False
            for obj in imported_objects:
                if obj.type == 'MESH':
                    has_mesh = True
                    for v in obj.bound_box:
                        world_v = obj.matrix_world @ mathutils.Vector(v)
                        for i in range(3):
                            min_co[i] = min(min_co[i], world_v[i])
                            max_co[i] = max(max_co[i], world_v[i])
            scale_factor = 1.0
            if has_mesh:
                size = max(max_co[0] - min_co[0], max_co[1] - min_co[1], max_co[2] - min_co[2])
                if size > 0:
                    scale_factor = 0.4 / size # Normalize max dimension to 0.4 meters (handheld size)

            # Create a control empty
            bpy.ops.object.empty_add(type='PLAIN_AXES')
            hand_empty = bpy.context.active_object
            hand_empty.name = "FPS_Hand_Control"
            
            # Parent imported objects to the empty
            for obj in imported_objects:
                # only parent top-level objects to avoid double transforms
                if obj.parent is None:
                    obj.parent = hand_empty
                
            # Parent the empty to the camera
            hand_empty.parent = cam
            
            # Apply normalized scale
            hand_empty.scale = (scale_factor, scale_factor, scale_factor)
            
            # Position: Right (+X), Down (-Y), Forward (-Z) relative to camera
            hand_empty.location = (0.2, -0.15, -0.4) 
            
            # Default rotation (you may need to tweak this if the object points backward)
            hand_empty.rotation_euler = (0, 0, 0)
            
            # Add a slight hand sway/breathing independent of the camera
            hand_empty.keyframe_insert(data_path="rotation_euler", frame=1)
            hand_empty.keyframe_insert(data_path="location", frame=1)
            
            if hand_empty.animation_data and hand_empty.animation_data.action:
                for fcurve in hand_empty.animation_data.action.fcurves:
                    noise = fcurve.modifiers.new('NOISE')
                    noise.scale = 15.0
                    noise.strength = 0.02
                    noise.offset = random.uniform(0, 100)
    else:
        print("GLB File not found!")
    
    # 5. FAST PREVIEW RENDER SETTINGS (EEVEE)
    scn = bpy.context.scene
    scn.render.engine = 'BLENDER_EEVEE_NEXT'
    scn.eevee.use_bloom = True
    scn.eevee.bloom_intensity = 0.05
    
    scn.frame_start = 1
    scn.frame_end = 150
    scn.render.fps = 24
    
    scn.render.resolution_x = 1280
    scn.render.resolution_y = 720
    scn.render.resolution_percentage = 50
    
    out_dir = "e:/blender master/output"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    scn.render.filepath = os.path.join(out_dir, "fps_preview_neon_maze.mp4")
    scn.render.image_settings.file_format = 'FFMPEG'
    scn.render.ffmpeg.format = 'MPEG4'
    scn.render.ffmpeg.codec = 'H264'
    scn.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    
    print("Starting FPS EEVEE Preview Render...")
    bpy.ops.render.render(animation=True)
    print("FPS Preview Complete!")

if __name__ == "__main__":
    prepare_fps_animation()
