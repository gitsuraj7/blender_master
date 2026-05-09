import bpy, bmesh, math, random, os
from mathutils import Vector

OUTPUT = "e:/blender master/ancient_ruins/output/sacred_cavern_v10_final.png"

# ============================================================
# STEP 1 — WORLD RESET
# ============================================================
def step1_reset():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for block in [bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.textures]:
        for item in block:
            block.remove(item)
    
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.render.resolution_x = 1920
    s.render.resolution_y = 1080
    s.cycles.samples = 128
    s.cycles.use_denoising = True
    s.unit_settings.system = 'METRIC'
    s.view_settings.view_transform = 'AgX'
    s.view_settings.look = 'AgX - High Contrast'
    print("[STEP 1] World reset complete.")

# ============================================================
# STEP 2 — CAMERA & LIGHT FIRST
# ============================================================
def step2_camera_and_light():
    # Camera
    bpy.ops.object.camera_add(location=(0, -45, 8))
    cam = bpy.context.active_object
    cam.name = "SacredCamera"
    cam.data.lens = 24
    
    # Point at (0, 0, 15) via Track To constraint
    bpy.ops.object.empty_add(location=(0, 5, 12))
    target = bpy.context.active_object
    target.name = "CameraTarget"
    
    bpy.context.view_layer.objects.active = cam
    cam.select_set(True)
    bpy.ops.object.constraint_add(type='TRACK_TO')
    cam.constraints["Track To"].target = target
    cam.constraints["Track To"].track_axis = 'TRACK_NEGATIVE_Z'
    cam.constraints["Track To"].up_axis = 'UP_Y'
    bpy.context.scene.camera = cam
    
    # God-ray spot — aimed at monument center (0, 10, 5)
    bpy.ops.object.light_add(type='SPOT', location=(2, 8, 100))
    spot = bpy.context.active_object
    spot.name = "GodRay"
    spot.data.energy = 8000000
    spot.data.spot_size = math.radians(12)
    spot.data.spot_blend = 0.15
    spot.data.shadow_soft_size = 1.0
    spot.data.use_shadow = True
    # Point at monument
    direction = Vector((0, 10, 5)) - Vector((2, 8, 100))
    spot.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    
    # Subtle ambient fill — cold teal bounce
    bpy.ops.object.light_add(type='AREA', location=(-30, -30, 40))
    fill = bpy.context.active_object
    fill.name = "AmbientFill"
    fill.data.energy = 500
    fill.data.color = (0.4, 0.6, 0.8)
    fill.data.size = 30
    fill.rotation_euler = (math.radians(45), 0, math.radians(30))
    
    print("[STEP 2] Camera & god-ray placed. SACRED. DO NOT MOVE.")

# ============================================================
# STEP 3 — THE CATHEDRAL VOLUME (6 pillars)
# ============================================================
def step3_cathedral():
    random.seed(42)
    pillar_rotations = []
    
    positions = []
    for x in [-25, 25]:
        for y_offset in [0, 20, 40]:
            positions.append((x, y_offset))
    
    for idx, (px, py) in enumerate(positions):
        bpy.ops.mesh.primitive_cube_add(location=(px, py, 30))
        p = bpy.context.active_object
        p.name = f"Pillar_{idx}"
        
        h_scale = random.uniform(0.85, 1.1)
        p.scale = (2, 2, 30 * h_scale)
        bpy.ops.object.transform_apply(scale=True)
        
        # Subdivide for displacement to work
        sub = p.modifiers.new("Subdivide", 'SUBSURF')
        sub.levels = 2
        sub.render_levels = 2
        
        # Bevel — BREAK STRAIGHT EDGES
        bev = p.modifiers.new("Bevel", 'BEVEL')
        bev.width = 0.1
        bev.segments = 3
        
        # Displace — BREAK UNIFORM SURFACES
        tex = bpy.data.textures.new(f"PillarCloud_{idx}", 'CLOUDS')
        tex.noise_scale = 2.0
        disp = p.modifiers.new("Displace", 'DISPLACE')
        disp.texture = tex
        disp.strength = 0.3
        
        # Random tilt — NO TWO PILLARS IDENTICAL
        tilt_x = math.radians(random.uniform(-2, 2))
        tilt_z = math.radians(random.uniform(-2, 2))
        p.rotation_euler = (tilt_x, 0, tilt_z)
        pillar_rotations.append((round(tilt_x, 8), round(tilt_z, 8)))
        
        for poly in p.data.polygons:
            poly.use_smooth = True
    
    unique = set(pillar_rotations)
    assert len(unique) == len(pillar_rotations), "VIOLATION: Duplicate pillar rotations!"
    print(f"[STEP 3] 6 pillars built. All rotations unique.")

# ============================================================
# STEP 4 — THE HERO ASSET
# ============================================================
def step4_hero_asset():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=64, radius=1, location=(0, 10, 0))
    hero = bpy.context.active_object
    hero.name = "AncientMonument"
    
    # Scale FIRST, then apply, then displace
    hero.scale = (9, 7, 8)
    bpy.ops.object.transform_apply(scale=True)
    
    # Displace 1: Musgrave — large erosion
    tex1 = bpy.data.textures.new("Musgrave_Hero", 'MUSGRAVE')
    tex1.musgrave_type = 'RIDGED_MULTIFRACTAL'
    tex1.noise_scale = 2.0
    disp1 = hero.modifiers.new("Musgrave", 'DISPLACE')
    disp1.texture = tex1
    disp1.strength = 2.5
    disp1.mid_level = 0.5
    
    # Displace 2: Voronoi — surface pitting
    tex2 = bpy.data.textures.new("Voronoi_Hero", 'VORONOI')
    tex2.noise_scale = 8.0
    disp2 = hero.modifiers.new("Voronoi", 'DISPLACE')
    disp2.texture = tex2
    disp2.strength = 0.8
    disp2.mid_level = 0.5
    
    for poly in hero.data.polygons:
        poly.use_smooth = True
    
    print(f"[STEP 4] Hero monument at (0,10,0)")

# ============================================================
# STEP 5 — MATERIALS
# ============================================================
def step5_materials():
    # --- STONE ---
    stone = bpy.data.materials.new("AncientStone")
    stone.use_nodes = True
    nt = stone.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes.get("Principled BSDF")
    
    bsdf.inputs['Base Color'].default_value = (0.08, 0.07, 0.06, 1)
    bsdf.inputs['Roughness'].default_value = 0.92
    
    # Bump
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.6
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 800
    noise.inputs['Detail'].default_value = 8
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    
    # Moss mask: Normal DOT (0,0,1) 
    geom = nodes.new('ShaderNodeNewGeometry')
    dot = nodes.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    links.new(geom.outputs['Normal'], dot.inputs[0])
    dot.inputs[1].default_value = (0, 0, 1)
    
    # Clamp to make sharp mask
    clamp = nodes.new('ShaderNodeClamp')
    clamp.inputs['Min'].default_value = 0.4
    clamp.inputs['Max'].default_value = 1.0
    links.new(dot.outputs['Value'], clamp.inputs['Value'])
    
    # Color ramp for smooth transition
    ramp = nodes.new('ShaderNodeMapRange')
    ramp.inputs['From Min'].default_value = 0.4
    ramp.inputs['From Max'].default_value = 0.8
    links.new(clamp.outputs['Result'], ramp.inputs['Value'])
    
    # Mix stone + moss
    mix = nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs[6].default_value = (0.08, 0.07, 0.06, 1)
    mix.inputs[7].default_value = (0.12, 0.18, 0.06, 1)
    links.new(ramp.outputs['Result'], mix.inputs['Factor'])
    links.new(mix.outputs[2], bsdf.inputs['Base Color'])
    
    # --- WATER ---
    water = bpy.data.materials.new("BlackMirrorWater")
    water.use_nodes = True
    wbsdf = water.node_tree.nodes.get("Principled BSDF")
    wbsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
    wbsdf.inputs['Roughness'].default_value = 0.0
    wbsdf.inputs['IOR'].default_value = 1.333
    
    # Micro-ripple
    wbump = water.node_tree.nodes.new('ShaderNodeBump')
    wbump.inputs['Strength'].default_value = 0.01
    wnoise = water.node_tree.nodes.new('ShaderNodeTexNoise')
    wnoise.inputs['Scale'].default_value = 500
    water.node_tree.links.new(wnoise.outputs['Fac'], wbump.inputs['Height'])
    water.node_tree.links.new(wbump.outputs['Normal'], wbsdf.inputs['Normal'])
    
    # Apply stone to geometry
    for obj in bpy.data.objects:
        if obj.name.startswith("Pillar_") or obj.name == "AncientMonument":
            if len(obj.data.materials) == 0:
                obj.data.materials.append(stone)
            else:
                obj.data.materials[0] = stone
    
    print("[STEP 5] Materials applied.")
    return stone, water

# ============================================================
# STEP 6 — WATER PLANE + DEBRIS
# ============================================================
def step6_water(water_mat, stone_mat):
    bpy.ops.mesh.primitive_plane_add(size=160, location=(0, 0, -0.5))
    plane = bpy.context.active_object
    plane.name = "WaterPlane"
    plane.data.materials.append(water_mat)
    
    random.seed(99)
    for i in range(5):
        rx = random.uniform(-20, 20)
        ry = random.uniform(-15, 35)
        bpy.ops.mesh.primitive_cube_add(location=(rx, ry, -0.2))
        rock = bpy.context.active_object
        rock.name = f"Debris_{i}"
        rock.scale = (random.uniform(0.5, 2.0), random.uniform(0.5, 2.0), random.uniform(0.3, 1.0))
        bpy.ops.object.transform_apply(scale=True)
        
        tex = bpy.data.textures.new(f"DebrisNoise_{i}", 'CLOUDS')
        tex.noise_scale = 1.5
        disp = rock.modifiers.new("Displace", 'DISPLACE')
        disp.texture = tex
        disp.strength = 0.3
        
        rock.rotation_euler = (
            math.radians(random.uniform(-15, 15)),
            math.radians(random.uniform(-15, 15)),
            math.radians(random.uniform(0, 360))
        )
        rock.data.materials.append(stone_mat)
        for poly in rock.data.polygons:
            poly.use_smooth = True
    
    print("[STEP 6] Water + 5 debris chunks placed.")

# ============================================================
# STEP 7 — VOLUMETRIC ATMOSPHERE
# ============================================================
def step7_volumetrics():
    bpy.ops.mesh.primitive_cube_add(location=(0, 10, 35))
    vol = bpy.context.active_object
    vol.name = "VolumeDomain"
    vol.scale = (50, 50, 40)
    bpy.ops.object.transform_apply(scale=True)
    vol.display_type = 'WIRE'
    
    vol_mat = bpy.data.materials.new("CavernVolume")
    vol_mat.use_nodes = True
    vnt = vol_mat.node_tree
    for n in vnt.nodes:
        vnt.nodes.remove(n)
    
    out = vnt.nodes.new('ShaderNodeOutputMaterial')
    vol_shader = vnt.nodes.new('ShaderNodeVolumePrincipled')
    vol_shader.inputs['Density'].default_value = 0.002
    vol_shader.inputs['Anisotropy'].default_value = 0.85
    vol_shader.inputs['Color'].default_value = (0.9, 0.85, 0.7, 1)
    
    vnt.links.new(vol_shader.outputs[0], out.inputs['Volume'])
    vol.data.materials.append(vol_mat)
    
    # Also set world to dark blue-black for ambient
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    wnt = world.node_tree
    for n in wnt.nodes:
        wnt.nodes.remove(n)
    bg = wnt.nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.005, 0.008, 0.015, 1)
    bg.inputs['Strength'].default_value = 0.5
    out_w = wnt.nodes.new('ShaderNodeOutputWorld')
    wnt.links.new(bg.outputs[0], out_w.inputs[0])
    
    print("[STEP 7] Volume domain + dark ambient world set.")

# ============================================================
# STEP 8 — THE FIGURE
# ============================================================
def step8_figure():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.8, location=(3, -18, 0.4))
    fig = bpy.context.active_object
    fig.name = "Figure"
    
    fig_mat = bpy.data.materials.new("FigureBlack")
    fig_mat.use_nodes = True
    fbsdf = fig_mat.node_tree.nodes.get("Principled BSDF")
    fbsdf.inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1)
    fbsdf.inputs['Roughness'].default_value = 0.95
    fig.data.materials.append(fig_mat)
    
    bpy.ops.object.light_add(type='POINT', location=(2, -17, 3))
    rim = bpy.context.active_object
    rim.name = "FigureRimLight"
    rim.data.energy = 800
    rim.data.color = (1.0, 0.85, 0.5)
    
    print("[STEP 8] Figure + rim light placed.")

# ============================================================
# STEP 9 — VERIFY
# ============================================================
def step9_verify():
    checks = []
    
    rotations = []
    for obj in bpy.data.objects:
        if obj.name.startswith("Pillar_"):
            rot = (round(obj.rotation_euler.x, 6), round(obj.rotation_euler.z, 6))
            rotations.append(rot)
    checks.append(("Unique pillar rotations", len(set(rotations)) == len(rotations)))
    
    hero = bpy.data.objects.get("AncientMonument")
    if hero:
        dims = hero.dimensions
        checks.append((f"Monument longest axis = {max(dims):.1f}m", max(dims) >= 10))
    
    wmat = bpy.data.materials.get("BlackMirrorWater")
    if wmat:
        bc = wmat.node_tree.nodes.get("Principled BSDF").inputs['Base Color'].default_value
        checks.append(("Water is absolute black", bc[0] == 0 and bc[1] == 0 and bc[2] == 0))
    
    cam = bpy.context.scene.camera
    if cam:
        loc = cam.location
        checks.append((f"Camera at ({loc.x:.0f},{loc.y:.0f},{loc.z:.0f})",
                       abs(loc.x) < 1 and abs(loc.y + 45) < 1 and abs(loc.z - 8) < 1))
    
    godray = bpy.data.objects.get("GodRay")
    if godray:
        angle_deg = math.degrees(godray.data.spot_size)
        checks.append((f"God-ray angle = {angle_deg:.1f}°", angle_deg <= 15))
    
    print("\n" + "="*60)
    print("STEP 9 — VERIFICATION REPORT")
    print("="*60)
    all_pass = True
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            all_pass = False
    print("="*60)
    return all_pass

# ============================================================
# STEP 10 — RENDER
# ============================================================
def step10_render():
    s = bpy.context.scene
    s.use_nodes = True
    tree = s.node_tree
    for n in tree.nodes:
        tree.nodes.remove(n)
    
    rl = tree.nodes.new('CompositorNodeRLayers')
    comp = tree.nodes.new('CompositorNodeComposite')
    
    glare = tree.nodes.new('CompositorNodeGlare')
    glare.glare_type = 'FOG_GLOW'
    glare.threshold = 0.8
    glare.size = 7
    glare.quality = 'HIGH'
    
    tree.links.new(rl.outputs['Image'], glare.inputs['Image'])
    tree.links.new(glare.outputs['Image'], comp.inputs['Image'])
    
    s.render.filepath = OUTPUT
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print(f"\n[STEP 10] Render saved to {OUTPUT}")

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("SACRED CAVERN V10 — THE ONE RULE:")
    print("Break every straight line and every uniform surface.")
    print("="*60 + "\n")
    
    step1_reset()
    step2_camera_and_light()
    step3_cathedral()
    step4_hero_asset()
    stone_mat, water_mat = step5_materials()
    step6_water(water_mat, stone_mat)
    step7_volumetrics()
    step8_figure()
    
    if step9_verify():
        step10_render()
    else:
        print("ABORTING — Fix failures first.")
