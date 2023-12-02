import asyncio
import requests

class AAAS:
    def call_aaas_api(self, qmgr=None, age=None):
        url = f"https://jsonplaceholder.typicode.com/{qmgr}/{age}"
        response = requests.get(url=url)
        return response.json()


async def my_async_code():
    aaas = AAAS()  # Instantiate the AAAS class
    # Call the call_aaas_api method using run_in_executor
    loop = asyncio.get_event_loop()
    aaas_response = await loop.run_in_executor(None, aaas.call_aaas_api, "todos", 1)
    # Use the response from call_aaas_api here
    print(aaas_response)

# Run the asynchronous code
asyncio.run(my_async_code())
requests.get is a synchronous operation and could potentially block if used directly in an asynchronous context, 
the use of run_in_executor helps mitigate this issue by executing it asynchronously in a separate thread pool.
----------------------------------------------------------------------------------------------------------------------------------
  
