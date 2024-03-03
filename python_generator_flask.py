import json
from flask import Flask, Response, jsonify
import random
from memory_profiler import profile
import uuid

app = Flask(__name__)

# Simulated API call function (replace with your actual implementation)
def api_call():
    messages = ["This is message 1", "This is message 2", "This is message 3"] * 100
    # messages = [None, "This is message 1"]
    return random.choice(messages)

@app.route('/browse')
# @profile
def browse_data():
    results = []
    for _ in range(100000):
        message = api_call()
        if message is not None:
            results.append({"message": message, "hex": "", "msg": "msg" })
        else:
            results.append("message not available")
    return {"haserror": False, "results": results}, 200

# @app.route('/browse')
# def browse_data():
#     def generate_results_json():
#         valid_messages = False
#         yield '{'  # Start JSON output
#         try:
#             for _ in range(100000):
#                 message = api_call()
#                 if message is None:
#                     break
#                 message_id = str(uuid.uuid4())
#                 yield f'"{message_id}": {{ "content": "{message}", "hex": "", "msg": "msg" }},'  # Yield message with ID
#                 valid_messages = True
#             if not valid_messages:
#                 yield '"message": "message not available",'
#                 yield '"haserror": true,'  # Set haserror to true
#             else:
#                 yield '"haserror": false,'
#         except Exception as e:
#             print(e)
#             yield '"haserror": true,'  # Set haserror to true
#             yield '"message": "message not availassble",'
#         yield '}'  # End JSON output

#     response = Response()
#     response.response = generate_results_json()
#     response.status_code = 200
#     response.headers['Content-Type'] = 'application/json'
#     return response

# def generate_results_json():
#     yield '{'  # Start JSON output
#     yield '"haserror": false,'

#     valid_messages = False

#     try:
#         for _ in range(10):  # Adjust loop count as needed
#             message = api_call()
#             if message is None:
#                 break

#             message_id = str(uuid.uuid4())
#             yield f'"{message_id}": {{ "content": "{message}", "hex": "", "msg": "msg", "id": "{message_id}" }},'
#             valid_messages = True
#     except Exception as e:
#         has_error = True  # Set has_error flag within generate_results_json
#         yield f'"error": "{str(e)}",'  # Include error message in JSON

#     if not valid_messages:
#         yield '"message": "message not available",'

#     yield '}'  # End JSON output


# @app.route('/browse')
# def browse_data():
#     response = Response()
#     response.response = generate_results_json()
#     has_error = any(True for result in generate_results_json() if isinstance(result, str))
#     response.status_code = 500 if has_error else 200  # Set status code based on error check
#     response.headers['Content-Type'] = 'application/json'

#     return response


# @profile
# def generate_results():
#     has_error = False
#     valid_messages = False  # Flag to track if any valid messages are found
#     try:
#         for _ in range(10000):
#             message = api_call()
#             if message is None:
#                 break
#             valid_messages = True
#             yield {"message": message}
#         if not valid_messages:
#             yield "message not available"
#     except Exception as e:
#         has_error = True
#         yield "message not available"
#         print(f"An error occurred: {e}")

# @app.route('/browse')
# def browse_data():
#     results = list(generate_results())
    # has_error = any(True for result in results if isinstance(result, str))
    # status_code = 500 if has_error else 200
#     response_data = {"haserror": has_error, "results": results}
#     return Response(json.dumps(response_data), content_type='application/json'), status_code

if __name__ == '__main__':
    app.run(debug=True)




# -------------------------------------------------------------------
# import sys
# from flask import Flask, jsonify, Response
# import random

# app = Flask(__name__)

# # Simulated API call function (replace with your actual implementation)
# def api_call():
#     import random
#     # messages = ["This is message 1", "This is message 2", "This is message 3"] * 100
#     messages = ["This is message 1", None]
#     return random.choice(messages)
#     # if random.random() < 0.9 else None  # Simulate occasional errors
#     # return message

# def generate_results():
#     status_code = 200
#     has_error = False
#     valid_messages = False  # Flag to track if any valid messages are found
#     try:
#         for _ in range(10000):
#             message = api_call()
#             print(message,"==============")
#             if message is None:
#                 break
#             valid_messages = True
#             yield {"message": message}
#         if not valid_messages:
#             yield "message not available"
#     except Exception as e:
#         has_error = True
#         status_code = 500
#         yield "message not available"
#         print(f"An error occurred: {e}")


# @app.route('/browse')
# def browse_data():
#     # results_generator = generate_results()
#     # results = list(results_generator)  # Materialize the generator into a list
#     # print(sys.getsizeof(results), "----------")
#     has_error = any(True for result in generate_results() if isinstance(result, str))
#     status_code = 500 if has_error else 200
#     return {"haserror": has_error, "results": list(generate_results())}, status_code

# if __name__ == '__main__':
#     app.run(debug=True)

# -------------------------------------------------------------------
# from flask import Flask
# import random

# app = Flask(__name__)

# # Simulated API call function (replace with your actual implementation)
# def api_call():
#     messages = [None, "This is message 1"]
#     return random.choice(messages)

# @app.route('/browse')
# def browse_data():
#     status_code = 500

#     def generate_results():
#         nonlocal status_code  # Declare status_code as nonlocal
#         has_error = False
#         valid_messages = False  # Flag to track if any valid messages are found
#         for _ in range(5):
#             message = api_call()
#             print(message)
#             if message is None:
#                 break  # Skip to the next iteration if message is None
#             valid_messages = True
#             yield {"message": message}
#         print("1111111111111111")
#         if not valid_messages:
#             print("222222222222222")
#             yield "message not available"
#             status_code = 200
#         # elif not has_error:
#         #     print("33333333333")
#         #     status_code = 200

#     results = list(generate_results())
#     print(results, "----------")
#     has_error = status_code != 200

#     return {"haserror": has_error, "results": results}, status_code

# if __name__ == '__main__':
#     app.run(debug=True)
----------------------------------------------------------------
You're absolutely correct. The key difference between the two approaches lies in how they handle memory usage:

List Approach (Memory Inefficient):

In your first code snippet using a list (results), the entire response is built in memory before being returned. This means the code iterates through all messages, creates dictionaries for each message, and appends them to the results list. The entire list is then held in memory until the response is returned. This can be problematic for large datasets because a significant amount of memory is used to store the complete response before sending it.
Generator Approach (Memory Efficient):

The generator-based approach iterates through the messages one by one. Instead of creating a complete response upfront, it yields each part of the response (e.g., keys, values) as it's generated. This allows the response to be built "on the fly" without holding the entire dataset in memory at once. This is much more efficient for large datasets as memory usage is minimized.
Here's an analogy to illustrate the difference:

List Approach: Imagine building a large brick wall. You gather all the bricks first and then start building the wall. This requires a lot of space to store all the bricks at once.
Generator Approach: Instead of gathering all the bricks first, you take each brick one by one and use it to build the wall. This is much more space-efficient as you only need space for the current brick being used.
Benefits of Generators:

Reduced Memory Usage: By iterating and yielding data gradually, generators significantly reduce the memory footprint of the application for handling large responses.
Incremental Response: When using generators, the client can start receiving data as soon as it's generated, improving user experience and perceived performance.
Efficient Error Handling: Generators can be used to handle errors gracefully and potentially terminate the loop early if necessary, optimizing resource usage.
Therefore, using generators is a preferred approach for building efficient API endpoints that handle potentially large datasets effectively.


