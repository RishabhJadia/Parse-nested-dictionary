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
