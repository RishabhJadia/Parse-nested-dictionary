from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
import logging
from typing import Optional
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Calculator API with MCP",
    description="FastAPI app with multiple calculator tools and MCP integration",
    version="0.2.0"
)

# Calculator Tools ------------------------------------------------------------


class CalculationInput(BaseModel):
    a: float
    b: float


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


@app.post("/subtract", operation_id="subtract_numbers")
async def subtract(numbers: CalculationInput) -> dict:
    """
    Subtract two numbers
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Difference between a and b
    """
    result = numbers.a - numbers.b
    logger.info(f"Subtraction: {numbers.a} - {numbers.b} = {result}")
    return {"result": result}


@app.post("/multiply", operation_id="multiply_numbers")
async def multiply(numbers: CalculationInput) -> dict:
    """
    Multiply two numbers
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Product of a and b
    """
    result = numbers.a * numbers.b
    logger.info(f"Multiplication: {numbers.a} * {numbers.b} = {result}")
    return {"result": result}


@app.post("/divide", operation_id="divide_numbers")
async def divide(numbers: CalculationInput) -> dict:
    """
    Divide two numbers
    
    Args:
        a: First number (numerator)
        b: Second number (denominator)
    
    Returns:
        Quotient of a divided by b
    Raises:
        HTTPException: If division by zero is attempted
    """
    if numbers.b == 0:
        logger.error("Division by zero attempted")
        return {"error": "Cannot divide by zero"}
    result = numbers.a / numbers.b
    logger.info(f"Division: {numbers.a} / {numbers.b} = {result}")
    return {"result": result}

# Original Greeting Tool -------------------------------------------------------


@app.get("/greet", operation_id="greet_user")
async def greet(name: str = "World") -> dict:
    """
    Greets the user with a personalized message.
    
    Args:
        name: The name to include in the greeting (default: 'World')
    
    Returns:
        A greeting message
    """
    logger.info(f"Received request to greet: {name}")
    return {"message": f"Hello, {name}!"}


# Initialize and mount MCP server
try:
    mcp = FastApiMCP(
        app,
        name="Calculator API MCP",
        description="MCP server with calculator tools",
    )
    mcp.mount(mount_path="/sse", transport="sse")
    logger.info("MCP server mounted successfully at /sse")
except Exception as e:
    logger.error(f"Failed to mount MCP server: {str(e)}")
    raise

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="localhost",
        port=8003,
        log_level="info",
        reload=True  # Optional: Enable auto-reload for development
    )

# uvicorn fastapi_mcp_server:app --host localhost --port 8003
