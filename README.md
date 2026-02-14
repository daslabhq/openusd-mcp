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

Then try it with the included example scenes:

*"Inspect the scene graph of examples/desk_setup.usda and describe what's on the desk."*

*"What color options does the product in examples/product_configurator.usda have? Switch it to gold."*

### With any MCP client

```bash
openusd-mcp --stdio
```

The server communicates over stdin/stdout using the [MCP protocol](https://modelcontextprotocol.io).

## Examples

The repo includes two example scenes that exercise all 8 tools.

### Desk setup — scene inspection

A desk with a table, monitor, keyboard, and mug. 5 PBR materials (wood, metal, screen, ceramic, dark plastic), 10 meshes, real-world dimensions.

```
You: What's in examples/desk_setup.usda?

Claude: A desk scene with 25 prims, 10 meshes, 5 materials:

  /Desk (Xform)
    /Desk/Table/Top (Mesh) — Wood, 120×60×3 cm
    /Desk/Table/Leg1..4 (Mesh) — Metal
    /Desk/Monitor/Screen (Mesh) — dark glossy
    /Desk/Monitor/Stand (Mesh) — Metal
    /Desk/Monitor/Base (Mesh) — Metal
    /Desk/Keyboard (Mesh) — DarkPlastic
    /Desk/Mug/Body (Mesh) — Ceramic

  Bounds: 1200 × 835 × 1250 mm

You: Export the tabletop as STL

Claude: Exported /Desk/Table/Top to tabletop.stl (12 triangles, 684 bytes)
```

### Product configurator — variant switching

A device with 3 variant sets: **size** (small, medium, large), **color** (midnight, silver, gold, red), and **finish** (matte, satin, glossy).

```
You: What configuration options does examples/product_configurator.usda have?

Claude: The product at /Product has 3 variant sets:

  size:   small | medium* | large
  color:  midnight* | silver | gold | red
  finish: matte | satin* | glossy

  (* = currently selected)

You: Switch to gold, large, glossy

Claude: Done. Updated /Product:
  size:   large (1.4× scale)
  color:  gold — diffuseColor: (0.83, 0.69, 0.22), metallic: 0.9
  finish: glossy — roughness: 0.1
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
