import time
from flask import request
from collections import deque

# A dictionary to store call history for each IP address
call_history = {}

# The rate_limited decorator takes two parameters: max_calls and time_frame
def rate_limited(max_calls=5, time_frame='1m'):
    # The actual decorator function that wraps around the route handler
    def decorator(handler):
        # The wrapper function that performs rate limiting
        def wrapper(*args, **kwargs):
            # Get the IP address of the requester from the Flask request object
            ip_address = request.remote_addr

            # If this is the first request from this IP, create a deque for call history
            if ip_address not in call_history:
                call_history[ip_address] = deque()

            # Retrieve the call history deque for the current IP
            queue = call_history[ip_address]
            
            # Get the current time
            current_time = time.time()

            # Extract the unit and value from the time_frame parameter
            unit = time_frame[-1].lower()
            value = int(time_frame[:-1])

            # Convert time_frame to seconds based on the unit
            if unit == 's':
                time_frame_seconds = value
            elif unit == 'm':
                time_frame_seconds = value * 60
            elif unit == 'h':
                time_frame_seconds = value * 3600
            elif unit == 'd':
                time_frame_seconds = value * 86400
            else:
                # Raise a ValueError if an invalid unit is provided
                raise ValueError("Invalid time unit. Use 's', 'm', 'h', or 'd'.")

            # Remove calls from the history that are older than the specified time frame
            while len(queue) > 0 and current_time - queue[0] > time_frame_seconds:
                queue.popleft()

            # If the number of calls within the time frame exceeds max_calls, return an error
            if len(queue) >= max_calls:
                time_passed = current_time - queue[0]
                time_to_wait = int(time_frame_seconds - time_passed)
                error_message = f'Rate limit exceeded. Please try again in {time_to_wait} seconds.'
                return error_message, 429

            # Add the current time to the call history
            queue.append(current_time)

            # Call the original handler function
            return handler(*args, **kwargs)

        # Return the wrapper function
        return wrapper

    # Return the decorator function
    return decorator
