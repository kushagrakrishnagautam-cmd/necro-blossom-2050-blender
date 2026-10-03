import bpy
import random
import math
from mathutils import Vector

# ------------------------------------------------------------
# Clean scene
# ------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 64
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.film_transparent = False

# World background
world = bpy.data.worlds.new("World")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.03, 0.05, 0.08, 1.0)
bg.inputs[1].default_value = 0.4
bpy.context.scene.world = world

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
def set_material(obj, color, metallic=0.0, roughness=0.5, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name=obj.name + "_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness

    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def add_cube(name, location, scale, color, metallic=0.0, roughness=0.5):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    set_material(obj, color, metallic, roughness)
    return obj


def add_cylinder(name, location, radius, depth, color, metallic=0.0, roughness=0.5, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    set_material(obj, color, metallic, roughness)
    return obj


def add_uv_sphere(name, location, radius, color, metallic=0.0, roughness=0.5, emission=None, emission_strength=0.0):
    bpy.ops.mesh.primitive_uv_sphere_add(location=location, segments=32, ring_count=16, radius=radius)
    obj = bpy.context.active_object
    obj.name = name
    set_material(obj, color, metallic, roughness, emission, emission_strength)
    return obj


def add_plane(name, location, scale, color):
    bpy.ops.mesh.primitive_plane_add(location=location, scale=scale)
    obj = bpy.context.active_object
    obj.name = name
    set_material(obj, color, 0.0, 0.85)
    return obj


def add_text_label(text, location, size=0.35, color=(1, 1, 1, 1), emission=(0.3, 0.8, 1, 1)):
    bpy.ops.object.text_add(location=location)
    txt = bpy.context.active_object
    txt.data.body = text
    txt.data.align_x = 'CENTER'
    txt.data.align_y = 'CENTER'
    txt.scale = (size, size, size)

    mat = bpy.data.materials.new(name=text + "_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Emission Color"].default_value = emission
    bsdf.inputs["Emission Strength"].default_value = 1.0
    txt.data.materials.append(mat)
    return txt


def add_vine(name, start, end, radius=0.05, segments=7):
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 8
    curve_data.resolution_u = 24

    spline = curve_data.splines.new(type='BEZIER')
    spline.bezier_points.add(segments - 1)

    pts = []
    p0 = Vector(start)
    p1 = Vector(end)
    direction = p1 - p0
    for i in range(segments):
        t = i / (segments - 1)
        point = p0.lerp(p1, t)
        offset = Vector((random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), 0.0))
        point += offset * (1.0 - abs(t - 0.5) * 1.2)
        point.z += math.sin(t * math.pi) * random.uniform(0.2, 0.8)
        pts.append(point)

    for i, bp in enumerate(spline.bezier_points):
        bp.co = pts[i]
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)

    vine_mat = bpy.data.materials.new(name=name + "_mat")
    vine_mat.use_nodes = True
    bsdf = vine_mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.10, 0.30, 0.22, 1.0)
    bsdf.inputs["Emission Color"].default_value = (0.18, 0.95, 1.0, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 0.55
    bsdf.inputs["Roughness"].default_value = 0.2

    obj.data.materials.append(vine_mat)
    return obj

# ------------------------------------------------------------
# Environment: city + alley
# ------------------------------------------------------------
# Ground
add_plane("AlleyGround", (0, 0, -0.05), (24, 18, 1), (0.22, 0.22, 0.24, 1.0))

# Back walls / building sides
add_cube("WallLeft", (-8, 0, 4), (1.0, 14.0, 7.0), (0.32, 0.33, 0.36, 1.0))
add_cube("WallRight", (8, 0, 4), (1.0, 14.0, 7.0), (0.32, 0.33, 0.36, 1.0))

# Overhead supports / slabs
for i in range(5):
    x = -7 + i * 3.5
    z = 5.5
    add_cube(f"Support_{i}", (x, -2, z), (0.6, 0.6, 3.2), (0.35, 0.37, 0.42, 1.0))
    add_cube(f"SupportTop_{i}", (x, -2, z + 2.3), (1.8, 1.3, 0.3), (0.45, 0.47, 0.52, 1.0))

# Distant city / upper towers
for i in range(9):
    x = -18 + i * 4.8
    y = 18
    height = random.uniform(6.0, 10.5)
    add_cube(f"CityTower_{i}", (x, y, height/2), (1.8, 1.8, height), (0.80, 0.84, 0.88, 1.0))

# Thin mirrors / glass facades
for i in range(9):
    x = -18 + i * 4.8
    y = 18.5
    add_cube(f"CityGlass_{i}", (x, y + 0.2, 7), (1.1, 0.1, 2.6), (0.52, 0.72, 0.90, 1.0), metallic=0.2, roughness=0.15)

# Hanging girders and pipes
for i in range(8):
    x = -9 + i * 2.5
    add_cylinder(f"Pipe_{i}", (x, -2.8, 6.0), 0.06, 6.0, (0.55, 0.58, 0.62, 1.0), metallic=0.8, roughness=0.2, rotation=(math.radians(90), 0, 0))

# ------------------------------------------------------------
# Sick vines / biotech corruption
# ------------------------------------------------------------
for i in range(10):
    start = (random.uniform(-5.5, 5.5), random.uniform(-6.2, 4.8), random.uniform(0.2, 2.5))
    end = (start[0] + random.uniform(-1.2, 1.2), start[1] + random.uniform(0.7, 2.2), random.uniform(4.5, 7.5))
    add_vine(f"CorruptVine_{i}", start, end, radius=random.uniform(0.04, 0.09), segments=8)

# Add a few thick vines spreading across wall
for i in range(5):
    start = (-6.8 + i * 2.7, -5.5, 0.2)
    end = (-6.2 + i * 2.6, 5.0, 5.8)
    add_vine(f"WallVine_{i}", start, end, radius=0.12, segments=10)

# ------------------------------------------------------------
# Holographic signage
# ------------------------------------------------------------
add_text_label("BREATHE DEEP", (0, -8.7, 2.8), size=0.28, color=(0.9, 0.95, 1, 1), emission=(0.2, 0.8, 1, 1))
add_text_label("ECO-CORP", (0, -8.1, 1.7), size=0.18, color=(0.9, 0.95, 1, 1), emission=(0.5, 1.0, 0.7, 1))

# ------------------------------------------------------------
# Drone
# ------------------------------------------------------------
def add_drone():
    add_uv_sphere("DroneBody", (3.0, -1.0, 4.5), 0.45, (0.93, 0.95, 0.98, 1.0), metallic=0.8, roughness=0.2)
    add_cylinder("DroneRing", (3.0, -1.0, 4.53), 0.7, 0.08, (0.30, 0.35, 0.42, 1.0), metallic=0.9, roughness=0.2)
    add_uv_sphere("DroneLens", (3.0, -1.0, 4.55), 0.12, (0.15, 0.15, 0.15, 1.0), metallic=0.2, roughness=0.4, emission=(1.0, 0.1, 0.12, 1.0), emission_strength=2.0)

    for angle in [0, 90, 180, 270]:
        rad = math.radians(angle)
        arm_x = math.cos(rad) * 0.75
        arm_y = math.sin(rad) * 0.75
        add_cylinder(f"DroneArm_{angle}", (3.0 + arm_x, -1.0 + arm_y, 4.5), 0.04, 1.1, (0.73, 0.74, 0.78, 1.0), metallic=0.7, roughness=0.25, rotation=(0, 0, rad))
        add_cylinder(f"DroneRotor_{angle}", (3.0 + arm_x, -1.0 + arm_y, 4.9), 0.11, 0.04, (0.36, 0.38, 0.42, 1.0), metallic=0.6, roughness=0.4, rotation=(math.radians(90), 0, 0))

add_drone()

# ------------------------------------------------------------
# Jeremy-like silhouette
# ------------------------------------------------------------
def add_human(name, location):
    add_cube(name + "_Torso", location, (0.35, 0.22, 0.7), (0.82, 0.86, 0.9, 1.0), roughness=0.7)
    add_uv_sphere(name + "_Head", (location[0], location[1], location[2] + 0.8), 0.22, (0.85, 0.73, 0.62, 1.0), roughness=0.9)
    add_uv_sphere(name + "_Mask", (location[0], location[1], location[2] + 0.82), 0.19, (0.15, 0.18, 0.25, 1.0), roughness=0.6)
    add_cube(name + "_BootL", (location[0] - 0.12, location[1], location[2] - 0.45), (0.12, 0.18, 0.12), (0.13, 0.12, 0.14, 1.0))
    add_cube(name + "_BootR", (location[0] + 0.12, location[1], location[2] - 0.45), (0.12, 0.18, 0.12), (0.13, 0.12, 0.14, 1.0))

add_human("Jeremy", (-1.0, -3.8, 0.58))

# ------------------------------------------------------------
# Camera + lighting
# ------------------------------------------------------------
camera_data = bpy.data.cameras.new("MainCamera")
camera = bpy.data.objects.new("MainCamera", camera_data)
bpy.context.collection.objects.link(camera)
camera.location = (18, -18, 7.5)
camera.rotation_euler = (math.radians(64), 0.0, math.radians(32))
bpy.context.scene.camera = camera

spot_data = bpy.data.lights.new(name="RedSearchlight", type='SPOT')
spot = bpy.data.objects.new("RedSearchlight", spot_data)
bpy.context.collection.objects.link(spot)
spot.location = (2.2, -2.8, 7.2)
spot.rotation_euler = (math.radians(90), 0, math.radians(10))
spot_data.energy = 2000
spot_data.color = (1.0, 0.12, 0.18)
spot_data.spot_size = math.radians(18)
spot_data.spot_blend = 0.7

area_data = bpy.data.lights.new(name="AreaFill", type='AREA')
area = bpy.data.objects.new("AreaFill", area_data)
bpy.context.collection.objects.link(area)
area.location = (-4, -11, 6)
area.rotation_euler = (math.radians(90), 0, 0)
area_data.energy = 800
area_data.shape = 'RECTANGLE'
area_data.size = 8
area_data.size_y = 8
area_data.color = (0.75, 0.85, 1.0)

for i in range(4):
    glow = bpy.data.lights.new(name=f"Glow_{i}", type='POINT')
    obj = bpy.data.objects.new(f"Glow_{i}", glow)
    bpy.context.collection.objects.link(obj)
    x = random.uniform(-5, 5)
    y = random.uniform(-8, 5)
    z = random.uniform(2, 6)
    obj.location = (x, y, z)
    glow.energy = 50
    glow.color = (0.2, 1.0, 0.9)

# ------------------------------------------------------------
# Simple keyframe camera move
# ------------------------------------------------------------
camera.keyframe_insert(data_path="location", frame=1)
camera.keyframe_insert(data_path="rotation_euler", frame=1)

camera.location = (8, -15, 5.8)
camera.rotation_euler = (math.radians(58), 0.0, math.radians(18))
camera.keyframe_insert(data_path="location", frame=90)
camera.keyframe_insert(data_path="rotation_euler", frame=90)

camera.location = (14, -18, 6.8)
camera.rotation_euler = (math.radians(62), 0.0, math.radians(28))
camera.keyframe_insert(data_path="location", frame=180)
camera.keyframe_insert(data_path="rotation_euler", frame=180)

# ------------------------------------------------------------
# Render settings cleanup
# ------------------------------------------------------------
scene.render.filepath = "//necro_blossom_2050_start.png"
scene.eevee.use_bloom = True
scene.eevee.taa_render_samples = 8
scene.eevee.use_gtao = True
scene.eevee.use_shadow_high_bitdepth = True

print("Scene generated: Neo-Eden lower maintenance slice ready.")
