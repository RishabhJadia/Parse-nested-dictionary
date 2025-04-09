import streamlit as st
from langchain_core.language_models.llms import LLM
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END, MessageState
from typing import Optional, List, Dict, Any
import requests
import json

# PromptTemplate without tool result or examples
multi_tool_prompt_template = PromptTemplate(
    input_variables=["history", "input"],
    template="""
You are an assistant that can handle casual conversation and Jobmask API requests.

1. **Casual Conversation**: For greetings, questions, or general inquiries (e.g., "Hi, how are you?", "What is Autosys?"), respond with a plain text friendly and informative reply.
2. **Jobmask API**: Requires:
   - Required: environment (string), product (string)
   - Optional: seal (string), name (string), page_size (string)
   - Parameter Identification Rules:
     - **Seal**: If a number between 3 and 6 digits (e.g., 100 to 999999) appears in the input (with or without the keyword "seal"), treat it as the 'seal' parameter.
     - **Environment**: If a value matches "prod", "dev", "uat", "test", "qa", or "cat" (with or without the keyword "environment"), treat it as the 'environment' parameter. Look for phrases like "of <value>" or standalone mentions.
     - **Product**: If a value matches "autosys" or "controlm" (with or without the keyword "product"), treat it as the 'product' parameter. Look for phrases like "of <value>" or standalone mentions.
     - **Page Size**: If a number is 1 or 2 digits (e.g., 0 to 99) and appears in the input (with or without the keyword "page_size"), treat it as the 'page_size' parameter.
     - For ambiguous terms like "mapped to <value>", assume the value is the 'seal' if it fits the 3-6 digit rule.
     - Return: {"action": "call_tool", "tool": "jobmask", "query_params": {...}, "context": "Fetching job listings"}
   - If required parameters are missing in the current input:
     - If only 'environment' is missing, return: {"error": "missing_parameters", "message": "Please specify the 'environment' (e.g., prod, dev, uat, test, qa, cat) for the Jobmask request."}
     - If only 'product' is missing, return: {"error": "missing_parameters", "message": "Please specify the 'product' (e.g., autosys, controlm) for the Jobmask request."}
     - If both 'environment' and 'product' are missing, return: {"error": "missing_parameters", "message": "Please specify the 'environment' (e.g., prod, dev, uat, test, qa, cat) and 'product' (e.g., autosys, controlm) for the Jobmask request."}

Conversation history:
{history}

User input:
{input}

Return your response as either plain text (for casual input) or a JSON object (for tool requests). The response will be wrapped in {"Message": <your_response>} by the system.
"""
)

# Define the CustomLLM with API call
class CustomLLM(LLM):
    model_name: str = "custom_model"
    api_endpoint: str = "http://your-api-host/chat/invoke"  # Replace with actual endpoint
    
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
            return json.dumps({"Message": api_response.get("Mesaage", "Error: 'Mesaage' key missing")})
        except requests.exceptions.RequestException as e:
            return json.dumps({"Message": f"Failed to call /chat/invoke: {str(e)}"})
    
    @property
    def _llm_type(self) -> str:
        return "custom_llm"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name, "api_endpoint": self.api_endpoint}

# Instantiate the custom LLM
custom_llm = CustomLLM(api_endpoint="http://your-api-host/chat/invoke")

# Define a generic LLM node
def llm_node(state: MessageState) -> MessageState:
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage) or isinstance(last_message, AIMessage):
        history = state["messages"][:-1]
        history_str = "\n".join([msg.content for msg in history])
        
        # Format the prompt
        input_content = last_message.content if isinstance(last_message, HumanMessage) else json.loads(last_message.content).get("Message", "")
        formatted_prompt = multi_tool_prompt_template.format(history=history_str, input=input_content)
        
        # Call the LLM
        response = custom_llm(formatted_prompt)
        state["messages"].append(AIMessage(content=response))
    return state

# Define the Jobmask tool with default page_size
def jobmask_tool(query_params: Dict[str, str]) -> str:
    """Tool to call the Jobmask API with query parameters, defaulting page_size to 10."""
    if "page_size" not in query_params:
        query_params["page_size"] = "10"
    
    try:
        api_url = "https://api.jobmask.com/search"  # Replace with actual Jobmask API URL
        response = requests.get(api_url, params=query_params)
        response.raise_for_status()
        data = response.json()
        return json.dumps({"result": data})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Jobmask API call failed: {str(e)}"})

# Define the Jobmask tool node
def jobmask_tool_node(state: MessageState) -> MessageState:
    last_message = json.loads(state["messages"][-1].content)
    message_content = last_message["Message"]
    inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "jobmask":
        query_params = inner_content["query_params"]
        result = jobmask_tool(query_params)
        state["messages"].append(AIMessage(content=result))
    return state

# Define the router function
def router_function(state: MessageState) -> str:
    last_message = json.loads(state["messages"][-1].content)
    message_content = last_message["Message"]
    
    try:
        inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
        if inner_content.get("action") == "call_tool":
            tool_name = inner_content.get("tool")
            if tool_name == "jobmask":
                return "jobmask_tool"
    except json.JSONDecodeError:
        pass
    
    return END

# Create the graph
graph_builder = StateGraph(MessageState)
graph_builder.add_node("llm", llm_node)
graph_builder.add_node("jobmask_tool", jobmask_tool_node)
graph_builder.set_entry_point("llm")
graph_builder.add_conditional_edges("llm", router_function)
graph_builder.add_edge("jobmask_tool", END)
graph = graph_builder.compile()

# Streamlit App
def main():
    st.title("Chat with Jobmask Assistant")

    # Initialize session state for messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display conversation history
    for message in st.session_state.messages:
        if isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.write(message.content)
        elif isinstance(message, AIMessage):
            with st.chat_message("assistant"):
                content = json.loads(message.content).get("Message", message.content)
                if isinstance(content, dict) and "action" in content:
                    st.json(content)  # Display tool call JSON
                elif isinstance(content, dict) and "result" in content:
                    st.json(content)  # Display raw API result
                else:
                    st.write(content)  # Display plain text

    # Input form
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Type your message here...", key="input")
        submit_button = st.form_submit_button(label="Send")

    # Process input when submitted
    if submit_button and user_input:
        # Add user message to state
        st.session_state.messages.append(HumanMessage(content=user_input))
        
        # Run the graph with current state
        state = {"messages": st.session_state.messages}
        result = graph.invoke(state)
        
        # Update session state with the result
        st.session_state.messages = result["messages"]
        
        # Rerun to refresh the UI
        st.rerun()

if __name__ == "__main__":
    main()
------------------------------------------------------
# Prevent re rendering of all message history but should maintaining history
import streamlit as st
from langchain_core.language_models.llms import LLM
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END, MessageState
from typing import Optional, List, Dict, Any
import requests
import json

# PromptTemplate with Jobmask, Weather, and basic arithmetic
multi_tool_prompt_template = PromptTemplate(
    input_variables=["history", "input"],
    template="""
You are an assistant that can handle casual conversation, basic arithmetic, Jobmask API requests, and Weather API requests.

1. **Casual Conversation**: For greetings, questions, or general inquiries (e.g., "Hi, how are you?", "What is Autosys?", "What is my name"), respond with a plain text friendly and informative reply. Use conversation history to answer questions about prior inputs (e.g., names provided earlier).

2. **Basic Arithmetic**: If the input contains "add", "sum", "plus", or similar terms followed by two numbers (e.g., "add 5 and 3"), compute the result and return it as plain text (e.g., "The sum of 5 and 3 is 8"). If numbers are missing, return: {"error": "missing_numbers", "message": "Please provide two numbers to add (e.g., 'add 5 and 3')."}

3. **Jobmask API**: Requires:
   - Required: environment (string), product (string)
   - Optional: seal (string), name (string), page_size (string)
   - Parameter Identification Rules:
     - **Seal**: If a number between 3 and 6 digits (e.g., 100 to 999999) appears in the input (with or without the keyword "seal"), treat it as the 'seal' parameter.
     - **Environment**: If a value matches "prod", "dev", "uat", "test", "qa", or "cat" (with or without the keyword "environment"), treat it as the 'environment' parameter. Look for phrases like "of <value>" or standalone mentions.
     - **Product**: If a value matches "autosys" or "controlm" (with or without the keyword "product"), treat it as the 'product' parameter. Look for phrases like "of <value>" or standalone mentions.
     - **Page Size**: If a number is 1 or 2 digits (e.g., 0 to 99) and appears in the input (with or without the keyword "page_size"), treat it as the 'page_size' parameter.
     - For ambiguous terms like "mapped to <value>", assume the value is the 'seal' if it fits the 3-6 digit rule.
     - Return: {"action": "call_tool", "tool": "jobmask", "query_params": {...}, "context": "Fetching job listings"}
   - If required parameters are missing in the current input:
     - If only 'environment' is missing, return: {"error": "missing_parameters", "message": "Please specify the 'environment' (e.g., prod, dev, uat, test, qa, cat) for the Jobmask request."}
     - If only 'product' is missing, return: {"error": "missing_parameters", "message": "Please specify the 'product' (e.g., autosys, controlm) for the Jobmask request."}
     - If both 'environment' and 'product' are missing, return: {"error": "missing_parameters", "message": "Please specify the 'environment' (e.g., prod, dev, uat, test, qa, cat) and 'product' (e.g., autosys, controlm) for the Jobmask request."}

4. **Weather API**: Requires:
   - Required: location (string)
   - Optional: units (string, either "metric" or "imperial")
   - Parameter Identification Rules:
     - **Location**: If a word or phrase in the input matches a known city name (e.g., "London", "New York", "Tokyo") or is preceded by "in", "at", or "for" (e.g., "weather in London"), treat it as the 'location' parameter. If ambiguous, assume the last non-numeric, non-matching word/phrase is the location.
     - **Units**: If "metric" or "imperial" appears in the input (with or without the keyword "units"), treat it as the 'units' parameter. If not specified, do not include it in the query.
     - Trigger words like "weather", "temperature", or "forecast" indicate a Weather API request.
     - Return: {"action": "call_tool", "tool": "weather", "query_params": {...}, "context": "Fetching weather information"}
   - If required parameters are missing in the current input:
     - If 'location' is missing, return: {"error": "missing_parameters", "message": "Please specify the 'location' (e.g., London, New York) for the Weather request."}

Conversation history:
{history}

User input:
{input}

Return your response as either plain text (for casual input) or a JSON object (for tool requests or errors). The response will be wrapped in {"Message": <your_response>} by the system.
"""
)

# Define the CustomLLM with API call
class CustomLLM(LLM):
    model_name: str = "custom_model"
    api_endpoint: str = "http://your-api-host/chat/invoke"  # Replace with actual endpoint
    
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
            return json.dumps({"Message": api_response.get("Mesaage", "Error: 'Mesaage' key missing")})
        except requests.exceptions.RequestException as e:
            return json.dumps({"Message": f"Failed to call /chat/invoke: {str(e)}"})
    
    @property
    def _llm_type(self) -> str:
        return "custom_llm"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name, "api_endpoint": self.api_endpoint}

# Instantiate the custom LLM
custom_llm = CustomLLM(api_endpoint="http://your-api-host/chat/invoke")

# Define a generic LLM node
def llm_node(state: MessageState) -> MessageState:
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage) or isinstance(last_message, AIMessage):
        history = state["messages"][:-1]
        history_str = "\n".join([msg.content for msg in history])
        
        # Format the prompt
        input_content = last_message.content if isinstance(last_message, HumanMessage) else json.loads(last_message.content).get("Message", "")
        formatted_prompt = multi_tool_prompt_template.format(history=history_str, input=input_content)
        
        # Call the LLM
        response = custom_llm(formatted_prompt)
        state["messages"].append(AIMessage(content=response))
    return state

# Define the Jobmask tool with default page_size
def jobmask_tool(query_params: Dict[str, str]) -> str:
    """Tool to call the Jobmask API with query parameters, defaulting page_size to 10."""
    if "page_size" not in query_params:
        query_params["page_size"] = "10"
    
    try:
        api_url = "https://api.jobmask.com/search"  # Replace with actual Jobmask API URL
        response = requests.get(api_url, params=query_params)
        response.raise_for_status()
        data = response.json()
        return json.dumps({"result": data})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Jobmask API call failed: {str(e)}"})

# Define the Weather tool
def weather_tool(query_params: Dict[str, str]) -> str:
    """Tool to call the OpenWeatherMap API with query parameters."""
    api_key = "YOUR_OPENWEATHERMAP_API_KEY"  # Replace with your actual API key
    api_url = "http://api.openweathermap.org/data/2.5/weather"
    
    params = {"q": query_params["location"], "appid": api_key}
    if "units" in query_params:
        params["units"] = query_params["units"]
    
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        return json.dumps({"result": data})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Weather API call failed: {str(e)}"})

# Define the Jobmask tool node
def jobmask_tool_node(state: MessageState) -> MessageState:
    last_message = json.loads(state["messages"][-1].content)
    message_content = last_message["Message"]
    inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "jobmask":
        query_params = inner_content["query_params"]
        result = jobmask_tool(query_params)
        state["messages"].append(AIMessage(content=result))
    return state

# Define the Weather tool node
def weather_tool_node(state: MessageState) -> MessageState:
    last_message = json.loads(state["messages"][-1].content)
    message_content = last_message["Message"]
    inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "weather":
        query_params = inner_content["query_params"]
        result = weather_tool(query_params)
        state["messages"].append(AIMessage(content=result))
    return state

# Define the router function
def router_function(state: MessageState) -> str:
    last_message = json.loads(state["messages"][-1].content)
    message_content = last_message["Message"]
    
    try:
        inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
        if inner_content.get("action") == "call_tool":
            tool_name = inner_content.get("tool")
            if tool_name == "jobmask":
                return "jobmask_tool"
            elif tool_name == "weather":
                return "weather_tool"
    except json.JSONDecodeError:
        pass
    
    return END

# Create the graph
graph_builder = StateGraph(MessageState)
graph_builder.add_node("llm", llm_node)
graph_builder.add_node("jobmask_tool", jobmask_tool_node)
graph_builder.add_node("weather_tool", weather_tool_node)
graph_builder.set_entry_point("llm")
graph_builder.add_conditional_edges("llm", router_function)
graph_builder.add_edge("jobmask_tool", END)
graph_builder.add_edge("weather_tool", END)
graph = graph_builder.compile()

# Streamlit App with efficient latest message rendering
def main():
    st.title("Chatbot with Jobmask & Weather")

    # Initialize session state for messages and message count
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.message_count = 0

    # Container for initial history (rendered only once on first load)
    if st.session_state.message_count == 0 and st.session_state.messages:
        with st.container():
            for message in st.session_state.messages:
                if isinstance(message, HumanMessage):
                    with st.chat_message("user"):
                        st.markdown(f"**You:** {message.content}")
                elif isinstance(message, AIMessage):
                    with st.chat_message("assistant"):
                        content = json.loads(message.content).get("Message", message.content)
                        if isinstance(content, dict) and "action" in content:
                            st.json(content)
                        elif isinstance(content, dict) and "result" in content:
                            st.json(content)
                        elif isinstance(content, dict) and "error" in content:
                            st.markdown(f"**Assistant:** {content['message']}")
                        else:
                            st.markdown(f"**Assistant:** {content}")

    # Container for new messages
    new_message_container = st.container()

    # Chat input
    user_input = st.chat_input("Type your message here...")

    # Process new input and render only the latest messages
    if user_input:
        # Add user message to state
        st.session_state.messages.append(HumanMessage(content=user_input))
        st.session_state.message_count += 1

        # Display only the new user message
        with new_message_container:
            with st.chat_message("user"):
                st.markdown(f"**You:** {user_input}")

        # Run the graph with current state
        state = {"messages": st.session_state.messages}
        result = graph.invoke(state)

        # Update session state with the result
        st.session_state.messages = result["messages"]

        # Display only the new AI responses
        new_messages = result["messages"][-2 if len(result["messages"]) > 1 and "action" in json.loads(result["messages"][-2].content).get("Message", {}) else -1:]
        with new_message_container:
            for message in new_messages:
                if isinstance(message, AIMessage):
                    with st.chat_message("assistant"):
                        content = json.loads(message.content).get("Message", message.content)
                        if isinstance(content, dict) and "action" in content:
                            st.json(content)
                        elif isinstance(content, dict) and "result" in content:
                            st.json(content)
                        elif isinstance(content, dict) and "error" in content:
                            st.markdown(f"**Assistant:** {content['message']}")
                        else:
                            st.markdown(f"**Assistant:** {content}")

if __name__ == "__main__":
    main()
---------------------------------------------------------------------
# with chaching implementation

import streamlit as st
from langchain_core.language_models.llms import LLM
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END, MessageState
from typing import Optional, List, Dict, Any
import requests
import json
import time

# Updated PromptTemplate (removed caching rule)
multi_tool_prompt_template = PromptTemplate(
    input_variables=["history", "input"],
    template="""
You are an assistant that can handle casual conversation, basic arithmetic, Jobmask API requests, and Weather API requests.

1. **Casual Conversation**: For greetings, questions, or general inquiries (e.g., "Hi, how are you?", "What is Autosys?", "What is my name"), respond with a plain text friendly and informative reply. Use conversation history to answer questions about prior inputs (e.g., names provided earlier). For example, if the user says "my name is <name>", store and recall it later.

2. **Basic Arithmetic**: If the input contains "add", "sum", "plus", or similar terms followed by two numbers (e.g., "add 5 and 3"), compute the result and return it as plain text (e.g., "The sum of 5 and 3 is 8"). If numbers are missing, return: {"error": "missing_numbers", "message": "Please provide two numbers to add (e.g., 'add 5 and 3')."}

3. **Jobmask API**: Requires:
   - Required: environment (string), product (string)
   - Optional: seal (string), name (string), page_size (string)
   - Trigger Rule: Any phrase where a verb synonymous with querying or retrieving (e.g., "get", "fetch", "retrieve", "obtain", "query", "pull", "grab", "extract", "collect") is followed by "jobmask" (e.g., "get jobmask", "fetch jobmask", "retrieve jobmask", "query jobmask") indicates a Jobmask API request. The presence of "jobmask" after such a verb is the key indicator, regardless of additional words (e.g., "get all the jobmask" or "fetch the jobmask data" still triggers it).
   - Parameter Identification Rules:
     - **Seal**: If a number between 3 and 6 digits (e.g., 100 to 999999) appears in the input (with or without the keyword "seal"), treat it as the 'seal' parameter.
     - **Environment**: If a value matches "prod", "dev", "uat", "test", "qa", or "cat" (with or without the keyword "environment"), treat it as the 'environment' parameter. Look for phrases like "of <value>", "in <value>", "for <value>", "from <value>", "in the <value> environment", or standalone mentions. Ignore surrounding words like "the" or quotes around the value.
     - **Product**: 
       - Valid products are strictly "autosys" or "controlm".
       - If a value matches "autosys" or "controlm" exactly (with or without the keyword "product"), treat it as the 'product' parameter. Look for phrases like "of <value>", "for <value>", "for the product <value>", or standalone mentions. Ignore quotes around the value (e.g., "'autosys'" is "autosys").
       - **Misspelling Handling**: Before any other checks, if a product-like term doesn’t match "autosys" or "controlm" exactly but closely resembles them (e.g., "autosis", "autosyss", "autoys", "autossiss", "contrl", "controllm"), silently map it to the closest match:
         - Terms resembling "autosys" (e.g., "autosis", "autosyss", "autoys", "autossiss") → "autosys"
         - Terms resembling "controlm" (e.g., "control", "controllm", "contrlm") → "controlm"
         - Use the corrected value as the 'product' for all subsequent steps without announcing the correction.
       - **Invalid Product**: If the product-like term doesn’t match or closely resemble "autosys" or "controlm" (e.g., "randomproduct", "xyz"), return: "I have information related to autosys and controlm only."
     - **Page Size**: If a number is 1 or 2 digits (e.g., 0 to 99) and appears in the input (with or without the keyword "page_size"), treat it as the 'page_size' parameter.
     - For ambiguous terms like "mapped to <value>", assume the value is the 'seal' if it fits the 3-6 digit rule.
     - **Contextual Continuation**: If the current input provides some Jobmask parameters (e.g., environment, product) but lacks others (e.g., seal), check the last 3 messages in the conversation history for missing parameters related to a Jobmask request (e.g., "get jobmask", "fetch jobmask", "query jobmask"). Combine them to form a complete query if possible.
     - **Execution Rule**: If both required parameters ('environment' and 'product') are present (after silent misspelling correction), proceed with the Jobmask API call by returning the tool call JSON. Do not ask for 'seal' as it is optional, and do not comment on corrections or processing steps—just return the tool call JSON.
   - If required parameters are missing in the current input and cannot be found in recent history:
     - If neither 'environment' nor 'product' is provided (regardless of whether optional parameters like 'seal' are present), return: {"error": "missing_parameters", "message": "Please provide correct input with environment and product, e.g., 'get jobmask for 88154 in prod for autosys'."}
     - If only 'environment' is missing (and 'product' is present after correction), return: {"error": "missing_parameters", "message": "Please specify the 'environment' (e.g., prod, dev, uat, test, qa, cat) for the Jobmask request."}
     - If only 'product' is missing (and 'environment' is present), return: {"error": "missing_parameters", "message": "Please specify the 'product' (e.g., autosys, controlm) for the Jobmask request."}
     - Return: {"action": "call_tool", "tool": "jobmask", "query_params": {...}, "context": "Fetching job listings"}

4. **Weather API**: Requires:
   - Required: location (string)
   - Optional: units (string, either "metric" or "imperial")
   - Parameter Identification Rules:
     - **Location**: If a word or phrase in the input matches a known city name (e.g., "London", "New York", "Tokyo") or is preceded by "in", "at", or "for" (e.g., "weather in London"), treat it as the 'location' parameter. If ambiguous, assume the last non-numeric, non-matching word/phrase is the location.
     - **Units**: If "metric" or "imperial" appears in the input (with or without the keyword "units"), treat it as the 'units' parameter. If not specified, do not include it in the query.
     - Trigger words like "weather", "temperature", or "forecast" indicate a Weather API request.
     - Return: {"action": "call_tool", "tool": "weather", "query_params": {...}, "context": "Fetching weather information"}
   - If required parameters are missing in the current input:
     - If 'location' is missing, return: {"error": "missing_parameters", "message": "Please specify the 'location' (e.g., London, New York) for the Weather request."}

Conversation history:
{history}

User input:
{input}

Return your response as either plain text (for casual input or invalid product) or a JSON object (for tool requests or errors). Do not include explanatory text about corrections or processing unless explicitly asked by the user. If the input resembles a Jobmask request but isn’t parsed correctly, return: {"error": "parsing_error", "message": "I understood this as a Jobmask request, but couldn’t parse it correctly. Try 'get jobmask for autosys in prod'."} The response will be wrapped in {"Message": <your_response>} by the system.
"""
)

# Define the CustomLLM with API call
class CustomLLM(LLM):
    model_name: str = "custom_model"
    api_endpoint: str = "http://your-api-host/chat/invoke"  # Replace with actual endpoint
    
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
            return json.dumps({"Message": api_response.get("Mesaage", "Error: 'Mesaage' key missing")})
        except requests.exceptions.RequestException as e:
            return json.dumps({"Message": f"Failed to call /chat/invoke: {str(e)}"})
    
    @property
    def _llm_type(self) -> str:
        return "custom_llm"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name, "api_endpoint": self.api_endpoint}

# Instantiate the custom LLM
custom_llm = CustomLLM(api_endpoint="http://your-api-host/chat/invoke")

# Define a generic LLM node
def llm_node(state: MessageState) -> MessageState:
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage) or isinstance(last_message, AIMessage):
        history = state["messages"][:-1]
        history_str = "\n".join([msg.content for msg in history])
        
        # Format the prompt
        input_content = last_message.content if isinstance(last_message, HumanMessage) else json.loads(last_message.content).get("Message", "")
        formatted_prompt = multi_tool_prompt_template.format(history=history_str, input=input_content)
        
        # Call the LLM
        response = custom_llm(formatted_prompt)
        state["messages"].append(AIMessage(content=response))
    return state

# Define the Jobmask tool with default page_size
def jobmask_tool(query_params: Dict[str, str]) -> str:
    """Tool to call the Jobmask API with query parameters, defaulting page_size to 10."""
    if "page_size" not in query_params:
        query_params["page_size"] = "10"
    
    try:
        api_url = "https://api.jobmask.com/search"  # Replace with actual Jobmask API URL
        response = requests.get(api_url, params=query_params)
        response.raise_for_status()
        data = response.json()
        return json.dumps({"result": data})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Jobmask API call failed: {str(e)}"})

# Define a caching check function
def check_cache(state: MessageState) -> Optional[Dict[str, Any]]:
    """Check the conversation history for a cached Jobmask result with identical query_params."""
    last_message = json.loads(state["messages"][-1].content)
    message_content = last_message["Message"]
    inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
    
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "jobmask":
        current_query_params = inner_content["query_params"]
        # Ensure page_size defaults to "10" for comparison
        if "page_size" not in current_query_params:
            current_query_params["page_size"] = "10"
        
        # Reverse iterate through history to find the most recent match
        for i in range(len(state["messages"]) - 2, -1, -1):
            msg = state["messages"][i]
            if isinstance(msg, AIMessage):
                try:
                    prev_content = json.loads(msg.content)["Message"]
                    if isinstance(prev_content, dict) and "result" in prev_content:
                        # Find the corresponding tool call (previous message)
                        if i > 0 and isinstance(state["messages"][i-1], AIMessage):
                            tool_call = json.loads(state["messages"][i-1].content)["Message"]
                            if (tool_call.get("action") == "call_tool" and 
                                tool_call.get("tool") == "jobmask" and 
                                tool_call["query_params"] == current_query_params):
                                return prev_content  # Return cached result
                except (json.JSONDecodeError, KeyError):
                    continue
    return None

# Define the Jobmask tool node with caching
def jobmask_tool_node(state: MessageState) -> MessageState:
    # Check cache first
    cached_result = check_cache(state)
    if cached_result:
        state["messages"].append(AIMessage(content=json.dumps({"Message": cached_result})))
    else:
        last_message = json.loads(state["messages"][-1].content)
        message_content = last_message["Message"]
        inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
        if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "jobmask":
            query_params = inner_content["query_params"]
            result = jobmask_tool(query_params)
            state["messages"].append(AIMessage(content=result))
    return state

# Define the Weather tool node
def weather_tool_node(state: MessageState) -> MessageState:
    last_message = json.loads(state["messages"][-1].content)
    message_content = last_message["Message"]
    inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "weather":
        query_params = inner_content["query_params"]
        result = weather_tool(query_params)
        state["messages"].append(AIMessage(content=result))
    return state

# Define the router function with caching check
def router_function(state: MessageState) -> str:
    last_message = json.loads(state["messages"][-1].content)
    message_content = last_message["Message"]
    
    try:
        inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
        if inner_content.get("action") == "call_tool":
            tool_name = inner_content.get("tool")
            if tool_name == "jobmask":
                return "jobmask_tool"
            elif tool_name == "weather":
                return "weather_tool"
    except json.JSONDecodeError:
        pass
    
    return END

# Create the graph
graph_builder = StateGraph(MessageState)
graph_builder.add_node("llm", llm_node)
graph_builder.add_node("jobmask_tool", jobmask_tool_node)
graph_builder.add_node("weather_tool", weather_tool_node)
graph_builder.set_entry_point("llm")
graph_builder.add_conditional_edges("llm", router_function)
graph_builder.add_edge("jobmask_tool", END)
graph_builder.add_edge("weather_tool", END)
graph = graph_builder.compile()

# Function to stream text incrementally
def stream_text(container, text, delay=0.05):
    """Stream text into a container character-by-character with a delay."""
    current_text = ""
    for char in text:
        current_text += char
        container.markdown(f"**Assistant:** {current_text}")
        time.sleep(delay)

# Streamlit App with streaming effect
def main():
    st.title("Chatbot with Jobmask & Weather (Streaming)")

    # Initialize session state for messages and message count
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.message_count = 0

    # Container for initial history (rendered only once on first load)
    if st.session_state.message_count == 0 and st.session_state.messages:
        with st.container():
            for message in st.session_state.messages:
                if isinstance(message, HumanMessage):
                    with st.chat_message("user"):
                        st.markdown(f"**You:** {message.content}")
                elif isinstance(message, AIMessage):
                    with st.chat_message("assistant"):
                        content = json.loads(message.content).get("Message", message.content)
                        if isinstance(content, dict) and "action" in content:
                            st.json(content)
                        elif isinstance(content, dict) and "result" in content:
                            st.json(content)
                        elif isinstance(content, dict) and "error" in content:
                            st.markdown(f"**Assistant:** {content['message']}")
                        else:
                            st.markdown(f"**Assistant:** {content}")

    # Container for new messages
    new_message_container = st.container()

    # Chat input
    user_input = st.chat_input("Type your message here...")

    # Process new input and stream the response
    if user_input:
        # Add user message to state and display it immediately
        st.session_state.messages.append(HumanMessage(content=user_input))
        st.session_state.message_count += 1
        with new_message_container:
            with st.chat_message("user"):
                st.markdown(f"**You:** {user_input}")

        # Run the graph with current state
        state = {"messages": st.session_state.messages}
        result = graph.invoke(state)

        # Update session state with the result
        st.session_state.messages = result["messages"]

        # Stream only the new AI responses
        new_messages = result["messages"][-2 if len(result["messages"]) > 1 and "action" in json.loads(result["messages"][-2].content).get("Message", {}) else -1:]
        with new_message_container:
            for message in new_messages:
                if isinstance(message, AIMessage):
                    with st.chat_message("assistant"):
                        content = json.loads(message.content).get("Message", message.content)
                        if isinstance(content, dict) and "action" in content:
                            st.json(content)  # Tool call JSON (no streaming)
                        elif isinstance(content, dict) and "result" in content:
                            st.json(content)  # API result JSON (no streaming)
                        elif isinstance(content, dict) and "error" in content:
                            stream_text(st.empty(), content["message"])
                        else:
                            stream_text(st.empty(), content)

if __name__ == "__main__":
    main()
