import logging

from mcp.server.fastmcp import FastMCP


mcp = FastMCP(
    name="ConfiguredServer",
    host="localhost",
    port=8001,  # Directly maps to ServerSettings
    # on_duplicate_tools="error" # Set duplicate handling
)
print(mcp.settings.port)  # Output: 8001
print(mcp.settings.host)  # Output: localhost
print(mcp.settings.stateless_http)  # Output: False
print(mcp.settings.sse_path)  # Output: /sse
# print(mcp.settings.on_duplicate_tools) # Output: "error"


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    logging.info(f"Adding {a} + {b}")
    return a + b


if __name__ == "__main__":
    mcp.run(transport="sse")

# fastmcp run mcp_server.py:mcp --transport sse
# fastmcp run mcp_server.py --transport sse
# mcp run mcp_server.py:mcp --transport sse
# python mcp_server.py
