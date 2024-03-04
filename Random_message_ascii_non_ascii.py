import random
import string

def generate_message(size_kb):
    # Define the ratio of ASCII to non-ASCII characters
    ascii_ratio = 0.9

    # Calculate the number of ASCII and non-ASCII characters
    ascii_size = int(size_kb * 1024 * ascii_ratio)
    non_ascii_size = int(size_kb * 1024 * (1 - ascii_ratio))

    # Generate ASCII characters
    ascii_characters = string.ascii_letters + string.digits + string.punctuation
    ascii_message = ''.join(random.choice(ascii_characters) for _ in range(ascii_size))

    # Generate non-ASCII characters
    non_ascii_message = ''.join(chr(random.randint(128, 255)) for _ in range(non_ascii_size))

    # Combine ASCII and non-ASCII messages
    combined_message = ascii_message + non_ascii_message

    return combined_message.encode('utf-8')

# Generate a 5 KB message
message = generate_message(5)
print("Length of the generated message:", len(message), "bytes")
