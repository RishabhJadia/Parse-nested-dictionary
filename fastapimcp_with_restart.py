# server.py
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from pydantic import BaseModel
import httpx
from typing import Any

# Initialize FastAPI app
app = FastAPI(
    title="Weather API MCP",
    description="MCP server for weather alerts",
    version="0.1.0"
)

# Constants for NWS API
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

# Pydantic model for request
class AlertRequest(BaseModel):
    state: str  # e.g., "CA" for California

# Helper function to make NWS API request
async def make_nws_request(url: str) -> dict[str, Any] | None:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching NWS data: {e}")
            return None

# Format weather alert
def format_alert(feature: dict) -> str:
    props = feature["properties"]
    return (
        f"Event: {props.get('event', 'Unknown')}\n"
        f"Area: {props.get('areaDesc', 'Unknown')}\n"
        f"Severity: {props.get('severity', 'Unknown')}\n"
        f"Description: {props.get('description', 'No description available')}\n"
        f"Instructions: {props.get('instruction', 'No specific instructions provided')}"
    )

# FastAPI endpoint to get weather alerts
@app.post("/alerts", operation_id="get_weather_alerts")
async def get_weather_alerts(request: AlertRequest):
    url = f"{NWS_API_BASE}/alerts/active?area={request.state}"
    data = await make_nws_request(url)
    if not data or not data.get("features"):
        return {"message": f"No active alerts for state: {request.state}"}
    alerts = [format_alert(feature) for feature in data["features"]]
    return {"alerts": alerts}

# Initialize and mount FastAPI-MCP
mcp = FastApiMCP(
    app,
    name="Weather MCP",
    description="MCP server for accessing weather alerts",
    base_url="http://localhost:8000"
)
mcp.mount()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
-------------------------------------------------------
# client.py
import asyncio
import os
import time
import random
from typing import Dict, List, Union
from contextlib import AsyncExitStack
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

# Extract AI message content
def extract_ai_message_content(response: Dict[str, List[Union[AIMessage, HumanMessage]]]) -> str:
    for message in response.get('messages', []):
        if isinstance(message, AIMessage) and message.content:
            return message.content
    return ""

# Connect to MCP server with retry logic
async def connect_with_retry(client: MultiServerMCPClient, server_name: str, url: str, max_retries: int = 5):
    base_delay = 1  # seconds
    max_delay = 30  # seconds
    for attempt in range(max_retries):
        try:
            print(f"Connecting to {server_name} (Attempt {attempt + 1}/{max_retries})...")
            await client.connect_to_server(server_name, type="sse", url=url)
            print(f"Successfully connected to {server_name}")
            return True
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Failed to connect to {server_name} after {max_retries} attempts: {e}")
                return False
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0, 0.1 * delay)
            print(f"Connection to {server_name} failed: {e}. Retrying in {delay + jitter:.2f}s")
            await asyncio.sleep(delay + jitter)
    return False

async def run_agent():
    async with AsyncExitStack() as stack:
        client = await stack.enter_async_context(MultiServerMCPClient())
        
        # Connect to FastAPI-MCP server
        server_name = "weather_mcp"
        mcp_url = "http://localhost:8000/mcp"
        if not await connect_with_retry(client, server_name, mcp_url):
            print("Failed to connect to MCP server. Exiting.")
            return

        # Get tools from the MCP server
        tools = client.get_tools()
        if not tools:
            print("No tools available. Exiting.")
            return

        # Create and run the agent
        model = ChatOpenAI(model="gpt-4o")
        agent = create_react_agent(model, tools)

        # Process user queries
        while True:
            query = input("Enter your query (or 'quit' to exit): ")
            if query.lower() == "quit":
                break
            try:
                response = await agent.ainvoke({"messages": query})
                print("Response:", extract_ai_message_content(response))
            except Exception as e:
                print(f"Error processing query: {e}")
                # Attempt to reconnect
                if not await connect_with_retry(client, server_name, mcp_url):
                    print("Reconnection failed. Continuing without MCP server.")

def main():
    asyncio.run(run_agent())

if __name__ == "__main__":
    main()
