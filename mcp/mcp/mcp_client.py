import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client


async def main():
    # Connect to the server using SSE
    async with sse_client("http://localhost:9000/sse") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools_result = await session.list_tools()
            print(f"Available tools: {tools_result}")
            # Call our calculator tool
            result = await session.call_tool("add", {"a":5, "b":3})
            print(f"Result: {result.content[0].text}")


if __name__ == "__main__":
    asyncio.run(main())
