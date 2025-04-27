from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
import logging
import asyncio
import threading
import uvicorn

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Simple FastAPI with MCP",
    description="A FastAPI app with a single endpoint and MCP server integration",
    version="0.1.0"
)

# Initialize MCP server
try:
    mcp = FastMCP(
        name="Greeting FastAPI with FastMCP",
        host="0.0.0.0",
        port=8050,
    )
    logger.info("MCP server initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MCP server: {str(e)}")
    raise


# Define endpoint that works with both HTTP and MCP


@mcp.tool()
@app.get("/greet", operation_id="greet_user")
async def greet(name: str = "World") -> dict:
    """
    Greets the user with a personalized message.
    
    Args:
        name (str): The name to include in the greeting (default: 'World')
    
    Returns:
        dict: A JSON response with the greeting message
    """
    logger.info(f"Received request to greet: {name}")
    return {"message": f"Hello, {name}!"}


def run_mcp_server():
    """Run MCP server with SSE transport in a separate thread"""
    logger.info("Starting MCP SSE server")
    mcp.run(transport="sse")


def run_fastapi():
    """Run FastAPI HTTP server"""
    logger.info("Starting FastAPI HTTP server")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    # Start MCP server in a separate thread
    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()

    # Start FastAPI in main thread
    run_fastapi()
