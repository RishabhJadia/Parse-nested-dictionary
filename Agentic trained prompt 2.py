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
---------------------------------------------------------------------------------------------------
- Cache implementation, Chat history (Strict Empty Chat Prevention), welcome message (Sidebar Welcome Button),  (GROK)
import streamlit as st
from langchain_core.language_models.llms import LLM
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END, MessageState
from typing import Optional, List, Dict, Any
import requests
import json
import time
from datetime import datetime

# Updated PromptTemplate (unchanged)
multi_tool_prompt_template = PromptTemplate(
    input_variables=["history", "input"],
    template="""
You are an assistant that can handle casual conversation, basic arithmetic, Jobmask API requests, and Weather API requests.

1. **Casual Conversation**: For greetings, questions, or general inquiries (e.g., "Hi, how are you?", "What is Autosys?", "What is my name"), respond with a plain text friendly and informative reply. Use conversation history to answer questions about prior inputs (e.g., names provided earlier). For example, if the user says "my name is <name>", store and recall it later.

2. **Basic Arithmetic**: If the input contains "add", "sum", "plus", or similar terms followed by two numbers (e.g., "add 5 and 3"), compute the result and return it as plain text (e.g., "The sum of 5 and 3 is 8"). If numbers are missing, return: {"error": "missing_numbers", "message": "Please provide two numbers to add (e.g., 'add 5 and 3')."}

3. **Jobmask API**: Requires:
   - Required: environment (string), product (string)
   - Optional: seal (string), name (string), page_size (string)
   - Trigger Rule: Any phrase where a verb synonymous with querying or retrieving (e.g., "get", "fetch", "retrieve", "obtain", "query", "pull", "grab", "extract", "collect") is followed by "jobmask" (e.g., "get jobmask", "fetch jobmask", "retrieve jobmask", "query jobmask") indicates a Jobmask API request. The presence of "jobmask" after such aНК verb is the key indicator, regardless of additional words (e.g., "get all the jobmask" or "fetch the jobmask data" still triggers it).
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

class CustomLLM(LLM):
    model_name: str = "custom_model"
    api_endpoint: str = "http://your-api-host/chat/invoke"
    
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

custom_llm = CustomLLM(api_endpoint="http://your-api-host/chat/invoke")

def llm_node(state: MessageState) -> MessageState:
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage) or isinstance(last_message, AIMessage):
        history = state["messages"][:-1]
        history_str = "\n".join([msg.content for msg in history])
        
        input_content = last_message.content if isinstance(last_message, HumanMessage) else json.loads(last_message.content).get("Message", "")
        formatted_prompt = multi_tool_prompt_template.format(history=history_str, input=input_content)
        
        response = custom_llm(formatted_prompt)
        state["messages"].append(AIMessage(content=response))
    return state

def jobmask_tool(query_params: Dict[str, str]) -> str:
    if "page_size" not in query_params:
        query_params["page_size"] = "10"
    
    try:
        api_url = "https://api.jobmask.com/search"
        response = requests.get(api_url, params=query_params)
        response.raise_for_status()
        data = response.json()
        return json.dumps({"result": data})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Jobmask API call failed: {str(e)}"})

def weather_tool(query_params: Dict[str, str]) -> str:
    try:
        api_url = "https://api.openweathermap.org/data/2.5/weather"
        response = requests.get(api_url, params=query_params)
        response.raise_for_status()
        data = response.json()
        return json.dumps({"result": data})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Weather API call failed: {str(e)}"})

def check_cache(state: MessageState) -> Optional[Dict[str, Any]]:
    last_message = json.loads(state["messages"][-1].content)
    message_content = last_message["Message"]
    inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
    
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "jobmask":
        current_query_params = inner_content["query_params"]
        if "page_size" not in current_query_params:
            current_query_params["page_size"] = "10"
        
        for i in range(len(state["messages"]) - 2, -1, -1):
            msg = state["messages"][i]
            if isinstance(msg, AIMessage):
                try:
                    prev_content = json.loads(msg.content)["Message"]
                    if isinstance(prev_content, dict) and "result" in prev_content:
                        if i > 0 and isinstance(state["messages"][i-1], AIMessage):
                            tool_call = json.loads(state["messages"][i-1].content)["Message"]
                            if (tool_call.get("action") == "call_tool" and 
                                tool_call.get("tool") == "jobmask" and 
                                tool_call["query_params"] == current_query_params):
                                return prev_content
                except (json.JSONDecodeError, KeyError):
                    continue
    return None

def jobmask_tool_node(state: MessageState) -> MessageState:
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

def weather_tool_node(state: MessageState) -> MessageState:
    last_message = json.loads(state["messages"][-1].content)
    message_content = last_message["Message"]
    inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "weather":
        query_params = inner_content["query_params"]
        result = weather_tool(query_params)
        state["messages"].append(AIMessage(content=result))
    return state

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

graph_builder = StateGraph(MessageState)
graph_builder.add_node("llm", llm_node)
graph_builder.add_node("jobmask_tool", jobmask_tool_node)
graph_builder.add_node("weather_tool", weather_tool_node)
graph_builder.set_entry_point("llm")
graph_builder.add_conditional_edges("llm", router_function)
graph_builder.add_edge("jobmask_tool", END)
graph_builder.add_edge("weather_tool", END)
graph = graph_builder.compile()

# ========== Streamlit Chat Interface ==========
def initialize_session_state():
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = {}
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'session_counter' not in st.session_state:
        st.session_state.session_counter = 0
    if 'show_welcome' not in st.session_state:
        st.session_state.show_welcome = True
    if 'chat_created' not in st.session_state:
        st.session_state.chat_created = False

def start_new_chat():
    if not st.session_state.chat_created:
        st.session_state.chat_created = True
    elif st.session_state.current_session_id:
        current_session = st.session_state.chat_sessions.get(st.session_state.current_session_id, {})
        if not current_session.get("messages"):
            st.warning("Please start a conversation before creating a new chat.")
            return

    st.session_state.session_counter += 1
    session_id = f"Chat {st.session_state.session_counter} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    st.session_state.chat_sessions[session_id] = {
        "messages": [],
        "title": "New Chat",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.current_session_id = session_id
    st.session_state.show_welcome = False
    st.rerun()

def show_welcome_message():
    st.session_state.current_session_id = None
    st.session_state.show_welcome = True
    st.rerun()

def render_sidebar():
    with st.sidebar:
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.markdown("### Conversations")
        with col2:
            if st.button("ℹ️", help="Show Welcome Message", key="welcome_button"):
                show_welcome_message()

        if st.button("➕ New Chat", key="new_chat_button"):
            start_new_chat()

        if st.session_state.chat_sessions:
            sorted_sessions = sorted(
                st.session_state.chat_sessions.items(),
                key=lambda x: x[1]["created_at"],
                reverse=True
            )
            for session_id, session_data in sorted_sessions:
                if st.button(
                    session_data["title"],
                    key=f"btn_{session_id}",
                    help=f"Created at {session_data['created_at']}"
                ):
                    st.session_state.current_session_id = session_id
                    st.session_state.show_welcome = False
                    st.rerun()

def process_user_input(user_input):
    if not st.session_state.current_session_id:
        return

    session = st.session_state.chat_sessions[st.session_state.current_session_id]
    session["messages"].append(HumanMessage(content=user_input))

    if session["title"] == "New Chat":
        session["title"] = user_input[:30] + ("..." if len(user_input) > 30 else "")

    state = {"messages": session["messages"]}
    with st.spinner("Thinking..."):
        time.sleep(1)  # Simulate processing time for better UX
        result = graph.invoke(state)
    session["messages"] = result["messages"]
    st.rerun()

def display_welcome():
    st.title("💬 Advanced Chatbot")
    st.write("""
    Welcome to your AI assistant! This chatbot can:
    - Have natural conversations
    - Perform calculations
    - Query Jobmask data
    - Fetch weather information
    """)
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png",
             caption="AI Assistant", width=200)

def display_chat():
    st.title("💬 Current Chat")

    if st.session_state.current_session_id not in st.session_state.chat_sessions:
        st.warning("Session not found. Starting a new chat.")
        start_new_chat()
        return

    session = st.session_state.chat_sessions[st.session_state.current_session_id]

    for msg in session["messages"]:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(msg.content)
        elif isinstance(msg, AIMessage):
            with st.chat_message("assistant"):
                try:
                    content = json.loads(msg.content).get("Message", msg.content)
                    if isinstance(content, dict):
                        if "error" in content:
                            st.error(content["error"])
                        elif "result" in content:
                            st.json(content["result"])
                        elif "action" in content:
                            st.info(f"Executing {content['tool']} action...")
                    else:
                        st.markdown(content)
                except json.JSONDecodeError:
                    st.markdown(msg.content)

    if prompt := st.chat_input("Type your message here...", key=f"input_{st.session_state.current_session_id}"):
        process_user_input(prompt)

def main():
    st.set_page_config(page_title="Advanced Chatbot", page_icon="💬")
    initialize_session_state()
    render_sidebar()

    if st.session_state.show_welcome or not st.session_state.current_session_id:
        display_welcome()
    else:
        display_chat()

if __name__ == "__main__":
    main()
-------------------------------------------------------------------------------------------------------
- Cache implementation, Chat history (Strict Empty Chat Prevention), Chat history title (msg - timestamp), welcome message (Sidebar Welcome Button),  (GROK)
import streamlit as st
import time
from datetime import datetime
from langchain_core.language_models.llms import LLM
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END, MessageState
from typing import Optional, List, Dict, Any
import requests
import json

# Define the PromptTemplate for the chatbot
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

Conversation W history:
{history}

User input:
{input}

Return your response as either plain text (for casual input or invalid product) or a JSON object (for tool requests or errors). Do not include explanatory text about corrections or processing unless explicitly asked by the user. If the input resembles a Jobmask request but isn’t parsed correctly, return: {"error": "parsing_error", "message": "I understood this as a Jobmask request, but couldn’t parse it correctly. Try 'get jobmask for autosys in prod'."} The response will be wrapped in {"Message": <your_response>} by the system.
"""
)

# Custom LLM class for API interaction
class CustomLLM(LLM):
    model_name: str = "custom_model"
    api_endpoint: str = "http://your-api-host/chat/invoke"
    
    def __init__(self, api_endpoint: Optional[str] = None):
        super().__init__()
        if api_endpoint:
            self.api_endpoint = api_endpoint
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        payload = {"Questions": prompt}  # Prepare API payload
        try:
            response = requests.post(self.api_endpoint, json=payload)  # Make API call
            response.raise_for_status()  # Check for HTTP errors
            api_response = response.json()  # Parse response
            return json.dumps({"Message": api_response.get("Mesaage", "Error: 'Mesaage' key missing")})  # Return JSON response
        except requests.exceptions.RequestException as e:
            return json.dumps({"Message": f"Failed to call /chat/invoke: {str(e)}"})  # Handle errors
    
    @property
    def _llm_type(self) -> str:
        return "custom_llm"  # Identify LLM type
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name, "api_endpoint": self.api_endpoint}  # Provide identifying parameters

# Instantiate custom LLM
custom_llm = CustomLLM(api_endpoint="http://your-api-host/chat/invoke")

# Define LLM node for processing user input
def llm_node(state: MessageState) -> MessageState:
    last_message = state["messages"][-1]  # Get the latest message
    if isinstance(last_message, HumanMessage) or isinstance(last_message, AIMessage):
        history = state["messages"][:-1]  # Exclude the latest message for history
        history_str = "\n".join([msg.content for msg in history])  # Format history as string
        
        input_content = last_message.content if isinstance(last_message, HumanMessage) else json.loads(last_message.content).get("Message", "")
        formatted_prompt = multi_tool_prompt_template.format(history=history_str, input=input_content)  # Create prompt
        
        response = custom_llm(formatted_prompt)  # Call LLM
        state["messages"].append(AIMessage(content=response))  # Append response
    return state

# Define Jobmask tool for API calls
def jobmask_tool(query_params: Dict[str, str]) -> str:
    if "page_size" not in query_params:
        query_params["page_size"] = "10"  # Set default page size
    
    try:
        api_url = "https://api.jobmask.com/search"  # Jobmask API endpoint
        response = requests.get(api_url, params=query_params)  # Make API call
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()  # Parse response
        return json.dumps({"result": data})  # Return JSON result
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Jobmask API call failed: {str(e)}"})  # Handle errors

# Define Weather tool for API calls
def weather_tool(query_params: Dict[str, str]) -> str:
    try:
        api_url = "https://api.openweathermap.org/data/2.5/weather"  # Weather API endpoint
        response = requests.get(api_url, params=query_params)  # Make API call
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()  # Parse response
        return json.dumps({"result": data})  # Return JSON result
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Weather API call failed: {str(e)}"})  # Handle errors

# Check cache for previous Jobmask results
def check_cache(state: MessageState) -> Optional[Dict[str, Any]]:
    last_message = json.loads(state["messages"][-1].content)  # Parse last message
    message_content = last_message["Message"]
    inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
    
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "jobmask":
        current_query_params = inner_content["query_params"]  # Get query parameters
        if "page_size" not in current_query_params:
            current_query_params["page_size"] = "10"  # Set default page size
        
        for i in range(len(state["messages"]) - 2, -1, -1):  # Iterate backward through messages
            msg = state["messages"][i]
            if isinstance(msg, AIMessage):
                try:
                    prev_content = json.loads(msg.content)["Message"]
                    if isinstance(prev_content, dict) and "result" in prev_content:
                        if i > 0 and isinstance(state["messages"][i-1], AIMessage):
                            tool_call = json.loads(state["messages"][i-1].content)["Message"]
                            if (tool_call.get("action") == "call_tool" and 
                                tool_call.get("tool") == "jobmask" and 
                                tool_call["query_params"] == current_query_params):
                                return prev_content  # Return cached result
                except (json.JSONDecodeError, KeyError):
                    continue
    return None

# Define Jobmask tool node
def jobmask_tool_node(state: MessageState) -> MessageState:
    cached_result = check_cache(state)  # Check for cached result
    if cached_result:
        state["messages"].append(AIMessage(content=json.dumps({"Message": cached_result})))  # Use cached result
    else:
        last_message = json.loads(state["messages"][-1].content)  # Parse last message
        message_content = last_message["Message"]
        inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
        if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "jobmask":
            query_params = inner_content["query_params"]  # Get query parameters
            result = jobmask_tool(query_params)  # Call Jobmask tool
            state["messages"].append(AIMessage(content=result))  # Append result
    return state

# Define Weather tool node
def weather_tool_node(state: MessageState) -> MessageState:
    last_message = json.loads(state["messages"][-1].content)  # Parse last message
    message_content = last_message["Message"]
    inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "weather":
        query_params = inner_content["query_params"]  # Get query parameters
        result = weather_tool(query_params)  # Call Weather tool
        state["messages"].append(AIMessage(content=result))  # Append result
    return state

# Router function to direct flow
def router_function(state: MessageState) -> str:
    last_message = json.loads(state["messages"][-1].content)  # Parse last message
    message_content = last_message["Message"]
    
    try:
        inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
        if inner_content.get("action") == "call_tool":
            tool_name = inner_content.get("tool")  # Get tool name
            if tool_name == "jobmask":
                return "jobmask_tool"  # Route to Jobmask node
            elif tool_name == "weather":
                return "weather_tool"  # Route to Weather node
    except json.JSONDecodeError:
        pass
    
    return END  # End flow for non-tool responses

# Build and compile the LangChain graph
graph_builder = StateGraph(MessageState)
graph_builder.add_node("llm", llm_node)  # Add LLM node
graph_builder.add_node("jobmask_tool", jobmask_tool_node)  # Add Jobmask tool node
graph_builder.add_node("weather_tool", weather_tool_node)  # Add Weather tool node
graph_builder.set_entry_point("llm")  # Set entry point
graph_builder.add_conditional_edges("llm", router_function)  # Add conditional routing
graph_builder.add_edge("jobmask_tool", END)  # End after Jobmask tool
graph_builder.add_edge("weather_tool", END)  # End after Weather tool
graph = graph_builder.compile()  # Compile graph

# Initialize session state variables
def initialize_session_state():
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = {}  # Store all chat sessions
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None  # Track active session
    if 'session_counter' not in st.session_state:
        st.session_state.session_counter = 0  # Counter for session IDs
    if 'chat_created' not in st.session_state:
        st.session_state.chat_created = False  # Flag for any chat creation
    if 'show_welcome' not in st.session_state:
        st.session_state.show_welcome = True  # Control welcome message display

# Function to start a new chat session
def start_new_chat():
    if not st.session_state.chat_created:  # If no chat exists, allow creation
        st.session_state.chat_created = True
    elif st.session_state.current_session_id:  # Check if current session exists
        current_session = st.session_state.chat_sessions.get(
            st.session_state.current_session_id, {})
        if not current_session.get("messages"):  # Warn if session is empty
            st.warning(
                "Please start a conversation before creating a new chat.")
            return

    st.session_state.session_counter += 1  # Increment session counter
    session_id = f"Chat {st.session_state.session_counter}"  # Create unique session ID
    st.session_state.chat_sessions[session_id] = {
        "messages": [], "title": "New Chat"}  # Initialize session with empty messages and default title
    st.session_state.current_session_id = session_id  # Set as current session
    st.session_state.show_welcome = False  # Hide welcome message
    st.rerun()  # Refresh the app

# Function to display the welcome message
def show_welcome_message():
    st.session_state.current_session_id = None  # Clear current session
    st.session_state.show_welcome = True  # Show welcome message
    st.rerun()  # Refresh the app

# Sidebar for conversation history
def render_sidebar():
    with st.sidebar:
        # Header section
        col1, col2 = st.columns([0.8, 0.2])  # Split columns for title and button
        with col1:
            st.markdown("### Conversations")  # Display history title
        with col2:
            # Button to show welcome message
            if st.button("ℹ️", help="Show Welcome Message", key="welcome_button"):
                show_welcome_message()

        # Button to create a new chat
        if st.button("New Chat", key="new_chat"):
            start_new_chat()

        # Display chat history buttons
        if st.session_state.chat_sessions:
            for session_id in reversed(list(st.session_state.chat_sessions.keys())):  # Reverse to show newest first
                title = st.session_state.chat_sessions[session_id]["title"]  # Get session title
                if st.button(title, key=session_id):  # Create button for session
                    st.session_state.current_session_id = session_id  # Set as current session
                    st.session_state.show_welcome = False  # Hide welcome message
        else:
            st.markdown("*No conversations yet.*")  # Show if no sessions exist

# Process user input and invoke the graph
def process_user_input(user_input):
    if not st.session_state.current_session_id:  # Ensure a session is active
        return

    session = st.session_state.chat_sessions[st.session_state.current_session_id]  # Get current session
    session["messages"].append(HumanMessage(content=user_input))  # Append user message

    # Update session title with first message and timestamp
    if session["title"] == "New Chat":
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get current timestamp
        session["title"] = f"{user_input[:30]}{'...' if len(user_input) > 30 else ''} - {timestamp}"  # Set title as <input> - <timestamp>

    # Process the input through the LangChain graph
    state = {"messages": session["messages"]}  # Prepare state for graph
    with st.spinner("Thinking..."):
        time.sleep(1)  # Simulate processing delay for better UX
        result = graph.invoke(state)  # Invoke LangChain graph
        session["messages"] = result["messages"]  # Update session messages with graph output

    # Update session state
    st.session_state.chat_sessions[st.session_state.current_session_id]["messages"] = session["messages"]  # Update messages
    st.session_state.chat_sessions[st.session_state.current_session_id]["title"] = session["title"]  # Update title
    st.rerun()  # Refresh the app

# Display welcome screen
def display_welcome():
    st.title("💬 Advanced Chatbot")  # App title
    st.write(
        "This is an advanced chatbot built with Streamlit and LangChain. Click 'New Chat' to start a conversation!")  # Welcome message
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png",
             caption="AI Assistant", width=200)  # Placeholder image

# Display chat interface
def display_chat():
    st.title("💬 Advanced Chatbot")  # App title

    # Get current session data
    current_session = st.session_state.chat_sessions[st.session_state.current_session_id]  # Retrieve current session
    messages = current_session["messages"]  # Retrieve session messages

    # Display chat messages
    for msg in messages:
        if isinstance(msg, HumanMessage):
            st.chat_message("user").write(msg.content)  # Show user message content without timestamp
        elif isinstance(msg, AIMessage):
            with st.chat_message("assistant"):
                try:
                    content = json.loads(msg.content).get("Message", msg.content)  # Parse AI message
                    if isinstance(content, dict):
                        if "error" in content:
                            st.error(content.get("message", content["error"]))  # Display error message
                        elif "result" in content:
                            st.json(content["result"])  # Display JSON result
                        elif "action" in content:
                            st.info(f"Executing {content['tool']} action...")  # Indicate tool action
                        else:
                            st.markdown(json.dumps(content))  # Display raw JSON
                    else:
                        st.write(content)  # Display plain text response
                except json.JSONDecodeError:
                    st.write(msg.content)  # Fallback for unparsable content

    # Chat input field
    user_input = st.chat_input(
        "Type your message here...",
        key=f"input_{st.session_state.current_session_id}"  # Unique key for input
    )
    if user_input:
        process_user_input(user_input)  # Process user input

# Main function to run the app
def main():
    st.set_page_config(page_title="Advanced Chatbot", page_icon="💬")  # Configure page
    initialize_session_state()  # Initialize session state

    # Sidebar for conversation history
    with st.sidebar:
        # Header section
        col1, col2 = st.columns([0.8, 0.2])  # Split columns for title and button
        with col1:
            st.markdown("### Conversations")  # Display history title
        with col2:
            # Button to show welcome message
            if st.button("ℹ️", help="Show Welcome Message", key="welcome_button"):
                show_welcome_message()

        # Button to create a new chat
        if st.button("New Chat", key="new_chat"):
            start_new_chat()

        # Display chat history buttons
        if st.session_state.chat_sessions:
            for session_id in reversed(list(st.session_state.chat_sessions.keys())):  # Reverse to show newest first
                title = st.session_state.chat_sessions[session_id]["title"]  # Get session title
                if st.button(title, key=session_id):  # Create button for session
                    st.session_state.current_session_id = session_id  # Set as current session
                    st.session_state.show_welcome = False  # Hide welcome message
        else:
            st.markdown("*No conversations yet.*")  # Show if no sessions exist

    # Main content area
    if st.session_state.show_welcome or st.session_state.current_session_id is None:
        # Display welcome screen
        st.title("💬 Advanced Chatbot")  # App title
        st.write(
            "This is an advanced chatbot built with Streamlit and LangChain. Click 'New Chat' to start a conversation!")  # Welcome message
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png",
                 caption="AI Assistant", width=200)  # Placeholder image
    else:
        # Display chat interface
        display_chat()

# Entry point
if __name__ == "__main__":
    main()
--------------------------------------------------------------------------------------------------------
- Cache implementation, Chat history (Strict Empty Chat Prevention), welcome message (Sidebar Welcome Button),  (DEEPSEEK)
import streamlit as st
from langchain_core.language_models.llms import LLM
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END, MessageState
from typing import Optional, List, Dict, Any
import requests
import json
import time
from datetime import datetime

# Updated PromptTemplate (unchanged)
multi_tool_prompt_template = PromptTemplate(
    input_variables=["history", "input"],
    template="""
You are an assistant that can handle casual conversation, basic arithmetic, Jobmask API requests, and Weather API requests.

1. **Casual Conversation**: For greetings, questions, or general inquiries (e.g., "Hi, how are you?", "What is Autosys?", "What is my name"), respond with a plain text friendly and informative reply. Use conversation history to answer questions about prior inputs (e.g., names provided earlier). For example, if the user says "my name is <name>", store and recall it later.

2. **Basic Arithmetic**: If the input contains "add", "sum", "plus", or similar terms followed by two numbers (e.g., "add 5 and 3"), compute the result and return it as plain text (e.g., "The sum of 5 and 3 is 8"). If numbers are missing, return: {"error": "missing_numbers", "message": "Please provide two numbers to add (e.g., 'add 5 and 3')."}

3. **Jobmask API**: Requires:
   - Required: environment (string), product (string)
   - Optional: seal (string), name (string), page_size (string)
   - Trigger Rule: Any phrase where a verb synonymous with querying or retrieving (e.g., "get", "fetch", "retrieve", "obtain", "query", "pull", "grab", "extract", "collect") is followed by "jobmask" (e.g., "get jobmask", "fetch jobmask", "retrieve jobmask", "query jobmask") indicates a Jobmask API request. The presence of "jobmask" after such aНК verb is the key indicator, regardless of additional words (e.g., "get all the jobmask" or "fetch the jobmask data" still triggers it).
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
class CustomLLM(LLM):
    model_name: str = "custom_model"
    api_endpoint: str = "http://your-api-host/chat/invoke"
    
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

custom_llm = CustomLLM(api_endpoint="http://your-api-host/chat/invoke")

def llm_node(state: MessageState) -> MessageState:
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage) or isinstance(last_message, AIMessage):
        history = state["messages"][:-1]
        history_str = "\n".join([msg.content for msg in history])
        
        input_content = last_message.content if isinstance(last_message, HumanMessage) else json.loads(last_message.content).get("Message", "")
        formatted_prompt = multi_tool_prompt_template.format(history=history_str, input=input_content)
        
        response = custom_llm(formatted_prompt)
        state["messages"].append(AIMessage(content=response))
    return state

def jobmask_tool(query_params: Dict[str, str]) -> str:
    if "page_size" not in query_params:
        query_params["page_size"] = "10"
    
    try:
        api_url = "https://api.jobmask.com/search"
        response = requests.get(api_url, params=query_params)
        response.raise_for_status()
        data = response.json()
        return json.dumps({"result": data})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Jobmask API call failed: {str(e)}"})

def weather_tool(query_params: Dict[str, str]) -> str:
    try:
        api_url = "https://api.openweathermap.org/data/2.5/weather"
        response = requests.get(api_url, params=query_params)
        response.raise_for_status()
        data = response.json()
        return json.dumps({"result": data})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Weather API call failed: {str(e)}"})

def check_cache(state: MessageState) -> Optional[Dict[str, Any]]:
    last_message = json.loads(state["messages"][-1].content)
    message_content = last_message["Message"]
    inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
    
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "jobmask":
        current_query_params = inner_content["query_params"]
        if "page_size" not in current_query_params:
            current_query_params["page_size"] = "10"
        
        for i in range(len(state["messages"]) - 2, -1, -1):
            msg = state["messages"][i]
            if isinstance(msg, AIMessage):
                try:
                    prev_content = json.loads(msg.content)["Message"]
                    if isinstance(prev_content, dict) and "result" in prev_content:
                        if i > 0 and isinstance(state["messages"][i-1], AIMessage):
                            tool_call = json.loads(state["messages"][i-1].content)["Message"]
                            if (tool_call.get("action") == "call_tool" and 
                                tool_call.get("tool") == "jobmask" and 
                                tool_call["query_params"] == current_query_params):
                                return prev_content
                except (json.JSONDecodeError, KeyError):
                    continue
    return None

def jobmask_tool_node(state: MessageState) -> MessageState:
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

def weather_tool_node(state: MessageState) -> MessageState:
    last_message = json.loads(state["messages"][-1].content)
    message_content = last_message["Message"]
    inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "weather":
        query_params = inner_content["query_params"]
        result = weather_tool(query_params)
        state["messages"].append(AIMessage(content=result))
    return state

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

graph_builder = StateGraph(MessageState)
graph_builder.add_node("llm", llm_node)
graph_builder.add_node("jobmask_tool", jobmask_tool_node)
graph_builder.add_node("weather_tool", weather_tool_node)
graph_builder.set_entry_point("llm")
graph_builder.add_conditional_edges("llm", router_function)
graph_builder.add_edge("jobmask_tool", END)
graph_builder.add_edge("weather_tool", END)
graph = graph_builder.compile()

# ========== Streamlit Chat Interface ==========
def initialize_session_state():
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = {}
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'session_counter' not in st.session_state:
        st.session_state.session_counter = 0
    if 'show_welcome' not in st.session_state:
        st.session_state.show_welcome = True
    if 'new_chat_clicked' not in st.session_state:
        st.session_state.new_chat_clicked = False
    if 'sidebar_collapsed' not in st.session_state:
        st.session_state.sidebar_collapsed = False

def start_new_chat():
    # Check if current chat exists and is empty
    current_session = st.session_state.current_session_id
    if (current_session and 
        current_session in st.session_state.chat_sessions and
        len(st.session_state.chat_sessions[current_session]["messages"]) == 0):
        st.warning("Please start a conversation in the current chat before creating a new one.")
        return
    
    st.session_state.session_counter += 1
    session_id = f"session_{st.session_state.session_counter}"
    st.session_state.chat_sessions[session_id] = {
        "messages": [],
        "title": f"New Chat {st.session_state.session_counter}",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.current_session_id = session_id
    st.session_state.show_welcome = False
    st.session_state.new_chat_clicked = True
    st.rerun()

def display_welcome():
    st.title("💬 Advanced Chatbot")
    st.write("""
    Welcome to your AI assistant! This chatbot can:
    - Have natural conversations
    - Perform calculations
    - Query Jobmask data
    - Fetch weather information
    """)
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png",
             caption="AI Assistant", width=200)
    
    if st.button("Start New Chat"):
        start_new_chat()

def render_sidebar():
    with st.sidebar:
        # Sidebar header with clickable welcome button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("Chat Sessions")
        with col2:
            if st.button("ℹ️", help="Show Welcome Message"):
                st.session_state.show_welcome = True
                st.session_state.current_session_id = None
                st.rerun()
        
        # New Chat button
        if st.button("➕ New Chat", use_container_width=True):
            start_new_chat()
        
        # Chat history list
        if not st.session_state.chat_sessions:
            st.write("No chat history yet")
        else:
            for session_id in sorted(st.session_state.chat_sessions.keys(), reverse=True):
                session = st.session_state.chat_sessions[session_id]
                btn_label = f"{session['title']} ({session_id})"
                if st.button(btn_label, key=session_id, use_container_width=True):
                    st.session_state.current_session_id = session_id
                    st.session_state.show_welcome = False
                    st.session_state.new_chat_clicked = False
                    st.rerun()

def process_user_input(user_input):
    if not st.session_state.current_session_id:
        return
    
    st.session_state.new_chat_clicked = False
    
    session = st.session_state.chat_sessions[st.session_state.current_session_id]
    session["messages"].append(HumanMessage(content=user_input))
    
    if session["title"].startswith("New Chat"):
        session["title"] = user_input[:30] + ("..." if len(user_input) > 30 else "")
    
    state = {"messages": session["messages"]}
    result = graph.invoke(state)
    session["messages"] = result["messages"]
    st.rerun()

def display_chat():
    if st.session_state.current_session_id not in st.session_state.chat_sessions:
        st.warning("Session not found. Starting a new chat.")
        start_new_chat()
        return
    
    session = st.session_state.chat_sessions[st.session_state.current_session_id]
    
    # Display all messages
    for msg in session["messages"]:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(msg.content)
        elif isinstance(msg, AIMessage):
            with st.chat_message("assistant"):
                try:
                    content = json.loads(msg.content).get("Message", msg.content)
                    if isinstance(content, dict):
                        if "error" in content:
                            st.error(content["message"])
                        elif "result" in content:
                            st.json(content["result"])
                        elif "action" in content:
                            st.info(f"Executing {content['tool']} action...")
                    else:
                        st.markdown(content)
                except json.JSONDecodeError:
                    st.markdown(msg.content)
    
    # Input box
    if prompt := st.chat_input("Type your message here..."):
        process_user_input(prompt)

def main():
    st.set_page_config(
        page_title="Advanced Chatbot", 
        page_icon="💬",
        layout="wide"
    )
    initialize_session_state()
    
    render_sidebar()
    
    if st.session_state.show_welcome or not st.session_state.current_session_id:
        display_welcome()
    else:
        display_chat()

if __name__ == "__main__":
    main()
--------------------------------------------------------------------------------------------------------
import streamlit as st
import time
from datetime import datetime
from langchain_core.language_models.llms import LLM
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, END, MessageState
from typing import Optional, List, Dict, Any
import requests
import json
import os

# Define the PromptTemplate for the chatbot
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

# Custom LLM class for API interaction
def create_custom_llm(api_endpoint: str = "http://your-api-host/chat/invoke") -> LLM:
    class CustomLLM(LLM):
        model_name: str = "custom_model"
        api_endpoint: str = api_endpoint
        
        def __init__(self):
            super().__init__()
        
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
    
    return CustomLLM()

# Define LLM node
def llm_node(state: MessageState) -> MessageState:
    last_message = state["messages"][-1]
    if isinstance(last_message, (HumanMessage, AIMessage)):
        history = state["messages"][:-1]
        history_str = "\n".join([msg.content for msg in history])
        input_content = last_message.content if isinstance(last_message, HumanMessage) else json.loads(last_message.content).get("Message", "")
        formatted_prompt = multi_tool_prompt_template.format(history=history_str, input=input_content)
        custom_llm = create_custom_llm()
        response = custom_llm(formatted_prompt)
        state["messages"].append(AIMessage(content=response))
    return state

# Define Jobmask tool
def jobmask_tool(query_params: Dict[str, str]) -> str:
    if "page_size" not in query_params:
        query_params["page_size"] = "10"
    try:
        api_url = "https://api.jobmask.com/search"
        response = requests.get(api_url, params=query_params)
        response.raise_for_status()
        data = response.json()
        return json.dumps({"result": data})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Jobmask API call failed: {str(e)}"})

# Define Weather tool
def weather_tool(query_params: Dict[str, str]) -> str:
    try:
        api_url = "https://api.openweathermap.org/data/2.5/weather"
        response = requests.get(api_url, params=query_params)
        response.raise_for_status()
        data = response.json()
        return json.dumps({"result": data})
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Weather API call failed: {str(e)}"})

# Check cache for Jobmask results
def check_cache(state: MessageState) -> Optional[Dict[str, Any]]:
    last_message = json.loads(state["messages"][-1].content)
    message_content = last_message["Message"]
    inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
    
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "jobmask":
        current_query_params = inner_content["query_params"]
        if "page_size" not in current_query_params:
            current_query_params["page_size"] = "10"
        
        for i in range(len(state["messages"]) - 2, -1, -1):
            msg = state["messages"][i]
            if isinstance(msg, AIMessage):
                try:
                    prev_content = json.loads(msg.content)["Message"]
                    if isinstance(prev_content, dict) and "result" in prev_content:
                        if i > 0 and isinstance(state["messages"][i-1], AIMessage):
                            tool_call = json.loads(state["messages"][i-1].content)["Message"]
                            if (tool_call.get("action") == "call_tool" and 
                                tool_call.get("tool") == "jobmask" and 
                                tool_call["query_params"] == current_query_params):
                                return prev_content
                except (json.JSONDecodeError, KeyError):
                    continue
    return None

# Define tool nodes
def jobmask_tool_node(state: MessageState) -> MessageState:
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

def weather_tool_node(state: MessageState) -> MessageState:
    last_message = json.loads(state["messages"][-1].content)
    message_content = last_message["Message"]
    inner_content = json.loads(message_content) if isinstance(message_content, str) else message_content
    if inner_content.get("action") == "call_tool" and inner_content.get("tool") == "weather":
        query_params = inner_content["query_params"]
        result = weather_tool(query_params)
        state["messages"].append(AIMessage(content=result))
    return state

# Router function
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

# Setup LangChain graph
def setup_graph():
    graph_builder = StateGraph(MessageState)
    graph_builder.add_node("llm", llm_node)
    graph_builder.add_node("jobmask_tool", jobmask_tool_node)
    graph_builder.add_node("weather_tool", weather_tool_node)
    graph_builder.set_entry_point("llm")
    graph_builder.add_conditional_edges("llm", router_function)
    graph_builder.add_edge("jobmask_tool", END)
    graph_builder.add_edge("weather_tool", END)
    return graph_builder.compile()

# Initialize session state
def initialize_session_state():
    if 'graph' not in st.session_state:
        st.session_state.graph = setup_graph()
    if 'chat_histories' not in st.session_state:
        st.session_state.chat_histories = {}
    if 'current_history_session_id' not in st.session_state:
        st.session_state.current_history_session_id = None
    if 'session_counter' not in st.session_state:
        st.session_state.session_counter = 0
    if 'chat_created' not in st.session_state:
        st.session_state.chat_created = False
    if 'show_welcome' not in st.session_state:
        st.session_state.show_welcome = True
    if 'last_processed_index' not in st.session_state:
        st.session_state.last_processed_index = {}
    if 'pending_input' not in st.session_state:
        st.session_state.pending_input = None  # Track user input for immediate display

# Start a new chat session
def start_new_chat():
    if not st.session_state.chat_created:
        st.session_state.chat_created = True
    elif st.session_state.current_history_session_id:
        current_session = st.session_state.chat_histories.get(
            st.session_state.current_history_session_id, {})
        if not current_session.get("messages"):
            st.warning("Please start a conversation before creating a new chat.")
            return
    st.session_state.session_counter += 1
    session_id = f"Chat {st.session_state.session_counter}"
    st.session_state.chat_histories[session_id] = {"messages": [], "title": "New Chat"}
    st.session_state.current_history_session_id = session_id
    st.session_state.last_processed_index[session_id] = -1
    st.session_state.show_welcome = False
    st.session_state.pending_input = None
    st.rerun()

# Show welcome message
def show_welcome_message():
    st.session_state.current_history_session_id = None
    st.session_state.show_welcome = True
    st.session_state.pending_input = None
    st.rerun()

# Render sidebar
def render_sidebar():
    with st.sidebar:
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.markdown("### Conversations")
        with col2:
            if st.button("ℹ️", help="Show Welcome Message", key="welcome_button"):
                show_welcome_message()
        if st.button("New Chat", key="new_chat"):
            start_new_chat()
        if st.session_state.chat_histories:
            for session_id in reversed(list(st.session_state.chat_histories.keys())):
                title = st.session_state.chat_histories[session_id]["title"]
                if st.button(title, key=session_id):
                    st.session_state.current_history_session_id = session_id
                    st.session_state.show_welcome = False
                    st.session_state.pending_input = None
        else:
            st.markdown("*No conversations yet.*")

# Format message output
def format_output(content: str) -> str:
    if '!@#$' in content:
        lines = content.split('!@#$')
        formatted_lines = [f"- {line}" for line in lines]
        return "\n".join(formatted_lines)
    return content.strip()

# Parse AI message content
def parse_ai_message(msg: AIMessage) -> str:
    try:
        content = json.loads(msg.content)
        message_content = content.get("Message", msg.content)
        if isinstance(message_content, dict):
            return format_output(json.dumps(message_content))
        return format_output(message_content)
    except json.JSONDecodeError:
        return format_output(msg.content)

# Render previous messages statically
def render_previous_messages(messages: List, last_processed_index: int):
    for i in range(last_processed_index + 1):
        if i < len(messages):
            msg = messages[i]
            if isinstance(msg, HumanMessage):
                st.chat_message("user").markdown(msg.content)
            elif isinstance(msg, AIMessage):
                with st.chat_message("assistant"):
                    st.markdown(parse_ai_message(msg))

# Stream assistant response
def stream_assistant_response(msg: AIMessage):
    with st.chat_message("assistant"):
        formatted_content = parse_ai_message(msg)
        placeholder = st.empty()
        displayed_response = ""
        for char in formatted_content:
            displayed_response += char
            placeholder.markdown(displayed_response)
            time.sleep(0.05)
        return formatted_content

# Update session state
def update_session_state(session_id: str, messages: List, title: str):
    st.session_state.chat_histories[session_id]["messages"] = messages
    st.session_state.chat_histories[session_id]["title"] = title

# Invoke LangChain graph with thinking steps
def invoke_langchain_graph(state: Dict, session_id: str):
    with st.status("Processing your request...", expanded=True) as status:
        status.write("Collecting context...")
        time.sleep(0.5)
        status.write("Analyzing problems and errors...")
        time.sleep(0.5)
        status.write("Generating response...")
        result = st.session_state.graph.invoke(state)
    return result

# Process user input
def process_user_input(user_input: str, session_id: str):
    if not session_id:
        return
    session = st.session_state.chat_histories[session_id]
    session["messages"].append(HumanMessage(content=user_input))
    if session["title"] == "New Chat":
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        session["title"] = f"{user_input[:10]}{'...' if len(user_input) > 10 else ''} - {timestamp}"
    state = {"messages": session["messages"]}
    result = invoke_langchain_graph(state, session_id)
    session["messages"] = result["messages"]
    update_session_state(session_id, session["messages"], session["title"])
    st.session_state.pending_input = None  # Clear pending input

# Display welcome screen
def display_welcome():
    col1, col2 = st.columns([0.2, 1])
    with col1:
        try:
            ai_assistant_image_path = os.path.join(os.getenv('ROOT_DIR', ''), 'static', 'ai_assistant.png')
            st.image(ai_assistant_image_path, caption="AI Assistant", width=200)
        except:
            st.image("https://via.placeholder.com/200", caption="AI Assistant", width=200)
    with col2:
        st.title("JobMask Registration Agent")
        st.markdown(
            """
            Welcome to JobMask Registration Agent.
            Designed specifically for managing and orchestrating job masks in autosys and Control-M environments.
            **To start the conversation, click on 'New Chat'.**
            """
        )

# Display chat interface
def display_chat():
    session_id = st.session_state.current_history_session_id
    if not session_id:
        return
    current_session = st.session_state.chat_histories[session_id]
    messages = current_session["messages"]
    last_processed_index = st.session_state.last_processed_index.get(session_id, -1)
    
    # Render previous messages
    render_previous_messages(messages, last_processed_index)
    
    # Handle pending input from previous submission
    if st.session_state.pending_input:
        user_input, input_session_id = st.session_state.pending_input
        if input_session_id == session_id:
            st.chat_message("user").markdown(user_input)
            process_user_input(user_input, session_id)
            if messages and isinstance(messages[-1], AIMessage):
                stream_assistant_response(messages[-1])
                st.session_state.last_processed_index[session_id] = len(messages) - 1
    
    # Chat input
    user_input = st.chat_input("Type your message here...", key=f"input_{session_id}")
    if user_input:
        user_input = user_input.strip()
        st.chat_message("user").markdown(user_input)
        st.session_state.pending_input = (user_input, session_id)
        st.rerun()

# Run the interface
def run_interface():
    st.set_page_config(page_title="Advanced Chatbot", page_icon="💬")
    initialize_session_state()
    render_sidebar()
    if st.session_state.show_welcome or st.session_state.current_history_session_id is None:
        display_welcome()
    else:
        display_chat()

# Entry point
if __name__ == "__main__":
    run_interface()
