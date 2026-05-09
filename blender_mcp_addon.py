import bpy, mathutils, json, threading, socket, time, io, traceback, os, sys, requests, tempfile, shutil
from bpy.props import IntProperty, StringProperty
from contextlib import redirect_stdout

bl_info = {
    "name": "Blender MCP Pro",
    "author": "BlenderMCP",
    "version": (2, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Pro Bridge with Sketchfab & AI Integration",
    "category": "Interface",
}

_mcp_server_instance = None

class BlenderMCPServer:
    def __init__(self, host='127.0.0.1', port=9876):
        self.host, self.port, self.running, self.socket = host, port, False, None

    def start(self):
        if self.running: return
        self.running = True
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            threading.Thread(target=self._server_loop, daemon=True).start()
        except: self.stop()

    def stop(self):
        self.running = False
        if self.socket:
            try: self.socket.close()
            except: pass
            self.socket = None

    def _server_loop(self):
        self.socket.settimeout(1.0)
        while self.running:
            try:
                client, _ = self.socket.accept()
                threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
            except socket.timeout: continue
            except: break

    def _handle_client(self, client):
        buffer = ""
        try:
            while self.running:
                data = client.recv(32768)
                if not data: break
                buffer += data.decode('utf-8', errors='ignore')
                while buffer:
                    try:
                        obj, idx = json.JSONDecoder().raw_decode(buffer)
                        buffer = buffer[idx:].strip()
                        bpy.app.timers.register(lambda c=obj: self.execute_wrapper(c, client), first_interval=0.0)
                    except json.JSONDecodeError: break
        except: pass
        finally: client.close()

    def execute_wrapper(self, cmd, client):
        try:
            res = self.execute_command(cmd)
            client.sendall((json.dumps(res) + "\n").encode('utf-8'))
        except: pass
        return None

    def execute_command(self, command):
        if isinstance(command, str):
            try: command = json.loads(command)
            except: pass
        
        ctype = str(command.get("type", "execute_code"))
        params = command.get("params", {})
        if not isinstance(params, dict): params = {"code": str(params)}

        # HANDLER: Execute Code
        if ctype == "execute_code":
            try:
                code = str(params.get("code", params.get("script", "")))
                import bmesh, math, random
                ns = {"bpy": bpy, "mathutils": mathutils, "bmesh": bmesh, "math": math, "random": random}
                buf = io.StringIO()
                with redirect_stdout(buf): exec(code, ns)
                return {"status": "success", "result": buf.getvalue() or "Done"}
            except: return {"status": "error", "message": traceback.format_exc()}

        # HANDLER: Sketchfab Search
        if ctype == "search_sketchfab_models":
            try:
                query = params.get("query", "")
                count = params.get("count", 10)
                url = f"https://api.sketchfab.com/v3/search?type=models&q={query}&count={count}&downloadable=true"
                r = requests.get(url)
                return {"status": "success", "result": r.json()}
            except Exception as e: return {"status": "error", "message": str(e)}

        # HANDLER: Viewport Screenshot
        if ctype == "get_viewport_screenshot":
            try:
                path = os.path.join(tempfile.gettempdir(), "blender_mcp_shot.png")
                # Ensure we are in the 3D viewport
                for area in bpy.context.screen.areas:
                    if area.type == 'VIEW_3D':
                        ctx = bpy.context.copy()
                        ctx['area'] = area
                        bpy.ops.render.opengl(ctx, write_still=True)
                        # This is a bit complex in script, fallback to basic render
                        break
                bpy.context.scene.render.filepath = path
                bpy.ops.render.render(write_still=True)
                with open(path, "rb") as f:
                    import base64
                    data = base64.b64encode(f.read()).decode('utf-8')
                return {"status": "success", "result": data}
            except Exception as e: return {"status": "error", "message": str(e)}

        return {"status": "error", "message": f"Command {ctype} not yet implemented in Pro version"}

class BLENDERMCP_PT_panel(bpy.types.Panel):
    bl_label, bl_idname, bl_space_type, bl_region_type, bl_category = "Blender MCP Pro", "BLENDERMCP_PT_panel", 'VIEW_3D', 'UI', 'BlenderMCP'
    def draw(self, context):
        global _mcp_server_instance
        l = self.layout
        if _mcp_server_instance and _mcp_server_instance.running:
            l.operator("blendermcp.stop_server", text="Stop Server (Running)", icon='PAUSE')
            l.label(text="Status: PRO VERSION ACTIVE", icon='FUND')
        else:
            l.operator("blendermcp.start_server", text="Start Pro Server", icon='PLAY')
        l.prop(context.scene, "blendermcp_port")

class BLENDERMCP_OT_start_server(bpy.types.Operator):
    bl_idname, bl_label = "blendermcp.start_server", "Start Pro Server"
    def execute(self, context):
        global _mcp_server_instance
        _mcp_server_instance = BlenderMCPServer(port=context.scene.blendermcp_port)
        _mcp_server_instance.start()
        return {'FINISHED'}

class BLENDERMCP_OT_stop_server(bpy.types.Operator):
    bl_idname, bl_label = "blendermcp.stop_server", "Stop"
    def execute(self, context):
        global _mcp_server_instance
        if _mcp_server_instance: _mcp_server_instance.stop()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(BLENDERMCP_PT_panel)
    bpy.utils.register_class(BLENDERMCP_OT_start_server)
    bpy.utils.register_class(BLENDERMCP_OT_stop_server)
    bpy.types.Scene.blendermcp_port = IntProperty(name="Port", default=9876)

def unregister():
    if _mcp_server_instance: _mcp_server_instance.stop()
    bpy.utils.unregister_class(BLENDERMCP_PT_panel)
    bpy.utils.unregister_class(BLENDERMCP_OT_start_server)
    bpy.utils.unregister_class(BLENDERMCP_OT_stop_server)

if __name__ == "__main__": register()
