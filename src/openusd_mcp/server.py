"""MCP server for OpenUSD.

Exposes USD scene inspection and manipulation as MCP tools.
Uses the official MCP Python SDK (FastMCP).

Usage:
    openusd-mcp              # stdio transport (for Claude Desktop, Cursor, etc.)
    openusd-mcp --http       # HTTP transport (for MCP Inspector, web clients)
"""

import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

from openusd_mcp import tools

# -- Server -----------------------------------------------------------------

mcp = FastMCP(
    "OpenUSD",
    instructions="MCP server for reading and manipulating OpenUSD scenes",
)


# -- Tools ------------------------------------------------------------------

@mcp.tool()
def usd_inspect(path: str) -> str:
    """Read the scene graph of a USD file.

    Returns the full prim hierarchy with types, face counts, and child structure.
    Supports .usda, .usdc, and .usdz files.
    """
    result = tools.inspect_scene(path)
    return json.dumps(result, indent=2)


@mcp.tool()
def usd_get_prim(path: str, prim_path: str) -> str:
    """Get detailed attributes, metadata, and material binding for a specific prim.

    Args:
        path: Path to the USD file
        prim_path: Scene graph path, e.g. /World/Body
    """
    result = tools.get_prim(path, prim_path)
    return json.dumps(result, indent=2)


@mcp.tool()
def usd_get_materials(path: str) -> str:
    """List all materials in the scene with their shader parameters.

    Returns diffuse color, metallic, roughness, and other PBR properties
    for each material.
    """
    result = tools.get_materials(path)
    return json.dumps(result, indent=2)


@mcp.tool()
def usd_get_transforms(path: str, prim_path: Optional[str] = None) -> str:
    """Get local and world-space transforms for prims.

    Args:
        path: Path to the USD file
        prim_path: Optional specific prim path. Omit to get all xformable prims.
    """
    result = tools.get_transforms(path, prim_path)
    return json.dumps(result, indent=2)


@mcp.tool()
def usd_list_variants(path: str) -> str:
    """List all variant sets and their options for prims in the scene.

    USD variants allow switching between different configurations
    (e.g. material options, LOD levels, regional variants).
    """
    result = tools.list_variants(path)
    return json.dumps(result, indent=2)


@mcp.tool()
def usd_set_variant(path: str, prim_path: str, variant_set: str, variant: str) -> str:
    """Switch a variant selection on a prim.

    Args:
        path: Path to the USD file
        prim_path: Prim that has the variant set
        variant_set: Name of the variant set
        variant: Variant to select
    """
    result = tools.set_variant(path, prim_path, variant_set, variant)
    return json.dumps(result, indent=2)


@mcp.tool()
def usd_export_mesh(path: str, prim_path: str, output: str, format: str = "stl") -> str:
    """Export a mesh prim as STL or OBJ.

    Args:
        path: Path to the USD file
        prim_path: Path to the mesh prim to export
        output: Output file path (.stl or .obj)
        format: Output format - 'stl' (default) or 'obj'
    """
    result = tools.export_mesh(path, prim_path, output, format)
    return json.dumps(result, indent=2)


@mcp.tool()
def usd_scene_stats(path: str) -> str:
    """Get scene statistics: prim count, mesh count, material count, total faces, and bounding box.

    Returns dimensions in millimeters (assuming the stage uses standard USD units).
    """
    result = tools.scene_stats(path)
    return json.dumps(result, indent=2)


# -- Entry point ------------------------------------------------------------

def main():
    """Run the MCP server."""
    import sys

    if "--http" in sys.argv:
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
