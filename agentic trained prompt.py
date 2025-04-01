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
