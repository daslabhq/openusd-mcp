#!/usr/bin/env python3
"""Generate example USD scenes for openusd-mcp demos.

Creates two USDA files that exercise all 8 MCP tools:
  - examples/desk_setup.usda       — scene hierarchy, materials, transforms
  - examples/product_configurator.usda — variant sets for product configuration

Requires: usd-core (pip install usd-core)

Usage:
    python scripts/generate_examples.py
"""

import os
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_material(stage, path, color, metallic=0.0, roughness=0.5, opacity=1.0):
    """Create a UsdPreviewSurface material and return it."""
    mat = UsdShade.Material.Define(stage, path)
    shader = UsdShade.Shader.Define(stage, f"{path}/PBRShader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
    mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return mat


def _bind_material(prim, material):
    """Bind a material to a prim."""
    UsdShade.MaterialBindingAPI.Apply(prim.GetPrim()).Bind(material)


def _set_xform(xformable, translate=None, rotate=None, scale=None):
    """Set translate/rotate/scale on an xformable prim."""
    if translate:
        xformable.AddTranslateOp().Set(Gf.Vec3d(*translate))
    if rotate:
        xformable.AddRotateXYZOp().Set(Gf.Vec3f(*rotate))
    if scale:
        xformable.AddScaleOp().Set(Gf.Vec3f(*scale))


def _add_mesh_box(stage, path, size_x, size_y, size_z):
    """Create a box as a Mesh prim (not a Cube) so mesh tools work on it."""
    mesh = UsdGeom.Mesh.Define(stage, path)

    hx, hy, hz = size_x / 2, size_y / 2, size_z / 2

    # 8 vertices of a box
    points = [
        (-hx, -hy, -hz), ( hx, -hy, -hz), ( hx,  hy, -hz), (-hx,  hy, -hz),  # bottom
        (-hx, -hy,  hz), ( hx, -hy,  hz), ( hx,  hy,  hz), (-hx,  hy,  hz),  # top
    ]
    mesh.GetPointsAttr().Set([Gf.Vec3f(*p) for p in points])

    # 6 faces, 4 vertices each
    mesh.GetFaceVertexCountsAttr().Set([4, 4, 4, 4, 4, 4])
    mesh.GetFaceVertexIndicesAttr().Set([
        0, 3, 2, 1,  # bottom
        4, 5, 6, 7,  # top
        0, 1, 5, 4,  # front
        2, 3, 7, 6,  # back
        0, 4, 7, 3,  # left
        1, 2, 6, 5,  # right
    ])

    mesh.GetExtentAttr().Set([Gf.Vec3f(-hx, -hy, -hz), Gf.Vec3f(hx, hy, hz)])
    return mesh


def _add_mesh_cylinder(stage, path, radius, height, segments=16):
    """Create a cylinder as a Mesh prim."""
    import math
    mesh = UsdGeom.Mesh.Define(stage, path)

    points = []
    face_vertex_counts = []
    face_vertex_indices = []

    # Bottom center = 0, top center = 1
    points.append(Gf.Vec3f(0, 0, 0))
    points.append(Gf.Vec3f(0, 0, height))

    # Ring vertices: bottom ring starts at index 2, top ring at 2 + segments
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        points.append(Gf.Vec3f(x, y, 0))       # bottom ring
        points.append(Gf.Vec3f(x, y, height))   # top ring

    # Side faces (quads)
    for i in range(segments):
        bl = 2 + i * 2          # bottom-left
        br = 2 + ((i + 1) % segments) * 2  # bottom-right
        tl = bl + 1             # top-left
        tr = br + 1             # top-right
        face_vertex_counts.append(4)
        face_vertex_indices.extend([bl, br, tr, tl])

    # Bottom cap (triangle fan)
    for i in range(segments):
        curr = 2 + i * 2
        nxt = 2 + ((i + 1) % segments) * 2
        face_vertex_counts.append(3)
        face_vertex_indices.extend([0, nxt, curr])

    # Top cap (triangle fan)
    for i in range(segments):
        curr = 2 + i * 2 + 1
        nxt = 2 + ((i + 1) % segments) * 2 + 1
        face_vertex_counts.append(3)
        face_vertex_indices.extend([1, curr, nxt])

    mesh.GetPointsAttr().Set(points)
    mesh.GetFaceVertexCountsAttr().Set(face_vertex_counts)
    mesh.GetFaceVertexIndicesAttr().Set(face_vertex_indices)
    mesh.GetExtentAttr().Set([Gf.Vec3f(-radius, -radius, 0), Gf.Vec3f(radius, radius, height)])
    return mesh


# ---------------------------------------------------------------------------
# Scene 1: Desk Setup
# ---------------------------------------------------------------------------

def generate_desk_setup():
    """A desk scene with table, monitor, keyboard, and mug.

    Demonstrates: inspect, get_prim, get_materials, get_transforms, scene_stats, export_mesh
    """
    path = str(EXAMPLES_DIR / "desk_setup.usda")
    stage = Usd.Stage.CreateNew(path)

    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)  # centimeters

    root = UsdGeom.Xform.Define(stage, "/Desk")

    # -- Materials --
    wood = _add_material(stage, "/Desk/Materials/Wood",
                         color=(0.55, 0.35, 0.17), roughness=0.7)
    metal = _add_material(stage, "/Desk/Materials/Metal",
                          color=(0.7, 0.7, 0.72), metallic=0.9, roughness=0.2)
    screen_mat = _add_material(stage, "/Desk/Materials/Screen",
                               color=(0.05, 0.05, 0.08), metallic=0.0, roughness=0.1)
    ceramic = _add_material(stage, "/Desk/Materials/Ceramic",
                            color=(0.9, 0.9, 0.85), roughness=0.4)
    plastic = _add_material(stage, "/Desk/Materials/DarkPlastic",
                            color=(0.15, 0.15, 0.15), roughness=0.5)

    # -- Table (120 x 60 x 3 cm top, 75cm legs) --
    table = UsdGeom.Xform.Define(stage, "/Desk/Table")

    tabletop = _add_mesh_box(stage, "/Desk/Table/Top", 120, 60, 3)
    _set_xform(tabletop, translate=(0, 75, 0))
    _bind_material(tabletop, wood)

    for i, (lx, ly) in enumerate([(-55, -25), (55, -25), (55, 25), (-55, 25)]):
        leg = _add_mesh_box(stage, f"/Desk/Table/Leg{i+1}", 4, 4, 75)
        _set_xform(leg, translate=(lx, 37.5, ly))
        _bind_material(leg, metal)

    # -- Monitor --
    monitor = UsdGeom.Xform.Define(stage, "/Desk/Monitor")
    _set_xform(monitor, translate=(0, 76.5, -15))

    screen = _add_mesh_box(stage, "/Desk/Monitor/Screen", 60, 35, 1.5)
    _set_xform(screen, translate=(0, 25, 0))
    _bind_material(screen, screen_mat)

    stand = _add_mesh_box(stage, "/Desk/Monitor/Stand", 8, 20, 2)
    _set_xform(stand, translate=(0, 5, 0))
    _bind_material(stand, metal)

    base = _add_mesh_box(stage, "/Desk/Monitor/Base", 25, 1.5, 15)
    _bind_material(base, metal)

    # -- Keyboard --
    keyboard = _add_mesh_box(stage, "/Desk/Keyboard", 44, 1.5, 14)
    _set_xform(keyboard, translate=(0, 77, 10))
    _bind_material(keyboard, plastic)

    # -- Mug --
    mug_xform = UsdGeom.Xform.Define(stage, "/Desk/Mug")
    _set_xform(mug_xform, translate=(40, 76.5, 10))

    mug = _add_mesh_cylinder(stage, "/Desk/Mug/Body", radius=4, height=9, segments=16)
    _bind_material(mug, ceramic)

    stage.GetRootLayer().Save()
    print(f"  Created {path}")
    return path


# ---------------------------------------------------------------------------
# Scene 2: Product Configurator
# ---------------------------------------------------------------------------

def generate_product_configurator():
    """A product with size, color, and finish variants.

    Demonstrates: list_variants, set_variant, plus all inspection tools.
    """
    path = str(EXAMPLES_DIR / "product_configurator.usda")
    stage = Usd.Stage.CreateNew(path)

    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)  # centimeters

    root = UsdGeom.Xform.Define(stage, "/Product")
    root_prim = stage.GetPrimAtPath("/Product")

    # -- The body mesh (a box representing a device/speaker) --
    body = _add_mesh_box(stage, "/Product/Body", 12, 8, 12)
    _set_xform(body, translate=(0, 4, 0))

    accent = _add_mesh_box(stage, "/Product/Accent", 12.2, 0.5, 12.2)
    _set_xform(accent, translate=(0, 7, 0))

    grille = _add_mesh_box(stage, "/Product/Grille", 10, 5, 0.3)
    _set_xform(grille, translate=(0, 4, 6.15))

    # -- Size variants --
    size_vs = root_prim.GetVariantSets().AddVariantSet("size")
    sizes = {
        "small":  (0.7, 0.7, 0.7),
        "medium": (1.0, 1.0, 1.0),
        "large":  (1.4, 1.4, 1.4),
    }
    for name, scale in sizes.items():
        size_vs.AddVariant(name)
        size_vs.SetVariantSelection(name)
        with size_vs.GetVariantEditContext():
            xform = UsdGeom.Xformable(root_prim)
            xform.AddScaleOp(opSuffix="size").Set(Gf.Vec3f(*scale))
    size_vs.SetVariantSelection("medium")

    # -- Color variants (applied to body material) --
    color_vs = root_prim.GetVariantSets().AddVariantSet("color")
    colors = {
        "midnight": ((0.08, 0.08, 0.10), 0.0),   # (diffuse, metallic)
        "silver":   ((0.75, 0.75, 0.77), 0.85),
        "gold":     ((0.83, 0.69, 0.22), 0.90),
        "red":      ((0.72, 0.08, 0.08), 0.15),
    }
    for name, (color, met) in colors.items():
        color_vs.AddVariant(name)
        color_vs.SetVariantSelection(name)
        with color_vs.GetVariantEditContext():
            mat = _add_material(
                stage,
                f"/Product/Materials/{name.capitalize()}",
                color=color, metallic=met, roughness=0.3,
            )
            _bind_material(body, mat)
    color_vs.SetVariantSelection("midnight")

    # -- Finish variants (roughness) --
    finish_vs = root_prim.GetVariantSets().AddVariantSet("finish")
    finishes = {
        "matte":  0.8,
        "satin":  0.4,
        "glossy": 0.1,
    }
    for name, roughness in finishes.items():
        finish_vs.AddVariant(name)
        finish_vs.SetVariantSelection(name)
        with finish_vs.GetVariantEditContext():
            mat = _add_material(
                stage,
                f"/Product/Materials/Finish{name.capitalize()}",
                color=(0.08, 0.08, 0.10), roughness=roughness,
            )
            _bind_material(body, mat)
    finish_vs.SetVariantSelection("satin")

    # -- Accent material (always metallic gray) --
    accent_mat = _add_material(stage, "/Product/Materials/AccentMetal",
                               color=(0.5, 0.5, 0.52), metallic=0.95, roughness=0.15)
    _bind_material(accent, accent_mat)

    # -- Grille material (dark perforated look) --
    grille_mat = _add_material(stage, "/Product/Materials/Grille",
                               color=(0.12, 0.12, 0.12), metallic=0.3, roughness=0.6)
    _bind_material(grille, grille_mat)

    stage.GetRootLayer().Save()
    print(f"  Created {path}")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating example scenes...")
    generate_desk_setup()
    generate_product_configurator()
    print("Done.")
