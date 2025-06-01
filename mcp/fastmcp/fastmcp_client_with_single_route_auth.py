import asyncio
import logging
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport  # Import the specific transport
# from fastmcp.client.transports import SSETransport  # Import the specific transport

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


async def main():
    # Define the authentication headers
    auth_headers = {
        "authorization": "Bearer test-token",
        "x-api-key": "your-secret-api-key"
    }

    # Initialize the SSETransport with the URL and headers
    # The Client will then use this configured transport
    streamable_transport = StreamableHttpTransport(
        url="http://localhost:8002/mcp",
        headers=auth_headers
    )
    # sse_transport = SSETransport(
    #     url="http://localhost:8002/sse",
    #     headers=auth_headers
    # )
    
    # Initialize FastMCP Client with the pre-configured transport
    # async with Client(sse_transport) as client:
    async with Client(streamable_transport) as client:
        try:
            logging.info("Client connected. Listing tools...")
            # List available tools
            tools_result = await client.list_tools()
            logging.info(f"Available tools: {tools_result}")

            # Call the 'add' tool with parameters
            # Make sure your FastMCP server has an 'add' tool
            logging.info("Calling 'add' tool...")
            result = await client.call_tool("add", {"a": 5, "b": 3})
            # FastMCP tool results are typically a list of content objects
            # You'll need to check the type before accessing .text
            if result and hasattr(result[0], 'text'):
                logging.info(f"Result: {result[0].text}")
            else:
                logging.info(f"Tool call result: {result}")

        except Exception as e:
            logging.error(f"Error during client operation: {e}")
            # Re-raise the exception after logging if you want it to propagate
            raise

if __name__ == "__main__":
    asyncio.run(main())

# import httpx

# with httpx.stream("GET", "http://localhost:8002/health") as response:
#     for line in response.iter_lines():
#         if line:
#             print("Event:", line)
