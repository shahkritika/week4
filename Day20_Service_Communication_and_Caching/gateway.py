import uuid
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI(title="API Gateway", description="Unified Ingress Gateway routing to Auth & Inventory microservices")

AUTH_SERVICE = "http://localhost:8001"
INVENTORY_SERVICE = "http://localhost:8002"

@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Request-ID", f"gw-{uuid.uuid4().hex[:8]}")
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = correlation_id
    return response

@app.api_route("/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_auth(request: Request, path: str):
    return await forward_request(f"{AUTH_SERVICE}/{path}", request)

@app.api_route("/api/v1/inventory/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_inventory(request: Request, path: str):
    return await forward_request(f"{INVENTORY_SERVICE}/{path}", request)

async def forward_request(target_url: str, request: Request):
    headers = dict(request.headers)
    headers["X-Request-ID"] = request.state.correlation_id
    body = await request.body()
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=body,
                timeout=10.0
            )
            return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get("content-type"))
        except httpx.RequestError as exc:
            return JSONResponse(status_code=502, content={"error": f"Upstream microservice unreachable: {str(exc)}"})

