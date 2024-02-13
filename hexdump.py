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
-----------------------------------------------------------------------------------------------------
def generate_memory_representation(data):
    addr = 0
    memory_dict = {'message': {'hex': {}, 'content': ''}}
    while addr < len(data):
        breakpoint
        hex_part = ''.join(f'{x:02X}' for x in data[addr:addr+4])
        memory_dict['message']['hex'][f'{addr:08X}'] = hex_part
        ascii_part = ''.join(chr(x) if 32 <= x < 127 else '.' for x in data[addr:addr+4])
        memory_dict['message']['content'] += ascii_part
        addr += 4
    return memory_dict

# Example usage:
#data = bytes(range(256))
data = b'Mary had a little lamb, Its fleece was white as snow, And every where that Mary went The lamb was sure to go; He followed her to school one day, That was against the rule, It made the children laugh and play, To see a lamb at school.'
memory_dict = generate_memory_representation(data)
print(memory_dict)

{'message': {'hex': {'00000000': '10111213', '00000004': '14151617', '00000008': '18191A1B', "0000000C": 1C 1D 1E 1F'}, 'content': '................!"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{}
