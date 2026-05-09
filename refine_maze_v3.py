import bpy
import math
import random
import os

# ─────────────────────────────────────────────────────────
# REFINEMENT SCRIPT — runs AFTER build_neon_maze_env_v2.py
# Purpose: Push "good cyberpunk hallway" → "AAA cinematic frame with intent"
# Intent: "A player is approaching a dangerous unseen presence around the corner."
# ─────────────────────────────────────────────────────────

random.seed(42)  # Reproducible imperfection

# ── HELPER ──
def get_or_create_mat(name, base_color, roughness=0.8, metallic=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    b = mat.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = base_color
    b.inputs['Roughness'].default_value = roughness
    b.inputs['Metallic'].default_value = metallic
    return mat

# ─── 1. STORYTELLING ELEMENTS (exactly 3, no more) ───

# 1A. BROKEN WALL PANEL — right wall, mid-corridor
#     One panel displaced outward + rotated, exposing a gap
mat_wall = bpy.data.materials.get("Dark_Wall")

bpy.ops.mesh.primitive_cube_add(
    location=(1.55, 5.5, 0.6),
    scale=(0.08, 0.6, 0.5)
)
broken_panel = bpy.context.active_object
broken_panel.name = "Broken_Panel"
broken_panel.rotation_euler = (math.radians(4), math.radians(-8), math.radians(3))
broken_panel.data.materials.append(mat_wall)

# 1B. HANGING CABLE — from ceiling, near Y=8
#     Use a thin tilted cylinder instead of bezier for API compatibility
bpy.ops.mesh.primitive_cylinder_add(
    location=(0.4, 8.5, 2.0),
    radius=0.012,
    depth=2.2
)
cable = bpy.context.active_object
cable.name = "Hanging_Cable"
cable.rotation_euler = (math.radians(12), math.radians(5), math.radians(-3))

mat_cable = get_or_create_mat("Cable_Dark", (0.02, 0.02, 0.02, 1), roughness=0.6, metallic=0.7)
cable.data.materials.append(mat_cable)

# 1C. WALL STAIN / LEAK — dark drip mark on left wall near corner
#     Thin plane with a dark, slightly glossy material
bpy.ops.mesh.primitive_plane_add(
    location=(-1.33, 10.5, 1.8),
    size=0.01
)
stain = bpy.context.active_object
stain.name = "Wall_Stain"
stain.scale = (0.15, 0.6, 1.0)
stain.rotation_euler = (0, math.radians(90), 0)

mat_stain = bpy.data.materials.new(name="Stain_Drip")
mat_stain.use_nodes = True
s_ns = mat_stain.node_tree.nodes
s_bsdf = s_ns['Principled BSDF']
s_bsdf.inputs['Base Color'].default_value = (0.005, 0.005, 0.005, 1)
s_bsdf.inputs['Roughness'].default_value = 0.15  # Wet drip
s_bsdf.inputs['Alpha'].default_value = 0.7
stain.data.materials.append(mat_stain)


# ─── 2. FOREGROUND DEPTH — dark pillar edge barely visible at camera left ───

bpy.ops.mesh.primitive_cube_add(
    location=(-1.4, -0.3, 1.5),
    scale=(0.15, 0.3, 1.6)
)
fg_pillar = bpy.context.active_object
fg_pillar.name = "FG_Shadow_Pillar"
fg_pillar.data.materials.append(mat_wall)


# ─── 3. LIGHTING REFINEMENT ───

# 3A. Shift cyan light slightly off-center (break symmetry)
for obj in bpy.data.objects:
    if obj.type == 'LIGHT' and obj.location.x < -0.5 and obj.location.z > 1.5:
        obj.location.x -= 0.15
        obj.location.z -= 0.2
        # Reduce fill slightly to darken foreground
        obj.data.energy = 12
        break

# 3B. Push magenta harder as focal
for obj in bpy.data.objects:
    if obj.type == 'LIGHT' and obj.location.x > 0.5:
        obj.data.energy = 80  # Boost focal point
        # Tighten spread for harder shadows
        if hasattr(obj.data, 'spread'):
            obj.data.spread = math.radians(60)
        break

# 3C. Deepen non-essential shadows — add a negative-like blocker
#     A thin dark panel on the ceiling near camera to eat ambient bounce
bpy.ops.mesh.primitive_plane_add(
    location=(0, 1.0, 2.95),
    size=2.5
)
shadow_catcher = bpy.context.active_object
shadow_catcher.name = "Ceil_Shadow_Panel"
shadow_catcher.data.materials.append(mat_wall)


# ─── 4. BREAK REMAINING SYMMETRY ───

# Shift one existing pipe
for obj in bpy.data.objects:
    if "Pipe_1" in obj.name:
        obj.location.x += 0.08
        obj.rotation_euler[1] += 0.04
        break

# Rotate one left wall panel more aggressively
for obj in bpy.data.objects:
    if "Wall_L_2" in obj.name:
        obj.rotation_euler[2] += 0.05
        obj.location.x -= 0.03
        break


# ─── 5. RENDER ───

scn = bpy.context.scene
scn.cycles.samples = 128  # Higher quality for the money shot
scn.render.resolution_x = 1920
scn.render.resolution_y = 1080

out_dir = "e:/blender master/output"
if not os.path.exists(out_dir):
    os.makedirs(out_dir)
scn.render.filepath = os.path.join(out_dir, "maze_v3_refined.png")
bpy.ops.render.render(write_still=True)

print("V3 Refinement Complete. Rendered to maze_v3_refined.png")
