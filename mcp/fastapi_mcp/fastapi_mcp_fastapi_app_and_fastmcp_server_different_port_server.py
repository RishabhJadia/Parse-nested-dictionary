# server.py
from fastapi import FastAPI
from fastmcp import FastMCP
import logging
from pydantic import BaseModel
import uvicorn
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application for HTTP endpoints
app = FastAPI(
    title="Calculator API",
    description="FastAPI app with calculator tools",
    version="0.2.0"
)

# Initialize MCP server
try:
    mcp = FastMCP(
        name="ConfiguredServer",
        host="localhost",
        port=8003,  # Directly maps to ServerSettings
        # on_duplicate_tools="error" # Set duplicate handling
    )
    print(mcp.settings.port)  # Output: 8003
    print(mcp.settings.host)  # Output: 0.0.0.0
    print(mcp.settings.stateless_http)  # Output: False
    print(mcp.settings.sse_path)  # Output: /sse
    # print(mcp.settings.on_duplicate_tools) # Output: "error"
    logger.info("MCP server mounted successfully at /sse")
except Exception as e:
    logger.error(f"Failed to mount MCP server: {str(e)}")
    raise

# Calculator Tools ------------------------------------------------------------


class CalculationInput(BaseModel):
    a: int
    b: int

# Define HTTP endpoints for app


@mcp.tool('add_numbers_tool')
@app.post("/add", operation_id="add_numbers")
async def add(numbers: CalculationInput) -> dict:
    """
    Add two numbers

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    result = numbers.a + numbers.b
    logger.info(f"Addition: {numbers.a} + {numbers.b} = {result}")
    return {"result": result}


@mcp.tool('subtract_numbers_tool')
@app.post("/subtract", operation_id="subtract_numbers")
async def subtract(numbers: CalculationInput) -> dict:
    """
    Subtract two numbers

    Args:
        a: First number
        b: Second number

    Returns:
        Subtraction of a and b
    """
    result = numbers.a - numbers.b
    logger.info(f"Subtraction: {numbers.a} - {numbers.b} = {result}")
    return {"result": result}


@mcp.tool('multiply_numbers_tool')
@app.post("/multiply", operation_id="multiply_numbers")
async def multiply(numbers: CalculationInput) -> dict:
    """
    Multipy two numbers

    Args:
        a: First number
        b: Second number

    Returns:
        Multiplication of a and b
    """
    result = numbers.a * numbers.b
    logger.info(f"Multiplication: {numbers.a} * {numbers.b} = {result}")
    return {"result": result}


@mcp.tool('divide_numbers_tool')
@app.post("/divide", operation_id="divide_numbers")
async def divide(numbers: CalculationInput) -> dict:
    """
    Divide two numbers

    Args:
        a: First number
        b: Second number

    Returns:
        Division of a and b
    """
    if numbers.b == 0:
        logger.error("Division by zero attempted")
        return {"error": "Cannot divide by zero"}
    result = numbers.a / numbers.b
    logger.info(f"Division: {numbers.a} / {numbers.b} = {result}")
    return {"result": result}


@mcp.tool('greet_user_tool')
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


mcp_app = mcp.http_app(transport="sse")


def run_mcp_server():
    """Run FastAPI server for MCP on port 8003"""
    logger.info("Starting MCP SSE server on port 8003")
    # mcp.run(transport="sse", host="localhost", port="8003")
    uvicorn.run(mcp_app, host="localhost", port=8003)


def run_fastapi():
    """Run FastAPI HTTP server on port 8001"""
    logger.info("Starting FastAPI HTTP server on port 8001")
    uvicorn.run(app, host="localhost", port=8001)


if __name__ == "__main__":
    # Start MCP server in a separate thread
    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()

    # Start FastAPI HTTP server in the main thread
    run_fastapi()

# Terminal 1: Run HTTP server
# uvicorn fastapi_mcp_fastapi_app_and_fastmcp_server_different_port_server:app --host localhost --port 8001
# Terminal 2: Run MCP server
# uvicorn fastapi_mcp_fastapi_app_and_fastmcp_server_different_port_server:mcp_app --host localhost --port 8003

# when run mcp server without uvivorn
# fastapi_mcp_fastapi_app_and_fastmcp_server_different_port_server.py
