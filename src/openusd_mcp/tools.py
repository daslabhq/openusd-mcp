"""USD scene inspection and manipulation tools.

Each function corresponds to an MCP tool. They take file paths and prim paths
as input and return dicts suitable for JSON serialization.

Requires: pip install usd-core
"""

from __future__ import annotations

import os
import struct
from typing import Any, Optional


def _open_stage(path: str):
    """Open a USD stage from a file path."""
    from pxr import Usd

    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    stage = Usd.Stage.Open(path)
    if stage is None:
        raise ValueError(f"Failed to open USD stage: {path}")
    return stage


def inspect_scene(path: str) -> dict[str, Any]:
    """Read the scene graph — list all prims with types and hierarchy."""
    from pxr import Usd, UsdGeom

    stage = _open_stage(path)

    def _walk(prim) -> dict:
        children = [_walk(child) for child in prim.GetChildren()]
        info: dict[str, Any] = {
            "path": str(prim.GetPath()),
            "type": prim.GetTypeName(),
        }
        if prim.GetTypeName() == "Mesh":
            mesh = UsdGeom.Mesh(prim)
            face_counts = mesh.GetFaceVertexCountsAttr().Get()
            if face_counts:
                info["faces"] = len(face_counts)
        if children:
            info["children"] = children
        return info

    root = stage.GetPseudoRoot()
    return {
        "scene": [_walk(child) for child in root.GetChildren()],
        "up_axis": str(UsdGeom.GetStageUpAxis(stage)),
        "meters_per_unit": UsdGeom.GetStageMetersPerUnit(stage),
    }


def get_prim(path: str, prim_path: str) -> dict[str, Any]:
    """Get detailed attributes and metadata for a specific prim."""
    from pxr import Usd, UsdGeom, UsdShade

    stage = _open_stage(path)
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        return {"error": f"Prim not found: {prim_path}"}

    attrs = {}
    for attr in prim.GetAttributes():
        val = attr.Get()
        if val is not None:
            attrs[attr.GetName()] = str(val)

    result: dict[str, Any] = {
        "path": prim_path,
        "type": prim.GetTypeName(),
        "attributes": attrs,
    }

    # Material binding
    if prim.IsA(UsdGeom.Gprim):
        binding_api = UsdShade.MaterialBindingAPI(prim)
        mat, _ = binding_api.ComputeBoundMaterial()
        if mat:
            result["material"] = str(mat.GetPath())

    return result


def get_materials(path: str) -> dict[str, Any]:
    """List all materials with their shader parameters."""
    from pxr import Usd, UsdShade

    stage = _open_stage(path)
    materials = []

    for prim in stage.Traverse():
        if prim.IsA(UsdShade.Material):
            mat = UsdShade.Material(prim)
            surface = mat.GetSurfaceOutput()
            shader_info: dict[str, Any] = {"path": str(prim.GetPath())}

            # Get connected shader
            sources, _invalid = surface.GetConnectedSources()
            for source_info in sources:
                shader_prim = source_info.source.GetPrim()
                shader = UsdShade.Shader(shader_prim)
                params = {}
                for inp in shader.GetInputs():
                    val = inp.Get()
                    if val is not None:
                        params[inp.GetBaseName()] = str(val)
                shader_info["shader"] = str(shader_prim.GetPath())
                shader_info["params"] = params

            materials.append(shader_info)

    return {"materials": materials}


def get_transforms(path: str, prim_path: Optional[str] = None) -> dict[str, Any]:
    """Get transforms for one or all xformable prims."""
    from pxr import Usd, UsdGeom

    stage = _open_stage(path)
    time = Usd.TimeCode.Default()
    results = []

    if prim_path:
        prims = [stage.GetPrimAtPath(prim_path)]
    else:
        prims = [p for p in stage.Traverse() if p.IsA(UsdGeom.Xformable)]

    for prim in prims:
        if not prim.IsValid():
            continue
        xform = UsdGeom.Xformable(prim)
        local = xform.GetLocalTransformation(time)
        world = xform.ComputeLocalToWorldTransform(time)
        results.append({
            "path": str(prim.GetPath()),
            "local_transform": str(local),
            "world_transform": str(world),
        })

    return {"transforms": results}


def list_variants(path: str) -> dict[str, Any]:
    """List all variant sets and their options."""
    stage = _open_stage(path)
    results = []

    for prim in stage.Traverse():
        vsets = prim.GetVariantSets()
        names = vsets.GetNames()
        if names:
            prim_variants = []
            for name in names:
                vset = vsets.GetVariantSet(name)
                prim_variants.append({
                    "name": name,
                    "options": vset.GetVariantNames(),
                    "selected": vset.GetVariantSelection(),
                })
            results.append({
                "path": str(prim.GetPath()),
                "variant_sets": prim_variants,
            })

    return {"variants": results}


def set_variant(path: str, prim_path: str, variant_set: str, variant: str) -> dict[str, Any]:
    """Switch a variant selection on a prim."""
    stage = _open_stage(path)
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        return {"error": f"Prim not found: {prim_path}"}

    vsets = prim.GetVariantSets()
    if not vsets.HasVariantSet(variant_set):
        return {"error": f"Variant set not found: {variant_set}"}

    vset = vsets.GetVariantSet(variant_set)
    if variant not in vset.GetVariantNames():
        return {"error": f"Variant not found: {variant}. Available: {vset.GetVariantNames()}"}

    vset.SetVariantSelection(variant)
    return {
        "path": prim_path,
        "variant_set": variant_set,
        "selected": variant,
        "status": "ok",
    }


def export_mesh(path: str, prim_path: str, output: str, fmt: str = "stl") -> dict[str, Any]:
    """Export a mesh prim as binary STL or OBJ."""
    from pxr import UsdGeom, Gf

    stage = _open_stage(path)
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid() or not prim.IsA(UsdGeom.Mesh):
        return {"error": f"Not a valid mesh prim: {prim_path}"}

    mesh = UsdGeom.Mesh(prim)
    points = mesh.GetPointsAttr().Get()
    face_vertex_counts = mesh.GetFaceVertexCountsAttr().Get()
    face_vertex_indices = mesh.GetFaceVertexIndicesAttr().Get()

    if not points or not face_vertex_counts or not face_vertex_indices:
        return {"error": "Mesh has no geometry data"}

    # Triangulate (simple fan triangulation for convex faces)
    triangles = []
    idx = 0
    for count in face_vertex_counts:
        for i in range(1, count - 1):
            v0 = face_vertex_indices[idx]
            v1 = face_vertex_indices[idx + i]
            v2 = face_vertex_indices[idx + i + 1]
            triangles.append((v0, v1, v2))
        idx += count

    if fmt == "obj":
        lines = [f"# Exported from {prim_path}"]
        for p in points:
            lines.append(f"v {p[0]} {p[1]} {p[2]}")
        for tri in triangles:
            lines.append(f"f {tri[0]+1} {tri[1]+1} {tri[2]+1}")
        with open(output, "w") as f:
            f.write("\n".join(lines))
    else:
        # Binary STL
        with open(output, "wb") as f:
            f.write(b"\x00" * 80)  # header
            f.write(struct.pack("<I", len(triangles)))
            for tri in triangles:
                p0 = Gf.Vec3f(*points[tri[0]])
                p1 = Gf.Vec3f(*points[tri[1]])
                p2 = Gf.Vec3f(*points[tri[2]])
                normal = (p1 - p0) ^ (p2 - p0)
                if normal.GetLength() > 0:
                    normal = normal.GetNormalized()
                f.write(struct.pack("<3f", *normal))
                f.write(struct.pack("<3f", *p0))
                f.write(struct.pack("<3f", *p1))
                f.write(struct.pack("<3f", *p2))
                f.write(struct.pack("<H", 0))

    file_size = os.path.getsize(output)
    return {
        "output": output,
        "format": fmt,
        "triangles": len(triangles),
        "size_bytes": file_size,
        "status": "ok",
    }


def scene_stats(path: str) -> dict[str, Any]:
    """Get scene statistics."""
    from pxr import UsdGeom

    stage = _open_stage(path)

    prim_count = 0
    mesh_count = 0
    material_count = 0
    total_faces = 0

    for prim in stage.Traverse():
        prim_count += 1
        if prim.GetTypeName() == "Mesh":
            mesh_count += 1
            mesh = UsdGeom.Mesh(prim)
            fc = mesh.GetFaceVertexCountsAttr().Get()
            if fc:
                total_faces += len(fc)
        elif prim.GetTypeName() == "Material":
            material_count += 1

    # Bounding box
    bbox_cache = UsdGeom.BBoxCache(0, [UsdGeom.Tokens.default_])
    root_prim = stage.GetPseudoRoot()
    bounds = bbox_cache.ComputeWorldBound(root_prim)
    bbox_range = bounds.ComputeAlignedRange()
    bbox_min = bbox_range.GetMin()
    bbox_max = bbox_range.GetMax()
    size = bbox_max - bbox_min

    meters_per_unit = UsdGeom.GetStageMetersPerUnit(stage)
    scale = 1000.0 * meters_per_unit  # to mm

    return {
        "prim_count": prim_count,
        "mesh_count": mesh_count,
        "material_count": material_count,
        "total_faces": total_faces,
        "up_axis": str(UsdGeom.GetStageUpAxis(stage)),
        "meters_per_unit": meters_per_unit,
        "bounds_mm": {
            "x": round(size[0] * scale, 1),
            "y": round(size[1] * scale, 1),
            "z": round(size[2] * scale, 1),
        },
    }
