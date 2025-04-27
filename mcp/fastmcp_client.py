# pip install nest_asyncio
# pip install uv
# pip install fastmcp
# mcp dev server.py # The easiest way to test your server is using the MCP Inspector:
# Using UV(recommended)
# uv run server.py

import asyncio
import nest_asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

nest_asyncio.apply()  # Needed to run interactive python

"""
Make sure:
1. The server is running before running this script.
2. The server is configured to use SSE transport.
3. The server is listening on port 8050.

To run the server:
uv run server.py
"""


async def main():
    # Connect to the server using SSE
    async with sse_client("http://localhost:8050/sse") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools_result = await session.list_tools()
            print("Available tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            user_params = {
                "name": "Alice",
                "age": 30,
                "email": "alice@example.com"
            }
            # Call our calculator tool
            result = await session.call_tool("greet", arguments=user_params)
            print(f"2 + 3 = {result.content[0].text}")


if __name__ == "__main__":
    asyncio.run(main())
