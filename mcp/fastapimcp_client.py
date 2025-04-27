# pip install nest_asyncio
# pip install fastapi-mcp
# pip install uv
# pip install langchain-mcp-adapters==0.0.9

import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient


async def main():
    # Configure the MCP server connection (using SSE transport)
    mcp_config = {
        "user_server": {
            "url": "http://localhost:8050/mcp",  # MCP server endpoint
            "transport": "sse",
        }
    }
    # Connect to the MCP server and load tools
    async with MultiServerMCPClient(mcp_config) as client:
        # Get the available tools
        tools = client.get_tools()

        # Find the get_user tool
        get_user_tool = next(
            (tool for tool in tools if tool.name == "greet_user"), None)
        if not get_user_tool:
            print("Error: get_user tool not found")
            return

        # Define the parameters for the get_user tool
        user_params = {
            "name": "Alice",
            "age": 30,
            "email": "alice@example.com"
        }

        # Directly invoke the get_user tool
        try:
            response = await get_user_tool.ainvoke(user_params)
            print("MCP Server Response:", response)
        except Exception as e:
            print("Error invoking get_user tool:", str(e))

if __name__ == "__main__":
    asyncio.run(main())
