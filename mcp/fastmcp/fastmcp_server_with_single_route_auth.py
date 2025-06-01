import logging
from fastmcp import FastMCP
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route  # Keep for /health endpoint
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Define the authentication function


def check_auth(request: Request):
    auth = request.headers.get("authorization", "")
    api_key = request.headers.get("x-api-key")

    if not auth or not api_key:
        logging.warning(
            "Authentication headers missing for request to %s", request.url.path)
        raise HTTPException(
            status_code=401, detail="Missing authorization or x-api-key")

    expected_api_key = "your-secret-api-key"
    # This should ideally be validated (e.g., token contents)
    expected_auth_header = "Bearer test-token"

    if api_key != expected_api_key or auth != expected_auth_header:
        logging.warning(
            f"Invalid credentials for {request.url.path}. Auth: '{auth}', API Key: '{api_key}'")
        raise HTTPException(
            status_code=403, detail="Invalid authentication credentials.")

    logging.info(f"Authentication successful for: {request.url.path}")
    return True

# Define custom middleware class

# For production, uncomment the line below
# uvicorn fastmcp_server_with_auth:http_app --host 0.0.0.0 --port 8002

# https://www.starlette.io/middleware/#using-middleware # for recommended appraoch
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Exclude /health from authentication checks
        if request.url.path == "/health":
            return await call_next(request)

        try:
            check_auth(request)  # Perform the authentication check

            # If authentication passes, proceed to the next middleware or route handler.
            # This 'await call_next(request)' will eventually hit the FastMCP SSE endpoint handler.
            response = await call_next(request)

            # --- THE CRITICAL FIX FOR SSE ---
            # If the response is an SSE stream (Content-Type: text/event-stream),
            # we must simply return it without further processing its body.
            # BaseHTTPMiddleware tries to iterate over the body, which breaks SSE's continuous stream.
            if response.headers.get('content-type') == 'text/event-stream':
                logging.debug(
                    "Detected SSE response, passing through AuthMiddleware directly.")
                return response

            # For other standard HTTP responses (JSON, etc.), BaseHTTPMiddleware's
            # default handling (which involves consuming the body iterator) is fine.
            return response

        except HTTPException as e:
            logging.error(
                f"Authentication failed for {request.url.path}: {e.detail}")
            return JSONResponse(
                content={"detail": e.detail},
                status_code=e.status_code
            )
        except Exception as e:
            # Use exception for full traceback
            logging.exception(
                f"Unhandled error in AuthMiddleware for {request.url.path}")
            return JSONResponse(
                content={"detail": "Internal server error during authentication."},
                status_code=500
            )

# Define /health endpoint (standard FastAPI route)

async def health_check(request: Request):
    logging.info("Health check requested.")
    return JSONResponse({"status": "healthy"})

# Initialize FastMCP
mcp = FastMCP(
    name="ConfiguredServer",
    # No auth_middleware argument here; it's handled via FastAPI middleware
)

# Print configuration (optional)
logging.info(f"Port: {mcp.settings.port}")
logging.info(f"Host: {mcp.settings.host}")
logging.info(f"Stateless HTTP: {mcp.settings.stateless_http}")
logging.info(f"SSE Path: {mcp.settings.sse_path}")  # Default is /sse

# Define a tool


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    logging.info(f"Adding {a} + {b}")
    result = a + b
    logging.info(f"Tool result: {result}")
    return result


# Create FastAPI app that includes FastMCP's routes (including SSE)
http_app = mcp.http_app()

# Add the /health endpoint to the FastAPI app's routes.
# It's usually good to add non-middleware-affected routes first.

# # Under the Hood
# # add_route(...) → creates a Route(...) and appends it to app.routes
# # routes.append(...) → directly appends a Route instance(no extra logic)

# http_app.routes.append(Route("/health", health_check, methods=["GET"]))
http_app.add_route("/health", health_check, methods=["GET"])

# Add the custom authentication middleware to the FastAPI app.
# This middleware will now apply to all routes handled by 'http_app',
# including the FastMCP SSE endpoint, but it will pass SSE streams through correctly.
http_app.add_middleware(AuthMiddleware)

if __name__ == "__main__":
    logging.info(
        f"FastMCP server starting with routes: {[route.path for route in http_app.routes]}")
    # Uvicorn runs the FastAPI application 'http_app'
    uvicorn.run(http_app, host="localhost", port=8002)
