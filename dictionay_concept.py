from collections import defaultdict

D1 = {'1414': [1, 2], '1413': [3, 4]}
D2 = {1: 'app_id', '2': 'appid', 3: 'app_id', 4: 'app_id'}

output = defaultdict(list)

for port, ips in D1.items():
    for ip in ips:
        app_key = D2[ip]
        output[app_key].append((int(port), ip))

result = {}
for app_key, ports_ips in output.items():
    ports_ips.sort()
    prev_port = None
    for port, ip in ports_ips:
        if port != prev_port:
            result.setdefault(app_key, []).append({'port': port, 'ips': []})
            prev_port = port
        result[app_key][-1]['ips'].append(ip)

print(result)
