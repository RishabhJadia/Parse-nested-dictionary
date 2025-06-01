import asyncio
from fastmcp.client import Client
from fastmcp.client.transports import SSETransport

# Issue fixed as part of PR
# https://github.com/jlowin/fastmcp/issues/595
# https://github.com/jlowin/fastmcp/pull/605

# Configuration with multiple servers
config = {
    "mcpServers": {
        "math": {
            "url": "http://localhost:8003/sse"
        },
        "multiply": {
            "url": "http://localhost:8004/sse"  # This server is down
        }
    }
}


async def main():
    # Create separate clients for each server
    clients = {}
    for server_name, server_config in config["mcpServers"].items():
        transport = SSETransport(server_config["url"])
        client = Client(transport=transport)
        clients[server_name] = client

    # Collect tools from all servers that are up
    all_tools = []

    for server_name, client in clients.items():
        try:
            async with client:
                tools = await client.list_tools()
                # Prefix tool names with server name to avoid conflicts
                prefixed_tools = [
                    {**tool, "name": f"{server_name}.{tool['name']}"} for tool in tools]
                all_tools.extend(prefixed_tools)
                print(
                    f"Tools from {server_name}: {[tool['name'] for tool in prefixed_tools]}")
        except Exception as err:
            print(f"Error loading tools from {server_name}: {err}")

    # Call a specific tool (e.g., math.add) if available
    tool_name = "math.add"
    if tool_name in [tool.name for tool in all_tools]:
        server_name = tool_name.split(".")[0]  # Extract server name (math)
        client = clients[tool_name]
        async with client:
            try:
                result = await client.call_tool("add", {"a": 5, "b": 3})
                print(f"Result from {tool_name}: {result[0].text}")
            except Exception as err:
                print(f"Error calling {tool_name}: {err}")
    else:
        print(f"{tool_name} not available")

if __name__ == "__main__":
    asyncio.run(main())
