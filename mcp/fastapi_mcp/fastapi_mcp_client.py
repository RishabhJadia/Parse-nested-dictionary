# 1st way
from fastmcp import Client
import asyncio

async def main():
    # Connect to the server using SSE
    async with Client("http://localhost:8003/sse") as client:
        # List available tools
        tools_result = await client.list_tools()
        print(f"Available tools: {tools_result}")
        # Call our calculator tool
        result = await client.call_tool("add_numbers", {"a": 5, "b": 3})
        print(f"Result: {result[0].text}")

if __name__ == "__main__":
    asyncio.run(main())


# 2nd way
# import asyncio
# from fastmcp import Client

# config = {
#     "mcpServers": {
#         "math": {
#             "url": "http://localhost:8003/sse",
#             "transport": "sse"
#         }
#     }
# }


# async def main():
#     client = Client(config)
#     # Connect to the server using SSE
#     async with client:
#         # List available tools
#         tools_result = await client.list_tools()
#         print(f"Available tools: {tools_result}")
#         # Call our calculator tool
#         result = await client.call_tool("add_numbers", {"a": 5, "b": 3})
#         print(f"Result: {result[0].text}")

# if __name__ == "__main__":
#     asyncio.run(main())


    
# 3rd way
# import asyncio
# from mcp import ClientSession
# from mcp.client.sse import sse_client


# async def main():
#     # Connect to the server using SSE
#     async with sse_client("http://localhost:8003/sse") as (read_stream, write_stream):
#         async with ClientSession(read_stream, write_stream) as session:
#             # Initialize the connection
#             await session.initialize()

#             # List available tools
#             tools_result = await session.list_tools()
#             print("Available tools:", tools_result.tools)
#             # Call our calculator tool
#             result = await session.call_tool("add_numbers", {"a": 5, "b": 3})
#             print(f"Result: {result.content[0].text}")

# if __name__ == "__main__":
#     asyncio.run(main())
