import bpy
import bmesh
import math
import os
import random

# --- MASTERPIECE V10: THE FINAL POLISH ---
OUTPUT_PATH = "e:/blender master/ancient_ruins/output/sacred_cavern_v10.png"

def reset():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def create_materials():
    mats = {}
    stone = bpy.data.materials.new("PolishedStone")
    stone.use_nodes = True
    stone.node_tree.nodes.get("Principled BSDF").inputs['Base Color'].default_value = (0.08, 0.08, 0.08, 1)
    stone.node_tree.nodes.get("Principled BSDF").inputs['Roughness'].default_value = 0.7
    mats['stone'] = stone
    
    water = bpy.data.materials.new("MirrorWater")
    water.use_nodes = True
    w_bsdf = water.node_tree.nodes.get("Principled BSDF")
    w_bsdf.inputs['Base Color'].default_value = (0.002, 0.005, 0.01, 1)
    w_bsdf.inputs['Roughness'].default_value = 0.05
    mats['water'] = water
    
    moss = bpy.data.materials.new("VividMoss")
    moss.use_nodes = True
    moss.node_tree.nodes.get("Principled BSDF").inputs['Base Color'].default_value = (0.05, 0.15, 0.02, 1)
    mats['moss'] = moss
    
    return mats

def sculpt_face(mat):
    # Optimized sculptor for V10
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 30, 8))
    obj = bpy.context.active_object
    obj.scale = (4, 3, 6)
    bpy.ops.object.transform_apply(scale=True)
    sub = obj.modifiers.new(name="Sub", type='SUBSURF')
    sub.levels = 4
    bpy.ops.object.modifier_apply(modifier="Sub")
    
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for v in bm.verts:
        if v.co.y < 30: # Front
            x, z = v.co.x, v.co.z
            if 6 < z < 9 and 0.5 < abs(x) < 2: v.co.y += 0.8 # Sockets
            elif 9.5 < z < 11 and abs(x) < 2.5: v.co.y -= 0.6 # Brow
            elif 4 < z < 10 and abs(x) < 0.8: v.co.y -= 1.2 # Nose
    bm.to_mesh(obj.data)
    bm.free()
    
    obj.data.materials.append(mat)
    for p in obj.data.polygons: p.use_smooth = True
    return obj

def build():
    reset()
    mats = create_materials()
    
    # Floor
    bpy.ops.mesh.primitive_plane_add(size=1000)
    bpy.context.active_object.data.materials.append(mats['water'])
    
    # Pillars
    for x in [-30, 30]:
        for y in [0, 60, 120]:
            bpy.ops.mesh.primitive_cube_add(location=(x, y, 40))
            p = bpy.context.active_object
            p.scale = (5, 5, 40)
            p.data.materials.append(mats['stone'])
            if y < 120:
                bpy.ops.mesh.primitive_cube_add(location=(x, y+30, 80))
                b = bpy.context.active_object
                b.scale = (3, 30, 1)
                b.data.materials.append(mats['stone'])

    # The Head
    head = sculpt_face(mats['moss'])
    
    # Scale Figure
    bpy.ops.mesh.primitive_cube_add(location=(0, -10, 1.8))
    fig = bpy.context.active_object
    fig.scale = (0.5, 0.5, 1.8)
    
    # Lighting
    bpy.ops.object.light_add(type='SPOT', location=(0, 25, 100))
    spot = bpy.context.active_object
    spot.data.energy = 10000000
    spot.data.spot_size = math.radians(40)
    spot.data.spot_blend = 1.0
    
    # Fog
    bpy.context.scene.world.use_nodes = True
    nodes = bpy.context.scene.world.node_tree.nodes
    for n in nodes: nodes.remove(n)
    w_out = nodes.new('ShaderNodeOutputWorld')
    w_vol = nodes.new('ShaderNodeVolumeScatter')
    w_vol.inputs['Density'].default_value = 0.005
    bpy.context.scene.world.node_tree.links.new(w_vol.outputs[0], w_out.inputs[1])

    # Camera
    bpy.ops.object.camera_add(location=(0, -40, 10), rotation=(math.radians(85), 0, 0))
    bpy.context.scene.camera = bpy.context.active_object
    bpy.context.scene.camera.data.lens = 20

    # Render
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 256
    bpy.context.scene.view_settings.view_transform = 'AgX'
    bpy.context.scene.view_settings.look = 'AgX - High Contrast'

if __name__ == "__main__":
    build()
    bpy.context.scene.render.filepath = OUTPUT_PATH
    bpy.ops.render.render(write_still=True)
