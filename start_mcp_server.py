import bpy
import sys
import os
import time

# Add current directory to path so we can import the addon
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import blender_mcp_official_addon
    blender_mcp_official_addon.register()
    bpy.ops.blendermcp.start_server()
    print("Blender MCP Server started successfully.")
except Exception as e:
    print("Failed to start server:", e)

# Keep blender alive
while True:
    time.sleep(1)
