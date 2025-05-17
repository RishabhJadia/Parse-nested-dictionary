import asyncio
import logging
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langgraph.graph import StateGraph, END

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simulated chunk function (split every 5000 chars or by section)
def chunk_openapi_spec(openapi_spec: str, max_tokens: int = 5000) -> list:
    enc = tiktoken.encoding_for_model("gpt-4")
    tokens = enc.encode(openapi_spec)
    chunks = [tokens[i:i+max_tokens] for i in range(0, len(tokens), max_tokens)]
    return [enc.decode(chunk) for chunk in chunks]

# LangChain-compatible LLM
llm = ChatOpenAI(temperature=0, model="gpt-4")  # Or use gpt-3.5-turbo for speed

# Prompt template using provided system prompt
system_prompt = """
You are a Python developer converting OpenAPI spec chunks into Python functions.

Each function should:
- Represent one path from the chunk.
- Use the `requests` library to perform the HTTP call.
- Include proper error handling with `try/except` for request exceptions.
- Include a unique, detailed docstring and parameter descriptions based on the chunk.

Requirements:
- Convert every path; do not merge or skip.
- Do not add extra functions or content.
- Process each chunk independently without altering the order.
- Uniquely describe each function and its parameters.
- Clearly differentiate path, query, and body parameters.

Return only Python code, no explanations. If the chunk is invalid or lacks paths, return:

```python
# Please cross verify all the functions
```

Use the following format for each function:

@mcp.tool()
def {{function_name}}({{param1}}: {{{param1_type}}}, {{param2}}: {{{param2_type}}} = None, token: str = None) -> dict:
    \"\"\"{{function_description}}"""
    {{detail.get("summary")}}. Provide a detailed and unique description of the function based on the OpenAPI specification chunk.'
    Args:
        {{param1}} ({{{param1_type}}}): {{{param1_description}}}
        {{param2}} ({{{param2_type}}}, optional): {{{param2_description}}}. Defaults to None.
        token (str, optional): The authentication token. Default is None.
    \"\"\"
    url = f"{base_url}{{url}}"
    headers = {{}}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.request(method="{{method}}", url=url, headers=headers, params={{query_params}}, json={{body_params}}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return {"error": f"Request error occurred: {req_err}"}

Here is the OpenAPI specification chunk:

{chunk}
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{chunk}")
])

# Memory object
memory = ConversationBufferMemory(memory_key="history", return_messages=True)

# Function to call LLM with memory
async def call_llm_with_memory(state):
    chunk = state["chunk"]
    base_url = state["base_url"]
    messages = prompt_template.format_messages(chunk=chunk, base_url=base_url)
    memory.chat_memory.add_user_message(chunk)

    logger.info(f"Processing chunk of size {len(chunk)}")
    result = await llm.ainvoke(messages)
    memory.chat_memory.add_ai_message(result.content)

    logger.info("Chunk processed successfully")
    return {"chunk": "", "result": result.content}

# Build LangGraph workflow
def build_graph():
    builder = StateGraph()
    builder.add_node("process_chunk", call_llm_with_memory)
    builder.set_entry_point("process_chunk")
    builder.set_finish_point(END)
    builder.add_edge("process_chunk", END)
    return builder.compile()

# Async main function
async def main(openapi_spec: str):
    chunks = chunk_openapi_spec(openapi_spec)
    graph = build_graph()

    combined_result = ""
    for chunk in chunks:
        output = await graph.invoke({"chunk": chunk, "base_url":base_url})
        combined_result += output["result"]

    logger.info("All chunks processed")
    print("Final Generated Code:")
    print(combined_result)
    generated_code = generated_code.replace("```python", "").replace("```", "").strip()
    final_code = f"""# pip install fastmcp==2.3.3 mcp==1.8.1\n# doc: https://gofastmcp.com/getting-started/welcome

import requests
from requests.exceptions import RequestException
from fastmcp import FastMCP

mcp = FastMCP(
    name="{mcp_server_name}Server",
    log_level="DEBUG",  # Sets the logging level
    on_duplicate_tools="warn"  # Warn if tools with the same name are registered (options: 'error', 'warn', 'ignore')
)

{generated_code}

if __name__ == "__main__":
    mcp.run(transport="sse")

# To run from CLI
# fastmcp run {filename} --transport sse --port 9000 --host 0.0.0.0
"""
    logger.info("Python functions generation completed")
    logger.info(f"Final generated code: {final_code}")
    # Clear the memory buffer before returning
    memory.clear()
    logger.info("ConversationBufferMemory cleared")
    return final_code


# Run this with your OpenAPI spec string
if __name__ == "__main__":
    with open("your_openapi.yaml", "r") as f:
        spec = f.read()
    asyncio.run(main(spec))
