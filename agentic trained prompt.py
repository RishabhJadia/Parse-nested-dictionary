import llm_api  # Hypothetical LLM API library

input_data = [{'name': 'job1', 'seal': '88153', 'instances': ['L1', 'L0']}]
prompt = f"Given the following input data: {input_data}, process it as follows: if there are multiple entries, group all job names by their seal into a list of dictionaries with seal as key and list of job names as value; if there is only one entry, extract each job name and its seal into a list of dictionaries with job name as key and seal as value. Return the result in JSON-like format."
response = llm_api.call(prompt)
print(response)  # Expect: [{'job1': '88153'}]
------------------------------------------------------------------------------
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI  # or any other LLM you prefer
from langchain.chains import LLMChain

# Initialize the LLM (replace with your preferred model and API key)
llm = OpenAI(temperature=0, openai_api_key="your-api-key-here")

# Create a prompt template that instructs the LLM to handle API calls generically
prompt_template = PromptTemplate(
    input_variables=["api_url", "method", "headers", "payload"],
    template="""
    You are an API calling assistant. Your task is to generate a response based on an API call without hardcoding the logic. 
    Use the following information to simulate an API call and process the response:
    - API URL: {api_url}
    - Method: {method}
    - Headers: {headers}
    - Payload: {payload}

    Instructions:
    1. Simulate calling the API with the provided details.
    2. If the response status is 200:
       - If response['results'] is empty (==[]), return {{"error": "No results found in API response"}}
       - If response['results'] is not empty, return the contents of response['results']
    3. If the response status is not 200 or an exception occurs, return {{"error": "API call failed with status {status} or exception {exception}"}}

    Provide the response in JSON format based on these rules. Do not write actual API calling code, just simulate the outcome.
    """
)

# Create a chain to process the prompt
api_chain = LLMChain(llm=llm, prompt=prompt_template)

# Function to call the API dynamically
def call_api_dynamic(api_url, method="GET", headers=None, payload=None):
    # Default headers and payload if not provided
    headers = headers or {}
    payload = payload or {}
    
    # Pass the kwargs to the chain
    response = api_chain.run({
        "api_url": api_url,
        "method": method,
        "headers": str(headers),
        "payload": str(payload)
    })
    
    # Assuming the LLM returns a JSON string, parse it
    # In a real scenario, you might need to clean the response
    import json
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {"error": "Failed to parse API response"}

# Example usage
if __name__ == "__main__":
    # Test case 1: Successful call with results
    result1 = call_api_dynamic(
        api_url="https://api.example.com/data",
        method="POST",
        headers={"Authorization": "Bearer token123"},
        payload={"query": "test"}
    )
    print("Test 1:", result1)

    # Test case 2: Successful call with empty results
    result2 = call_api_dynamic(
        api_url="https://api.example.com/empty",
        method="GET"
    )
    print("Test 2:", result2)

    # Test case 3: Failed call
    result3 = call_api_dynamic(
        api_url="https://api.example.com/fail",
        method="GET"
    )
    print("Test 3:", result3)
-------------------------------------------------------------------------
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_community.llms import OpenAI
from langchain.chains import LLMChain
from langchain.tools import tool, Tool
from langchain.agents import initialize_agent, AgentType
import requests
import json
import uuid

# Jobmask API Tool
@tool
def fetch_jobmask(seal_id: str = None, jobmask: str = None):
    """API call to fetch jobmask or seal_id details."""
    params = {}
    if seal_id:
        params["seal"] = seal_id
    elif jobmask:
        params["name"] = jobmask
    # Replace with actual API endpoint
    try:
        response = requests.get("https://your-jobmask-api.com/fetch", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API call failed with status {response.status_code}"}
    except Exception as e:
        return {"error": f"API call failed with exception {str(e)}"}

# Prompt Template for Job Mask Processing
jobmask_prompt = PromptTemplate(
    input_variables=["user_input", "environment"],
    template="""
    You are a job mask processing assistant for Autosys. Process the following user input and return a JSON response.
    Default environment is {environment}. Other possible environments are: prod, dev, qa, uat, test.
    User input: {user_input}

    Instructions:
    1. Parse the user input to extract seal_id, jobmask, and environment (if specified, else use default).
    2. Determine the action (query, register, or synonyms like get, fetch, lookup for query; create, add for register).
    3. Create a JSON response with keys: jobmask, environment, seal_id, next_environment, action, error.
       - jobmask: name of jobmask if provided, else None
       - environment: prod, dev, qa, uat, or test (default to {environment})
       - seal_id: extracted seal_id if provided, else None
       - next_environment: an environment not yet tried (e.g., dev if prod is current)
       - action: query or register based on input
       - error: None if no error, otherwise an error message
    4. If error is not None, return immediately with only the error key populated.
    5. Return the JSON as a string.

    Example inputs and outputs:
    - Input: "get the jobmask mapped to seal id 88153 for product autosys"
      Output: {{"jobmask": null, "environment": "prod", "seal_id": "88153", "next_environment": "dev", "action": "query", "error": null}}
    - Input: "lookup jobmask mapped to seal id 88153 for platform autosys in dev"
      Output: {{"jobmask": null, "environment": "dev", "seal_id": "88153", "next_environment": "qa", "action": "query", "error": null}}
    """
)

# Initialize LLM and Chain
llm = OpenAI(temperature=0, openai_api_key="your-openai-api-key")
jobmask_chain = LLMChain(llm=llm, prompt=jobmask_prompt)

# Process jobmask request and call API if needed
def process_jobmask_request(user_input, default_env="prod"):
    response = jobmask_chain.run({"user_input": user_input, "environment": default_env})
    try:
        json_response = json.loads(response)
    except json.JSONDecodeError:
        return {"error": "Failed to parse LLM response"}

    if json_response.get("error") is not None:
        return json_response

    # Create Tool object
    jobmask_tool = Tool(
        name="fetch_jobmask",
        func=fetch_jobmask,
        description="Fetches jobmask or seal_id details from an API"
    )

    # Call API based on response
    if json_response["seal_id"]:
        api_result = jobmask_tool.run({"seal_id": json_response["seal_id"]})
    elif json_response["jobmask"]:
        api_result = jobmask_tool.run({"jobmask": json_response["jobmask"]})
    else:
        return {"error": "No seal_id or jobmask provided"}

    # Combine API result with initial response
    if "error" in api_result:
        json_response["error"] = api_result["error"]
    else:
        json_response["jobmask"] = api_result.get("data", {}).get("name", json_response["jobmask"])
    return json_response

# Chatbot APIs
def invoke_chat(message):
    try:
        response = requests.post(
            "https://your-api.com/chat/invoke",
            json={"Message": message}
        )
        if response.status_code == 200:
            return response.json()
        return {"Message": "Error: API call failed", "ConverdationId": None}
    except Exception as e:
        return {"Message": f"Error: {str(e)}", "ConverdationId": None}

def invoke_followup(message, conversation_id):
    try:
        response = requests.post(
            "https://your-api.com/chat/invoke/followup",
            json={"Message": message, "ConverdationId": conversation_id}
        )
        if response.status_code == 200:
            return response.json()
        return {"ConverdationId": conversation_id, "FollowUpQuestions": ["Error: API call failed"]}
    except Exception as e:
        return {"ConverdationId": conversation_id, "FollowUpQuestions": [f"Error: {str(e)}"]}

# Streamlit Chatbot
def main():
    st.title("Autosys Jobmask Chatbot")

    # Initialize session state
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("Ask about job masks or chat..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Check if it's a jobmask request
        if "jobmask" in prompt.lower() or "seal" in prompt.lower():
            with st.chat_message("assistant"):
                result = process_jobmask_request(prompt)
                response_text = json.dumps(result, indent=2)
                st.markdown(f"Jobmask Response:\n```\n{response_text}\n```")
                st.session_state.messages.append({"role": "assistant", "content": response_text})
        else:
            # Chatbot interaction
            with st.chat_message("assistant"):
                if st.session_state.conversation_id is None:
                    chat_response = invoke_chat(prompt)
                    st.session_state.conversation_id = chat_response["ConverdationId"]
                    st.markdown(chat_response["Message"])
                    st.session_state.messages.append({"role": "assistant", "content": chat_response["Message"]})
                else:
                    followup_response = invoke_followup(prompt, st.session_state.conversation_id)
                    st.markdown(f"Response: {prompt}\nFollow-up Questions: {', '.join(followup_response['FollowUpQuestions'])}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Response: {prompt}\nFollow-up Questions: {', '.join(followup_response['FollowUpQuestions'])}"})

if __name__ == "__main__":
    main()
  --------------------------------------------------------
Below is the complete updated code incorporating the changes we discussed. This version includes the logic to:

Detect and require a product (Autosys or Control-M) if not specified.
Persist context across prompts using jobmask_context (e.g., product, accumulated user input).
Ask for missing information (e.g., jobmask or seal_id) when processing Autosys requests.
Reset context after a successful response or cancellation.


import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_community.llms import OpenAI
from langchain.chains import LLMChain
from langchain.tools import tool, Tool
import requests
import json

# Jobmask API Tool
@tool
def fetch_jobmask(seal_id: str = None, jobmask: str = None):
    """API call to fetch jobmask or seal_id details."""
    params = {}
    if seal_id:
        params["seal"] = seal_id
    elif jobmask:
        params["name"] = jobmask
    try:
        response = requests.get("https://your-jobmask-api.com/fetch", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API call failed with status {response.status_code}"}
    except Exception as e:
        return {"error": f"API call failed with exception {str(e)}"}

# Prompt Template for Job Mask Processing
jobmask_prompt = PromptTemplate(
    input_variables=["user_input", "environment"],
    template="""
    You are a job mask processing assistant for Autosys. Process the following user input and return a JSON response.
    Default environment is {environment}. Other possible environments are: prod, dev, qa, uat, test.
    User input: {user_input}

    Instructions:
    1. Parse the user input to extract seal_id, jobmask, and environment (if specified, else use default).
    2. Determine the action (query, register, or synonyms like get, fetch, lookup for query; create, add for register).
    3. Create a JSON response with keys: jobmask, environment, seal_id, next_environment, action, error, missing.
       - jobmask: name of jobmask if provided, else None
       - environment: prod, dev, qa, uat, or test (default to {environment})
       - seal_id: extracted seal_id if provided, else None
       - next_environment: an environment not yet tried (e.g., dev if prod is current)
       - action: query or register based on input, default to "query" if unclear
       - error: None if no error, otherwise an error message
       - missing: list of missing required fields (e.g., ["seal_id"] or ["seal_id", "jobmask"])
    4. If neither seal_id nor jobmask is provided, set error to "Insufficient information" and add missing fields to 'missing'.
    5. If error is not None, return immediately with error and missing keys populated.
    6. Return the JSON as a string.
    """
)

# Initialize LLM and Chain
llm = OpenAI(temperature=0, openai_api_key="your-openai-api-key")
jobmask_chain = LLMChain(llm=llm, prompt=jobmask_prompt)

# Process jobmask request and call API if complete
def process_jobmask_request(user_input, default_env="prod"):
    response = jobmask_chain.run({"user_input": user_input, "environment": default_env})
    try:
        json_response = json.loads(response)
    except json.JSONDecodeError:
        return {"error": "Failed to parse LLM response", "missing": []}

    if json_response.get("error") is not None:
        return json_response

    if not json_response["seal_id"] and not json_response["jobmask"]:
        json_response["error"] = "Insufficient information"
        return json_response

    jobmask_tool = Tool(
        name="fetch_jobmask",
        func=fetch_jobmask,
        description="Fetches jobmask or seal_id details from an API"
    )

    if json_response["seal_id"]:
        api_result = jobmask_tool.run({"seal_id": json_response["seal_id"]})
    else:
        api_result = jobmask_tool.run({"jobmask": json_response["jobmask"]})

    if "error" in api_result:
        json_response["error"] = api_result["error"]
    else:
        json_response["jobmask"] = api_result.get("data", {}).get("name", json_response["jobmask"])
    return json_response

# Chatbot APIs
def invoke_chat(message):
    try:
        response = requests.post(
            "https://your-api.com/chat/invoke",
            json={"Message": message}
        )
        if response.status_code == 200:
            return response.json()
        return {"Message": "Error: API call failed", "ConverdationId": None}
    except Exception as e:
        return {"Message": f"Error: {str(e)}", "ConverdationId": None}

def invoke_followup(message, conversation_id):
    try:
        response = requests.post(
            "https://your-api.com/chat/invoke/followup",
            json={"Message": message, "ConverdationId": conversation_id}
        )
        if response.status_code == 200:
            return response.json()
        return {"ConverdationId": conversation_id, "FollowUpQuestions": ["Error: API call failed"]}
    except Exception as e:
        return {"ConverdationId": conversation_id, "FollowUpQuestions": [f"Error: {str(e)}"]}

# Streamlit Chatbot
def main():
    st.title("Autosys Jobmask Chatbot")

    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "jobmask_context" not in st.session_state:
        st.session_state.jobmask_context = {"user_input": "", "attempts": 0, "product": None}
    if "max_attempts" not in st.session_state:
        st.session_state.max_attempts = 3

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about job masks or chat..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Handle stop/cancel command
        if prompt.lower() in ["stop", "cancel", "exit"]:
            if st.session_state.jobmask_context["user_input"]:
                st.session_state.jobmask_context = {"user_input": "", "attempts": 0, "product": None}
                with st.chat_message("assistant"):
                    st.markdown("Request cancelled. How can I assist you now?")
                    st.session_state.messages.append({"role": "assistant", "content": "Request cancelled. How can I assist you now?"})
            return

        # Detect product (autosys or controlm)
        prompt_lower = prompt.lower()
        if "autosys" in prompt_lower:
            st.session_state.jobmask_context["product"] = "autosys"
        elif "controlm" in prompt_lower:
            st.session_state.jobmask_context["product"] = "controlm"

        # If no product is defined yet, ask for it
        if not st.session_state.jobmask_context["product"]:
            with st.chat_message("assistant"):
                response = "Can you provide the product, either Autosys or Control-M?"
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            return

        # Handle product-specific request
        if st.session_state.jobmask_context["product"] == "autosys":
            with st.chat_message("assistant"):
                # Accumulate user input
                st.session_state.jobmask_context["user_input"] += f" {prompt}" if st.session_state.jobmask_context["user_input"] else prompt
                st.session_state.jobmask_context["attempts"] += 1

                result = process_jobmask_request(st.session_state.jobmask_context["user_input"])
                if result.get("error") and result.get("missing"):
                    if st.session_state.jobmask_context["attempts"] >= st.session_state.max_attempts:
                        st.session_state.jobmask_context = {"user_input": "", "attempts": 0, "product": None}
                        st.markdown("Max attempts reached. Request cancelled. Please provide complete information next time.")
                        st.session_state.messages.append({"role": "assistant", "content": "Max attempts reached. Request cancelled. Please provide complete information next time."})
                    else:
                        missing_fields = ", ".join(result["missing"])
                        followup_msg = f"Please provide the missing information: {missing_fields}"
                        chat_response = invoke_chat(followup_msg)
                        st.session_state.conversation_id = chat_response["ConverdationId"]
                        st.markdown(followup_msg)
                        st.session_state.messages.append({"role": "assistant", "content": followup_msg})
                else:
                    st.session_state.jobmask_context = {"user_input": "", "attempts": 0, "product": None}
                    response_text = json.dumps(result, indent=2)
                    st.markdown(f"Jobmask Response:\n```\n{response_text}\n```")
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
        else:
            # General chat handling (e.g., for Control-M or other queries)
            with st.chat_message("assistant"):
                if st.session_state.conversation_id is None:
                    chat_response = invoke_chat(prompt)
                    st.session_state.conversation_id = chat_response["ConverdationId"]
                    st.markdown(chat_response["Message"])
                    st.session_state.messages.append({"role": "assistant", "content": chat_response["Message"]})
                else:
                    followup_response = invoke_followup(prompt, st.session_state.conversation_id)
                    st.markdown(f"Response: {prompt}\nFollow-up Questions: {', '.join(followup_response['FollowUpQuestions'])}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Response: {prompt}\nFollow-up Questions: {', '.join(followup_response['FollowUpQuestions'])}"})

if __name__ == "__main__":
    main()

----------------------------------------------------
#Langgraph
from langchain_core.language_models.llms import LLM
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from typing import Optional, List, Dict, Any, TypedDict, Annotated
from langchain.tools import tool

# Define the CustomLLM
class CustomLLM(LLM):
    """A custom LLM with simple logic."""
    model_name: str = "custom_model"
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """Custom logic: Echoes the prompt or suggests a search."""
        if "search" in prompt.lower():
            return "I suggest searching for this!"
        return f"Custom response to: {prompt}"
    
    @property
    def _llm_type(self) -> str:
        return "custom_llm"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}

# Instantiate the custom LLM
custom_llm = CustomLLM()

# Define the state
class State(TypedDict):
    messages: Annotated[list, "A list of messages"]

# Define the LLM node
def llm_node(state: State) -> State:
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        response = custom_llm(last_message.content)
        state["messages"].append(AIMessage(content=response))
    return state

# Define the search tool
@tool
def search_web(query: str) -> str:
    """Mock web search tool."""
    return f"Search results for {query}"

# Define the tool node
def tool_node(state: State) -> State:
    last_message = state["messages"][-1].content
    result = search_web(last_message)
    state["messages"].append(AIMessage(content=result))
    return state

# Create the graph
graph_builder = StateGraph(State)

# Add nodes
graph_builder.add_node("llm", llm_node)
graph_builder.add_node("tool", tool_node)

# Define entry point
graph_builder.set_entry_point("llm")

# Add conditional edges from LLM node
graph_builder.add_conditional_edges(
    "llm",
    lambda state: "tool" if "search" in state["messages"][-1].content.lower() else END
)

# Add edge from tool to end
graph_builder.add_edge("tool", END)

# Compile the graph
graph = graph_builder.compile()

# Test the graph
# Test Case 1: Normal input
initial_state = {"messages": [HumanMessage(content="Hello, how are you?")]}
result = graph.invoke(initial_state)
print("Test 1 Output:")
for message in result["messages"]:
    print(f"{message.type}: {message.content}")

# Test Case 2: Trigger the search tool
initial_state = {"messages": [HumanMessage(content="Search for AI news")]}
result = graph.invoke(initial_state)
print("\nTest 2 Output:")
for message in result["messages"]:
    print(f"{message.type}: {message.content}")
----------------------------------------------------------------------------------------------------
from langchain_core.language_models.llms import LLM
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END, MessageState
from typing import Optional, List, Dict, Any
import requests
import json

# Define the PromptTemplate for Jobmask API
jobmask_prompt_template = PromptTemplate(
    input_variables=["history", "input"],
    template="""
You are an assistant that processes user requests for the Jobmask API. The API requires:
- Required parameters: environment (string), product (string)
- Optional parameters: seal (string), name (string), page_size (string, default "10")

Given the conversation history and user input, extract the parameters and return a JSON response.
- If all required parameters are present, return: {"action": "call_tool", "query_params": {...}, "context": "..."}
- If any required parameters are missing, return: {"error": "...", "message": "..."}

Conversation history:
{history}

User input:
{input}

Return your response as a JSON string.
"""
)

# Define the CustomLLM with API call
class CustomLLM(LLM):
    model_name: str = "custom_model"
    prompt_template: PromptTemplate
    api_endpoint: str = "http://your-api-host/chat/invoke"  # Replace with actual endpoint
    
    def __init__(self, prompt_template: PromptTemplate, api_endpoint: Optional[str] = None):
        super().__init__()
        self.prompt_template = prompt_template
        if api_endpoint:
            self.api_endpoint = api_endpoint
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        # Get history from kwargs (passed via state)
        history = kwargs.get("history", [])
        history_str = "\n".join([msg.content for msg in history])
        
        # Format the prompt using the PromptTemplate
        formatted_prompt = self.prompt_template.format(history=history_str, input=prompt)
        
        # Prepare payload for /chat/invoke
        payload = {"Questions": formatted_prompt}
        
        # Call the external API
        try:
            response = requests.post(self.api_endpoint, json=payload)
            response.raise_for_status()
            # Assume the API returns JSON directly
            return response.text  # Return raw JSON string
        except requests.exceptions.RequestException as e:
            return json.dumps({"error": f"Failed to call /chat/invoke: {str(e)}"})
    
    @property
    def _llm_type(self) -> str:
        return "custom_llm"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name, "prompt_template": str(self.prompt_template), "api_endpoint": self.api_endpoint}

# Instantiate the custom LLM with the PromptTemplate and API endpoint
custom_llm = CustomLLM(prompt_template=jobmask_prompt_template, api_endpoint="http://your-api-host/chat/invoke")

# Define the LLM node
def llm_node(state: MessageState) -> MessageState:
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        # Pass full history as context
        response = custom_llm(last_message.content, history=state["messages"][:-1])
        state["messages"].append(AIMessage(content=response))
    return state

# Define the search tool
@tool
def search_jobmask_api(query_params: Dict[str, str]) -> str:
    """Tool to call the Jobmask API with query parameters."""
    try:
        api_url = "https://api.jobmask.com/search"  # Replace with actual Jobmask API URL
        response = requests.get(api_url, params=query_params)
        response.raise_for_status()
        data = response.json()
        return json.dumps({"result": data})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"API call failed: {str(e)}"})

# Define the tool node
def tool_node(state: MessageState) -> MessageState:
    # Get the LLM's JSON response (last message)
    llm_response = json.loads(state["messages"][-1].content)
    if llm_response.get("action") == "call_tool":
        query_params = llm_response["query_params"]
        result = search_jobmask_api(query_params)
        state["messages"].append(AIMessage(content=result))
    return state

# Define the router function
def router_function(state: MessageState) -> str:
    # Parse the LLM's JSON response
    last_message = state["messages"][-1].content
    try:
        response = json.loads(last_message)
        if response.get("action") == "call_tool":
            return "tool"
    except json.JSONDecodeError:
        pass
    return END

# Create the graph
graph_builder = StateGraph(MessageState)
graph_builder.add_node("llm", llm_node)
graph_builder.add_node("tool", tool_node)
graph_builder.set_entry_point("llm")
graph_builder.add_conditional_edges("llm", router_function)
graph_builder.add_edge("tool", END)
graph = graph_builder.compile()

# Test cases
test_cases = [
    "Get all the jobmask for product autosys of prod environment",
    "Get all the jobmask for product autosys of prod environment with page_size 10",
    "Get all the jobmask for product autosys of prod environment with page_size 10 and seal 12345",
    "Get seal for product autosys of prod environment with page_size 10 and name slrad",
    "Get jobmask with seal 12345"  # Corner case: missing required params
]

for i, test_input in enumerate(test_cases, 1):
    print(f"\nTest Case {i}: {test_input}")
    initial_state = {"messages": [HumanMessage(content=test_input)]}
    result = graph.invoke(initial_state)
    for message in result["messages"]:
        print(f"{message.type}: {message.content}")
----------------------------------------------------------

from langchain_core.language_models.llms import LLM
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END, MessageGraph
from typing import Optional, List, Dict, Any
import requests
import json
from langchain_core.tools import tool

# Enhanced PromptTemplate with comprehensive synonym support
multi_tool_prompt_template = PromptTemplate(
    input_variables=["history", "input"],
    template="""
You are an assistant handling casual conversation, Jobmask API (GET and PATCH), and Weather API requests.

1. **Casual Conversation**: For greetings, questions, or non-API requests (e.g., "Hi", "What is Autosys?"), respond with plain text.
2. **Jobmask API (GET)**:
   - Required: environment (e.g., "prod", "dev", "test"), product ("autosys" or "controlm")
   - Optional: seal (string), name (string), page_size (string, default "10")
   - Synonyms for "get": "get", "retrieve", "fetch", "list", "show", "display", "pull", "grab"
   - Environment synonyms: "production" → "prod", "development" → "dev", "testing" → "test"
   - Product synonyms: "auto" → "autosys", "ctrl" → "controlm"
   - If input or history implies a GET intent (e.g., "jobmask" with "get" synonyms), return: {"action": "call_tool", "tool": "jobmask", "query_params": {...}, "context": "..."}
   - If parameters are missing/invalid, return: {"error": "...", "message": "..."}
3. **Jobmask API (PATCH)**:
   - Required: environment, product, name, seal
   - Synonyms for "patch": "update", "modify", "change", "edit", "alter", "adjust", "revise"
   - Use same environment/product synonym mapping as GET
   - If input or history implies a PATCH intent, return: {"action": "call_tool", "tool": "jobmask_patch", "query_params": {...}, "context": "..."}
   - If parameters are missing/invalid, return: {"error": "...", "message": "..."}
4. **Weather API**:
   - Required: city (string)
   - Synonyms for "weather": "weather", "forecast", "temperature", "climate"
   - If input mentions weather synonyms or "city", return: {"action": "call_tool", "tool": "weather", "query_params": {"city": "..."}, "context": "..."}

Conversation history:
{history}

User input:
{input}

Return plain text for casual responses or a JSON object for tool requests/errors. Response will be wrapped in {"Message": <your_response>}.
"""
)

# Custom LLM class
class CustomLLM(LLM):
    model_name: str = "custom_model"
    api_endpoint: str = "http://your-api-host/chat/invoke"  # Replace with your endpoint
    
    def __init__(self, api_endpoint: Optional[str] = None):
        super().__init__()
        if api_endpoint:
            self.api_endpoint = api_endpoint
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        payload = {"Questions": prompt}
        try:
            response = requests.post(self.api_endpoint, json=payload)
            response.raise_for_status()
            api_response = response.json()
            return json.dumps({"Message": api_response.get("Message", "Error: 'Message' key missing")})
        except requests.exceptions.RequestException as e:
            return json.dumps({"Message": f"Failed to call /chat/invoke: {str(e)}"})
    
    @property
    def _llm_type(self) -> str:
        return "custom_llm"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name, "api_endpoint": self.api_endpoint}

# Instantiate the LLM
custom_llm = CustomLLM(api_endpoint="http://your-api-host/chat/invoke")

# Define Jobmask GET tool
@tool
def jobmask_tool(query_params: Dict[str, str]) -> str:
    """Tool to call Jobmask API with GET request."""
    try:
        api_url = "https://api.jobmask.com/search"  # Replace with actual URL
        response = requests.get(api_url, params=query_params)
        response.raise_for_status()
        return json.dumps({"result": response.json()})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Jobmask GET failed: {str(e)}"})

# Define Jobmask PATCH tool
@tool
def jobmask_patch_tool(query_params: Dict[str, str]) -> str:
    """Tool to call Jobmask API with PATCH request."""
    try:
        api_url = "https://api.jobmask.com/update"  # Replace with actual URL
        response = requests.patch(api_url, json=query_params)
        response.raise_for_status()
        return json.dumps({"result": response.json()})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Jobmask PATCH failed: {str(e)}"})

# Define Weather tool
@tool
def weather_tool(query_params: Dict[str, str]) -> str:
    """Tool to call Weather API."""
    try:
        api_url = "https://api.weather.example.com/weather"  # Replace with actual URL
        response = requests.get(api_url, params=query_params)
        response.raise_for_status()
        return json.dumps({"result": response.json()})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Weather API failed: {str(e)}"})

# LLM Node
def llm_node(state: MessageGraph) -> MessageGraph:
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        history = "\n".join([msg.content for msg in state["messages"][:-1]])
        prompt = multi_tool_prompt_template.format(history=history, input=last_message.content)
        response = custom_llm(prompt)
        state["messages"].append(AIMessage(content=response))
    return state

# Tool Nodes
def jobmask_tool_node(state: MessageGraph) -> MessageGraph:
    last_message = json.loads(state["messages"][-1].content)["Message"]
    inner_content = json.loads(last_message) if isinstance(last_message, str) else last_message
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "jobmask":
        result = jobmask_tool(inner_content["query_params"])
        state["messages"].append(AIMessage(content=result))
    return state

def jobmask_patch_tool_node(state: MessageGraph) -> MessageGraph:
    last_message = json.loads(state["messages"][-1].content)["Message"]
    inner_content = json.loads(last_message) if isinstance(last_message, str) else last_message
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "jobmask_patch":
        result = jobmask_patch_tool(inner_content["query_params"])
        state["messages"].append(AIMessage(content=result))
    return state

def weather_tool_node(state: MessageGraph) -> MessageGraph:
    last_message = json.loads(state["messages"][-1].content)["Message"]
    inner_content = json.loads(last_message) if isinstance(last_message, str) else last_message
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "weather":
        result = weather_tool(inner_content["query_params"])
        state["messages"].append(AIMessage(content=result))
    return state

# Router Function
def router_function(state: MessageGraph) -> str:
    last_message = json.loads(state["messages"][-1].content)["Message"]
    try:
        inner_content = json.loads(last_message) if isinstance(last_message, str) else last_message
        if inner_content.get("action") == "call_tool":
            tool_name = inner_content.get("tool")
            if tool_name == "jobmask":
                return "jobmask_tool"
            elif tool_name == "jobmask_patch":
                return "jobmask_patch_tool"
            elif tool_name == "weather":
                return "weather_tool"
    except json.JSONDecodeError:
        pass
    return END

# Build Graph
graph_builder = StateGraph(MessageGraph)
graph_builder.add_node("llm", llm_node)
graph_builder.add_node("jobmask_tool", jobmask_tool_node)
graph_builder.add_node("jobmask_patch_tool", jobmask_patch_tool_node)
graph_builder.add_node("weather_tool", weather_tool_node)
graph_builder.set_entry_point("llm")
graph_builder.add_conditional_edges("llm", router_function)
graph_builder.add_edge("jobmask_tool", END)
graph_builder.add_edge("jobmask_patch_tool", END)
graph_builder.add_edge("weather_tool", END)
graph = graph_builder.compile()

# 30 Test Cases Covering All Scenarios
test_cases = [
    # Casual Conversation
    "Hi, how are you?",
    "What is Autosys?",
    "Tell me about Control-M",
    
    # Jobmask GET - Valid
    "Get jobmask for autosys in prod",
    "Retrieve jobmask for controlm in dev",
    "List jobmask for auto in production",
    "Show jobmask for ctrl in test with page_size 5",
    "Fetch jobmask for autosys in prod with seal 123",
    "Display jobmask for controlm in dev with name job1",
    "Pull jobmask for autosys in test",
    
    # Jobmask GET - Invalid/Missing Params
    "Get jobmask for prod",  # Missing product
    "Retrieve jobmask for auto",  # Missing environment
    "Show jobmask with seal 123",  # Missing both
    "List jobmask for invalid in prod",  # Invalid product
    
    # Jobmask PATCH - Valid
    "Update jobmask for autosys in prod with name job1 and seal 456",
    "Modify jobmask for controlm in dev with name job2 and seal 789",
    "Change jobmask for auto in test with name job3 and seal 101",
    "Edit jobmask for ctrl in production with name job4 and seal 112",
    
    # Jobmask PATCH - Invalid/Missing Params
    "Update jobmask for autosys in prod",  # Missing name, seal
    "Modify jobmask for controlm with name job5",  # Missing environment, seal
    "Change jobmask with seal 999",  # Missing all required
    "Edit jobmask for invalid in dev with name job6 and seal 333",  # Invalid product
    
    # Weather API - Valid
    "What’s the weather in New York?",
    "Show me the forecast for London",
    "Get temperature in Tokyo",
    "Check climate in Sydney",
    
    # Weather API - Invalid/Missing Params
    "What’s the weather?",  # Missing city
    
    # Multi-Turn Scenarios
    "Fetch jobmask for prod",  # Missing product
    "Autosys",  # Follow-up providing product
    "Adjust jobmask in test with name job7",  # Missing seal
    "seal 444"  # Follow-up providing seal
]

# Run Test Cases
for i, test_input in enumerate(test_cases, 1):
    print(f"\nTest Case {i}: {test_input}")
    initial_state = {"messages": [HumanMessage(content=test_input)]}
    if i > 27:  # Simulate multi-turn by reusing prior state for cases 28-30
        if i == 28:
            state = graph.invoke({"messages": [HumanMessage(content=test_cases[27])]})
            result = graph.invoke({"messages": state["messages"] + [HumanMessage(content=test_input)]})
        elif i == 29:
            state = graph.invoke({"messages": [HumanMessage(content=test_cases[28])]})
            result = graph.invoke({"messages": state["messages"] + [HumanMessage(content=test_input)]})
        elif i == 30:
            state = graph.invoke({"messages": [HumanMessage(content=test_cases[29])]})
            result = graph.invoke({"messages": state["messages"] + [HumanMessage(content=test_input)]})
    else:
        result = graph.invoke(initial_state)
    for message in result["messages"]:
        print(f"{message.type}: {message.content}")
