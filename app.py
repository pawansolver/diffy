"""
Diffy FastMCP Server Entry Point
Native Starlette + FastMCP (Local & GitHub Skills Provider)
"""
import os
import uvicorn
from starlette.routing import Route
from starlette.responses import HTMLResponse

from main import (
    SkillsProviderServer,
    health_endpoint,
    get_base_instruction_endpoint,
    get_default_user_prompt_endpoint,
    ApiKeyMiddleware,
)

# Initialize FastMCP Skills Server
server_instance = SkillsProviderServer("skills.settings.json")

# FastMCP native Starlette HTTP app with streamable-http transport mounted at /mcp
app = server_instance.mcp.http_app(path="/mcp")

# Add exact matching route for /mcp/ so BOTH /mcp and /mcp/ work natively
mcp_route = next(r for r in app.router.routes if getattr(r, "path", "") == "/mcp")
app.router.routes.append(
    Route("/mcp/", endpoint=mcp_route.endpoint, methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"])
)

# Auxiliary API endpoints for Dify / Open WebUI integration
app.router.routes.insert(0, Route("/health", health_endpoint, methods=["GET"]))
app.router.routes.insert(1, Route("/get-base-instruction", get_base_instruction_endpoint, methods=["GET"]))
app.router.routes.insert(2, Route("/get-default-user-prompt", get_default_user_prompt_endpoint, methods=["GET"]))

# Landing page
async def index_endpoint(request):
    return HTMLResponse("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Diffy FastMCP Server</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background:#0f172a; color:#f8fafc; display:flex; justify-content:center;
         align-items:center; min-height:100vh; }
  .card { background:#1e293b; padding:40px; border-radius:16px;
          border:1px solid #334155; max-width:560px; width:90%;
          box-shadow:0 20px 60px rgba(0,0,0,0.5); }
  .badge { display:inline-flex; align-items:center; gap:8px;
           background:rgba(16,185,129,0.15); color:#10b981;
           border:1px solid rgba(16,185,129,0.3); padding:6px 16px;
           border-radius:999px; font-size:13px; font-weight:600; }
  .dot { width:8px; height:8px; background:#10b981; border-radius:50%;
         box-shadow:0 0 8px #10b981; animation:pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }
  h1 { margin:20px 0 8px; font-size:26px; }
  .sub { color:#94a3b8; margin-bottom:24px; font-size:14px; }
  .label { font-size:11px; color:#64748b; text-transform:uppercase;
           font-weight:700; margin-top:16px; margin-bottom:4px; }
  .ep { background:#0f172a; border:1px solid #334155; border-radius:8px;
        padding:10px 14px; font-family:monospace; color:#38bdf8; font-size:13px; }
</style>
</head>
<body>
<div class="card">
  <div class="badge"><div class="dot"></div> Server Online</div>
  <h1>Diffy FastMCP Server</h1>
  <p class="sub">Autonomous MCP Skills Microservice</p>
  <div class="label">MCP Endpoint (for Open WebUI)</div>
  <div class="ep">http://diffy:7860/mcp (or /mcp/)</div>
  <div class="label">Health Check</div>
  <div class="ep">/health</div>
</div>
</body>
</html>""")

app.router.routes.insert(3, Route("/", index_endpoint, methods=["GET"]))
app.add_middleware(ApiKeyMiddleware)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
