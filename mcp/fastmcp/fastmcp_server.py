# https://apidog.com/blog/fastmcp/
import logging


from fastmcp import FastMCP


mcp = FastMCP(
    name="ConfiguredServer",
    # on_duplicate_tools="error" # Set duplicate handling
)
print(mcp.settings.port) # Output: 8002
print(mcp.settings.host)  # Output: 0.0.0.0
print(mcp.settings.stateless_http)  # Output: False
print(mcp.settings.sse_path)  # Output: /sse
# print(mcp.settings.on_duplicate_tools) # Output: "error"

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    logging.info(f"Adding {a} + {b}")
    return a + b

# mcp_app = mcp.http_app(transport="sse")

if __name__ == "__main__":
    mcp.run(transport="sse", host="localhost", port="8002")
    # import uvicorn
    # uvicorn.run(mcp_app, host="localhost", port=8002)

# fastmcp run fastmcp_server.py:mcp --transport sse --host localhost --port 8002
# fastmcp run fastmcp_server.py --transport sse --host localhost --port 8002
# python fastmcp_server.py

# with uvicorn uncomment the line for recommeded for production
# uvicorn fastmcp_server:mcp_app --host 0.0.0.0 --port 8002
