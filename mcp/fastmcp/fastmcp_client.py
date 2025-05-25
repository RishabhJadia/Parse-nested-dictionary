import asyncio
from fastmcp import Client

# # 1st simple way
async def main():
    # Connect to the server using SSE
    async with Client("http://localhost:8002/sse") as client:
        # List available tools
        tools_result = await client.list_tools()
        print(f"Available tools: {tools_result}")
        # Call our calculator tool
        result = await client.call_tool("add", {"a": 5, "b": 3})
        print(f"Result: {result[0].text}")

if __name__ == "__main__":
    asyncio.run(main())


# # 2nd multiple servers when sure all are up and running
# config = {
#     "mcpServers": {
#         "math": {
#             "url": "http://localhost:8002/sse"
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
#         result = await client.call_tool("add", {"a": 5, "b": 3})
#         print(f"Result: {result[0].text}")

# if __name__ == "__main__":
#     asyncio.run(main())
