# https: // github.com/daveebbelaar/ai-cookbook/blob/main/mcp/crash-course/3-simple-server-setup/README.md
# from mcp.server.fastmcp import FastMCP
# from dotenv import load_dotenv

# load_dotenv("../.env")

# # Create an MCP server
# mcp = FastMCP(
#     name="Calculator",
#     host="0.0.0.0",  # only used for SSE transport (localhost)
#     port=8050,  # only used for SSE transport (set this to any port)
# )


# # Add a simple calculator tool
# @mcp.tool()
# def add(a: int, b: int) -> int:
#     """Add two numbers together"""
#     return a + b


# # Run the server
# if __name__ == "__main__":
#     transport = "sse"
#     if transport == "stdio":
#         print("Running server with stdio transport")
#         mcp.run(transport="stdio")
#     elif transport == "sse":
#         print("Running server with SSE transport")
#         mcp.run(transport="sse")
#     else:
#         raise ValueError(f"Unknown transport: {transport}")
    


from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
import logging

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Simple FastAPI with FastApiMCP",
    description="A FastAPI app with a single endpoint and MCP server integration",
    version="0.1.0"
)

# Define a single endpoint


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


# Initialize and mount MCP server with explicit configuration
try:
    mcp = FastApiMCP(
        app,
        name="Greeting FastAPI with FastApiMCP",
        description="MCP server for the greeting API",
    )
    mcp.mount()
    logger.info("MCP server mounted successfully at /mcp")
except Exception as e:
    logger.error(f"Failed to mount MCP server: {str(e)}")
    raise

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)
