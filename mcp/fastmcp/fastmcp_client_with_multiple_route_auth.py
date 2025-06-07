import asyncio
import logging
from fastmcp import Client

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


# Define the authentication headers
auth_headers = {
    "authorization": "Bearer test-token",
    "x-api-key": "your-secret-api-key"
}

config = {
    "mcpServers": {
        "math": {
            "url": "http://localhost:8002/mcp",
            "transport": "streamable-http",
            "headers": auth_headers
        },
        "multiply": {
            "url": "http://localhost:8003/mcp",
            "transport": "streamable-http",
            "headers": auth_headers
        }
    }
}


async def main():
    client = Client(config)
    # Connect to the server using SSE
    async with client:
        # List available tools
        tools_result = await client.list_tools()
        breakpoint()
        print(f"Available tools: {tools_result}")
        # Call our calculator tool
        result = await client.call_tool("math_add", {"a": 5, "b": 3})
        print(f"Result: {result[0].text}")

if __name__ == "__main__":
    asyncio.run(main())
