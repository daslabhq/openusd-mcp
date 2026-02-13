# openusd-mcp

An MCP server that lets AI assistants read, inspect, and manipulate [OpenUSD](https://openusd.org) scenes.

```
pip install openusd-mcp
```

## What it does

Connect this MCP server to Claude, ChatGPT, Cursor, or any MCP-compatible client. Your AI assistant can then work directly with `.usda`, `.usdc`, and `.usdz` files — inspecting scene graphs, querying properties, exporting meshes, and switching variants.

## Tools

| Tool | Description |
|------|-------------|
| `usd_inspect` | Read the scene graph — list all prims, types, hierarchy |
| `usd_get_prim` | Get detailed properties, attributes, and metadata for a specific prim |
| `usd_get_materials` | List all materials and their shader parameters |
| `usd_get_transforms` | Get world-space transforms for prims |
| `usd_list_variants` | List all variant sets and their options |
| `usd_set_variant` | Switch a variant selection |
| `usd_export_mesh` | Export a mesh prim as STL or OBJ |
| `usd_scene_stats` | Get scene statistics — prim count, mesh count, material count, bounding box |

## Quick start

### With Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openusd": {
      "command": "openusd-mcp",
      "args": []
    }
  }
}
```

Then ask Claude: *"Inspect the scene graph of my-scene.usdz and list all mesh prims with their materials."*

### With any MCP client

```bash
openusd-mcp --stdio
```

The server communicates over stdin/stdout using the [MCP protocol](https://modelcontextprotocol.io).

### As a Python library

```python
from openusd_mcp import inspect_scene, get_prim, export_mesh

# Get the full scene graph
tree = inspect_scene("scene.usdz")
print(tree)

# Query a specific prim
prim = get_prim("scene.usdz", "/World/Body")
print(prim.attributes)

# Export a mesh as STL
export_mesh("scene.usdz", "/World/Body", "body.stl")
```

## Example

```
You: Inspect the scene graph of case.usdz

Claude: Here's the scene graph for case.usdz:

  /Case (Xform)
    /Case/Body (Mesh) — 2,847 faces, material: OrangePBR
    /Case/Logo (Mesh) — 1,204 faces, material: BlackPBR

  Materials:
    OrangePBR — diffuseColor: (1.0, 0.55, 0.0), metallic: 0.0, roughness: 0.4
    BlackPBR  — diffuseColor: (0.1, 0.1, 0.1), metallic: 0.0, roughness: 0.3

  Scene bounds: (42mm x 26mm x 13mm)
  Up axis: Z, meters per unit: 0.001

You: Export the Body mesh as STL

Claude: Exported /Case/Body to body.stl (2,847 triangles, 142KB)
```

## Requirements

- Python 3.9+
- `usd-core` (Pixar's USD Python bindings)

```
pip install usd-core
```

## How it works

The server uses Pixar's official `pxr` Python bindings (the same libraries used by NVIDIA Omniverse, Apple's Reality Composer, and every major VFX pipeline) to read and manipulate USD stages. It exposes these capabilities as MCP tools that any AI assistant can call.

OpenUSD is the [industry standard](https://aousd.org) for describing 3D scenes, backed by Pixar, Apple, NVIDIA, Adobe, and Autodesk. As of December 2025, the Alliance for OpenUSD has ratified [Core Specification 1.0](https://aousd.org/news/core-spec-announcement/).

## Author

[Mirko Kiefer](https://github.com/mirkokiefer) — [Daslab](https://daslab.dev)

## License

MIT

## Links

- [OpenUSD](https://openusd.org) — Universal Scene Description
- [AOUSD](https://aousd.org) — Alliance for OpenUSD
- [MCP](https://modelcontextprotocol.io) — Model Context Protocol
- [Daslab](https://daslab.dev) — Where AI meets the physical world
