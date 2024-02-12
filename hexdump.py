#https://pypi.org/project/hexdump/#description
import hexdump
def generate_hexdump_dict(data):
    dump_str = hexdump.hexdump(data, result="return")
    print(dump_str)
    lines = dump_str.split('\n')[1:-1]  # Skip first and last line
    aa = {
        "message": {
            "hex": {},
            "content": ""
        }
    }   
    for idx, line in enumerate(lines):
        addr = f"{idx * 16:08X}"
        hexdump_part = line[10:58].strip()
        aa["message"]["hex"][addr] = hexdump_part
        aa["message"]["content"] += line[59:].strip()
    return aa

# Example usage:
data = bytes(range(256))
aa = generate_hexdump_dict(data)
print(aa)
