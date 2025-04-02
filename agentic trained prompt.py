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
