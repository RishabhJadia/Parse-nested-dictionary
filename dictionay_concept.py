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

----------------------------------------------------------------------------------------

D1 = {'1414': [1, 2], '1413': [3, 4]}
D2 = {1: 'app_id', '2': 'appid', 3: 'app_id', 4: 'app_id'}

output = {}
for key, values in D1.items():
    for value in values:
        app_key = D2.get(value)
        if app_key:
            if app_key not in output:
                output[app_key] = []
            existing_port = next((d for d in output[app_key] if d['port'] == int(key)), None)
            if existing_port:
                existing_port['ips'].append(value)
            else:
                output[app_key].append({'port': int(key), 'ips': [value]})

print(output)
