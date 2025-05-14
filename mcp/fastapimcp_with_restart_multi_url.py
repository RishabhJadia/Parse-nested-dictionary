# weather_server.py
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from pydantic import BaseModel
import httpx

app = FastAPI(title="Weather MCP Server", description="MCP server for weather alerts", version="0.1.0")

NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

class AlertRequest(BaseModel):
    state: str

async def make_nws_request(url: str) -> dict | None:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching NWS data: {e}")
            return None

def format_alert(feature: dict) -> str:
    props = feature["properties"]
    return (
        f"Event: {props.get('event', 'Unknown')}\n"
        f"Area: {props.get('areaDesc', 'Unknown')}\n"
        f"Severity: {props.get('severity', 'Unknown')}\n"
        f"Description: {props.get('description', 'No description')}"
    )

@app.post("/alerts", operation_id="get_weather_alerts")
async def get_weather_alerts(request: AlertRequest):
    url = f"{NWS_API_BASE}/alerts/active?area={request.state}"
    data = await make_nws_request(url)
    if not data or not data.get("features"):
        return {"message": f"No active alerts for state: {request.state}"}
    alerts = [format_alert(feature) for feature in data["features"]]
    return {"alerts": alerts}

mcp = FastApiMCP(app, name="Weather", description="Weather alerts", base_url="http://localhost:8000")
mcp.mount()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

--------------------------------------------------
# news_server.py
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv
import os

load_dotenv()
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

app = FastAPI(title="News MCP Server", description="MCP server for news headlines", version="0.1.0")

NEWSAPI_BASE = "https://newsapi.org/v2"

class NewsRequest(BaseModel):
    query: str  # e.g., "technology"

async def make_newsapi_request(url: str) -> dict | None:
    headers = {"Authorization": f"Bearer {NEWSAPI_KEY}"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching NewsAPI data: {e}")
            return None

def format_article(article: dict) -> str:
    return (
        f"Title: {article.get('title', 'Unknown')}\n"
        f"Source: {article.get('source', {}).get('name', 'Unknown')}\n"
        f"Description: {article.get('description', 'No description')}"
    )

@app.post("/headlines", operation_id="get_news_headlines")
async def get_news_headlines(request: NewsRequest):
    url = f"{NEWSAPI_BASE}/everything?q={request.query}&language=en&sortBy=publishedAt"
    data = await make_newsapi_request(url)
    if not data or not data.get("articles"):
        return {"message": f"No recent headlines for query: {request.query}"}
    articles = [format_article(article) for article in data["articles"][:3]]  # Limit to 3
    return {"headlines": articles}

mcp = FastApiMCP(app, name="News", description="News headlines", base_url="http://localhost:8001")
mcp.mount()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
 ------------------------------------------------
# geo_server.py

from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from pydantic import BaseModel
import httpx

app = FastAPI(title="Geo MCP Server", description="MCP server for geocoding", version="0.1.0")

GEOCODING_API_BASE = "https://geocoding-api.open-meteo.com/v1"

class GeoRequest(BaseModel):
    city: str

async def make_geocoding_request(url: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching Geocoding data: {e}")
            return None

@app.post("/coordinates", operation_id="get_city_coordinates")
async def get_city_coordinates(request: GeoRequest):
    url = f"{GEOCODING_API_BASE}/search?name={request.city}&count=1&language=en&format=json"
    data = await make_geocoding_request(url)
    if not data or not data.get("results"):
        return {"message": f"No coordinates found for city: {request.city}"}
    result = data["results"][0]
    return {
        "city": result.get("name"),
        "latitude": result.get("latitude"),
        "longitude": result.get("longitude"),
        "country": result.get("country")
    }

mcp = FastApiMCP(app, name="Geo", description="City coordinates", base_url="http://localhost:8002")
mcp.mount()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
 -----------------------------------------------
# client.py
import asyncio
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
        
        # Server configurations
        servers = {
            "weather_mcp": "http://localhost:8000/mcp",
            "news_mcp": "http://localhost:8001/mcp",
            "geo_mcp": "http://localhost:8002/mcp"
        }

        # Connect to all servers
        connected_servers = []
        for server_name, url in servers.items():
            if await connect_with_retry(client, server_name, url):
                connected_servers.append(server_name)

        if not connected_servers:
            print("No servers connected. Exiting.")
            return

        # Get tools from connected servers
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
                # Attempt to reconnect to all servers
                connected_servers = []
                for server_name, url in servers.items():
                    if await connect_with_retry(client, server_name, url):
                        connected_servers.append(server_name)
                if not connected_servers:
                    print("All reconnections failed. Continuing without MCP servers.")

def main():
    asyncio.run(run_agent())

if __name__ == "__main__":
    main()




